"""
Integration utilities for weekly summary and recommendations
"""
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import WeekSummary
from app.services.weekly_recommendations import WeeklyRecommendationGenerator


def generate_recommendations_for_week(
    user_id: int,
    week_start_date: str,
    db: Session
) -> None:
    """
    Generate and store recommendations after a weekly summary is created
    This function should be called whenever a new weekly summary is generated
    
    Args:
        user_id: ID of the user
        week_start_date: Start date of the week (YYYY-MM-DD format)
        db: Database session
    """
    try:
        generator = WeeklyRecommendationGenerator(db)
        generator.generate_weekly_recommendations(user_id, week_start_date)
    except Exception as e:
        # Log error but don't fail the main summary generation
        print(f"Error generating recommendations for week {week_start_date}: {str(e)}")


def get_weekly_summary_with_recommendations(
    user_id: int,
    week_start_date: str,
    db: Session
) -> dict:
    """
    Get a weekly summary with its associated recommendations
    
    Args:
        user_id: ID of the user
        week_start_date: Start date of the week (YYYY-MM-DD format)
        db: Database session
    
    Returns:
        Dictionary containing week summary and recommendations
    """
    from app.models import WeeklyRecommendation
    
    # Get week summary
    week_summary = db.query(WeekSummary).filter(
        WeekSummary.user_id == user_id,
        WeekSummary.week_start_date == week_start_date
    ).first()
    
    # Get recommendations
    recommendations = db.query(WeeklyRecommendation).filter(
        WeeklyRecommendation.user_id == user_id,
        WeeklyRecommendation.week_start_date == week_start_date
    ).all()
    
    return {
        "week_summary": week_summary,
        "recommendations": recommendations,
        "has_recommendations": len(recommendations) > 0
    }
