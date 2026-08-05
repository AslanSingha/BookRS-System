"""
BookRS Recommender Service
Combines ALS (collaborative filtering) + SBERT (content-based)
Using all settings justified by experiments 1-5.

Cold-start strategy (Option C):
  0 ratings   → Popular/Trending
  1-4 ratings → Content-based from rated books
  5+ ratings  → Full Hybrid (ALS + Content)
  UCSD user   → Full Hybrid (ALS + Content)
"""
import numpy as np
import pandas as pd
import scipy.sparse as sp
import implicit
from sentence_transformers import SentenceTransformer
from pathlib import Path
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class BookRecommender:
    def __init__(self):
        self.books_df     = None
        self.embeddings   = None
        self.user_factors = None
        self.book_factors = None
        self.user2idx     = {}
        self.book2idx     = {}
        self.idx2book     = {}
        self.similar_cache = {}
        self.model        = None
        self.is_ready     = False

    async def initialize(self):
        logger.info("Initializing BookRS recommender...")

        # Load books
        self.books_df = pd.read_parquet(settings.books_path)
        logger.info(f"Loaded {len(self.books_df):,} books")

        # Books from PostgreSQL are already deduplicated by entity resolution.
        # We preserve ORDER BY book_id so indices match embeddings.npy
        # which was also encoded ORDER BY book_id.
        logger.info(f"Catalogue loaded: {len(self.books_df):,} books (already deduplicated)")

        # Store sequential indices — no reordering needed
        self._dedup_indices = list(range(len(self.books_df)))
        # (these are identity indices; reordering step becomes a no-op)


        # Load SBERT model
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)

        # Load or compute embeddings
        embeddings_path = settings.models_path / "embeddings.npy"
        settings.models_path.mkdir(parents=True, exist_ok=True)

        if embeddings_path.exists():
            logger.info("Loading cached embeddings...")
            self.embeddings = np.load(str(embeddings_path))
        else:
            logger.info("Computing embeddings (first time)...")
            texts = (self.books_df["title"] + ". " + self.books_df["description"].fillna("")).tolist()
            self.embeddings = self.model.encode(
                texts, batch_size=128, show_progress_bar=True,
                normalize_embeddings=True, device="cuda"
            ).astype(np.float32)
            np.save(str(embeddings_path), self.embeddings)
            logger.info("Embeddings saved!")

        # Reorder embeddings to match deduplicated books_df
        # embeddings.npy was encoded ORDER BY book_id
        # parquet is also ORDER BY book_id
        # so _dedup_indices correctly maps parquet rows → embedding rows
        if hasattr(self, '_dedup_indices') and self._dedup_indices is not None:
            logger.info(f"Reordering embeddings to match {len(self._dedup_indices):,} deduplicated books...")
            self.embeddings = self.embeddings[self._dedup_indices]
            logger.info(f"Embeddings reordered: {self.embeddings.shape}")
            del self._dedup_indices
        # Truncate embeddings to match books_df size
        # embeddings.npy has 1,244,257 rows (pre-entity-resolution)
        # books_df has 883,468 rows (post-entity-resolution)
        # We only need the first len(books_df) rows since
        # books are in ORDER BY book_id in both parquet and embeddings
        if len(self.embeddings) > len(self.books_df):
            self.embeddings = self.embeddings[:len(self.books_df)]
            logger.info(f"Embeddings truncated to {self.embeddings.shape}")

        # Build book index — MUST use the saved mapping from encode_books.py
        # because embeddings.npy was generated using ORDER BY book_id::bigint
        # (numeric sort), NOT the string-sorted order of books_df["book_id"].
        book2idx_path = settings.models_path / "book2idx_sbert.npy"
        if book2idx_path.exists():
            self.book2idx = np.load(str(book2idx_path), allow_pickle=True).item()
            logger.info(f"Loaded book2idx_sbert.npy: {len(self.book2idx):,} entries")
        else:
            logger.warning("book2idx_sbert.npy not found — rebuilding from books_df (WARNING: may misalign with embeddings.npy!)")
            self.book2idx = {bid: i for i, bid in enumerate(self.books_df["book_id"])}
        self.idx2book = {i: bid for bid, i in self.book2idx.items()}

        # Train ALS
        await self._train_als()

        # Pre-build fast lookup arrays for similar books
        self._titles_lower = self.books_df["title"].str.lower().str.strip().values
        self._authors_lower = self.books_df["authors"].str.lower().str.split(",").str[0].str.strip().values
        self._ratings_count = self.books_df["ratings_count"].values
        logger.info("Fast lookup arrays built!")

        # GPU used only for SBERT encoding (already handled by sentence-transformers)
        # CPU is fast enough for similarity search (0.13s per query)

        # Pre-build trending pool at startup
        self._build_trending_pool()
        logger.info(f"Trending pool built: {len(self._trending_pool)} books")

        self.is_ready = True
        logger.info("BookRS recommender ready!")

    async def _train_als(self):
        """Load pre-trained ALS factor matrices from .npy files."""
        models_dir = settings.models_path
        u_path   = models_dir / "als_user_factors.npy"
        v_path   = models_dir / "als_item_factors.npy"
        u2i_path = models_dir / "user2idx.npy"

        if u_path.exists() and v_path.exists():
            logger.info("Loading pre-trained ALS factors...")
            U = np.load(str(u_path))  # (666238 x 128)
            V = np.load(str(v_path))  # (883468 x 128)

            # Load user2idx mapping
            if u2i_path.exists():
                self.user2idx = np.load(str(u2i_path), allow_pickle=True).item()

            # Convention: book_factors = V, user_factors = U
            self.user_factors = U
            self.book_factors  = V
            logger.info(f"ALS loaded! user_factors: {U.shape}  book_factors: {V.shape}")
        else:
            logger.warning("Pre-trained ALS .npy files not found — CF disabled")
            self.user_factors = None
            self.book_factors  = None


    def _compute_user_vector(self, rated_book_ids: list, ratings: list) -> np.ndarray:
        """
        ALS Folding-In: compute user vector for new users instantly.
        Uses frozen book_factors to solve for optimal user vector.
        Industry standard approach (Hu et al. 2008).
        
        Math: user_vec = (B.T @ B + λI)^-1 @ B.T @ r
        Where B = book factors for rated books, r = ratings
        """
        valid = [(self.book2idx[bid], r) for bid, r in zip(rated_book_ids, ratings)
                 if bid in self.book2idx]
        if not valid:
            return None

        idxs, rs = zip(*valid)
        B = self.book_factors[list(idxs)].astype(np.float64)
        r = np.array(rs, dtype=np.float64)

        # Confidence weighting (Experiment 5: Config C)
        confidence = 1.0 + r * 2.0

        # Weighted least squares: (B.T @ C @ B + λI) @ u = B.T @ C @ r
        C = np.diag(confidence)
        A = B.T @ C @ B + settings.ALS_REGULARIZATION * np.eye(B.shape[1])
        b = B.T @ C @ r

        try:
            user_vec = np.linalg.solve(A, b)
            return user_vec.astype(np.float32)
        except np.linalg.LinAlgError:
            return None

    def get_hybrid_recommendations(
        self,
        user_id: str,
        n: int = 10,
        rated_book_ids: Optional[list] = None,
        fav_book_ids: Optional[list] = None,
        clicked_book_ids: Optional[list] = None,
        viewed_book_ids: Optional[list] = None,
        exclude_book_ids: Optional[list] = None
    ) -> tuple[list[dict], str]:
        """
        Option C cold-start strategy:
        0 ratings   → Popular
        1-4 ratings → Content-based
        5+ ratings  → Full Hybrid
        UCSD user   → Full Hybrid
        """
        if not self.is_ready:
            return self._get_popular(n), "popular"

        rated_books  = rated_book_ids   or []
        fav_books    = fav_book_ids     or []
        clicked_books = clicked_book_ids or []
        viewed_books = viewed_book_ids  or []
        exclude = set(exclude_book_ids or []) | set(rated_books)
        n_books = len(self.books_df)

        # ── Stage 1: Check if UCSD user ──────────────────────
        is_ucsd_user = user_id in self.user2idx

        # ── Stage 2: Check local ratings count ───────────────
        n_rated = len(rated_books)
        # All implicit signals combined (for content profile)
        all_implicit = list(set(fav_books + clicked_books + viewed_books) - set(rated_books))

        # ── Cold start: 0 ratings, not UCSD user ─────────────
        if n_rated == 0 and not is_ucsd_user:
            recs = self._get_popular(n)
            return recs, "popular"

        # ── Content-based: 1-4 ratings, not UCSD user ────────
        if n_rated < 5 and not is_ucsd_user:
            recs = self._get_weighted_content(
                rated_books, fav_books, clicked_books, viewed_books, n, exclude
            )
            return recs, "content"

        # ── Full Hybrid: 5+ ratings OR UCSD user ─────────────
        # CF score
        method = "hybrid"
        if is_ucsd_user:
            # Direct ALS lookup for known UCSD users
            u_idx = self.user2idx[user_id]
            cf_scores = self.user_factors[u_idx] @ self.book_factors.T
        else:
            # Folding-in for new users with 5+ ratings
            ratings_list = [1.0] * len(rated_books)
            user_vec = self._compute_user_vector(rated_books, ratings_list)
            if user_vec is not None:
                cf_scores = user_vec @ self.book_factors.T
            else:
                cf_scores = np.zeros(n_books, dtype=np.float32)

        # Weighted content profile using all signals
        # Weights: rating(1+r) > favourite(5) > search_click(1.5) > view(0.5)
        weighted_vecs = []
        weighted_wts  = []
        for bid in rated_books:
            if bid in self.book2idx:
                r = 3.0  # default weight if rating unknown
                weighted_vecs.append(self.embeddings[self.book2idx[bid]])
                weighted_wts.append(1.0 + r)
        for bid in fav_books:
            if bid in self.book2idx and bid not in set(rated_books):
                weighted_vecs.append(self.embeddings[self.book2idx[bid]])
                weighted_wts.append(5.0)
        for bid in clicked_books:
            if bid in self.book2idx and bid not in set(rated_books) | set(fav_books):
                weighted_vecs.append(self.embeddings[self.book2idx[bid]])
                weighted_wts.append(1.5)
        for bid in viewed_books:
            if bid in self.book2idx and bid not in set(rated_books) | set(fav_books) | set(clicked_books):
                weighted_vecs.append(self.embeddings[self.book2idx[bid]])
                weighted_wts.append(0.5)

        if weighted_vecs:
            vecs = np.array(weighted_vecs)
            wts  = np.array(weighted_wts, dtype=np.float32)
            wts  = wts / wts.sum()
            profile = (vecs * wts[:, None]).sum(axis=0)
            content_scores = profile @ self.embeddings.T
        elif is_ucsd_user:
            content_scores = np.zeros(n_books, dtype=np.float32)
        else:
            content_scores = np.zeros(n_books, dtype=np.float32)

        # Normalize
        def norm(x):
            mn, mx = x.min(), x.max()
            return (x - mn) / (mx - mn + 1e-9)

        # Dynamic alpha: new users need more SBERT until ALS is reliable
        if is_ucsd_user:
            alpha = settings.ALPHA  # 0.1 — trust ALS for trained users
        elif n_rated >= 20:
            alpha = 0.3  # more ALS as ratings accumulate
        else:
            alpha = 0.7  # trust SBERT more for sparse new users
        hybrid = alpha * norm(content_scores) + \
                 (1 - alpha) * norm(cf_scores)

        # Exclude seen books
        for bid in exclude:
            if bid in self.book2idx:
                hybrid[self.book2idx[bid]] = -1

        top_idxs = np.argsort(hybrid)[-n:][::-1]
        # Build context for reason generation
        ctx = {
            "is_ucsd":  is_ucsd_user,
            "n_rated":  n_rated,
            "top_book": None,
        }
        # Find top rated book title for content reason
        if rated_books:
            for bid in rated_books:
                if bid in self.book2idx:
                    row = self.books_df[self.books_df["book_id"] == bid]
                    if len(row) > 0:
                        ctx["top_book"] = row.iloc[0]["title"][:40]
                        break
        recs = [self._book_to_dict(
                    self.books_df[self.books_df["book_id"] == self.idx2book[i]].iloc[0],
                    float(hybrid[i]), method, ctx)
                for i in top_idxs if self.idx2book[i] in self.books_df["book_id"].values]
        return recs, method

    def _get_weighted_content(self, rated_books, fav_books, clicked_books,
                               viewed_books, n, exclude) -> list[dict]:
        """Content-based recs using weighted signals from all user actions."""
        # Build weighted book list
        # Weights: rating(4.0) > favourite(5.0) > search_click(1.5) > view(0.5)
        seen = set()
        weighted_ids = []

        for bid in rated_books:
            if bid not in seen and bid in self.book2idx:
                weighted_ids.extend([bid] * 4)  # weight 4
                seen.add(bid)
        for bid in fav_books:
            if bid not in seen and bid in self.book2idx:
                weighted_ids.extend([bid] * 5)  # weight 5
                seen.add(bid)
        for bid in clicked_books:
            if bid not in seen and bid in self.book2idx:
                weighted_ids.extend([bid, bid])  # weight 1.5 ≈ 2
                seen.add(bid)
        for bid in viewed_books:
            if bid not in seen and bid in self.book2idx:
                weighted_ids.append(bid)  # weight 0.5 ≈ 1
                seen.add(bid)

        if not weighted_ids:
            return self._get_popular(n)

        # Compute weighted mean embedding
        idxs = [self.book2idx[b] for b in weighted_ids]
        profile = self.embeddings[idxs].mean(axis=0)
        scores = profile @ self.embeddings.T

        # Exclude already seen books
        for bid in exclude:
            if bid in self.book2idx:
                scores[self.book2idx[bid]] = -1

        # Build source info for filtering
        all_source_ids = list(set(rated_books + fav_books + clicked_books + viewed_books))
        return self._get_content_from_books(all_source_ids, n, exclude)

    def _get_content_from_books(self, book_ids: list, n: int, exclude: set) -> list[dict]:
        """Content-based recommendations from a list of book IDs with proper filtering."""
        valid_idxs = [self.book2idx[b] for b in book_ids if b in self.book2idx]
        if not valid_idxs:
            return self._get_popular(n)

        profile = self.embeddings[valid_idxs].mean(axis=0)
        scores = profile @ self.embeddings.T

        # Exclude rated/source books
        for bid in exclude:
            if bid in self.book2idx:
                scores[self.book2idx[bid]] = -1

        # Build exclusion info from source books
        source_authors = set()
        source_series  = set()
        source_keys    = set()
        for bid in book_ids:
            if bid not in self.book2idx:
                continue
            idx = self.book2idx[bid]
            author = self._authors_lower[idx]
            title  = self._titles_lower[idx]
            # Author last name
            parts = author.replace(".", " ").split()
            if parts:
                source_authors.add(parts[-1])
            # Series name
            if "(" in title:
                series = title.split("(")[-1].split(",")[0].strip()
                if len(series) > 4:
                    source_series.add(series)
            # Title key
            key = title.split("(")[0].strip()
            if len(key) > 4:
                source_keys.add(key)

        skip_keywords = [
            "companion", "guide", "review", "unofficial", "unauthorized",
            "parody", "philosophy", "trivia", "analysis", "quiz", "summary",
            "handbook", "cookbook", "essays", "anthology", "biography",
            "encyclopedia", "lexicon", "psycholog", "and history",
            "and philosophy", "a history", "the making of",
            "character vault", "treasury of", "magical worlds of",
            "the world of", "vault", "treasury", "a to z",
            "the unofficial", "field guide", "fan art"
        ]

        pool_size = min(500, len(scores))
        top_idxs  = np.argsort(scores)[-pool_size:][::-1]

        seen_titles  = set()
        seen_authors = set()
        filtered     = []

        for i in top_idxs:
            title   = self._titles_lower[i]
            author  = self._authors_lower[i]
            ratings = self._ratings_count[i]

            # Skip excluded books
            bid = self.idx2book[i]
            if bid in exclude: continue

            # Skip same author variants
            author_parts = author.replace(".", " ").split()
            author_last  = author_parts[-1] if author_parts else ""
            if any(al == author_last for al in source_authors if len(al) > 4): continue

            # Skip titles referencing source books (translations, editions)
            if any(key in title for key in source_keys if len(key) > 4): continue

            # Skip if title contains source author name (biographies)
            if any(al in title for al in source_authors if len(al) > 4): continue

            # Skip same series
            if "(" in title:
                cand_series = title.split("(")[-1].split(",")[0].strip()
                if cand_series in source_series: continue

            # Skip companion/guide books
            if any(kw in title for kw in skip_keywords): continue

            # Minimum quality threshold
            if ratings < 500: continue

            # Skip duplicates
            if title  in seen_titles:  continue
            if author in seen_authors: continue

            seen_titles.add(title)
            seen_authors.add(author)
            filtered.append(i)

            if len(filtered) >= n:
                break

        # Return using fast positional lookup
        results = []
        for i in filtered:
            bid = self.idx2book[i]
            row = self.books_df[self.books_df["book_id"] == bid]
            if len(row) == 0:
                continue
            results.append(self._book_to_dict(
                row.iloc[0], float(scores[i]), "content"
            ))
        return results


    async def _precompute_similar(self, top_n: int = 50000, k: int = 10):
        """Pre-compute similar books for top N most-rated books."""
        import asyncio
        logger.info(f"Pre-computing similar books for top {top_n:,} books...")
        top_books = self.books_df.nlargest(top_n, "ratings_count")
        count = 0
        for _, row in top_books.iterrows():
            book_id = row["book_id"]
            if book_id not in self.book2idx:
                continue
            idx = self.book2idx[book_id]
            scores = self.embeddings[idx] @ self.embeddings.T
            scores[idx] = -1
            top_idxs = np.argsort(scores)[-k:][::-1]
            self.similar_cache[book_id] = [
                self.idx2book[i] for i in top_idxs
            ]
            count += 1
            if count % 10000 == 0:
                logger.info(f"  Pre-computed {count:,}/{top_n:,} books...")
                await asyncio.sleep(0)  # yield control
        logger.info(f"Similar books pre-computed for {count:,} books!")

    def get_content_recommendations(self, book_id: str, n: int = 10) -> list[dict]:
        """
        Find books with similar SBERT embeddings.
        Dataset is pre-deduplicated at startup so simple
        title+author filtering is sufficient.
        """
        if book_id not in self.book2idx:
            return []

        if book_id not in self.similar_cache:
            idx = self.book2idx[book_id]

            # Fast CPU similarity — 0.13s on 1.24M embeddings
            scores = self.embeddings[idx] @ self.embeddings.T
            scores[idx] = -1  # exclude self

            # Small pool — dataset is deduplicated so no duplicate clusters
            pool_size = min(500, len(scores))
            top_idxs = np.argsort(scores)[-pool_size:][::-1]

            # Source book info for exclusion
            source_title  = self._titles_lower[idx]
            source_author = self._authors_lower[idx]

            seen_titles  = set()
            seen_authors = set()
            skip_keywords = ["companion", "guide", "review", "recipe", "unofficial", "unauthorized", "parody", "philosophy", "trivia", "analysis", "quiz", "summary", "handbook", "cookbook", "essays", "anthology", "vault", "treasury", "biography", "encyclopedia", "lexicon", "the end of", "psycholog", "and history", "and philosophy", "a history", "the wizard behind", "j. k. rowling", "j.k. rowling:", "rowling:", "authors on suzanne", "girl who was on fire"]
            source_key = source_title.split("(")[0].strip()
            # Author name variants for robust exclusion
            author_parts = source_author.replace(".", " ").split()
            author_last  = author_parts[-1] if author_parts else ""
            # Series name for same-series exclusion
            source_series = source_title.split("(")[-1].split(",")[0].strip() if "(" in source_title else ""

            filtered     = []

            for i in top_idxs:
                title        = self._titles_lower[i]
                author       = self._authors_lower[i]
                ratings      = self._ratings_count[i]

                # Skip source book
                # Skip source book
                if title == source_title: continue

                # Skip same author (handle j.k. rowling variants)
                if author == source_author: continue
                if author_last and len(author_last) > 4 and author_last in author: continue

                # Skip if title references source book or is a translation
                if source_key and len(source_key) > 4 and source_key in title: continue

                # Skip if candidate title contains source author last name
                # (catches biographies e.g. "Daniel Radcliffe" for HP)
                if author_last and len(author_last) > 4 and author_last in title: continue

                # Skip same series books
                if source_series and len(source_series) > 4:
                    cand_series = title.split("(")[-1].split(",")[0].strip() if "(" in title else ""
                    if cand_series == source_series: continue

                if any(kw in title for kw in skip_keywords): continue
                if ratings < 500: continue

                # Skip low-quality books


                # Skip title duplicates (belt-and-suspenders after dedup)
                if title  in seen_titles:  continue
                if author in seen_authors: continue

                seen_titles.add(title)
                seen_authors.add(author)
                filtered.append((self.idx2book[i], float(scores[i])))

                if len(filtered) >= n:
                    break
            self.similar_cache[book_id] = filtered

        cached_items = self.similar_cache[book_id][:n]
        results = []
        for bid, score in cached_items:
            if bid in self.book2idx:
                row = self.books_df[self.books_df["book_id"] == bid]
                if len(row) == 0:
                    continue
                results.append(self._book_to_dict(
                    row.iloc[0], score, "content"
                ))
        return results

    def get_popular(self, n: int = 10, genre: Optional[str] = None) -> list[dict]:
        df = self.books_df.copy()
        if genre:
            df = df[df["genre"] == genre]
        top = df.nlargest(n, "ratings_count")
        return [self._book_to_dict(row, row["ratings_count"], "popular")
                for _, row in top.iterrows()]

    def _prewarm_similar_cache(self, n_books: int = 50):
        """Pre-compute similar books for top N popular books at startup."""
        top_books = self.books_df.nlargest(n_books, "ratings_count")["book_id"].tolist()
        logger.info(f"Pre-warming similar books cache for {n_books} popular books...")
        for book_id in top_books:
            if book_id not in self.similar_cache:
                self.get_content_recommendations(book_id, n=12)
        logger.info(f"Cache pre-warmed: {len(self.similar_cache)} books cached!")

    def _build_trending_pool(self) -> list[dict]:
        """
        Build a pool of 200 diverse trending books.
        Called once at startup. Deduplicates by author first name.
        """
        import numpy as np

        df = self.books_df[self.books_df["ratings_count"] >= 1000].copy()
        df["score"] = df["avg_rating"] * np.log1p(df["ratings_count"])
        df = df.sort_values("score", ascending=False)

        # Max 1 book per author (use first word of first author name)
        df["_auth"] = df["authors"].str.lower().str.split().str[0].str.strip()
        df = df.drop_duplicates(subset="_auth", keep="first")
        df = df.drop(columns=["_auth"])

        pool = [
            self._book_to_dict(row, row["score"], "trending")
            for _, row in df.head(200).iterrows()
        ]
        self._trending_pool = pool
        logger.info(f"Trending pool built: {len(pool)} diverse books")
        return pool



    def get_trending(self, n: int = 10) -> list[dict]:
        """
        Returns diverse trending books from pre-built pool.
        Cached for 10 minutes. Different sample each window.
        """
        import time
        import numpy as np

        now = time.time()
        window = int(now // 600)

        if (hasattr(self, "_trending_cache") and
            hasattr(self, "_trending_window") and
            self._trending_window == window):
            return self._trending_cache[:n]

        pool = getattr(self, "_trending_pool", None)
        if pool is None:
            pool = self._build_trending_pool()

        rng = np.random.RandomState(window)
        size = min(100, len(pool))
        idx = rng.choice(len(pool), size=size, replace=False)
        result = sorted([pool[i] for i in idx],
                        key=lambda x: x["score"], reverse=True)

        self._trending_cache = result
        self._trending_window = window
        return result[:n]

    def personalized_search(
        self,
        query: str,
        user_id: str,
        rated_book_ids: list = None,
        n: int = 10
    ) -> list[dict]:
        """
        Personalized search: 0.7 × semantic + 0.3 × CF
        Query intent dominates, user taste re-ranks results.
        """
        rated_books = rated_book_ids or []
        n_books = len(self.books_df)

        # Semantic scores from query
        query_emb = self.model.encode(
            [query], normalize_embeddings=True, device="cuda"
        ).astype(np.float32)[0]
        semantic_scores = query_emb @ self.embeddings.T

        # CF scores
        cf_scores = np.zeros(n_books, dtype=np.float32)

        if user_id in self.user2idx:
            # UCSD user — direct ALS lookup
            u_idx = self.user2idx[user_id]
            cf_scores = self.user_factors[u_idx] @ self.book_factors.T
        elif len(rated_books) >= 5:
            # New user with enough ratings — folding in
            ratings_list = [1.0] * len(rated_books)
            user_vec = self._compute_user_vector(rated_books, ratings_list)
            if user_vec is not None:
                cf_scores = user_vec @ self.book_factors.T
        elif len(rated_books) > 0:
            # Few ratings — use content profile
            valid_idxs = [self.book2idx[b] for b in rated_books if b in self.book2idx]
            if valid_idxs:
                profile = self.embeddings[valid_idxs].mean(axis=0)
                cf_scores = profile @ self.embeddings.T

        # Normalize both
        def norm(x):
            mn, mx = x.min(), x.max()
            return (x - mn) / (mx - mn + 1e-9)

        # Query dominates (0.7), taste re-ranks (0.3)
        combined = 0.7 * norm(semantic_scores) + 0.3 * norm(cf_scores)

        top_idxs = np.argsort(combined)[-n:][::-1]
        return self._idxs_to_books(top_idxs, combined, "personalized")

    def search(self, query: str, n: int = 10) -> list[dict]:
        query_emb = self.model.encode(
            [query], normalize_embeddings=True, device="cuda"
        ).astype(np.float32)[0]
        scores = query_emb @ self.embeddings.T
        top_idxs = np.argsort(scores)[-n:][::-1]
        return self._idxs_to_books(top_idxs, scores, "search")

    def _get_popular(self, n: int) -> list[dict]:
        top = self.books_df.nlargest(n, "ratings_count")
        return [self._book_to_dict(row, row["ratings_count"], "popular")
                for _, row in top.iterrows()]

    def _idxs_to_books(self, idxs, scores, method) -> list[dict]:
        results = []
        for idx in idxs:
            book_id = self.idx2book[idx]
            row = self.books_df[self.books_df["book_id"] == book_id].iloc[0]
            results.append(self._book_to_dict(row, float(scores[idx]), method))
        return results

    def _book_to_dict(self, row, score, method, context: dict = None) -> dict:
        ctx = context or {}
        # Build human-readable reason
        reason_map = {
            "popular":      "Trending among all readers",
            "content":      "Matches your taste profile",
            "hybrid":       "Recommended by Hybrid AI (ALS + SBERT)",
            "personalized": "Personalised to your search",
            "search":       "Semantically similar to your query",
            "trending":     "Trending right now",
        }
        reason = reason_map.get(method, method)
        # Enrich reason with context
        if method == "hybrid" and ctx.get("is_ucsd"):
            reason = "Collaborative filtering match (ALS)"
        elif method == "hybrid" and ctx.get("n_rated", 0) >= 20:
            reason = "Hybrid AI: ALS + SBERT (strong profile)"
        elif method == "hybrid":
            reason = "Hybrid AI: SBERT + ALS"
        elif method == "content" and ctx.get("top_book"):
            reason = f"Similar to “{ctx['top_book']}”"
        elif method == "popular" and row.get("genre"):
            genre_labels = {
                "fiction": "Fiction", "non-fiction": "Non-Fiction",
                "fantasy, paranormal": "Fantasy",
                "mystery, thriller, crime": "Mystery",
                "science, technology, engineering, mathematics": "STEM",
                "history, historical fiction, biography": "History",
                "romance": "Romance", "young-adult": "Young Adult",
                "children": "Children", "poetry": "Poetry",
                "comics, graphic": "Comics",
            }
            g = genre_labels.get(row.get("genre",""), "")
            if g:
                reason = f"Popular in {g}"
        return {
            "book_id":      row["book_id"],
            "title":        row["title"],
            "authors":      row["authors"],
            "genre":        row.get("genre", ""),
            "avg_rating":   float(row["avg_rating"]),
            "image_url":    row.get("image_url", ""),
            "score":        round(float(score), 4),
            "reason":       reason,
        }

recommender = BookRecommender()
