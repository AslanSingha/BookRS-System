from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.book import Book
from app.schemas.book import BookDetail, BookList

router = APIRouter(prefix="/books", tags=["Books"])

@router.get("/", response_model=BookList)
async def get_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    genre: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Book)
    count_query = select(func.count(Book.book_id))

    if genre:
        query = query.where(Book.genre == genre)
        count_query = count_query.where(Book.genre == genre)

    total = await db.scalar(count_query)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    books = result.scalars().all()

    return BookList(books=books, total=total, page=page, page_size=page_size)

@router.get("/genres")
async def get_genres(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book.genre, func.count(Book.book_id).label("count"))
        .group_by(Book.genre)
        .order_by(func.count(Book.book_id).desc())
    )
    return [{"genre": row.genre, "count": row.count} for row in result]

@router.get("/{book_id}", response_model=BookDetail)
async def get_book(book_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.book_id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book
