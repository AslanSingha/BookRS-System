"""
BookRS — SBERT Book Encoding Script
Encodes all 883,468 books using all-MiniLM-L6-v2 into 384-dim vectors.
Output: models/embeddings.npy  (~1.9 GB, float32, L2-normalized)

Runtime: ~60 minutes on NVIDIA RTX 3050 (GPU)
         ~3-4 hours on CPU only
"""

import os
import time
import numpy as np
import psycopg2
import pandas as pd
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)s  %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────
DB_CONFIG = {
    'host':     '127.0.0.1',
    'port':     5432,
    'database': 'bookrs_db',
    'user':     'bookrs',
    'password': 'bookrs123',
}

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_NAME  = 'all-MiniLM-L6-v2'   # 384 dimensions — optimal speed/quality
BATCH_SIZE  = 512                    # increase if you have more VRAM
DEVICE      = 'cuda'                 # 'cuda' for GPU, 'cpu' for CPU only

# ── Load books from PostgreSQL ─────────────────────────────────
def load_books():
    log.info("Connecting to PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)

    log.info("Loading books...")
    query = """
        SELECT book_id, title, authors, description
        FROM books
        ORDER BY book_id
    """
    df = pd.read_sql(query, conn)
    conn.close()

    log.info(f"Loaded {len(df):,} books")
    return df

# ── Build text for encoding ────────────────────────────────────
def build_texts(df):
    """Concatenate title + authors + description for each book."""
    texts = []
    for _, row in df.iterrows():
        title   = str(row['title']       or '').strip()
        authors = str(row['authors']     or '').strip()
        desc    = str(row['description'] or '').strip()

        # Format: "Title. By Author. Description."
        parts = []
        if title:   parts.append(title)
        if authors: parts.append(f"By {authors}")
        if desc:    parts.append(desc[:500])  # cap description length

        texts.append('. '.join(parts) if parts else title)

    log.info(f"Built {len(texts):,} text inputs")
    log.info(f"Sample: {texts[0][:100]}...")
    return texts

# ── Encode with SBERT ──────────────────────────────────────────
def encode_books(texts):
    log.info(f"Loading SBERT model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME, device=DEVICE)
    log.info(f"Model loaded on device: {DEVICE}")
    log.info(f"Encoding {len(texts):,} books "
             f"(batch_size={BATCH_SIZE})...")

    t0 = time.time()
    embeddings = model.encode(
        texts,
        batch_size          = BATCH_SIZE,
        show_progress_bar   = True,
        normalize_embeddings= True,   # L2 normalize → cosine = dot product
        convert_to_numpy    = True,
    )
    elapsed = time.time() - t0

    log.info(f"Encoding complete in {elapsed/60:.1f} minutes")
    log.info(f"Embeddings shape: {embeddings.shape}")
    log.info(f"dtype: {embeddings.dtype}")

    return embeddings

# ── Save embeddings ────────────────────────────────────────────
def save_embeddings(embeddings, df):
    out_path = os.path.join(MODELS_DIR, 'embeddings.npy')
    np.save(out_path, embeddings)

    # Also save book_id → index mapping
    idx_path = os.path.join(MODELS_DIR, 'book2idx_sbert.npy')
    book2idx = {str(row['book_id']): i for i, row in df.iterrows()}
    np.save(idx_path, book2idx)

    size_gb = os.path.getsize(out_path) / 1e9
    log.info("")
    log.info("=" * 55)
    log.info("ENCODING COMPLETE")
    log.info("=" * 55)
    log.info(f"  Books encoded:  {embeddings.shape[0]:>10,}")
    log.info(f"  Dimensions:     {embeddings.shape[1]:>10}")
    log.info(f"  File size:      {size_gb:>9.2f} GB")
    log.info(f"  Saved to:       {out_path}")
    log.info("=" * 55)

# ── Main ──────────────────────────────────────────────────────
if __name__ == '__main__':
    log.info("BookRS SBERT Encoding Script")
    log.info(f"Model:  {MODEL_NAME}")
    log.info(f"Device: {DEVICE}")
    log.info(f"Output: {os.path.abspath(MODELS_DIR)}")
    log.info("")

    df         = load_books()
    texts      = build_texts(df)
    embeddings = encode_books(texts)
    save_embeddings(embeddings, df)
