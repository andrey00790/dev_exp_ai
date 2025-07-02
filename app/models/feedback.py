"""
Feedback Model for user feedback collection
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Feedback(Base):
    """User feedback model"""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(String(255), nullable=False, index=True)
    context = Column(String(100), nullable=False)  # search_result, rfc_generation, etc.
    feedback_type = Column(String(50), nullable=False)  # like, dislike, rating
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    comment = Column(Text, nullable=True)
    user_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __init__(
        self,
        target_id: str,
        context: str,
        feedback_type: str,
        rating: int = None,
        comment: str = None,
        user_id: str = None,
    ):
        self.target_id = target_id
        self.context = context
        self.feedback_type = feedback_type
        self.rating = rating
        self.comment = comment
        self.user_id = user_id
