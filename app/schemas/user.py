from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    user_id: str

class UserResponse(BaseModel):
    user_id: str
    created_at: datetime
    is_active: bool
    rating_count: Optional[int] = 0

    class Config:
        from_attributes = True

class RatingCreate(BaseModel):
    book_id: str
    rating: int
    is_reviewed: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "book_id": "1333909",
                "rating": 5,
                "is_reviewed": 1
            }
        }
