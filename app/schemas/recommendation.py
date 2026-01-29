"""
Pydantic schemas for recommendations
"""
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List
from datetime import datetime


class RecommendationType(str, Enum):
    """Types of recommendations"""
    REDUCE_SCOPE = "reduce_scope"
    REDESIGN_HABIT = "redesign_habit"
    ADD_STRETCH = "add_stretch"
    ENABLE_NEW_HABIT = "enable_new_habit"
    CONSISTENCY_IMPROVEMENT = "consistency_improvement"
    SCHEDULE_ADJUSTMENT = "schedule_adjustment"


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FailurePattern(BaseModel):
    """Failure pattern information"""
    pattern: str = Field(..., description="Description of the failure pattern")
    frequency: int = Field(..., ge=0, description="Number of times this pattern occurred")
    percentage: float = Field(..., ge=0, le=100, description="Percentage of total failures")
    last_occurred: Optional[datetime] = Field(None, description="When this pattern last occurred")


class HabitRecommendation(BaseModel):
    """Individual recommendation for a habit"""
    habit_id: int = Field(..., description="ID of the habit")
    habit_name: str = Field(..., description="Name of the habit")
    recommendation_type: RecommendationType = Field(..., description="Type of recommendation")
    title: str = Field(..., description="Short title of the recommendation")
    description: str = Field(..., description="Detailed description of the recommendation")
    action_items: List[str] = Field(default_factory=list, description="Specific actions to take")
    priority: RecommendationPriority = Field(default=RecommendationPriority.MEDIUM)
    reason: str = Field(..., description="Why this recommendation was made")
    
    # Supporting metrics
    current_completion_rate: Optional[float] = Field(
        None, ge=0, le=100, description="Current completion percentage"
    )
    trend: Optional[str] = Field(
        None, description="Trend direction: up, down, or stable"
    )
    failure_patterns: List[FailurePattern] = Field(
        default_factory=list, description="Common failure patterns for this habit"
    )
    
    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    """Response containing recommendations for a user"""
    user_id: int = Field(..., description="User ID")
    generated_at: datetime = Field(..., description="When recommendations were generated")
    
    # Habit-level recommendations
    habit_recommendations: List[HabitRecommendation] = Field(
        default_factory=list, description="Recommendations for individual habits"
    )
    
    # System-level recommendations
    system_recommendations: List[str] = Field(
        default_factory=list, description="General system-level recommendations"
    )
    
    # Summary statistics
    total_habits_tracked: int = Field(ge=0, description="Total number of active habits")
    average_completion_rate: float = Field(
        ge=0, le=100, description="Average completion rate across all habits"
    )
    habits_needing_attention: int = Field(
        ge=0, description="Number of habits with recommendations"
    )
    
    # Actionable next steps
    next_steps: List[str] = Field(
        default_factory=list, description="Prioritized actions for the user"
    )
    
    class Config:
        from_attributes = True


class ScopeReductionRecommendation(HabitRecommendation):
    """Recommendation to reduce habit scope"""
    recommendation_type: RecommendationType = RecommendationType.REDUCE_SCOPE
    
    # Specific metrics
    bad_weeks_count: int = Field(..., description="Number of consecutive bad weeks")
    suggested_reduction: str = Field(..., description="Suggested reduction (e.g., 5x → 3x per week)")


class HabitRedesignRecommendation(HabitRecommendation):
    """Recommendation to redesign a habit"""
    recommendation_type: RecommendationType = RecommendationType.REDESIGN_HABIT
    
    # Specific metrics
    failure_count: int = Field(..., description="Number of times same failure occurred")
    failure_type: str = Field(..., description="Type of failure (e.g., 'time constraint')")


class StretchRecommendation(HabitRecommendation):
    """Recommendation to add stretch goal"""
    recommendation_type: RecommendationType = RecommendationType.ADD_STRETCH
    
    # Specific metrics
    stability_score: float = Field(..., ge=0, le=100, description="Stability score")
    trend_days: int = Field(..., ge=0, description="Days of stable performance")
    suggested_stretch: str = Field(..., description="Suggested stretch goal")


class NewHabitEnabledRecommendation(HabitRecommendation):
    """Recommendation indicating new habit can be enabled"""
    recommendation_type: RecommendationType = RecommendationType.ENABLE_NEW_HABIT
    
    # Specific metrics
    weeks_at_threshold: int = Field(..., description="Weeks at 85%+ completion")
    consistency_score: float = Field(..., ge=0, le=100, description="Consistency score")


class WeeklyAdjustmentRecommendation(BaseModel):
    """Auto-generated recommendation for weekly summary"""
    week_start_date: str = Field(..., description="Start date of the week (YYYY-MM-DD)")
    habit_id: int = Field(..., description="ID of the habit")
    recommendation_type: RecommendationType = Field(..., description="Type of recommendation")
    suggestion: str = Field(..., description="The recommendation suggestion")
    created_at: datetime = Field(..., description="When the recommendation was created")
    
    class Config:
        from_attributes = True
