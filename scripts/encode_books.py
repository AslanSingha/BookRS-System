"""
BookRS — SBERT Book Encoding Script (Fast Version)
Encodes all 883,468 books using all-MiniLM-L6-v2 into 384-dim vectors.
Output: models/embeddings.npy  (~1.9 GB, float32, L2-normalized)

Optimizations:
  - Vectorized text building (no iterrows)
  - Batch size 512 for RTX 3050 4GB
  - Mixed precision disabled (SBERT handles internally)
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

DB_CONFIG = {
    'host':     '127.0.0.1',
    'port':     5432,
    'database': 'bookrs_db',
    'user':     'bookrs',
    'password': 'bookrs123',
}

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_NAME = 'all-MiniLM-L6-v2'
BATCH_SIZE = 512
DEVICE     = 'cuda'

def load_books():
    log.info("Loading books from PostgreSQL ORDER BY book_id...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()
    cur.execute("""
        SELECT book_id, title, authors, description
        FROM books
        ORDER BY book_id::bigint
    """)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    df = pd.DataFrame(rows, columns=cols)
    log.info(f"Loaded {len(df):,} books")
    return df

def build_texts(df):
    """Vectorized text building — much faster than iterrows."""
    title   = df['title'].fillna('').str.strip()
    authors = df['authors'].fillna('').str.strip()
    desc    = df['description'].fillna('').str.slice(0, 500).str.strip()

    texts = (title + '. By ' + authors + '. ' + desc).str.strip('. ').tolist()
    log.info(f"Built {len(texts):,} texts")
    log.info(f"Sample: {texts[0][:120]}")
    return texts

def encode_books(texts):
    log.info(f"Loading SBERT: {MODEL_NAME} on {DEVICE}")
    model = SentenceTransformer(MODEL_NAME, device=DEVICE)

    log.info(f"Encoding {len(texts):,} books (batch={BATCH_SIZE})...")
    t0 = time.time()

    embeddings = model.encode(
        texts,
        batch_size           = BATCH_SIZE,
        show_progress_bar    = True,
        normalize_embeddings = True,
        convert_to_numpy     = True,
    )

    elapsed = time.time() - t0
    log.info(f"Done in {elapsed/60:.1f} minutes")
    log.info(f"Shape: {embeddings.shape}  dtype: {embeddings.dtype}")
    return embeddings.astype(np.float32)

def save(embeddings, df):
    out = os.path.join(MODELS_DIR, 'embeddings.npy')
    np.save(out, embeddings)
    log.info(f"Saved embeddings: {out}  ({os.path.getsize(out)/1e9:.2f} GB)")

    # Save book_id → index mapping
    idx_path = os.path.join(MODELS_DIR, 'book2idx_sbert.npy')
    book2idx = {str(row['book_id']): i for i, row in df.iterrows()}
    np.save(idx_path, book2idx)
    log.info(f"Saved book2idx_sbert: {idx_path}")

    log.info("="*55)
    log.info("ENCODING COMPLETE")
    log.info(f"  Books: {embeddings.shape[0]:,}")
    log.info(f"  Dims:  {embeddings.shape[1]}")
    log.info("="*55)

if __name__ == '__main__':
    log.info("BookRS SBERT Encoding — Fast Version")
    df         = load_books()
    texts      = build_texts(df)
    embeddings = encode_books(texts)
    save(embeddings, df)
