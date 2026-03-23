"""
Experiment 3b: CF Model Comparison — All 5 models, 10K users (fair comparison)
"""
import pandas as pd
from pathlib import Path
import cornac
from cornac.eval_methods import RatioSplit
from cornac.metrics import Precision, Recall, MRR

DATA_DIR   = Path.home() / "projects/BookRS-DataPrep/outputs"
OUTPUT_DIR = Path.home() / "projects/BookRS/experiments/results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=== Loading data ===")
interactions = pd.read_parquet(DATA_DIR / "bookrs_ucsd_interactions.parquet")
top_books = interactions["book_id"].value_counts().head(2000).index
interactions = interactions[interactions["book_id"].isin(top_books)]
user_counts = interactions["user_id"].value_counts()
top_users = user_counts[user_counts >= 10].head(10000).index
interactions = interactions[interactions["user_id"].isin(top_users)].copy()
print(f"Books: 2,000 | Users: {len(top_users):,} | Interactions: {len(interactions):,}")

data = list(zip(
    interactions["user_id"].astype(str),
    interactions["book_id"].astype(str),
    interactions["rating"].astype(float)
))

eval_method = RatioSplit(
    data=data, test_size=0.2, rating_threshold=1.0, seed=42, verbose=False
)
metrics = [Precision(k=10), Recall(k=10), MRR()]

models = [
    cornac.models.MF(k=128, max_iter=10, learning_rate=0.01,
                     lambda_reg=0.1, seed=42, name="MF (SVD-style)"),
    cornac.models.BPR(k=64, max_iter=100, learning_rate=0.01,
                      lambda_reg=0.01, seed=42, name="BPR"),
    cornac.models.NMF(k=64, max_iter=50, seed=42, name="NMF"),
    cornac.models.ItemKNN(k=50, similarity="cosine", name="Item-KNN"),
    cornac.models.UserKNN(k=50, similarity="cosine", name="User-KNN"),
]

print("\n=== Running CF Model Comparison (5 models, 10K users) ===")
exp = cornac.Experiment(
    eval_method=eval_method,
    models=models,
    metrics=metrics,
    user_based=True,
    verbose=True,
)
exp.run()

# Save results manually from printed table
print("\n=== Saving Results ===")
results = [
    {'model': 'MF (SVD-style)', 'precision_at_10': None, 'recall_at_10': None, 'mrr': None},
    {'model': 'BPR',            'precision_at_10': None, 'recall_at_10': None, 'mrr': None},
    {'model': 'NMF',            'precision_at_10': None, 'recall_at_10': None, 'mrr': None},
    {'model': 'Item-KNN',       'precision_at_10': None, 'recall_at_10': None, 'mrr': None},
    {'model': 'User-KNN',       'precision_at_10': None, 'recall_at_10': None, 'mrr': None},
]
print("Results will be printed in the table above — paste them here after!")
print("=== DONE ===")
