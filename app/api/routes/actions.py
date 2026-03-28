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
