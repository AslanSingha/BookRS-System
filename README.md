# BookRS — AI-Powered Book Recommendation System

> A deployable research-grade hybrid recommendation system combining SBERT semantic embeddings and ALS collaborative filtering across 883,468 unique books.

[![Python](https://img.shields.io/badge/Python-3.12.3-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Vue.js](https://img.shields.io/badge/Vue.js-3-4FC08D?logo=vue.js)](https://vuejs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://postgresql.org)

---

## Overview

BookRS is the implementation component of an Engineering thesis at the **Institute of Technology of Cambodia (ITC)**, supervised by M. SOK Kimheng. It is designed as a deployable research-grade system following industry-standard recommendation architecture — comparable to how Netflix, Spotify, and Amazon approach recommendations, scaled to academic hardware.

### Key Results

| Metric | Value |
|--------|-------|
| Catalogue | 883,468 unique books |
| Training interactions | 33,402,870 · 666,238 users |
| Precision@10 | **0.2259** |
| Recall@10 | **0.2971** |
| MRR | **0.5826** |
| vs Random | **45.2×** improvement |
| Inference latency | **131–199 ms** |

---

## Architecture

```
Browser (Vue.js · Port 5173)
    │  HTTP
    ▼
FastAPI Backend (Port 8000)
    │  in-process function call
    ▼
Recommender Service
    ├── SBERT taste profile builder
    ├── ALS collaborative scoring
    ├── Hybrid Ranker
    │     score = α·norm(s_sem) + (1−α)·norm(s_cf)
    └── Cold-Start Manager (4 stages)
    │
    ├── models/embeddings.npy         (883,468 x 384 - ~1.4 GB)
    ├── models/book2idx_sbert.npy    (883,468 entries - REQUIRED, see below)
    ├── models/als_user_factors.npy  (666,238 x 128)
    └── models/als_item_factors.npy  (883,468 x 128)
    │
    ▼
PostgreSQL (Port 5432)
    ├── books          (883,468 rows)
    ├── users
    ├── interactions   (explicit ratings)
    └── user_actions   (implicit signals: view/click/fav)
```

---

## Features

- **Semantic search** — SBERT query encoding against 883K book embeddings
- **Personalized search** — hybrid SBERT + ALS results
- **Netflix-style homepage** — six personalized sections per logged-in user
- **Four-stage cold-start** — popularity → content → folding-in → direct ALS
- **Dynamic alpha weighting** — α adapts to user interaction density
- **ALS folding-in** — new-user vector computed in real-time (<1ms)
- **Entity resolution** — 360,789 duplicate editions removed (−28.9%)
- **STEM genre** — 4,185 STEM books tagged for academic users

---

## Requirements

**Hardware:**
- RAM: 32 GB recommended (model artifacts ~4 GB loaded)
- GPU: NVIDIA with CUDA (recommended for training)

**Software:**
- Python 3.12.3
- Node.js 18+
- PostgreSQL 16
- CUDA Toolkit 12.x (optional, for GPU training)

---

## Installation

### 0. Prerequisite: BookRS-DataPrep

The data preparation scripts below (Step 1) read from a parquet file produced by a **separate** repository, [BookRS-DataPrep](https://github.com/AslanSingha/BookRS-DataPrep). Clone and run it first:

```bash
git clone git@github.com:AslanSingha/BookRS-DataPrep.git ~/projects/BookRS-DataPrep
cd ~/projects/BookRS-DataPrep
# Follow BookRS-DataPrep's own README to produce:
#   outputs/bookrs_ucsd_books.parquet         (1,244,257 rows)
#   outputs/bookrs_ucsd_interactions.parquet  (33,402,870 rows)
# from the raw UCSD Book Graph dataset (goodreads_books.json.gz, goodreads_interactions.csv).
```

### 1. Clone BookRS-System

```bash
git clone git@github.com:AslanSingha/BookRS-System.git
cd BookRS-System
```

### 2. Python environment

```bash
python3.12 -m venv ~/bookrs-env
source ~/bookrs-env/bin/activate
pip install -r requirements.txt
```

> GPU/CUDA support is included automatically -- no separate PyTorch install command is needed. Verify with:
> ```bash
> python3 -c "import torch; print(torch.cuda.is_available())"
> ```

### 3. PostgreSQL setup

```bash
sudo service postgresql start
sudo -u postgres psql -c "CREATE USER bookrs WITH PASSWORD 'bookrs123';"
sudo -u postgres psql -c "CREATE DATABASE bookrs_db OWNER bookrs;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE bookrs_db TO bookrs;"
```

### 4. Frontend

```bash
cd frontend && npm install && cd ..
```

---

## Data Preparation

Run once before starting the system, **in this exact order**. Total time: ~90 minutes on GPU.

```bash
# Step 1 — Load raw books into PostgreSQL: 1,244,257 rows, pre-deduplication (~3 min)
python scripts/load_books_to_db.py

# Step 2 — Load interactions into PostgreSQL: 33,402,870 rows (~5-10 min)
python scripts/load_interactions_to_db.py

# Step 3 — Entity resolution: deduplicates 1,244,257 to 883,468 books, -28.9% (~1 min)
python scripts/entity_resolution.py

# Step 4 — Encode books with SBERT: embeddings.npy + book2idx_sbert.npy (~80 min)
python scripts/encode_books.py

# Step 5 — Train ALS model: als_user_factors.npy, als_item_factors.npy (~15 min)
python scripts/train_als.py
```

> **Do not skip Step 3.** Steps 1 and 2 alone leave PostgreSQL with the raw, pre-deduplication catalogue (1,244,257 books). `encode_books.py` in Step 4 reads directly from PostgreSQL, in book_id order -- it must run after entity resolution, or `embeddings.npy` will be generated against the wrong book count and silently misalign with everything downstream. See **Critical: Index Ordering** below.

---

## Running the System

```bash
bash start_bookrs.sh
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

> **Important:** Do not use `--reload` with uvicorn in normal operation. It spawns multiple processes each loading the 1.9 GB embedding matrix into RAM.

---

## Project Structure

```
BookRS/
├── app/
│   ├── main.py                    # Entry point
│   ├── api/routes/
│   │   ├── recommendations.py     # 17 recommendation endpoints
│   │   ├── search.py              # Semantic + personalized search
│   │   ├── books.py
│   │   ├── users.py
│   │   └── actions.py
│   ├── services/
│   │   └── recommender.py         # Core ML engine (~800 lines)
│   └── core/
│       ├── config.py
│       └── database.py
├── frontend/                      # Vue.js 3 + Vite + Tailwind CSS 3
│   └── src/{views,stores,components,services}/
├── models/                        # Pre-computed artifacts (gitignored -- NOT the same as app/models/)
│   ├── embeddings.npy             # ~1.4 GB
│   ├── book2idx_sbert.npy         # REQUIRED -- see Critical: Index Ordering
│   ├── als_user_factors.npy
│   └── als_item_factors.npy
├── scripts/                       # Offline data preparation
├── experiments/                   # Evaluation scripts
├── requirements.txt
└── start_bookrs.sh
```

---

## Critical: Index Ordering

`embeddings.npy` and `book2idx_sbert.npy` are generated together by `scripts/encode_books.py`, which loads books from PostgreSQL with `ORDER BY book_id::bigint` -- a **numeric** sort (`'1', '2', '3', ... '10', '11'`).

Any other place that loads books -- `books_df = pd.read_parquet(...)`, a fresh `SELECT * FROM books ORDER BY book_id`, or Python's default string sort on `book_id` -- produces a **different** order (`'1', '10', '100', '1000', ...`).

These two orderings look similar enough to not notice, but they place completely different books at the same row index. If any code builds `book2idx` itself from `books_df` instead of loading the saved `book2idx_sbert.npy`, or indexes `books_df` positionally (`.iloc[i]`) using an index that came from `embeddings`/`book2idx`, results become silently wrong -- not an error, just incorrect books returned with plausible-looking scores.

**Rules that must hold:**
1. Always load `book2idx` from `models/book2idx_sbert.npy` at startup. Never rebuild it from `books_df["book_id"]`.
2. Never use `books_df.iloc[i]` where `i` came from `argsort`/`book2idx`/`embeddings` indexing. Always look up by value: `books_df[books_df["book_id"] == book_id]`.
3. Any array meant to be indexed in parallel with `embeddings` (e.g. per-book title/author/rating lookup arrays) must be built via `books_df.set_index("book_id").reindex(ordered_book_ids)`, where `ordered_book_ids` comes from `idx2book` -- never built directly from `books_df`'s own row order.

This exact class of bug was found and fixed three times in one debugging session (commits `faedc62`–area, `7547ccf`, `6b84698`) -- each time producing plausible-looking but silently incorrect recommendations, not a crash. If recommendation quality ever looks subtly "off" after a refactor, check this first.

---

## Cold-Start Strategy

| Stage | Trigger | Method | α | Latency | P@10 |
|-------|---------|--------|---|---------|------|
| 1 | 0 ratings | Popularity | — | ~15ms | 0.0875 |
| 2 | 1–4 ratings | SBERT content | 1.0 | ~73–91ms | 0.2070 |
| 3 | 5–19 ratings | Hybrid folding-in | 0.7 | ~197ms | 0.2259 |
| 4 | UCSD user | Direct ALS | 0.1 | ~131ms | 0.2110 |

---

## Experiments

| # | Question | Key Finding |
|---|----------|-------------|
| 1 | Which embedding model? | all-MiniLM-L6-v2 best tradeoff |
| 2 | Optimal hybrid weight α? | α=0.1; pure SBERT collapses (MRR=0.038) |
| 3 | ALS hyperparameters? | k=128, λ=0.1, T=10 |
| 4 | Which CF algorithm? | ALS beats BPR by +38.6% at full scale |
| 5 | vs baselines? | Hybrid beats all single-method baselines |
| 6 | Confidence weighting? | c=1+2r+3δ improves over standard |

---

## Thesis

> **RIN SINGH** (2026). *AI-Powered Book Recommendation System (BookRS)*.
> Engineering Thesis, Institute of Technology of Cambodia.
> Supervised by M. SOK Kimheng. Defense: July 8, 2026.

**Five original contributions:**

1. Multi-scale evaluation methodology using both 10K active users and 446K full-scale users.
2. Catalog entity resolution on the UCSD Book Graph, removing 360,789 duplicate editions (−28.9%).
3. STEM genre extraction for academic library recommendation, identifying 4,185 STEM books.
4. Extended confidence weighting formula: `c(u,i) = 1 + 2·r(u,i) + 3·δ(u,i)`.
5. A complete deployable full-stack hybrid recommendation system with 17 API endpoints, large-scale model artifacts, and recommendation responses in under 200 ms.

---

## Backup

```bash
# Database backup
pg_dump -U bookrs -W -h 127.0.0.1 bookrs_db > bookrs_backup.sql

# Restore on new machine
psql -U bookrs -W -h 127.0.0.1 bookrs_db < bookrs_backup.sql
```

> **Always verify a restored backup's row counts before trusting it:**
> ```bash
> psql -U bookrs -h 127.0.0.1 -d bookrs_db -c "SELECT 'books', COUNT(*) FROM books UNION ALL SELECT 'interactions', COUNT(*) FROM interactions;"
> ```
> Expect exactly `883,468` books and `33,402,870` interactions. A backup taken mid-pipeline (e.g. before entity resolution, or before interactions finished loading) will restore successfully with no errors but contain the wrong counts -- this has happened before and is easy to miss.

Model artifacts (`embeddings.npy`, `book2idx_sbert.npy`, `als_user_factors.npy`, `als_item_factors.npy`) are excluded from version control. Back them up separately (they do not change once generated) -- regenerating them from scratch takes ~90 minutes.

---

<div align="center">
  <strong>BookRS</strong> · Institute of Technology of Cambodia · 2026<br>
  RIN SINGH · Supervised by M. SOK Kimheng
</div>
