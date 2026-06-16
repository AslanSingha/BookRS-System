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
    ├── models/embeddings.npy        (883,468 × 384 · ~1.9 GB)
    ├── models/als_user_factors.npy  (666,238 × 128)
    └── models/als_item_factors.npy  (883,468 × 128)
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

### 1. Clone

```bash
git clone https://github.com/AslanSingha/BookRS-System.git
cd BookRS-System
```

### 2. Python environment

```bash
python3.12 -m venv ~/bookrs-env
source ~/bookrs-env/bin/activate
pip install -r requirements.txt
```

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

Run once before starting the system. Total time: ~76 minutes on GPU.

```bash
# Step 1 — Load 883,468 books into PostgreSQL (~5 min)
python scripts/load_books_to_db.py

# Step 2 — Encode books with SBERT → embeddings.npy (~60 min)
python scripts/encode_books.py

# Step 3 — Train ALS model → als_*.npy (~15 min)
python scripts/train_als.py
```

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
├── models/                        # Pre-computed artifacts (gitignored)
│   ├── embeddings.npy             # ~1.9 GB
│   ├── als_user_factors.npy
│   └── als_item_factors.npy
├── scripts/                       # Offline data preparation
├── experiments/                   # Evaluation scripts
├── requirements.txt
└── start_bookrs.sh
```

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

Model artifacts are excluded from version control — regenerate with the data preparation scripts or restore from backup.

---

<div align="center">
  <strong>BookRS</strong> · Institute of Technology of Cambodia · 2026<br>
  RIN SINGH · Supervised by M. SOK Kimheng
</div>
