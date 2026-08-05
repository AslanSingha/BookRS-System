from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class UserAction(Base):
    __tablename__ = "user_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    book_id = Column(String, index=True, nullable=False)
    action_type = Column(String, nullable=False)  # view, favorite, search_click, rating
    value = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
