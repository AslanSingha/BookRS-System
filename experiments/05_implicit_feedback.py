"""
Experiment 5: Implicit Feedback with Confidence Weighting
Compares 3 ALS configurations:
  A) Rating only (baseline from Exp 3)
  B) Rating + is_reviewed confidence
  C) Rating magnitude + is_reviewed confidence (full implicit)
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
top_users = user_counts[user_counts >= 10].index
interactions = interactions[interactions["user_id"].isin(top_users)].copy()
print(f"Books: 2,000 | Users: {len(top_users):,} | Interactions: {len(interactions):,}")
print(f"Reviewed: {interactions['is_reviewed'].sum():,} ({interactions['is_reviewed'].mean()*100:.1f}%)")

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

# Train/test split
test_rows  = interactions.groupby("u_idx").sample(frac=0.2, random_state=42)
train_rows = interactions.drop(test_rows.index).copy()
train_rows = train_rows[(train_rows["u_idx"] < n_users) & (train_rows["b_idx"] < n_books)]
test_rows  = test_rows[(test_rows["u_idx"] < n_users) & (test_rows["b_idx"] < n_books)]
print(f"Train: {len(train_rows):,} | Test: {len(test_rows):,}")

test_lookup  = test_rows.groupby("u_idx")["b_idx"].apply(set).to_dict()
train_lookup = train_rows.groupby("u_idx")["b_idx"].apply(list).to_dict()
eval_users   = list(test_lookup.keys())[:2000]

def evaluate(user_factors, book_factors, eval_users, test_lookup, train_lookup):
    precisions, recalls, mrrs = [], [], []
    for u_idx in eval_users:
        true_items = test_lookup.get(u_idx, set())
        if not true_items: continue
        scores = user_factors[u_idx] @ book_factors.T
        seen = train_lookup.get(u_idx, [])
        scores[seen] = -np.inf
        top10 = np.argsort(scores)[-10:][::-1]
        hits  = [1 if b in true_items else 0 for b in top10]
        precisions.append(sum(hits) / 10)
        recalls.append(sum(hits) / len(true_items))
        mrrs.append(next((1/(j+1) for j, h in enumerate(hits) if h), 0))
    return round(np.mean(precisions),4), round(np.mean(recalls),4), round(np.mean(mrrs),4)

def train_and_eval(confidence_values, label):
    matrix = sp.csr_matrix(
        (confidence_values,
         (train_rows["u_idx"].values, train_rows["b_idx"].values)),
        shape=(n_users, n_books)
    )
    als = implicit.als.AlternatingLeastSquares(
        factors=128, regularization=0.1, iterations=10, use_gpu=False
    )
    als.fit(matrix.T.tocsr())
    book_factors = als.user_factors
    user_factors = als.item_factors
    p, r, mrr = evaluate(user_factors, book_factors, eval_users, test_lookup, train_lookup)
    print(f"  {label:<45} | P@10={p:.4f} | R@10={r:.4f} | MRR={mrr:.4f}")
    return {"method": label, "precision_at_10": p, "recall_at_10": r, "mrr": mrr}

print("\n=== Experiment 5: Implicit Feedback Comparison ===")
results = []

# Config A: Rating only (baseline)
conf_a = train_rows["rating"].astype(float).values
results.append(train_and_eval(conf_a, "A) Rating only (baseline)"))

# Config B: Rating + is_reviewed bonus
conf_b = train_rows["rating"].astype(float).values + \
         train_rows["is_reviewed"].astype(float).values * 3.0
results.append(train_and_eval(conf_b, "B) Rating + is_reviewed (+3.0)"))

# Config C: Confidence weighted (full implicit)
# confidence = 1 + rating*2 + is_reviewed*3
conf_c = (1.0 +
          train_rows["rating"].astype(float).values * 2.0 +
          train_rows["is_reviewed"].astype(float).values * 3.0)
results.append(train_and_eval(conf_c, "C) Confidence: 1 + rating×2 + reviewed×3"))

# Config D: is_reviewed only (pure implicit, no explicit rating)
conf_d = (1.0 + train_rows["is_reviewed"].astype(float).values * 5.0)
results.append(train_and_eval(conf_d, "D) Pure implicit: 1 + reviewed×5"))

results_df = pd.DataFrame(results)
best = results_df.loc[results_df["precision_at_10"].idxmax()]
print(f"\n=== BEST CONFIG: {best['method']} ===")
print(f"    P@10={best['precision_at_10']} | R@10={best['recall_at_10']} | MRR={best['mrr']}")

results_df.to_csv(OUTPUT_DIR / "implicit_feedback.csv", index=False)
print("\nSaved! === DONE ===")
