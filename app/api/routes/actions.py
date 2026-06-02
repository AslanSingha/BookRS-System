from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.user_action import UserAction
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/actions", tags=["User Actions"])

class ActionCreate(BaseModel):
    user_id: str
    book_id: str
    action_type: str  # 'view', 'favorite', 'search_click', 'rating'
    value: Optional[int] = 0

@router.post("/")
async def log_action(action: ActionCreate, db: AsyncSession = Depends(get_db)):
    """Log a user action for implicit feedback."""
    new_action = UserAction(
        user_id=action.user_id,
        book_id=action.book_id,
        action_type=action.action_type,
        value=action.value
    )
    db.add(new_action)
    await db.commit()
    return {"status": "logged", "action": action.action_type}

@router.get("/{user_id}")
async def get_user_actions(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get all actions for a user."""
    result = await db.execute(
        select(UserAction)
        .where(UserAction.user_id == user_id)
        .order_by(UserAction.created_at.desc())
        .limit(100)
    )
    actions = result.scalars().all()
    return actions

@router.get("/{user_id}/favorites")
async def get_user_favorites(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get user's favorited books."""
    result = await db.execute(
        select(UserAction)
        .where(UserAction.user_id == user_id)
        .where(UserAction.action_type == "favorite")
    )
    return result.scalars().all()

from sqlalchemy import delete as sql_delete

@router.delete("/{user_id}/{action_type}/{book_id}")
async def delete_action(
    user_id: str,
    action_type: str,
    book_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove a specific user action (e.g. unfavorite a book)."""
    result = await db.execute(
        select(UserAction)
        .where(UserAction.user_id == user_id)
        .where(UserAction.action_type == action_type)
        .where(UserAction.book_id == book_id)
    )
    action = result.scalar_one_or_none()
    if action is None:
        return {"status": "not_found"}
    await db.delete(action)
    await db.commit()
    return {"status": "deleted", "action_type": action_type, "book_id": book_id}

@router.post("/toggle-favorite")
async def toggle_favorite(
    action: ActionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Toggle favorite — add if not exists, remove if exists."""
    result = await db.execute(
        select(UserAction)
        .where(UserAction.user_id == action.user_id)
        .where(UserAction.action_type == "favorite")
        .where(UserAction.book_id == action.book_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        await db.delete(existing)
        await db.commit()
        return {"status": "removed", "favorited": False}
    else:
        new_action = UserAction(
            user_id=action.user_id,
            book_id=action.book_id,
            action_type="favorite",
            value=action.value
        )
        db.add(new_action)
        await db.commit()
        return {"status": "added", "favorited": True}
