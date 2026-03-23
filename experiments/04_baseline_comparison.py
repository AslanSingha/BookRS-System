"""
Experiment 4: Baseline Comparison
Compares BookRS hybrid against simpler baselines.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
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

interactions["u_idx"] = interactions["user_id"].map(user2idx).astype(int)
interactions["b_idx"] = interactions["book_id"].map(book2idx).astype(int)
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

test_lookup  = test_rows.groupby("u_idx")["b_idx"].apply(set).to_dict()
train_lookup = train_rows.groupby("u_idx")["b_idx"].apply(list).to_dict()
eval_users   = list(test_lookup.keys())[:200]

# ── Train ALS (best config from Exp 3) ───────────────────────
print("\n=== Training ALS (factors=128, reg=0.1, iters=10) ===")
train_matrix = sp.csr_matrix(
    (train_rows["rating"].values,
     (train_rows["u_idx"].values, train_rows["b_idx"].values)),
    shape=(n_users, n_books)
)
als = implicit.als.AlternatingLeastSquares(
    factors=128, regularization=0.1, iterations=10, use_gpu=False
)
als.fit(train_matrix.T.tocsr())
book_factors = als.user_factors   # (n_books, 128)
user_factors = als.item_factors   # (n_users, 128)
print("ALS trained!")

# ── Compute SBERT embeddings ──────────────────────────────────
print("\n=== Computing SBERT embeddings ===")
model = SentenceTransformer("all-MiniLM-L6-v2")
texts = (books_sample["title"] + ". " + books_sample["description"]).tolist()
embeddings = model.encode(texts, batch_size=64, show_progress_bar=True,
                          device="cpu", normalize_embeddings=True).astype(np.float32)

# ── Build BM25 ────────────────────────────────────────────────
print("\n=== Building BM25 index ===")
tokenized = [t.lower().split() for t in texts]
bm25 = BM25Okapi(tokenized)
print("BM25 ready!")

# ── Popularity scores ─────────────────────────────────────────
popularity = np.array(train_rows.groupby("b_idx")["rating"].count().reindex(
    range(n_books), fill_value=0).values, dtype=np.float32)

# ── Evaluation function ───────────────────────────────────────
def evaluate(score_fn, eval_users, test_lookup, train_lookup, label):
    precisions, recalls, mrrs = [], [], []
    for u_idx in eval_users:
        true_items = test_lookup.get(u_idx, set())
        if not true_items:
            continue
        scores = score_fn(u_idx).copy()
        seen = train_lookup.get(u_idx, [])
        scores[seen] = -np.inf
        top10 = np.argsort(scores)[-10:][::-1]
        hits  = [1 if b in true_items else 0 for b in top10]
        precisions.append(sum(hits) / 10)
        recalls.append(sum(hits) / len(true_items))
        mrrs.append(next((1/(j+1) for j, h in enumerate(hits) if h), 0))
    p, r, m = np.mean(precisions), np.mean(recalls), np.mean(mrrs)
    print(f"  {label:<30} | P@10={p:.4f} | R@10={r:.4f} | MRR={m:.4f}")
    return {"method": label, "precision_at_10": round(p,4),
            "recall_at_10": round(r,4), "mrr": round(m,4)}

print("\n=== Baseline Comparison ===")
results = []

# 1. Popularity baseline
results.append(evaluate(
    lambda u: popularity.copy(),
    eval_users, test_lookup, train_lookup, "Popularity Baseline"
))

# 2. BM25 — use user's top rated book as query
results.append(evaluate(
    lambda u: np.array(bm25.get_scores(
        texts[train_lookup[u][0]].lower().split()
        if train_lookup.get(u) else ["book"]
    ), dtype=np.float32),
    eval_users, test_lookup, train_lookup, "BM25 (keyword search)"
))

# 3. Pure ALS
results.append(evaluate(
    lambda u: user_factors[u] @ book_factors.T,
    eval_users, test_lookup, train_lookup, "Pure ALS (CF only)"
))

# 4. BookRS Hybrid (alpha=0.1)
def hybrid_score(u_idx):
    cf = user_factors[u_idx] @ book_factors.T
    train_items = train_lookup.get(u_idx, [])
    if train_items:
        profile = embeddings[train_items].mean(axis=0)
        content = profile @ embeddings.T
    else:
        content = np.zeros(n_books)
    def norm(x):
        mn, mx = x.min(), x.max()
        return (x - mn) / (mx - mn + 1e-9)
    return 0.1 * norm(content) + 0.9 * norm(cf)

results.append(evaluate(
    hybrid_score,
    eval_users, test_lookup, train_lookup, "BookRS Hybrid (α=0.1)"
))

results_df = pd.DataFrame(results)
print(f"\n{'='*60}")
print(results_df.to_string(index=False))
results_df.to_csv(OUTPUT_DIR / "baseline_comparison.csv", index=False)
print("\nSaved! === DONE ===")
