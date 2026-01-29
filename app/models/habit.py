"""
Habit model for user habits
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import BaseModel


class Habit(BaseModel):
    """Habit entity - individual habits tracked by users"""
    __tablename__ = "habits"
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_habits_user_id_name'),
    )
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    target_frequency = Column(Integer, default=1, nullable=False)  # e.g., daily = 1
    frequency_unit = Column(String(20), default="day", nullable=False)  # "day", "week", "month"
    is_active = Column(Boolean, default=True, nullable=False)
    color = Column(String(7), nullable=True)  # Hex color code
    icon = Column(String(100), nullable=True)  # Icon identifier
    
    # Relationships
    user = relationship("User", back_populates="habits")
    logs = relationship("HabitLog", back_populates="habit", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Habit(id={self.id}, user_id={self.user_id}, name={self.name})>"
