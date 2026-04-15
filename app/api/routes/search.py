from fastapi import APIRouter, Query
from typing import Optional
from app.services.recommender import recommender
from app.schemas.recommendation import SearchResponse, RecommendationItem

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/", response_model=SearchResponse)
async def search_books(
    q: str = Query(..., min_length=1),
    n: int = Query(10, ge=1, le=50)
):
    """Pure semantic search using SBERT."""
    results = recommender.search(query=q, n=n)
    return SearchResponse(
        query=q,
        results=[RecommendationItem(**r) for r in results],
        total=len(results)
    )

@router.get("/personalized", response_model=SearchResponse)
async def personalized_search(
    q: str = Query(..., min_length=1),
    user_id: str = Query(...),
    n: int = Query(10, ge=1, le=50),
    rated_books: Optional[str] = Query(None)
):
    """Personalized search: SBERT query + ALS user preferences."""
    rated = rated_books.split(",") if rated_books else []
    results = recommender.personalized_search(
        query=q,
        user_id=user_id,
        rated_book_ids=rated,
        n=n
    )
    return SearchResponse(
        query=q,
        results=[RecommendationItem(**r) for r in results],
        total=len(results)
    )
