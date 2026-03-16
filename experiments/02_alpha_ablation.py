"""
Experiment 2: Alpha Ablation Study (Memory-Safe Version)
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import implicit
import scipy.sparse as sp

DATA_DIR   = Path.home() / "projects/BookRS-DataPrep/outputs"
OUTPUT_DIR = Path.home() / "projects/BookRS/experiments/results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=== Loading data ===")
books = pd.read_parquet(DATA_DIR / "bookrs_ucsd_books.parquet")
interactions = pd.read_parquet(DATA_DIR / "bookrs_ucsd_interactions.parquet")

top_books = interactions["book_id"].value_counts().head(2000).index
interactions = interactions[interactions["book_id"].isin(top_books)]
books_sample = books[books["book_id"].isin(top_books)].reset_index(drop=True)

user_counts = interactions["user_id"].value_counts()
active_users = user_counts[user_counts >= 10].index
interactions = interactions[interactions["user_id"].isin(active_users)].copy()
print(f"Books: {len(books_sample):,} | Users: {len(active_users):,} | Interactions: {len(interactions):,}")

print("=== Building indices ===")
user_ids = interactions["user_id"].unique()
book_ids = books_sample["book_id"].values
user2idx = {u: i for i, u in enumerate(user_ids)}
book2idx = {b: i for i, b in enumerate(book_ids)}
n_users  = len(user_ids)
n_books  = len(book_ids)

interactions["u_idx"] = interactions["user_id"].map(user2idx)
interactions["b_idx"] = interactions["book_id"].map(book2idx)
interactions = interactions.dropna(subset=["u_idx","b_idx"]).copy()
interactions["u_idx"] = interactions["u_idx"].astype(int)
interactions["b_idx"] = interactions["b_idx"].astype(int)
interactions = interactions[
    (interactions["u_idx"] < n_users) &
    (interactions["b_idx"] < n_books)
].copy()

print("=== Train/test split ===")
test_rows  = interactions.groupby("u_idx").sample(frac=0.2, random_state=42)
train_rows = interactions.drop(test_rows.index).copy()
train_rows = train_rows[(train_rows["u_idx"] < n_users) & (train_rows["b_idx"] < n_books)]
test_rows  = test_rows[(test_rows["u_idx"] < n_users) & (test_rows["b_idx"] < n_books)]
print(f"Train: {len(train_rows):,} | Test: {len(test_rows):,}")

print("=== Training ALS ===")
train_matrix = sp.csr_matrix(
    (train_rows["rating"].values,
     (train_rows["u_idx"].values, train_rows["b_idx"].values)),
    shape=(n_users, n_books)
)
als = implicit.als.AlternatingLeastSquares(
    factors=64, regularization=0.1, iterations=20, use_gpu=False
)
als.fit(train_matrix.T.tocsr())
# ALS fit on transposed matrix: user_factors=(n_books,64), item_factors=(n_users,64)
book_factors = als.user_factors   # (n_books, 64)
user_factors = als.item_factors   # (n_users, 64)
print("ALS trained!")

print("=== Computing embeddings ===")
model = SentenceTransformer("all-MiniLM-L6-v2")
texts = (books_sample["title"] + ". " + books_sample["description"]).tolist()
embeddings = model.encode(texts, batch_size=64, show_progress_bar=True,
                          device="cpu", normalize_embeddings=True).astype(np.float32)
print(f"Embeddings: {embeddings.shape}")

# Build train lookup
train_lookup = train_rows.groupby("u_idx")["b_idx"].apply(list).to_dict()
test_lookup  = test_rows.groupby("u_idx")["b_idx"].apply(set).to_dict()

# Use only 200 eval users (memory safe)
eval_users = list(test_lookup.keys())[:200]

print("\n=== Alpha Ablation ===")
alphas  = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
results = []

for alpha in alphas:
    precisions, recalls, mrrs = [], [], []

    for u_idx in eval_users:
        true_items = test_lookup.get(u_idx, set())
        if not true_items:
            continue

        # CF score for this user only (n_books,)
        cf = user_factors[u_idx] @ book_factors.T

        # Content score: mean embedding of train items
        train_items = train_lookup.get(u_idx, [])
        if train_items:
            profile = embeddings[train_items].mean(axis=0)
            content = profile @ embeddings.T
        else:
            content = np.zeros(n_books, dtype=np.float32)

        # Normalize to [0,1]
        def norm(x):
            mn, mx = x.min(), x.max()
            return (x - mn) / (mx - mn + 1e-9)

        cf      = norm(cf)
        content = norm(content)
        hybrid  = alpha * content + (1 - alpha) * cf

        # Mask seen items
        for b in train_items:
            hybrid[b] = -1

        top10 = np.argsort(hybrid)[-10:][::-1]
        hits  = [1 if b in true_items else 0 for b in top10]
        precisions.append(sum(hits) / 10)
        recalls.append(sum(hits) / len(true_items))
        mrrs.append(next((1/(j+1) for j, h in enumerate(hits) if h), 0))

    results.append({
        "alpha":           alpha,
        "precision_at_10": round(np.mean(precisions), 4),
        "recall_at_10":    round(np.mean(recalls), 4),
        "mrr":             round(np.mean(mrrs), 4),
    })
    print(f"  α={alpha:.1f} | P@10={results[-1]['precision_at_10']:.4f} | "
          f"R@10={results[-1]['recall_at_10']:.4f} | MRR={results[-1]['mrr']:.4f}")

results_df = pd.DataFrame(results)
best = results_df.loc[results_df["precision_at_10"].idxmax()]
print(f"\n=== BEST ALPHA: {best['alpha']} (P@10={best['precision_at_10']}) ===")
results_df.to_csv(OUTPUT_DIR / "alpha_ablation.csv", index=False)
print("Saved! === DONE ===")
