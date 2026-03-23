from pydantic import BaseModel
from typing import Optional

class RecommendationItem(BaseModel):
    book_id: str
    title: str
    authors: str
    genre: Optional[str] = None
    avg_rating: float = 0.0
    image_url: Optional[str] = None
    score: float = 0.0
    reason: Optional[str] = None

class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: list[RecommendationItem]
    method: str  # "hybrid", "content", "collaborative", "popular"

class SearchResponse(BaseModel):
    query: str
    results: list[RecommendationItem]
    total: int
