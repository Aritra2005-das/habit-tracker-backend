"""
Service for generating weekly recommendations based on summary data
Integrates with weekly summary generation for automatic adjustment suggestions
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.models import Habit, WeekSummary, HabitLog, WeeklyRecommendation
from app.services.decision_engine import DecisionEngine
from app.services.failure_analysis import FailureAnalyzer
from app.schemas.recommendation import RecommendationType


class WeeklyRecommendationGenerator:
    """
    Generates and stores weekly adjustment recommendations
    Called automatically after weekly summary calculation
    """
    
    def __init__(self, db: Session):
        """
        Initialize the weekly recommendation generator
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.decision_engine = DecisionEngine(db)
        self.failure_analyzer = FailureAnalyzer(db)
    
    def generate_weekly_recommendations(
        self,
        user_id: int,
        week_start_date: str
    ) -> List[WeeklyRecommendation]:
        """
        Generate recommendations for a completed week
        This should be called after weekly summary generation
        
        Args:
            user_id: ID of the user
            week_start_date: Start date of the week (YYYY-MM-DD format)
        
        Returns:
            List of generated WeeklyRecommendation objects
        """
        recommendations = []
        
        # Get all active habits for user
        habits = self.db.query(Habit).filter(
            and_(
                Habit.user_id == user_id,
                Habit.is_active == True
            )
        ).all()
        
        # Get weekly summary for analysis
        week_summary = self._get_week_summary(user_id, week_start_date)
        
        for habit in habits:
            # Check various conditions and generate recommendations
            habit_recs = self._generate_habit_weekly_recommendations(
                habit, user_id, week_start_date, week_summary
            )
            recommendations.extend(habit_recs)
        
        # Save all recommendations to database
        self._save_recommendations(recommendations, user_id, week_start_date)
        
        return recommendations
    
    def _generate_habit_weekly_recommendations(
        self,
        habit: Habit,
        user_id: int,
        week_start_date: str,
        week_summary: Optional[WeekSummary]
    ) -> List[WeeklyRecommendation]:
        """
        Generate recommendations for a specific habit
        
        Args:
            habit: The habit to analyze
            user_id: User ID
            week_start_date: Week start date
            week_summary: The week's summary (optional)
        
        Returns:
            List of WeeklyRecommendation objects
        """
        recommendations = []
        
        # Get this week's completion for the habit
        week_completion = self._get_habit_week_completion(habit.id, user_id, week_start_date)
        
        # Rule 1: Very low completion (< 30%)
        if week_completion < 30:
            rec = WeeklyRecommendation(
                user_id=user_id,
                habit_id=habit.id,
                week_start_date=week_start_date,
                recommendation_type=RecommendationType.REDUCE_SCOPE,
                suggestion=f"Consider reducing the scope of '{habit.name}'",
                details=(
                    f"This week you completed '{habit.name}' only {week_completion:.0f}% of the time. "
                    f"This suggests the habit might be too ambitious. Try reducing the frequency or "
                    f"difficulty, and rebuild from there."
                )
            )
            recommendations.append(rec)
        
        # Rule 2: Check for repeated failures this week
        repeated_failures = self.failure_analyzer.identify_repeated_failures(
            habit.id, user_id, days=7
        )
        if repeated_failures and repeated_failures[0]["occurrences"] >= 2:
            top_failure = repeated_failures[0]
            rec = WeeklyRecommendation(
                user_id=user_id,
                habit_id=habit.id,
                week_start_date=week_start_date,
                recommendation_type=RecommendationType.REDESIGN_HABIT,
                suggestion=f"Redesign '{habit.name}' to address '{top_failure['pattern']}'",
                details=(
                    f"This week, '{habit.name}' failed {top_failure['occurrences']} times "
                    f"due to '{top_failure['pattern']}'. Next week, try a different approach "
                    f"that accounts for this barrier."
                )
            )
            recommendations.append(rec)
        
        # Rule 3: Excellent completion - suggest stretch
        if week_completion >= 85:
            rec = WeeklyRecommendation(
                user_id=user_id,
                habit_id=habit.id,
                week_start_date=week_start_date,
                recommendation_type=RecommendationType.ADD_STRETCH,
                suggestion=f"Add a stretch goal to '{habit.name}'",
                details=(
                    f"Great job! You completed '{habit.name}' {week_completion:.0f}% of the time. "
                    f"Next week, challenge yourself by increasing the frequency or difficulty. "
                    f"This will help you continue growing."
                )
            )
            recommendations.append(rec)
        
        # Rule 4: Moderate improvement
        if 70 <= week_completion < 85:
            rec = WeeklyRecommendation(
                user_id=user_id,
                habit_id=habit.id,
                week_start_date=week_start_date,
                recommendation_type=RecommendationType.CONSISTENCY_IMPROVEMENT,
                suggestion=f"Build consistency with '{habit.name}'",
                details=(
                    f"You're doing well with '{habit.name}' at {week_completion:.0f}% completion. "
                    f"Next week, focus on the {100 - week_completion:.0f}% you missed and aim for 90%+."
                )
            )
            recommendations.append(rec)
        
        # Rule 5: Schedule-related issues
        failure_patterns = self.failure_analyzer.get_failure_patterns_for_habit(
            habit.id, user_id, days=7
        )
        if failure_patterns["common_failure_days"]:
            top_failure_day = failure_patterns["common_failure_days"][0]
            rec = WeeklyRecommendation(
                user_id=user_id,
                habit_id=habit.id,
                week_start_date=week_start_date,
                recommendation_type=RecommendationType.SCHEDULE_ADJUSTMENT,
                suggestion=f"Adjust '{habit.name}' schedule on {top_failure_day['day']}s",
                details=(
                    f"You missed '{habit.name}' most often on {top_failure_day['day']}s "
                    f"({top_failure_day['count']} times). Try scheduling it at a different time "
                    f"on that day, or prepare in advance."
                )
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _get_habit_week_completion(
        self,
        habit_id: int,
        user_id: int,
        week_start_date: str
    ) -> float:
        """
        Get completion percentage for a habit in a specific week
        
        Args:
            habit_id: ID of the habit
            user_id: ID of the user
            week_start_date: Start date of the week (YYYY-MM-DD)
        
        Returns:
            Completion percentage (0-100)
        """
        from datetime import datetime
        
        start_date = datetime.strptime(week_start_date, "%Y-%m-%d").date()
        end_date = start_date + timedelta(days=6)
        
        logs = self.db.query(HabitLog).filter(
            and_(
                HabitLog.habit_id == habit_id,
                HabitLog.user_id == user_id,
                HabitLog.date >= start_date,
                HabitLog.date <= end_date
            )
        ).all()
        
        if not logs:
            return 0.0
        
        completed = sum(1 for log in logs if log.completed == 1)
        return (completed / len(logs)) * 100
    
    def _get_week_summary(
        self,
        user_id: int,
        week_start_date: str
    ) -> Optional[WeekSummary]:
        """
        Get the week summary for a specific week
        
        Args:
            user_id: ID of the user
            week_start_date: Start date of the week (YYYY-MM-DD)
        
        Returns:
            WeekSummary object if exists, None otherwise
        """
        return self.db.query(WeekSummary).filter(
            and_(
                WeekSummary.user_id == user_id,
                WeekSummary.week_start_date == week_start_date
            )
        ).first()
    
    def _save_recommendations(
        self,
        recommendations: List[WeeklyRecommendation],
        user_id: int,
        week_start_date: str
    ) -> None:
        """
        Save recommendations to the database
        Removes old recommendations for the same week first
        
        Args:
            recommendations: List of recommendation objects to save
            user_id: ID of the user
            week_start_date: Start date of the week
        """
        # Delete existing recommendations for this week
        self.db.query(WeeklyRecommendation).filter(
            and_(
                WeeklyRecommendation.user_id == user_id,
                WeeklyRecommendation.week_start_date == week_start_date
            )
        ).delete()
        
        # Add new recommendations
        for rec in recommendations:
            self.db.add(rec)
        
        # Commit changes
        self.db.commit()
    
    def get_pending_recommendations(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[WeeklyRecommendation]:
        """
        Get pending recommendations that haven't been acted upon
        
        Args:
            user_id: ID of the user
            limit: Maximum number of recommendations to return
        
        Returns:
            List of pending WeeklyRecommendation objects
        """
        return self.db.query(WeeklyRecommendation).filter(
            and_(
                WeeklyRecommendation.user_id == user_id,
                WeeklyRecommendation.is_acted_upon == 0
            )
        ).order_by(
            WeeklyRecommendation.created_at.desc()
        ).limit(limit).all()
    
    def mark_recommendation_acted_upon(
        self,
        recommendation_id: int
    ) -> WeeklyRecommendation:
        """
        Mark a recommendation as acted upon
        
        Args:
            recommendation_id: ID of the recommendation
        
        Returns:
            Updated WeeklyRecommendation object
        """
        rec = self.db.query(WeeklyRecommendation).get(recommendation_id)
        
        if rec:
            rec.is_acted_upon = 1
            rec.acted_upon_date = datetime.utcnow()
            self.db.commit()
        
        return rec
    
    def get_recommendations_by_week(
        self,
        user_id: int,
        week_start_date: str
    ) -> List[WeeklyRecommendation]:
        """
        Get all recommendations for a specific week
        
        Args:
            user_id: ID of the user
            week_start_date: Start date of the week (YYYY-MM-DD)
        
        Returns:
            List of WeeklyRecommendation objects for that week
        """
        return self.db.query(WeeklyRecommendation).filter(
            and_(
                WeeklyRecommendation.user_id == user_id,
                WeeklyRecommendation.week_start_date == week_start_date
            )
        ).all()
