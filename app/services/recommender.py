"""
BookRS Recommender Service
Combines ALS (collaborative filtering) + SBERT (content-based)
Using all settings justified by experiments 1-5.
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
        self.books_df        = None
        self.embeddings      = None
        self.user_factors    = None
        self.book_factors    = None
        self.user2idx        = {}
        self.book2idx        = {}
        self.idx2book        = {}
        self.model           = None
        self.is_ready        = False

    async def initialize(self):
        """Load data, train models, prepare for serving."""
        logger.info("Initializing BookRS recommender...")

        # Load books
        logger.info("Loading books dataset...")
        self.books_df = pd.read_parquet(settings.books_path)
        logger.info(f"Loaded {len(self.books_df):,} books")

        # Load SBERT model (Experiment 1: all-MiniLM-L6-v2)
        logger.info("Loading SBERT model...")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)

        # Compute or load embeddings
        embeddings_path = settings.models_path / "embeddings.npy"
        settings.models_path.mkdir(parents=True, exist_ok=True)

        if embeddings_path.exists():
            logger.info("Loading cached embeddings...")
            self.embeddings = np.load(str(embeddings_path))
        else:
            logger.info("Computing embeddings (first time, takes a few minutes)...")
            texts = (self.books_df["title"] + ". " + self.books_df["description"].fillna("")).tolist()
            self.embeddings = self.model.encode(
                texts, batch_size=128, show_progress_bar=True,
                normalize_embeddings=True, device="cuda"
            ).astype(np.float32)
            np.save(str(embeddings_path), self.embeddings)
            logger.info("Embeddings saved to cache!")

        # Build book index
        self.book2idx = {bid: i for i, bid in enumerate(self.books_df["book_id"])}
        self.idx2book = {i: bid for bid, i in self.book2idx.items()}

        # Train ALS on interactions
        await self._train_als()

        self.is_ready = True
        logger.info("✅ BookRS recommender ready!")

    async def _train_als(self):
        """Train ALS model with confidence weighting (Experiment 5: Config C)."""
        logger.info("Loading interactions and training ALS...")

        interactions = pd.read_parquet(settings.interactions_path)

        # Filter to books in our dataset
        valid_books = set(self.books_df["book_id"])
        interactions = interactions[interactions["book_id"].isin(valid_books)]

        # Build user index
        user_ids = interactions["user_id"].unique()
        self.user2idx = {u: i for i, u in enumerate(user_ids)}
        n_users = len(user_ids)
        n_books = len(self.books_df)

        interactions["u_idx"] = interactions["user_id"].map(self.user2idx)
        interactions["b_idx"] = interactions["book_id"].map(self.book2idx)
        interactions = interactions.dropna(subset=["u_idx", "b_idx"])
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

        # Train ALS (Experiment 3: factors=128, reg=0.1, iters=10)
        als = implicit.als.AlternatingLeastSquares(
            factors=settings.ALS_FACTORS,
            regularization=settings.ALS_REGULARIZATION,
            iterations=settings.ALS_ITERATIONS,
            use_gpu=False
        )
        als.fit(train_matrix.T.tocsr())

        # Swap factors (transposed matrix)
        self.book_factors = als.user_factors   # (n_books, 128)
        self.user_factors = als.item_factors   # (n_users, 128)

        logger.info(f"ALS trained! Users: {n_users:,} Books: {n_books:,}")

    def get_hybrid_recommendations(
        self,
        user_id: str,
        n: int = 10,
        exclude_book_ids: Optional[list] = None
    ) -> list[dict]:
        """
        Hybrid recommendation: α × content + (1-α) × collaborative
        α = 0.1 (Experiment 2)
        """
        if not self.is_ready:
            return self._get_popular(n)

        n_books = len(self.books_df)
        exclude = set(exclude_book_ids or [])

        # Collaborative score
        if user_id in self.user2idx:
            u_idx = self.user2idx[user_id]
            cf_scores = self.user_factors[u_idx] @ self.book_factors.T
        else:
            cf_scores = np.zeros(n_books)

        # Content score: mean embedding of user's rated books
        content_scores = np.zeros(n_books)
        if user_id in self.user2idx:
            u_idx = self.user2idx[user_id]
            # Get books this user interacted with
            user_book_idxs = np.where(
                self.user_factors[u_idx] @ self.book_factors.T > 0
            )[0][:20]
            if len(user_book_idxs) > 0:
                profile = self.embeddings[user_book_idxs].mean(axis=0)
                content_scores = profile @ self.embeddings.T

        # Normalize
        def norm(x):
            mn, mx = x.min(), x.max()
            return (x - mn) / (mx - mn + 1e-9)

        hybrid = settings.ALPHA * norm(content_scores) + \
                 (1 - settings.ALPHA) * norm(cf_scores)

        # Exclude already seen
        for bid in exclude:
            if bid in self.book2idx:
                hybrid[self.book2idx[bid]] = -1

        # Get top N
        top_idxs = np.argsort(hybrid)[-n:][::-1]
        return self._idxs_to_books(top_idxs, hybrid, "hybrid")

    def get_content_recommendations(self, book_id: str, n: int = 10) -> list[dict]:
        """Content-based: find similar books using SBERT embeddings."""
        if book_id not in self.book2idx:
            return []
        idx = self.book2idx[book_id]
        scores = self.embeddings[idx] @ self.embeddings.T
        scores[idx] = -1  # exclude self
        top_idxs = np.argsort(scores)[-n:][::-1]
        return self._idxs_to_books(top_idxs, scores, "content")

    def get_popular(self, n: int = 10, genre: Optional[str] = None) -> list[dict]:
        """Popularity-based recommendations."""
        df = self.books_df.copy()
        if genre:
            df = df[df["genre"] == genre]
        top = df.nlargest(n, "ratings_count")
        return [self._book_to_dict(row, row["ratings_count"], "popular")
                for _, row in top.iterrows()]

    def get_trending(self, n: int = 10) -> list[dict]:
        """Trending: high rated books (proxy for trending in static dataset)."""
        trending = self.books_df[self.books_df["ratings_count"] >= 1000]\
                       .nlargest(n * 3, "avg_rating")\
                       .sample(n, random_state=None)
        return [self._book_to_dict(row, row["avg_rating"], "trending")
                for _, row in trending.iterrows()]

    def search(self, query: str, n: int = 10) -> list[dict]:
        """Semantic search using SBERT embeddings."""
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
            "book_id":   row["book_id"],
            "title":     row["title"],
            "authors":   row["authors"],
            "genre":     row.get("genre", ""),
            "avg_rating": float(row["avg_rating"]),
            "image_url": row.get("image_url", ""),
            "score":     round(float(score), 4),
            "reason":    method,
        }

# Global instance
recommender = BookRecommender()
