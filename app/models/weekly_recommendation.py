"""
Weekly adjustment recommendation model for storing auto-generated recommendations
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class WeeklyRecommendation(BaseModel):
    """
    Auto-generated recommendation for a weekly summary
    Stores recommendations that were automatically generated for adjustment guidance
    """
    __tablename__ = "weekly_recommendations"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD format
    recommendation_type = Column(String(50), nullable=False)  # reduce_scope, redesign_habit, etc.
    suggestion = Column(String(500), nullable=False)  # The recommendation text
    details = Column(String(1000), nullable=True)  # Detailed explanation
    is_acted_upon = Column(Integer, default=0, nullable=False)  # 0 = no, 1 = yes
    acted_upon_date = Column(DateTime(timezone=True), nullable=True)  # When user acted on it
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    habit = relationship("Habit", foreign_keys=[habit_id])
    
    def __repr__(self) -> str:
        return (
            f"<WeeklyRecommendation("
            f"id={self.id}, "
            f"habit_id={self.habit_id}, "
            f"week_start_date={self.week_start_date}, "
            f"type={self.recommendation_type}"
            f")>"
        )
