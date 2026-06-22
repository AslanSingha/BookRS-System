"""
BookRS — ALS Training Script
Trains Alternating Least Squares on the UCSD Book Graph interactions.
Output: models/als_user_factors.npy and models/als_item_factors.npy

Runtime: ~15 minutes on NVIDIA RTX 3050 (use_gpu=True)
         ~60 minutes on CPU only
"""

import os
import time
import numpy as np
import pandas as pd
import psycopg2
from implicit.als import AlternatingLeastSquares
from scipy.sparse import csr_matrix
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

# Optimal hyperparameters (selected via Experiment 3 grid search)
K       = 128    # latent factors
LAMBDA  = 0.1    # regularization
ITERS   = 10     # training iterations
USE_GPU = True   # RTX 3050 4GB VRAM

# Confidence formula: c(u,i) = 1 + 2*r + 3*delta
ALPHA_RATING = 2
ALPHA_REVIEW = 3

# ── Load interactions from PostgreSQL ─────────────────────────
def load_interactions():
    log.info("Connecting to PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)

    log.info("Loading interactions...")
    query = """
        SELECT user_id, book_id, rating, is_reviewed
        FROM interactions
        WHERE rating IS NOT NULL
    """
    df = pd.read_sql(query, conn)
    conn.close()

    log.info(f"Loaded {len(df):,} interactions from "
             f"{df['user_id'].nunique():,} users "
             f"and {df['book_id'].nunique():,} books")
    return df

# ── Build confidence matrix ────────────────────────────────────
def build_confidence_matrix(df):
    log.info("Building user/item index maps...")

    # Create integer indices
    users  = df['user_id'].unique()
    books  = df['book_id'].unique()
    user2idx = {u: i for i, u in enumerate(users)}
    book2idx = {b: i for i, b in enumerate(books)}

    log.info(f"Users: {len(users):,}  |  Books: {len(books):,}")

    # Confidence: c = 1 + 2*r + 3*delta
    df = df.copy()
    df['confidence'] = (
        1
        + ALPHA_RATING * df['rating']
        + ALPHA_REVIEW * df['is_reviewed'].fillna(0)
    )

    # Build sparse matrix (users × books)
    row = df['user_id'].map(user2idx).values
    col = df['book_id'].map(book2idx).values
    data = df['confidence'].values.astype(np.float32)

    matrix = csr_matrix(
        (data, (row, col)),
        shape=(len(users), len(books))
    )

    log.info(f"Sparse matrix: {matrix.shape}  "
             f"nnz={matrix.nnz:,}  "
             f"density={matrix.nnz / (matrix.shape[0]*matrix.shape[1]):.6f}")

    return matrix, user2idx, book2idx, users, books

# ── Train ALS ─────────────────────────────────────────────────
def train_als(matrix):
    log.info(f"Training ALS: k={K}, lambda={LAMBDA}, "
             f"iterations={ITERS}, use_gpu={USE_GPU}")

    model = AlternatingLeastSquares(
        factors          = K,
        regularization   = LAMBDA,
        iterations       = ITERS,
        use_gpu          = USE_GPU,
        calculate_training_loss = True,
        random_state     = 42,
    )

    t0 = time.time()
    model.fit(matrix, show_progress=True)
    elapsed = time.time() - t0

    log.info(f"Training complete in {elapsed/60:.1f} minutes")
    return model

# ── Save artefacts ─────────────────────────────────────────────
def save_artefacts(model, user2idx, book2idx, users, books):
    # Factor matrices
    user_factors = model.user_factors  # (n_users × k)
    item_factors = model.item_factors  # (n_books × k)

    # Convert to numpy if GPU tensors
    if hasattr(user_factors, 'to_numpy'):
        user_factors = user_factors.to_numpy()
    if hasattr(item_factors, 'to_numpy'):
        item_factors = item_factors.to_numpy()

    u_path = os.path.join(MODELS_DIR, 'als_user_factors.npy')
    v_path = os.path.join(MODELS_DIR, 'als_item_factors.npy')
    ui_path = os.path.join(MODELS_DIR, 'user2idx.npy')
    bi_path = os.path.join(MODELS_DIR, 'book2idx.npy')

    np.save(u_path, user_factors)
    np.save(v_path, item_factors)
    np.save(ui_path, user2idx)
    np.save(bi_path, book2idx)

    log.info(f"Saved user factors:  {user_factors.shape}  → {u_path}")
    log.info(f"Saved item factors:  {item_factors.shape}  → {v_path}")
    log.info(f"Saved user2idx ({len(user2idx):,} users)  → {ui_path}")
    log.info(f"Saved book2idx ({len(book2idx):,} books)  → {bi_path}")

    # Summary
    log.info("")
    log.info("=" * 55)
    log.info("ALS TRAINING COMPLETE")
    log.info("=" * 55)
    log.info(f"  Users:        {user_factors.shape[0]:>10,}")
    log.info(f"  Books:        {item_factors.shape[0]:>10,}")
    log.info(f"  Latent dim:   {user_factors.shape[1]:>10}")
    log.info(f"  U matrix:     {user_factors.nbytes/1e6:>9.1f} MB")
    log.info(f"  V matrix:     {item_factors.nbytes/1e6:>9.1f} MB")
    log.info("=" * 55)

# ── Main ──────────────────────────────────────────────────────
if __name__ == '__main__':
    log.info("BookRS ALS Training Script")
    log.info(f"Models directory: {os.path.abspath(MODELS_DIR)}")
    log.info("")

    df                              = load_interactions()
    matrix, user2idx, book2idx, \
        users, books                = build_confidence_matrix(df)
    model                           = train_als(matrix)
    save_artefacts(model, user2idx, book2idx, users, books)
