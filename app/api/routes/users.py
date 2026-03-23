from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.models.interaction import Interaction
from app.schemas.user import UserCreate, UserResponse, RatingCreate

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.get(User, user.user_id)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = User(user_id=user.user_id)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/{user_id}/ratings")
async def add_rating(
    user_id: str,
    rating: RatingCreate,
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    interaction = Interaction(
        user_id=user_id,
        book_id=rating.book_id,
        rating=rating.rating,
        is_reviewed=rating.is_reviewed
    )
    db.add(interaction)
    await db.commit()
    return {"message": "Rating added successfully"}

@router.get("/{user_id}/ratings")
async def get_user_ratings(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Interaction).where(Interaction.user_id == user_id)
    )
    interactions = result.scalars().all()
    return interactions
