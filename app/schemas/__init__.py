"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional


# User Schemas
class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Habit Schemas
class HabitBase(BaseModel):
    """Base habit schema"""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    target_frequency: int = 1
    frequency_unit: str = "day"
    color: Optional[str] = None
    icon: Optional[str] = None


class HabitCreate(HabitBase):
    """Schema for creating a habit"""
    pass


class HabitUpdate(BaseModel):
    """Schema for updating a habit"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    target_frequency: Optional[int] = None
    frequency_unit: Optional[str] = None
    is_active: Optional[bool] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class HabitResponse(HabitBase):
    """Schema for habit response"""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# HabitLog Schemas
class HabitLogBase(BaseModel):
    """Base habit log schema"""
    date: date
    completed: int = 0
    value: Optional[float] = None
    notes: Optional[str] = None


class HabitLogCreate(HabitLogBase):
    """Schema for creating a habit log"""
    habit_id: int


class HabitLogUpdate(BaseModel):
    """Schema for updating a habit log"""
    completed: Optional[int] = None
    value: Optional[float] = None
    notes: Optional[str] = None


class HabitLogResponse(HabitLogBase):
    """Schema for habit log response"""
    id: int
    habit_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# DaySummary Schemas
class DaySummaryResponse(BaseModel):
    """Schema for day summary response"""
    id: int
    user_id: int
    date: date
    total_habits: int
    completed_habits: int
    completion_percentage: float
    streak_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# WeekSummary Schemas
class WeekSummaryResponse(BaseModel):
    """Schema for week summary response"""
    id: int
    user_id: int
    week_start_date: date
    total_days_tracked: int
    total_habits_completed: int
    average_completion_percentage: float
    best_day_completion: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
