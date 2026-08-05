from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Book(Base):
    __tablename__ = "books"

    book_id = Column(String, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    authors = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    genre = Column(String, nullable=True, index=True)
    avg_rating = Column(Float, default=0.0)
    ratings_count = Column(Integer, default=0)
    isbn13 = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
