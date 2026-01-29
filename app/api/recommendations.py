"""
API routes for recommendations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.schemas.recommendation import RecommendationResponse
from app.services.decision_engine import DecisionEngine

# Create router
router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.get("", response_model=RecommendationResponse)
async def get_recommendations(
    user_id: int,
    db: Session = Depends(get_db)
) -> RecommendationResponse:
    """
    Get intelligent recommendations for a user based on their habit data
    
    This endpoint analyzes the user's habit tracking data and generates:
    - Individual habit recommendations (reduce scope, redesign, stretch, etc.)
    - System-level insights and suggestions
    - Prioritized action items
    
    Rules applied:
    1. 2 bad weeks (< 50% completion) → suggest reducing scope
    2. Repeated failure pattern (3+) → suggest habit redesign
    3. High stability (70%+) + low trend → suggest adding stretch goal
    4. 85%+ for 3 weeks → indicate readiness for new habit
    
    Args:
        user_id: The user ID to generate recommendations for
        db: Database session (injected)
    
    Returns:
        RecommendationResponse containing all recommendations and insights
    
    Raises:
        HTTPException 404: If user not found
        HTTPException 500: If recommendation generation fails
    
    Example:
        GET /api/v1/recommendations?user_id=1
        
        Response:
        {
            "user_id": 1,
            "generated_at": "2024-01-28T10:30:45.123456",
            "habit_recommendations": [
                {
                    "habit_id": 1,
                    "habit_name": "Morning Run",
                    "recommendation_type": "reduce_scope",
                    "title": "Consider Reducing Habit Scope",
                    "description": "Your 'Morning Run' habit has had 2 consecutive weeks...",
                    "action_items": [...],
                    "priority": "high",
                    "reason": "2 consecutive weeks below 50% completion threshold",
                    "current_completion_rate": 35.5,
                    "trend": "down",
                    "failure_patterns": [...]
                }
            ],
            "system_recommendations": [
                "💡 Your overall completion is below 50%...",
                "⚠️ 2 habit(s) have high failure rates..."
            ],
            "total_habits_tracked": 5,
            "average_completion_rate": 62.5,
            "habits_needing_attention": 2,
            "next_steps": [
                "1. Consider Reducing Habit Scope for 'Morning Run'",
                "2. Redesign Habit for Better Success for 'Meditation'"
            ]
        }
    """
    try:
        # Create decision engine
        engine = DecisionEngine(db)
        
        # Generate recommendations
        recommendations = engine.generate_recommendations(user_id)
        
        return recommendations
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.get("/habit/{habit_id}", response_model=RecommendationResponse)
async def get_habit_recommendations(
    habit_id: int,
    user_id: int,
    db: Session = Depends(get_db)
) -> RecommendationResponse:
    """
    Get detailed recommendations for a specific habit
    
    Analyzes a single habit in detail and provides:
    - Specific recommendations for this habit
    - Failure pattern analysis
    - Comparison with user's other habits
    
    Args:
        habit_id: The habit ID to analyze
        user_id: The user ID (for validation)
        db: Database session (injected)
    
    Returns:
        RecommendationResponse with habit-specific recommendations
    
    Raises:
        HTTPException 404: If habit not found or doesn't belong to user
        HTTPException 500: If analysis fails
    """
    try:
        from app.models import Habit
        
        # Verify habit belongs to user
        habit = db.query(Habit).filter(
            Habit.id == habit_id,
            Habit.user_id == user_id
        ).first()
        
        if not habit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Habit not found"
            )
        
        # Create decision engine
        engine = DecisionEngine(db)
        
        # Generate recommendations for this habit only
        recommendations = engine._generate_habit_recommendations(habit, user_id)
        
        return RecommendationResponse(
            user_id=user_id,
            generated_at=datetime.utcnow(),
            habit_recommendations=recommendations,
            system_recommendations=[],
            total_habits_tracked=1,
            average_completion_rate=engine._get_current_completion_rate(habit, user_id),
            habits_needing_attention=len(recommendations),
            next_steps=[
                f"• {rec.title}" for rec in recommendations
            ]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate habit recommendations: {str(e)}"
        )


@router.get("/failure-analysis", response_model=dict)
async def get_failure_analysis(
    user_id: int,
    days: int = 14,
    db: Session = Depends(get_db)
) -> dict:
    """
    Get detailed failure analysis for all user habits
    
    Analyzes failure patterns and provides:
    - Failure rate per habit
    - Common failure reasons
    - Consecutive failure streaks
    - Patterns by day of week
    
    Args:
        user_id: The user ID
        days: Number of days to analyze (default: 14)
        db: Database session (injected)
    
    Returns:
        Dictionary with detailed failure analysis
    
    Example response:
        {
            "user_id": 1,
            "analysis_period_days": 14,
            "total_habits": 5,
            "habits_with_failures": 3,
            "top_failure_reasons": {
                "time": 5,
                "tired": 3,
                "forgot": 2
            },
            "habits": {
                "1": {
                    "habit_id": 1,
                    "habit_name": "Morning Run",
                    "total_days_tracked": 14,
                    "total_failures": 5,
                    "failure_rate": 35.71,
                    "consecutive_failures": 2,
                    "common_failure_days": [
                        {"day": "Monday", "count": 2},
                        {"day": "Friday", "count": 1}
                    ],
                    "patterns": {
                        "time": 3,
                        "tired": 2
                    }
                }
            }
        }
    """
    try:
        from app.models import Habit
        
        engine = DecisionEngine(db)
        
        # Get all user habits
        habits = db.query(Habit).filter(Habit.user_id == user_id).all()
        
        # Get failure patterns for all habits
        all_patterns = engine.failure_analyzer.get_failure_patterns_for_user(
            user_id, days=days
        )
        
        # Get top failure reasons
        top_reasons = engine.failure_analyzer.get_top_failure_reasons_across_habits(
            user_id, days=days
        )
        
        # Get critical habits
        critical_habits = engine.failure_analyzer.get_habits_with_critical_failures(
            user_id, failure_rate_threshold=50.0
        )
        
        return {
            "user_id": user_id,
            "analysis_period_days": days,
            "total_habits": len(habits),
            "habits_with_failures": len([h for h in all_patterns.values() if h["total_failures"] > 0]),
            "top_failure_reasons": top_reasons,
            "critical_habits": critical_habits,
            "habits": all_patterns
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate failure analysis: {str(e)}"
        )
