"""
WeekSummary model for weekly habit statistics
"""
from sqlalchemy import Column, Integer, ForeignKey, Date, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import BaseModel


class WeekSummary(BaseModel):
    """WeekSummary entity - aggregated weekly statistics for user's habits"""
    __tablename__ = "week_summaries"
    __table_args__ = (
        UniqueConstraint('user_id', 'week_start_date', name='uq_week_summaries_user_id_week_start_date'),
    )
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start_date = Column(Date, nullable=False, index=True)  # Monday of the week
    total_days_tracked = Column(Integer, default=0, nullable=False)  # Days with activity
    total_habits_completed = Column(Integer, default=0, nullable=False)  # Total completions
    average_completion_percentage = Column(Float, default=0.0, nullable=False)  # Average 0-100
    best_day_completion = Column(Float, default=0.0, nullable=False)  # Highest day completion %
    
    # Relationships
    user = relationship("User", back_populates="week_summaries")
    
    def __repr__(self) -> str:
        return f"<WeekSummary(id={self.id}, user_id={self.user_id}, week_start_date={self.week_start_date})>"
