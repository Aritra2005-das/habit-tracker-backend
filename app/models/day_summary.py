"""
DaySummary model for daily habit statistics
"""
from sqlalchemy import Column, Integer, ForeignKey, Date, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import BaseModel


class DaySummary(BaseModel):
    """DaySummary entity - aggregated daily statistics for user's habits"""
    __tablename__ = "day_summaries"
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_day_summaries_user_id_date'),
    )
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_habits = Column(Integer, default=0, nullable=False)  # Total habits for the user
    completed_habits = Column(Integer, default=0, nullable=False)  # Habits completed on this day
    completion_percentage = Column(Float, default=0.0, nullable=False)  # Percentage 0-100
    streak_count = Column(Integer, default=0, nullable=False)  # Current streak
    
    # Relationships
    user = relationship("User", back_populates="day_summaries")
    
    def __repr__(self) -> str:
        return f"<DaySummary(id={self.id}, user_id={self.user_id}, date={self.date}, completion={self.completion_percentage}%)>"
