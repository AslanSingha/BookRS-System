from pydantic import BaseModel
from typing import Optional

class BookBase(BaseModel):
    book_id: str
    title: str
    authors: str
    genre: Optional[str] = None
    avg_rating: float = 0.0
    ratings_count: int = 0
    image_url: Optional[str] = None

class BookDetail(BookBase):
    description: Optional[str] = None
    isbn13: Optional[str] = None

    class Config:
        from_attributes = True

class BookList(BaseModel):
    books: list[BookBase]
    total: int
    page: int
    page_size: int
