from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.models.interaction import Interaction
from app.schemas.user import UserCreate, UserResponse, RatingCreate
from app.services.recommender import recommender
import pandas as pd
from pathlib import Path

router = APIRouter(prefix="/users", tags=["Users"])

async def _sync_ucsd_ratings(user_id: str, db: AsyncSession):
    """If user exists in UCSD dataset, sync their ratings to PostgreSQL."""
    try:
        interactions = pd.read_parquet(
            Path.home() / "projects/BookRS-DataPrep/outputs/bookrs_ucsd_interactions.parquet"
        )
        user_ratings = interactions[
            interactions["user_id"].astype(str) == str(user_id)
        ]
        if len(user_ratings) == 0:
            return 0

        # Check if already synced
        existing = await db.execute(
            select(Interaction).where(Interaction.user_id == user_id).limit(1)
        )
        if existing.scalar_one_or_none():
            return 0  # Already synced

        # Insert UCSD ratings
        count = 0
        for _, row in user_ratings.iterrows():
            interaction = Interaction(
                user_id=user_id,
                book_id=str(row["book_id"]),
                rating=int(row["rating"]),
                is_reviewed=int(row["is_reviewed"])
            )
            db.add(interaction)
            count += 1

        await db.commit()
        return count
    except Exception as e:
        print(f"Failed to sync UCSD ratings: {e}")
        return 0

@router.post("/login")
async def login_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Login or create user, sync UCSD ratings if applicable."""
    # Create user if not exists
    existing = await db.get(User, user.user_id)
    if not existing:
        new_user = User(user_id=user.user_id)
        db.add(new_user)
        await db.commit()

    # Sync UCSD ratings
    synced = await _sync_ucsd_ratings(user.user_id, db)
    if synced > 0:
        print(f"Synced {synced} UCSD ratings for user {user.user_id}")

    return {"user_id": user.user_id, "synced_ratings": synced}

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
    # Create user if not exists
    user = await db.get(User, user_id)
    if not user:
        new_user = User(user_id=user_id)
        db.add(new_user)
        await db.commit()

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
    return result.scalars().all()

@router.get("/{user_id}/all-ratings")
async def get_all_ratings(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get combined ratings from both interactions (UCSD) and user_actions tables."""
    # Get UCSD ratings from interactions table
    result1 = await db.execute(
        select(Interaction).where(Interaction.user_id == user_id)
    )
    ucsd_ratings = result1.scalars().all()

    # Get app ratings from user_actions table
    from app.models.user_action import UserAction
    result2 = await db.execute(
        select(UserAction)
        .where(UserAction.user_id == user_id)
        .where(UserAction.action_type == "rating")
    )
    app_ratings = result2.scalars().all()

    # Combine — app ratings override UCSD ratings for same book
    ratings_map = {}

    # First add UCSD ratings
    for r in ucsd_ratings:
        ratings_map[r.book_id] = {
            "book_id": r.book_id,
            "rating": r.rating,
            "source": "ucsd"
        }

    # App ratings override
    for r in app_ratings:
        ratings_map[r.book_id] = {
            "book_id": r.book_id,
            "rating": r.value,
            "source": "app"
        }

    return list(ratings_map.values())
