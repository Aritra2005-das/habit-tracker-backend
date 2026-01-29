"""
User model for authentication and user management
"""
from sqlalchemy import Column, String, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import BaseModel


class User(BaseModel):
    """User entity for habit tracking application"""
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint('email', name='uq_users_email'),
    )
    
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    habit_logs = relationship("HabitLog", back_populates="user", cascade="all, delete-orphan")
    day_summaries = relationship("DaySummary", back_populates="user", cascade="all, delete-orphan")
    week_summaries = relationship("WeekSummary", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
