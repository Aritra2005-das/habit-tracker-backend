"""
HabitLog model for tracking individual habit completions
"""
from sqlalchemy import Column, Integer, ForeignKey, Date, Text, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import date
from .base import BaseModel


class HabitLog(BaseModel):
    """HabitLog entity - individual log entries for habit completions"""
    __tablename__ = "habit_logs"
    __table_args__ = (
        UniqueConstraint('habit_id', 'user_id', 'date', name='uq_habit_logs_habit_id_user_id_date'),
    )
    
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    completed = Column(Integer, default=0, nullable=False)  # 0 = not completed, 1 = completed
    value = Column(Float, nullable=True)  # Optional numeric value (e.g., hours, distance)
    notes = Column(Text, nullable=True)
    
    # Relationships
    habit = relationship("Habit", back_populates="logs")
    user = relationship("User", back_populates="habit_logs")
    
    def __repr__(self) -> str:
        return f"<HabitLog(id={self.id}, habit_id={self.habit_id}, date={self.date}, completed={self.completed})>"
