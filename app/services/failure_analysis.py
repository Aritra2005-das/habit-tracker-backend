"""
Failure analysis service for identifying habit failure patterns
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import Counter
from app.models import HabitLog, Habit, User


class FailureAnalyzer:
    """Analyzes failure patterns in habit logs"""
    
    def __init__(self, db: Session):
        """
        Initialize the failure analyzer
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_failure_patterns_for_habit(
        self,
        habit_id: int,
        user_id: int,
        days: int = 14
    ) -> Dict[str, any]:
        """
        Analyze failure patterns for a specific habit over the last N days
        
        Args:
            habit_id: ID of the habit to analyze
            user_id: ID of the user
            days: Number of days to analyze (default: 14)
        
        Returns:
            Dictionary containing failure pattern analysis
        """
        cutoff_date = datetime.now().date() - timedelta(days=days)
        
        # Get all logs for this habit in the period
        logs = self.db.query(HabitLog).filter(
            and_(
                HabitLog.habit_id == habit_id,
                HabitLog.user_id == user_id,
                HabitLog.date >= cutoff_date
            )
        ).all()
        
        if not logs:
            return {
                "habit_id": habit_id,
                "total_days_tracked": 0,
                "total_failures": 0,
                "failure_rate": 0.0,
                "patterns": [],
                "common_failure_days": [],
                "consecutive_failures": 0,
            }
        
        # Calculate basic metrics
        total_failures = sum(1 for log in logs if log.completed == 0)
        total_days = len(logs)
        failure_rate = (total_failures / total_days * 100) if total_days > 0 else 0
        
        # Identify patterns from notes
        patterns = self._extract_patterns_from_notes([log.notes for log in logs if log.notes])
        
        # Identify days with most failures
        failure_day_counts = Counter([log.date.strftime("%A") for log in logs if log.completed == 0])
        common_failure_days = failure_day_counts.most_common(3)
        
        # Calculate consecutive failures
        consecutive_failures = self._count_consecutive_failures(logs)
        
        return {
            "habit_id": habit_id,
            "total_days_tracked": total_days,
            "total_failures": total_failures,
            "failure_rate": round(failure_rate, 2),
            "patterns": patterns,
            "common_failure_days": [
                {"day": day, "count": count} for day, count in common_failure_days
            ],
            "consecutive_failures": consecutive_failures,
            "last_failure_date": max(
                [log.date for log in logs if log.completed == 0],
                default=None
            ),
        }
    
    def get_failure_patterns_for_user(
        self,
        user_id: int,
        days: int = 14
    ) -> Dict[int, Dict]:
        """
        Analyze failure patterns for all habits for a user
        
        Args:
            user_id: ID of the user
            days: Number of days to analyze
        
        Returns:
            Dictionary mapping habit_id to failure pattern analysis
        """
        # Get all active habits for this user
        habits = self.db.query(Habit).filter(
            and_(
                Habit.user_id == user_id,
                Habit.is_active == True
            )
        ).all()
        
        patterns = {}
        for habit in habits:
            patterns[habit.id] = self.get_failure_patterns_for_habit(
                habit.id, user_id, days
            )
        
        return patterns
    
    def identify_repeated_failures(
        self,
        habit_id: int,
        user_id: int,
        days: int = 14
    ) -> List[Dict[str, any]]:
        """
        Identify repeated failure patterns (same failure type occurring multiple times)
        
        Args:
            habit_id: ID of the habit
            user_id: ID of the user
            days: Number of days to analyze
        
        Returns:
            List of repeated failure patterns
        """
        patterns = self.get_failure_patterns_for_habit(habit_id, user_id, days)
        
        repeated = []
        for pattern, count in patterns.get("patterns", {}).items():
            if count >= 2:  # Pattern occurred at least twice
                repeated.append({
                    "pattern": pattern,
                    "occurrences": count,
                    "percentage": round(count / patterns["total_failures"] * 100, 2)
                    if patterns["total_failures"] > 0 else 0
                })
        
        return sorted(repeated, key=lambda x: x["occurrences"], reverse=True)
    
    def _extract_patterns_from_notes(self, notes: List[str]) -> Dict[str, int]:
        """
        Extract common failure patterns from log notes
        
        Args:
            notes: List of note strings from failed attempts
        
        Returns:
            Dictionary of pattern -> count
        """
        patterns = Counter()
        
        # Keywords that indicate specific failure types
        keyword_mapping = {
            "time": ["busy", "rush", "time", "schedule", "conflict", "late", "early"],
            "tired": ["tired", "fatigue", "exhausted", "sleep", "energy"],
            "motivation": ["motivation", "unmotivated", "lazy", "no reason"],
            "forgot": ["forgot", "forget", "missed", "didn't remember"],
            "sick": ["sick", "ill", "health", "doctor", "pain", "injury"],
            "travel": ["travel", "trip", "away", "vacation", "commute"],
            "weather": ["weather", "rain", "cold", "hot", "storm"],
            "other_priority": ["priority", "work", "family", "urgent", "emergency"],
        }
        
        for note in notes:
            if not note:
                continue
            
            note_lower = note.lower()
            matched = False
            
            for pattern_name, keywords in keyword_mapping.items():
                if any(keyword in note_lower for keyword in keywords):
                    patterns[pattern_name] += 1
                    matched = True
                    break
            
            if not matched and note.strip():
                patterns["other"] += 1
        
        return dict(patterns)
    
    def _count_consecutive_failures(self, logs: List[HabitLog]) -> int:
        """
        Count consecutive failures at the end of the log sequence
        
        Args:
            logs: List of habit logs sorted by date
        
        Returns:
            Number of consecutive failures from the end
        """
        if not logs:
            return 0
        
        # Sort by date
        sorted_logs = sorted(logs, key=lambda x: x.date)
        
        consecutive = 0
        for log in reversed(sorted_logs):
            if log.completed == 0:
                consecutive += 1
            else:
                break
        
        return consecutive
    
    def get_top_failure_reasons_across_habits(
        self,
        user_id: int,
        days: int = 14
    ) -> Dict[str, int]:
        """
        Get the most common failure reasons across all habits for a user
        
        Args:
            user_id: ID of the user
            days: Number of days to analyze
        
        Returns:
            Dictionary of failure reason -> count
        """
        cutoff_date = datetime.now().date() - timedelta(days=days)
        
        # Get all failed logs with notes
        failed_logs = self.db.query(HabitLog).filter(
            and_(
                HabitLog.user_id == user_id,
                HabitLog.completed == 0,
                HabitLog.date >= cutoff_date,
                HabitLog.notes.isnot(None)
            )
        ).all()
        
        notes = [log.notes for log in failed_logs if log.notes and log.notes.strip()]
        
        # Extract patterns from all notes
        all_patterns = self._extract_patterns_from_notes(notes)
        
        return all_patterns
    
    def get_habits_with_critical_failures(
        self,
        user_id: int,
        failure_rate_threshold: float = 50.0
    ) -> List[Dict[str, any]]:
        """
        Get habits that have a failure rate above the threshold
        
        Args:
            user_id: ID of the user
            failure_rate_threshold: Minimum failure rate to be considered critical (default: 50%)
        
        Returns:
            List of habits with high failure rates
        """
        patterns = self.get_failure_patterns_for_user(user_id, days=14)
        
        critical_habits = []
        for habit_id, analysis in patterns.items():
            if analysis["failure_rate"] >= failure_rate_threshold:
                habit = self.db.query(Habit).get(habit_id)
                if habit:
                    critical_habits.append({
                        "habit_id": habit_id,
                        "habit_name": habit.name,
                        "failure_rate": analysis["failure_rate"],
                        "total_failures": analysis["total_failures"],
                        "total_days_tracked": analysis["total_days_tracked"],
                        "consecutive_failures": analysis["consecutive_failures"],
                    })
        
        return sorted(critical_habits, key=lambda x: x["failure_rate"], reverse=True)
