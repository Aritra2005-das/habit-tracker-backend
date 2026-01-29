"""
Decision engine for intelligent habit recommendations
Implements rule-based logic for habit analysis and suggestions
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from app.models import Habit, HabitLog, DaySummary, WeekSummary
from app.schemas.recommendation import (
    HabitRecommendation, RecommendationType, RecommendationPriority,
    ScopeReductionRecommendation, HabitRedesignRecommendation,
    StretchRecommendation, NewHabitEnabledRecommendation,
    FailurePattern, RecommendationResponse
)
from app.services.failure_analysis import FailureAnalyzer


class DecisionEngine:
    """
    Rule-based decision engine for generating habit recommendations
    
    Rules:
    1. 2 bad weeks → suggest reducing scope
    2. Repeated same failure → suggest habit redesign
    3. High stability + low trend → suggest adding stretch
    4. Index ≥85 for 3 weeks → allow new habit
    """
    
    def __init__(self, db: Session):
        """
        Initialize the decision engine
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.failure_analyzer = FailureAnalyzer(db)
    
    def generate_recommendations(self, user_id: int) -> RecommendationResponse:
        """
        Generate all recommendations for a user
        
        Args:
            user_id: ID of the user
        
        Returns:
            RecommendationResponse with all recommendations
        """
        # Get user's active habits
        habits = self.db.query(Habit).filter(
            and_(
                Habit.user_id == user_id,
                Habit.is_active == True
            )
        ).all()
        
        if not habits:
            return RecommendationResponse(
                user_id=user_id,
                generated_at=datetime.utcnow(),
                habit_recommendations=[],
                system_recommendations=["Create your first habit to get started!"],
                total_habits_tracked=0,
                average_completion_rate=0.0,
                habits_needing_attention=0,
                next_steps=["Add a habit to begin tracking"]
            )
        
        # Generate recommendations for each habit
        habit_recommendations = []
        for habit in habits:
            recs = self._generate_habit_recommendations(habit, user_id)
            habit_recommendations.extend(recs)
        
        # Get system-level insights
        system_recommendations = self._generate_system_recommendations(user_id, habits)
        
        # Calculate summary statistics
        avg_completion = self._calculate_average_completion(user_id, habits)
        
        # Generate next steps
        next_steps = self._prioritize_actions(habit_recommendations)
        
        return RecommendationResponse(
            user_id=user_id,
            generated_at=datetime.utcnow(),
            habit_recommendations=habit_recommendations,
            system_recommendations=system_recommendations,
            total_habits_tracked=len(habits),
            average_completion_rate=avg_completion,
            habits_needing_attention=len(habit_recommendations),
            next_steps=next_steps
        )
    
    def _generate_habit_recommendations(
        self,
        habit: Habit,
        user_id: int
    ) -> List[HabitRecommendation]:
        """
        Generate recommendations for a specific habit
        
        Args:
            habit: The habit to analyze
            user_id: ID of the user
        
        Returns:
            List of recommendations for this habit
        """
        recommendations = []
        
        # Rule 1: Check for 2 bad weeks
        bad_weeks_rec = self._check_two_bad_weeks(habit, user_id)
        if bad_weeks_rec:
            recommendations.append(bad_weeks_rec)
        
        # Rule 2: Check for repeated failures
        repeated_failure_rec = self._check_repeated_failures(habit, user_id)
        if repeated_failure_rec:
            recommendations.append(repeated_failure_rec)
        
        # Rule 3: Check for high stability + low trend
        stretch_rec = self._check_stretch_opportunity(habit, user_id)
        if stretch_rec:
            recommendations.append(stretch_rec)
        
        # Rule 4: Check if ready for new habit (not a direct recommendation for this habit)
        # This is handled separately in system recommendations
        
        return recommendations
    
    def _check_two_bad_weeks(
        self,
        habit: Habit,
        user_id: int
    ) -> Optional[ScopeReductionRecommendation]:
        """
        Rule 1: If 2 consecutive bad weeks (< 50% completion), suggest reducing scope
        
        Args:
            habit: The habit to check
            user_id: ID of the user
        
        Returns:
            ScopeReductionRecommendation if rule applies, None otherwise
        """
        # Get last 2 weeks of summaries
        two_weeks_ago = datetime.now().date() - timedelta(days=14)
        
        week_summaries = self.db.query(WeekSummary).filter(
            and_(
                WeekSummary.user_id == user_id,
                WeekSummary.week_start_date >= two_weeks_ago
            )
        ).order_by(WeekSummary.week_start_date.desc()).limit(2).all()
        
        if len(week_summaries) < 2:
            return None
        
        # Check if both weeks have low completion (< 50%)
        bad_week_count = sum(
            1 for summary in week_summaries
            if summary.average_completion_percentage < 50.0
        )
        
        if bad_week_count >= 2:
            current_completion = self._get_current_completion_rate(habit, user_id)
            failure_patterns = self._get_failure_patterns(habit, user_id)
            
            return ScopeReductionRecommendation(
                habit_id=habit.id,
                habit_name=habit.name,
                title="Consider Reducing Habit Scope",
                description=(
                    f"Your '{habit.name}' habit has had 2 consecutive weeks with low completion "
                    f"(< 50%). This suggests the current scope might be too ambitious."
                ),
                action_items=[
                    f"Reduce frequency from {habit.target_frequency}x per {habit.frequency_unit} "
                    f"to a smaller number",
                    "Break the habit into smaller, more achievable steps",
                    "Consider setting a specific time or trigger for the habit",
                    "Review and remove any obstacles to completion"
                ],
                priority=RecommendationPriority.HIGH,
                reason="2 consecutive weeks below 50% completion threshold",
                current_completion_rate=current_completion,
                trend="down",
                failure_patterns=failure_patterns,
                bad_weeks_count=bad_week_count,
                suggested_reduction=f"{habit.target_frequency}x → {max(1, habit.target_frequency - 1)}x per {habit.frequency_unit}"
            )
        
        return None
    
    def _check_repeated_failures(
        self,
        habit: Habit,
        user_id: int
    ) -> Optional[HabitRedesignRecommendation]:
        """
        Rule 2: If same failure type occurs repeatedly (3+), suggest habit redesign
        
        Args:
            habit: The habit to check
            user_id: ID of the user
        
        Returns:
            HabitRedesignRecommendation if rule applies, None otherwise
        """
        repeated_failures = self.failure_analyzer.identify_repeated_failures(
            habit.id, user_id, days=14
        )
        
        if repeated_failures and repeated_failures[0]["occurrences"] >= 3:
            current_completion = self._get_current_completion_rate(habit, user_id)
            failure_patterns = self._get_failure_patterns(habit, user_id)
            top_failure = repeated_failures[0]
            
            return HabitRedesignRecommendation(
                habit_id=habit.id,
                habit_name=habit.name,
                title="Redesign Habit for Better Success",
                description=(
                    f"Your '{habit.name}' habit consistently fails due to '{top_failure['pattern']}' "
                    f"(occurred {top_failure['occurrences']} times in the last 2 weeks). "
                    "The habit design might not be compatible with your lifestyle."
                ),
                action_items=[
                    f"Address the '{top_failure['pattern']}' barrier directly",
                    f"Redesign the habit to work around {top_failure['pattern']}",
                    "Consider changing the time, location, or method of habit execution",
                    "Create a specific implementation plan for the new design",
                    "Test the redesigned habit for 1-2 weeks"
                ],
                priority=RecommendationPriority.HIGH,
                reason=f"Same failure pattern ({top_failure['pattern']}) repeated {top_failure['occurrences']} times",
                current_completion_rate=current_completion,
                trend="down",
                failure_patterns=failure_patterns,
                failure_count=top_failure["occurrences"],
                failure_type=top_failure["pattern"]
            )
        
        return None
    
    def _check_stretch_opportunity(
        self,
        habit: Habit,
        user_id: int
    ) -> Optional[StretchRecommendation]:
        """
        Rule 3: If high stability (consistent 70%+) + no upward trend, suggest stretch goal
        
        Args:
            habit: The habit to check
            user_id: ID of the user
        
        Returns:
            StretchRecommendation if rule applies, None otherwise
        """
        # Get recent week summaries (last 4 weeks)
        four_weeks_ago = datetime.now().date() - timedelta(days=28)
        
        week_summaries = self.db.query(WeekSummary).filter(
            and_(
                WeekSummary.user_id == user_id,
                WeekSummary.week_start_date >= four_weeks_ago
            )
        ).order_by(WeekSummary.week_start_date.desc()).all()
        
        if len(week_summaries) < 2:
            return None
        
        # Check stability: all recent weeks at 70%+
        completions = [s.average_completion_percentage for s in week_summaries]
        is_stable = all(c >= 70.0 for c in completions)
        
        if not is_stable:
            return None
        
        # Check for low trend: not improving much
        oldest_completion = completions[-1]  # Oldest in list
        newest_completion = completions[0]   # Newest in list
        trend = newest_completion - oldest_completion
        
        # If trend is stable or slightly declining, suggest stretch
        if trend < 10:  # Less than 10 percentage point improvement
            stability_score = sum(completions) / len(completions)
            current_completion = self._get_current_completion_rate(habit, user_id)
            
            return StretchRecommendation(
                habit_id=habit.id,
                habit_name=habit.name,
                title="You're Ready for a Stretch Goal!",
                description=(
                    f"You've maintained excellent consistency with '{habit.name}' "
                    f"at {stability_score:.0f}% completion. Since your performance has plateaued, "
                    "it's time to challenge yourself with a stretch goal."
                ),
                action_items=[
                    f"Increase frequency from {habit.target_frequency}x to {habit.target_frequency + 1}x per {habit.frequency_unit}",
                    "Or increase quality/duration of each completion",
                    "Add a numerical target (e.g., 'run 5km' instead of 'run')",
                    "Track your progress on the stretch goal for 2-3 weeks"
                ],
                priority=RecommendationPriority.MEDIUM,
                reason=f"Consistent {stability_score:.0f}% completion with stable trend",
                current_completion_rate=current_completion,
                trend="stable",
                stability_score=stability_score,
                trend_days=len(week_summaries) * 7,
                suggested_stretch=f"{habit.target_frequency}x → {habit.target_frequency + 1}x per {habit.frequency_unit}"
            )
        
        return None
    
    def _check_ready_for_new_habit(self, user_id: int) -> bool:
        """
        Rule 4: Check if user can add a new habit (85%+ for 3 weeks)
        
        Args:
            user_id: ID of the user
        
        Returns:
            True if user can add new habit, False otherwise
        """
        # Get last 3 weeks of summaries
        three_weeks_ago = datetime.now().date() - timedelta(days=21)
        
        week_summaries = self.db.query(WeekSummary).filter(
            and_(
                WeekSummary.user_id == user_id,
                WeekSummary.week_start_date >= three_weeks_ago
            )
        ).order_by(WeekSummary.week_start_date.desc()).limit(3).all()
        
        if len(week_summaries) < 3:
            return False
        
        # All 3 weeks must be at 85%+
        return all(summary.average_completion_percentage >= 85.0 for summary in week_summaries)
    
    def _generate_system_recommendations(
        self,
        user_id: int,
        habits: List[Habit]
    ) -> List[str]:
        """
        Generate system-level recommendations
        
        Args:
            user_id: ID of the user
            habits: List of user's habits
        
        Returns:
            List of system-level recommendation strings
        """
        recommendations = []
        
        # Check if ready for new habit
        if self._check_ready_for_new_habit(user_id):
            recommendations.append(
                f"🎉 You've demonstrated 85%+ completion for 3 weeks! "
                f"You're ready to add a new habit to your routine."
            )
        
        # Check overall performance
        avg_completion = self._calculate_average_completion(user_id, habits)
        if avg_completion < 50:
            recommendations.append(
                "💡 Your overall completion is below 50%. Try focusing on just "
                "2-3 core habits before adding more."
            )
        elif 50 <= avg_completion < 70:
            recommendations.append(
                "📈 You're making progress! Consider scheduling a weekly review "
                "to identify and fix obstacles."
            )
        elif avg_completion >= 85:
            recommendations.append(
                "🏆 You're tracking habits consistently at 85%+! "
                "Keep up this excellent momentum!"
            )
        
        # Check for habits with critical failures
        critical_habits = self.failure_analyzer.get_habits_with_critical_failures(
            user_id, failure_rate_threshold=60.0
        )
        if critical_habits:
            recommendations.append(
                f"⚠️ {len(critical_habits)} habit(s) have high failure rates. "
                f"Consider pausing one to focus on the others."
            )
        
        # Check top failure reasons
        top_failures = self.failure_analyzer.get_top_failure_reasons_across_habits(user_id)
        if top_failures:
            top_reason = max(top_failures.items(), key=lambda x: x[1])
            recommendations.append(
                f"🔍 Your most common failure reason is '{top_reason[0]}'. "
                f"Try to address this barrier proactively."
            )
        
        return recommendations
    
    def _get_current_completion_rate(self, habit: Habit, user_id: int) -> float:
        """Get the habit's completion rate in the last 7 days"""
        week_ago = datetime.now().date() - timedelta(days=7)
        
        logs = self.db.query(HabitLog).filter(
            and_(
                HabitLog.habit_id == habit.id,
                HabitLog.user_id == user_id,
                HabitLog.date >= week_ago
            )
        ).all()
        
        if not logs:
            return 0.0
        
        completed = sum(1 for log in logs if log.completed == 1)
        return round(completed / len(logs) * 100, 2)
    
    def _get_failure_patterns(self, habit: Habit, user_id: int) -> List[FailurePattern]:
        """Get failure patterns for a habit"""
        analysis = self.failure_analyzer.get_failure_patterns_for_habit(
            habit.id, user_id, days=14
        )
        
        patterns = []
        total_failures = analysis["total_failures"]
        
        for pattern_name, count in analysis.get("patterns", {}).items():
            if count > 0:
                patterns.append(FailurePattern(
                    pattern=pattern_name,
                    frequency=count,
                    percentage=round(count / total_failures * 100, 2) if total_failures > 0 else 0
                ))
        
        return sorted(patterns, key=lambda x: x.frequency, reverse=True)
    
    def _calculate_average_completion(
        self,
        user_id: int,
        habits: List[Habit]
    ) -> float:
        """Calculate average completion rate across all habits"""
        if not habits:
            return 0.0
        
        week_ago = datetime.now().date() - timedelta(days=7)
        
        total_completion = 0.0
        for habit in habits:
            total_completion += self._get_current_completion_rate(habit, user_id)
        
        return round(total_completion / len(habits), 2)
    
    def _prioritize_actions(
        self,
        recommendations: List[HabitRecommendation]
    ) -> List[str]:
        """
        Prioritize recommendations into actionable next steps
        
        Args:
            recommendations: List of recommendations
        
        Returns:
            List of prioritized action strings
        """
        # Sort by priority
        priority_order = {
            RecommendationPriority.CRITICAL: 0,
            RecommendationPriority.HIGH: 1,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 3,
        }
        
        sorted_recs = sorted(
            recommendations,
            key=lambda x: priority_order.get(x.priority, 999)
        )
        
        actions = []
        for i, rec in enumerate(sorted_recs[:5], 1):  # Top 5 actions
            action = f"{i}. {rec.title} for '{rec.habit_name}'"
            actions.append(action)
        
        return actions
