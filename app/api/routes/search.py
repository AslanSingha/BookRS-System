from fastapi import APIRouter, Query
from app.services.recommender import recommender
from app.schemas.recommendation import SearchResponse, RecommendationItem

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/", response_model=SearchResponse)
async def search_books(
    q: str = Query(..., min_length=1, description="Search query"),
    n: int = Query(10, ge=1, le=50)
):
    results = recommender.search(query=q, n=n)
    return SearchResponse(
        query=q,
        results=[RecommendationItem(**r) for r in results],
        total=len(results)
    )
