from fastapi import APIRouter, Query
from typing import Optional
from functools import partial
import asyncio
from app.services.recommender import recommender
from app.schemas.recommendation import RecommendationResponse, RecommendationItem

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

async def run_sync(func, *args, **kwargs):
    """Run CPU-heavy sync function in thread pool to avoid blocking event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))

@router.get("/hybrid/{user_id}", response_model=RecommendationResponse)
def get_hybrid_recommendations(
    user_id: str,
    n: int = Query(10, ge=1, le=50),
    rated_books: Optional[str] = Query(None),
    fav_books: Optional[str] = Query(None),
    clicked_books: Optional[str] = Query(None),
    viewed_books: Optional[str] = Query(None),
    exclude_books: Optional[str] = Query(None)
):
    rated   = rated_books.split(",")   if rated_books   else []
    favs    = fav_books.split(",")     if fav_books     else []
    clicks  = clicked_books.split(",") if clicked_books else []
    views   = viewed_books.split(",")  if viewed_books  else []
    exclude = exclude_books.split(",") if exclude_books else []
    recs, method = recommender.get_hybrid_recommendations(
        user_id=user_id, n=n,
        rated_book_ids=rated,
        fav_book_ids=favs,
        clicked_book_ids=clicks,
        viewed_book_ids=views,
        exclude_book_ids=exclude
    )
    return RecommendationResponse(
        user_id=user_id,
        recommendations=[RecommendationItem(**r) for r in recs],
        method=method
    )

@router.get("/similar/{book_id}", response_model=RecommendationResponse)
def get_similar_books(
    book_id: str,
    n: int = Query(10, ge=1, le=50)
):
    # Use sync def — FastAPI runs sync routes in threadpool automatically
    # This avoids CUDA threading issues with run_in_executor
    recs = recommender.get_content_recommendations(book_id=book_id, n=n)
    return RecommendationResponse(
        user_id="",
        recommendations=[RecommendationItem(**r) for r in recs],
        method="content"
    )

@router.get("/popular", response_model=RecommendationResponse)
async def get_popular_books(
    n: int = Query(10, ge=1, le=200),
    genre: str = Query(None)
):
    recs = await run_sync(recommender.get_popular, n=n, genre=genre)
    return RecommendationResponse(
        user_id="",
        recommendations=[RecommendationItem(**r) for r in recs],
        method="popular"
    )

@router.get("/trending", response_model=RecommendationResponse)
async def get_trending_books(n: int = Query(10, ge=1, le=200)):
    recs = await run_sync(recommender.get_trending, n=n)
    return RecommendationResponse(
        user_id="",
        recommendations=[RecommendationItem(**r) for r in recs],
        method="trending"
    )


@router.get("/because-searched", response_model=RecommendationResponse)
async def because_searched(
    query: str = Query(..., min_length=1),
    n: int = Query(10, ge=1, le=50),
):
    """Books related to what user just searched."""
    recs = await run_sync(recommender.search, query, n)
    return {"user_id": "system", "recommendations": recs, "method": "search_influenced"}

@router.get("/because-rated/{book_id}", response_model=RecommendationResponse)
def because_rated(
    book_id: str,
    n: int = Query(10, ge=1, le=50),
):
    """Books similar to a specific book the user rated highly."""
    recs = recommender.get_content_recommendations(book_id=book_id, n=n)
    return RecommendationResponse(
        user_id="system",
        recommendations=[RecommendationItem(**r) for r in recs],
        method="content_similar"
    )

@router.get("/by-genre", response_model=RecommendationResponse)
async def by_genre(
    genre: str = Query(..., min_length=1),
    n: int = Query(10, ge=1, le=50),
):
    """Popular books in a specific genre."""
    def _genre_popular(n, genre):
        df = recommender.books_df
        filtered = df[df["genre"].str.lower() == genre.lower()] if "genre" in df.columns else df
        if len(filtered) == 0:
            filtered = df
        top = filtered.nlargest(n, "ratings_count")
        return [recommender._book_to_dict(row, row["ratings_count"], "popular")
                for _, row in top.iterrows()]
    recs = await run_sync(_genre_popular, n, genre)
    return {"user_id": "system", "recommendations": recs, "method": "genre_popular"}

@router.post("/cache/clear")
async def clear_cache():
    recommender.similar_cache.clear()
    if hasattr(recommender, '_trending_cache'):
        del recommender._trending_cache
    return {"status": "cache cleared"}

@router.get("/debug/{book_id}")
def debug_similar(book_id: str):
    """Debug: show raw similarity scores for a book."""
    import numpy as np
    if book_id not in recommender.book2idx:
        return {"error": "book not found", "book2idx_size": len(recommender.book2idx)}
    idx = recommender.book2idx[book_id]
    scores = recommender.embeddings[idx] @ recommender.embeddings.T
    scores[idx] = -1
    top5 = np.argsort(scores)[-5:][::-1]
    results = []
    for i in top5:
        bid = recommender.idx2book[i]
        row = recommender.books_df.iloc[i]
        results.append({
            "position": int(i),
            "book_id": bid,
            "title": row["title"],
            "score": float(scores[i])
        })
    return {
        "query_book_id": book_id,
        "query_idx": idx,
        "embeddings_shape": list(recommender.embeddings.shape),
        "books_df_len": len(recommender.books_df),
        "top5": results
    }
