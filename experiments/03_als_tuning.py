"""
Experiment 3: ALS Hyperparameter Tuning
Grid search over factors, regularization, iterations
"""
import pandas as pd
import numpy as np
from pathlib import Path
import implicit
import scipy.sparse as sp

DATA_DIR   = Path.home() / "projects/BookRS-DataPrep/outputs"
OUTPUT_DIR = Path.home() / "projects/BookRS/experiments/results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=== Loading data ===")
interactions = pd.read_parquet(DATA_DIR / "bookrs_ucsd_interactions.parquet")

top_books = interactions["book_id"].value_counts().head(2000).index
interactions = interactions[interactions["book_id"].isin(top_books)]

user_counts = interactions["user_id"].value_counts()
active_users = user_counts[user_counts >= 10].index
interactions = interactions[interactions["user_id"].isin(active_users)].copy()
print(f"Users: {len(active_users):,} | Interactions: {len(interactions):,}")

print("=== Building indices ===")
user_ids = interactions["user_id"].unique()
book_ids = interactions["book_id"].unique()
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

train_matrix = sp.csr_matrix(
    (train_rows["rating"].values,
     (train_rows["u_idx"].values, train_rows["b_idx"].values)),
    shape=(n_users, n_books)
)

test_lookup  = test_rows.groupby("u_idx")["b_idx"].apply(set).to_dict()
train_lookup = train_rows.groupby("u_idx")["b_idx"].apply(list).to_dict()
eval_users   = list(test_lookup.keys())[:200]

def evaluate_als(user_factors, book_factors, eval_users, test_lookup, train_lookup, n_books):
    precisions, recalls, mrrs = [], [], []
    for u_idx in eval_users:
        true_items = test_lookup.get(u_idx, set())
        if not true_items:
            continue
        scores = user_factors[u_idx] @ book_factors.T
        seen   = train_lookup.get(u_idx, [])
        scores[seen] = -np.inf
        top10  = np.argsort(scores)[-10:][::-1]
        hits   = [1 if b in true_items else 0 for b in top10]
        precisions.append(sum(hits) / 10)
        recalls.append(sum(hits) / len(true_items))
        mrrs.append(next((1/(j+1) for j, h in enumerate(hits) if h), 0))
    return np.mean(precisions), np.mean(recalls), np.mean(mrrs)

# Grid search
factors_list  = [16, 32, 64, 128]
reg_list      = [0.01, 0.1, 0.5]
iter_list     = [10, 20, 50]

results = []
total = len(factors_list) * len(reg_list) * len(iter_list)
count = 0

print(f"\n=== Grid Search ({total} combinations) ===")
for factors in factors_list:
    for reg in reg_list:
        for iters in iter_list:
            count += 1
            als = implicit.als.AlternatingLeastSquares(
                factors=factors, regularization=reg,
                iterations=iters, use_gpu=False
            )
            als.fit(train_matrix.T.tocsr(), show_progress=False)
            # Factors are swapped (fit on transposed matrix)
            book_factors = als.user_factors  # (n_books, 64)
            user_factors = als.item_factors  # (n_users, 64)

            p, r, mrr = evaluate_als(
                user_factors, book_factors,
                eval_users, test_lookup, train_lookup, n_books
            )
            results.append({
                "factors": factors, "regularization": reg,
                "iterations": iters,
                "precision_at_10": round(p, 4),
                "recall_at_10":    round(r, 4),
                "mrr":             round(mrr, 4),
            })
            print(f"  [{count:>2}/{total}] factors={factors:>3} reg={reg} iters={iters:>2} "
                  f"| P@10={p:.4f} R@10={r:.4f} MRR={mrr:.4f}")

results_df = pd.DataFrame(results).sort_values("precision_at_10", ascending=False)
best = results_df.iloc[0]
print(f"\n=== BEST CONFIG ===")
print(f"  factors={best['factors']} | reg={best['regularization']} | iters={best['iterations']}")
print(f"  P@10={best['precision_at_10']} | R@10={best['recall_at_10']} | MRR={best['mrr']}")

results_df.to_csv(OUTPUT_DIR / "als_tuning.csv", index=False)
print("Saved! === DONE ===")
