from fastapi import APIRouter, Query
from typing import Optional
from app.services.recommender import recommender
from app.schemas.recommendation import RecommendationResponse, RecommendationItem

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("/hybrid/{user_id}", response_model=RecommendationResponse)
async def get_hybrid_recommendations(
    user_id: str,
    n: int = Query(10, ge=1, le=50),
    rated_books: Optional[str] = Query(None, description="Comma-separated rated book IDs"),
    exclude_books: Optional[str] = Query(None, description="Comma-separated book IDs to exclude")
):
    rated = rated_books.split(",") if rated_books else []
    exclude = exclude_books.split(",") if exclude_books else []

    recs, method = recommender.get_hybrid_recommendations(
        user_id=user_id, n=n,
        rated_book_ids=rated,
        exclude_book_ids=exclude
    )
    return RecommendationResponse(
        user_id=user_id,
        recommendations=[RecommendationItem(**r) for r in recs],
        method=method
    )

@router.get("/similar/{book_id}", response_model=RecommendationResponse)
async def get_similar_books(book_id: str, n: int = Query(10, ge=1, le=50)):
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
    recs = recommender.get_popular(n=n, genre=genre)
    return RecommendationResponse(
        user_id="",
        recommendations=[RecommendationItem(**r) for r in recs],
        method="popular"
    )

@router.get("/trending", response_model=RecommendationResponse)
async def get_trending_books(n: int = Query(10, ge=1, le=200)):
    recs = recommender.get_trending(n=n)
    return RecommendationResponse(
        user_id="",
        recommendations=[RecommendationItem(**r) for r in recs],
        method="trending"
    )
