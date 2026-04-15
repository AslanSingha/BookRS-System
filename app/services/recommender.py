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

        # Build book index
        self.book2idx = {bid: i for i, bid in enumerate(self.books_df["book_id"])}
        self.idx2book = {i: bid for bid, i in self.book2idx.items()}

        # Train ALS
        await self._train_als()

        self.is_ready = True
        logger.info("BookRS recommender ready!")

    async def _train_als(self):
        logger.info("Training ALS...")
        interactions = pd.read_parquet(settings.interactions_path)
        valid_books = set(self.books_df["book_id"])
        interactions = interactions[interactions["book_id"].isin(valid_books)]

        user_ids = interactions["user_id"].unique()
        self.user2idx = {u: i for i, u in enumerate(user_ids)}
        n_users = len(user_ids)
        n_books = len(self.books_df)

        interactions["u_idx"] = interactions["user_id"].map(self.user2idx)
        interactions["b_idx"] = interactions["book_id"].map(self.book2idx)
        interactions = interactions.dropna(subset=["u_idx","b_idx"])
        interactions["u_idx"] = interactions["u_idx"].astype(int)
        interactions["b_idx"] = interactions["b_idx"].astype(int)
        interactions = interactions[
            (interactions["u_idx"] < n_users) &
            (interactions["b_idx"] < n_books)
        ]

        # Confidence weighting (Experiment 5: Config C)
        confidence = (
            1.0 +
            interactions["rating"].astype(float) * 2.0 +
            interactions["is_reviewed"].astype(float) * 3.0
        ).values

        train_matrix = sp.csr_matrix(
            (confidence,
             (interactions["u_idx"].values, interactions["b_idx"].values)),
            shape=(n_users, n_books)
        )

        als = implicit.als.AlternatingLeastSquares(
            factors=settings.ALS_FACTORS,
            regularization=settings.ALS_REGULARIZATION,
            iterations=settings.ALS_ITERATIONS,
            use_gpu=False
        )
        als.fit(train_matrix.T.tocsr())
        self.book_factors = als.user_factors   # (n_books, 128)
        self.user_factors = als.item_factors   # (n_users, 128)
        logger.info(f"ALS trained! Users: {n_users:,} Books: {n_books:,}")


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

        rated_books = rated_book_ids or []
        exclude = set(exclude_book_ids or []) | set(rated_books)
        n_books = len(self.books_df)

        # ── Stage 1: Check if UCSD user ──────────────────────
        is_ucsd_user = user_id in self.user2idx

        # ── Stage 2: Check local ratings count ───────────────
        n_rated = len(rated_books)

        # ── Cold start: 0 ratings, not UCSD user ─────────────
        if n_rated == 0 and not is_ucsd_user:
            recs = self._get_popular(n)
            return recs, "popular"

        # ── Content-based: 1-4 ratings, not UCSD user ────────
        if n_rated < 5 and not is_ucsd_user:
            recs = self._get_content_from_books(rated_books, n, exclude)
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

        # Content score from rated books
        if rated_books:
            valid_idxs = [self.book2idx[b] for b in rated_books if b in self.book2idx]
            if valid_idxs:
                profile = self.embeddings[valid_idxs].mean(axis=0)
                content_scores = profile @ self.embeddings.T
            else:
                content_scores = np.zeros(n_books, dtype=np.float32)
        elif is_ucsd_user:
            # Use ALS factors as proxy for content profile
            u_idx = self.user2idx[user_id]
            content_scores = np.zeros(n_books, dtype=np.float32)
        else:
            content_scores = np.zeros(n_books, dtype=np.float32)

        # Normalize
        def norm(x):
            mn, mx = x.min(), x.max()
            return (x - mn) / (mx - mn + 1e-9)

        hybrid = settings.ALPHA * norm(content_scores) + \
                 (1 - settings.ALPHA) * norm(cf_scores)

        # Exclude seen books
        for bid in exclude:
            if bid in self.book2idx:
                hybrid[self.book2idx[bid]] = -1

        top_idxs = np.argsort(hybrid)[-n:][::-1]
        recs = self._idxs_to_books(top_idxs, hybrid, method)
        return recs, method

    def _get_content_from_books(self, book_ids: list, n: int, exclude: set) -> list[dict]:
        """Content-based recommendations from a list of book IDs."""
        valid_idxs = [self.book2idx[b] for b in book_ids if b in self.book2idx]
        if not valid_idxs:
            return self._get_popular(n)

        profile = self.embeddings[valid_idxs].mean(axis=0)
        scores = profile @ self.embeddings.T

        for bid in exclude:
            if bid in self.book2idx:
                scores[self.book2idx[bid]] = -1

        top_idxs = np.argsort(scores)[-n:][::-1]
        return self._idxs_to_books(top_idxs, scores, "content")

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
        if book_id not in self.book2idx:
            return []
        # Use cache if available (fast!)
        if book_id in self.similar_cache:
            cached_ids = self.similar_cache[book_id][:n]
            results = []
            for bid in cached_ids:
                if bid in self.book2idx:
                    idx = self.book2idx[bid]
                    row = self.books_df[self.books_df["book_id"] == bid]
                    if not row.empty:
                        results.append(self._book_to_dict(row.iloc[0], 1.0, "content"))
            return results
        # Fallback: compute on-the-fly for uncached books
        idx = self.book2idx[book_id]
        scores = self.embeddings[idx] @ self.embeddings.T
        scores[idx] = -1
        top_idxs = np.argsort(scores)[-n:][::-1]
        return self._idxs_to_books(top_idxs, scores, "content")

    def get_popular(self, n: int = 10, genre: Optional[str] = None) -> list[dict]:
        df = self.books_df.copy()
        if genre:
            df = df[df["genre"] == genre]
        top = df.nlargest(n, "ratings_count")
        return [self._book_to_dict(row, row["ratings_count"], "popular")
                for _, row in top.iterrows()]

    def get_trending(self, n: int = 10) -> list[dict]:
        trending = self.books_df[self.books_df["ratings_count"] >= 1000]\
                       .nlargest(n * 3, "avg_rating")\
                       .sample(n, random_state=None)
        return [self._book_to_dict(row, row["avg_rating"], "trending")
                for _, row in trending.iterrows()]


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

    def _book_to_dict(self, row, score, method) -> dict:
        return {
            "book_id":      row["book_id"],
            "title":        row["title"],
            "authors":      row["authors"],
            "genre":        row.get("genre", ""),
            "avg_rating":   float(row["avg_rating"]),
            "image_url":    row.get("image_url", ""),
            "score":        round(float(score), 4),
            "reason":       method,
        }

recommender = BookRecommender()
