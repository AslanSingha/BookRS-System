"""
Experiment 3c: Add ALS to CF comparison (same 10K users, same eval setup)
"""
import pandas as pd
import numpy as np
from pathlib import Path
import implicit
import scipy.sparse as sp

DATA_DIR   = Path.home() / "projects/BookRS-DataPrep/outputs"
OUTPUT_DIR = Path.home() / "projects/BookRS/experiments/results"

print("=== Loading data (same setup as 03b) ===")
interactions = pd.read_parquet(DATA_DIR / "bookrs_ucsd_interactions.parquet")
top_books = interactions["book_id"].value_counts().head(2000).index
interactions = interactions[interactions["book_id"].isin(top_books)]
user_counts = interactions["user_id"].value_counts()
top_users = user_counts[user_counts >= 10].head(10000).index
interactions = interactions[interactions["user_id"].isin(top_users)].copy()
print(f"Books: 2,000 | Users: {len(top_users):,} | Interactions: {len(interactions):,}")

# Build indices
user_ids = interactions["user_id"].unique()
book_ids = interactions["book_id"].unique()
user2idx = {u: i for i, u in enumerate(user_ids)}
book2idx = {b: i for i, b in enumerate(book_ids)}
n_users = len(user_ids)
n_books = len(book_ids)

interactions["u_idx"] = interactions["user_id"].map(user2idx).astype(int)
interactions["b_idx"] = interactions["book_id"].map(book2idx).astype(int)
interactions = interactions[
    (interactions["u_idx"] < n_users) &
    (interactions["b_idx"] < n_books)
].copy()

# Train/test split (same as 03b: 80/20)
test_rows  = interactions.groupby("u_idx").sample(frac=0.2, random_state=42)
train_rows = interactions.drop(test_rows.index).copy()
train_rows = train_rows[(train_rows["u_idx"] < n_users) & (train_rows["b_idx"] < n_books)]
test_rows  = test_rows[(test_rows["u_idx"] < n_users) & (test_rows["b_idx"] < n_books)]
print(f"Train: {len(train_rows):,} | Test: {len(test_rows):,}")

# Train ALS
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
book_factors = als.user_factors  # (n_books, 128)
user_factors = als.item_factors  # (n_users, 128)
print("ALS trained!")

# Evaluate
test_lookup  = test_rows.groupby("u_idx")["b_idx"].apply(set).to_dict()
train_lookup = train_rows.groupby("u_idx")["b_idx"].apply(list).to_dict()
eval_users   = list(test_lookup.keys())[:2000]

precisions, recalls, mrrs = [], [], []
for u_idx in eval_users:
    true_items = test_lookup.get(u_idx, set())
    if not true_items:
        continue
    scores = user_factors[u_idx] @ book_factors.T
    seen = train_lookup.get(u_idx, [])
    scores[seen] = -np.inf
    top10 = np.argsort(scores)[-10:][::-1]
    hits  = [1 if b in true_items else 0 for b in top10]
    precisions.append(sum(hits) / 10)
    recalls.append(sum(hits) / len(true_items))
    mrrs.append(next((1/(j+1) for j, h in enumerate(hits) if h), 0))

p  = round(np.mean(precisions), 4)
r  = round(np.mean(recalls), 4)
mrr = round(np.mean(mrrs), 4)
print(f"\nALS Results: P@10={p} | R@10={r} | MRR={mrr}")

# Load existing results and add ALS
existing = pd.read_csv(OUTPUT_DIR / "cf_comparison.csv")
als_row = pd.DataFrame([{"model": "ALS", "precision_at_10": p,
                          "recall_at_10": r, "mrr": mrr}])
final = pd.concat([existing, als_row]).sort_values("precision_at_10", ascending=False)
final.to_csv(OUTPUT_DIR / "cf_comparison.csv", index=False)

print("\n=== FINAL CF COMPARISON ===")
print(final.to_string(index=False))
print("\nSaved! === DONE ===")
