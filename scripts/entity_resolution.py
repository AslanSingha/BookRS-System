import re
import psycopg2
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s  %(levelname)s  %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger(__name__)

DB_CONFIG = {'host': '127.0.0.1', 'port': 5432, 'database': 'bookrs_db', 'user': 'bookrs', 'password': 'bookrs123'}

def canonical_key(title: str, author: str) -> str:
    t = str(title).lower().strip()
    t = re.sub(r"\s*[\(\[].*?[\)\]]", "", t)
    t = re.sub(r",?\s*(part|vol|book|#)\s*[\d.]+.*$", "", t)
    t = t.strip()
    a = str(author).lower().split(",")[0].strip()
    return f"{t}|||{a}"

def load_books(conn) -> pd.DataFrame:
    log.info("Loading books from PostgreSQL...")
    cur = conn.cursor()
    cur.execute("SELECT book_id, title, authors, ratings_count FROM books")
    rows = cur.fetchall()
    cur.close()
    df = pd.DataFrame(rows, columns=['book_id','title','authors','ratings_count'])
    log.info(f"  Loaded {len(df):,} books")
    return df

def resolve(df: pd.DataFrame):
    log.info("Building canonical keys...")
    df = df.copy()
    df['_key'] = df.apply(lambda r: canonical_key(str(r['title'] or ''), str(r['authors'] or '')), axis=1)
    df_sorted = df.sort_values('ratings_count', ascending=False)
    df_dedup  = df_sorted.drop_duplicates(subset='_key', keep='first')
    keep_ids   = set(df_dedup['book_id'].tolist())
    remove_ids = set(df['book_id'].tolist()) - keep_ids
    pct = len(remove_ids) / len(df) * 100
    log.info(f"  Before: {len(df):,}")
    log.info(f"  After:  {len(df_dedup):,}  (removed {len(remove_ids):,}  -{pct:.1f}%)")
    log.info(f"  Target: 883,468  (-28.9%)")
    return keep_ids, remove_ids

def apply_dedup(conn, remove_ids: set):
    if not remove_ids:
        return
    log.info(f"Deleting {len(remove_ids):,} duplicates from PostgreSQL...")
    cur = conn.cursor()
    ids = list(remove_ids)
    for i in range(0, len(ids), 1000):
        cur.execute("DELETE FROM books WHERE book_id = ANY(%s)", (ids[i:i+1000],))
        if i % 50000 == 0:
            log.info(f"  {i:,} / {len(ids):,}")
    conn.commit()
    cur.close()
    log.info("Done ✓")

def verify(conn) -> int:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM books")
    count = cur.fetchone()[0]
    cur.close()
    log.info(f"Final count: {count:,}  (target 883,468  diff={count-883468:+,})")
    return count

if __name__ == '__main__':
    log.info("BookRS — Entity Resolution")
    log.info("="*55)
    conn = psycopg2.connect(**DB_CONFIG)
    df                = load_books(conn)
    keep_ids, rem_ids = resolve(df)
    apply_dedup(conn, rem_ids)
    final             = verify(conn)
    conn.close()
    log.info("="*55)
    log.info(f"  Kept:    {len(keep_ids):,}")
    log.info(f"  Removed: {len(rem_ids):,}")
    log.info(f"  Final:   {final:,}")
    log.info("="*55)
    log.info("Next: python3 scripts/encode_books.py")
