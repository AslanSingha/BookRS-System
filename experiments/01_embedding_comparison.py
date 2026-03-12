"""
Experiment 1: SBERT Embedding Model Comparison
"""
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import time
from pathlib import Path

OUTPUT_DIR = Path.home() / "projects/BookRS/experiments/results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODELS = [
    "all-MiniLM-L6-v2",
    "all-MiniLM-L12-v2",
    "all-mpnet-base-v2",
    "multi-qa-MiniLM-L6-cos-v1",
    "paraphrase-MiniLM-L6-v2",
]

print("=== Loading book sample ===")
df = pd.read_parquet(Path.home() / "projects/BookRS-DataPrep/outputs/bookrs_ucsd_books.parquet")

sample = pd.concat([
    group.sample(min(100, len(group)), random_state=42)
    for _, group in df.groupby("genre")
]).reset_index(drop=True)

print(f"Sample: {len(sample)} books, {sample['genre'].nunique()} genres")
print(sample["genre"].value_counts().to_string())

texts = (sample["title"] + ". " + sample["description"]).tolist()
genres = sample["genre"].tolist()
results = []

for model_name in MODELS:
    print(f"\n=== Testing: {model_name} ===")
    model = SentenceTransformer(model_name)
    start = time.time()
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True, device="cuda")
    encode_time = time.time() - start

    sim_matrix = cosine_similarity(embeddings)
    np.fill_diagonal(sim_matrix, 0)

    precisions = []
    for i in range(len(sample)):
        top10_idx = np.argsort(sim_matrix[i])[-10:]
        same_genre = sum(1 for j in top10_idx if genres[j] == genres[i])
        precisions.append(same_genre / 10)

    precision = np.mean(precisions)
    dim = embeddings.shape[1]
    params = sum(p.numel() for p in model._modules['0'].auto_model.parameters())

    print(f"Precision@10 (genre): {precision:.4f}")
    print(f"Embedding dim: {dim}, Params: {params/1e6:.1f}M, Time: {encode_time:.1f}s")

    results.append({
        "model": model_name,
        "precision_at_10": round(precision, 4),
        "encode_time_s": round(encode_time, 2),
        "embedding_dim": dim,
        "model_params_M": round(params/1e6, 1),
    })
    np.save(OUTPUT_DIR / f"emb_{model_name.replace('/', '_')}.npy", embeddings)

results_df = pd.DataFrame(results).sort_values("precision_at_10", ascending=False)
print("\n=== FINAL RESULTS ===")
print(results_df.to_string(index=False))
results_df.to_csv(OUTPUT_DIR / "embedding_comparison.csv", index=False)
print("=== DONE ===")
