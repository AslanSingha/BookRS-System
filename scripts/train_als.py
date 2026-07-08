"""
BookRS — ALS Training Script (Thesis Exact)
==========================================
Matches thesis Table III.2 exactly:
  U matrix: 666,238 × 128  (user factors)
  V matrix: 883,468 × 128  (item factors)
  Interactions: 33,402,870

Key: builds sparse matrix with ALL 883,468
catalogue books as columns, not just rated ones.
"""
import os, time
import numpy as np
import pandas as pd
from implicit.als import AlternatingLeastSquares
from scipy.sparse import csr_matrix
import psycopg2
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)s  %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

DB_CONFIG = {
    'host':     '127.0.0.1',
    'port':     5432,
    'database': 'bookrs_db',
    'user':     'bookrs',
    'password': 'bookrs123',
}

K       = 128
LAMBDA  = 0.1
ITERS   = 10
USE_GPU = True

def load():
    log.info("Connecting to PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    log.info("Loading interactions...")
    t0 = time.time()
    cur.execute("""
        SELECT user_id, book_id, rating, is_reviewed
        FROM interactions
        WHERE rating > 0
    """)
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=['user_id','book_id','rating','is_reviewed'])
    log.info(f"  Loaded {len(df):,} interactions in {time.time()-t0:.0f}s")
    log.info(f"  Users: {df['user_id'].nunique():,}")

    log.info("Loading all 883,468 catalogue books...")
    cur.execute("SELECT book_id FROM books ORDER BY book_id")
    all_book_ids = [str(r[0]) for r in cur.fetchall()]
    log.info(f"  Catalogue: {len(all_book_ids):,} books")

    cur.close()
    conn.close()
    return df, all_book_ids

def build(df, all_book_ids):
    log.info("Building confidence matrix c=1+2r+3delta...")

    users    = df['user_id'].unique()
    user2idx = {str(u): i for i, u in enumerate(users)}
    book2idx = {str(b): i for i, b in enumerate(all_book_ids)}

    log.info(f"  Matrix: ({len(user2idx):,} x {len(book2idx):,})")

    df = df.copy()
    df['c'] = (
        1 + 2 * df['rating'] + 3 * df['is_reviewed'].fillna(0)
    ).astype(np.float32)

    df = df[df['book_id'].astype(str).isin(book2idx)].reset_index(drop=True)
    log.info(f"  Interactions after catalogue filter: {len(df):,}")

    row = df['user_id'].astype(str).map(user2idx).values
    col = df['book_id'].astype(str).map(book2idx).values
    mat = csr_matrix(
        (df['c'].values, (row, col)),
        shape=(len(users), len(all_book_ids))
    )
    log.info(f"  Sparse matrix: {mat.shape}  nnz={mat.nnz:,}")
    return mat, user2idx, book2idx

def train(mat):
    log.info(f"Training ALS: k={K} lambda={LAMBDA} T={ITERS} gpu={USE_GPU}")
    model = AlternatingLeastSquares(
        factors        = K,
        regularization = LAMBDA,
        iterations     = ITERS,
        use_gpu        = USE_GPU,
        random_state   = 42,
    )
    t0 = time.time()
    model.fit(mat, show_progress=True)
    log.info(f"  Done in {(time.time()-t0)/60:.1f} minutes")
    return model

def save(model, u2i, b2i):
    U = model.user_factors.to_numpy() \
        if hasattr(model.user_factors, 'to_numpy') \
        else np.array(model.user_factors)
    V = model.item_factors.to_numpy() \
        if hasattr(model.item_factors, 'to_numpy') \
        else np.array(model.item_factors)

    np.save(os.path.join(MODELS_DIR, 'als_user_factors.npy'), U)
    np.save(os.path.join(MODELS_DIR, 'als_item_factors.npy'), V)
    np.save(os.path.join(MODELS_DIR, 'user2idx.npy'), u2i)
    np.save(os.path.join(MODELS_DIR, 'book2idx.npy'), b2i)

    log.info("=" * 55)
    log.info("ALS TRAINING COMPLETE")
    log.info(f"  U: {U.shape}  <- should be (666238, 128)")
    log.info(f"  V: {V.shape}  <- should be (883468, 128)")
    log.info(f"  U size: {U.nbytes/1e6:.0f} MB")
    log.info(f"  V size: {V.nbytes/1e6:.0f} MB")
    log.info(f"  Saved to: {os.path.abspath(MODELS_DIR)}")
    log.info("=" * 55)

if __name__ == '__main__':
    log.info("BookRS ALS Training — Thesis Exact Specification")
    log.info("  Target U: (666,238 x 128)")
    log.info("  Target V: (883,468 x 128)")
    df, all_books = load()
    mat, u2i, b2i = build(df, all_books)
    model         = train(mat)
    save(model, u2i, b2i)
