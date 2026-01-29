"""
API Integration Guide for Recommendations System
This file documents how to integrate the recommendation system into the main API
"""

# To integrate recommendations into the main app, update app/main.py with:

"""
from fastapi import FastAPI
from app.api.recommendations import router as recommendations_router

app = FastAPI(...)

# Include the recommendations router
app.include_router(recommendations_router)
"""

# Example API Usage:

"""
1. Get all recommendations for a user:
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
         "description": "Your 'Morning Run' habit has had 2 consecutive weeks with low completion...",
         "action_items": ["Reduce frequency from 5x to 3x per week", ...],
         "priority": "high",
         "reason": "2 consecutive weeks below 50% completion threshold",
         "current_completion_rate": 35.5,
         "trend": "down",
         "failure_patterns": [
           {"pattern": "time", "frequency": 3, "percentage": 60.0}
         ]
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

2. Get recommendations for a specific habit:
   GET /api/v1/recommendations/habit/1?user_id=1
   
   Returns recommendations specific to that habit

3. Get failure analysis:
   GET /api/v1/recommendations/failure-analysis?user_id=1&days=14
   
   Response:
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
     "critical_habits": [
       {
         "habit_id": 2,
         "habit_name": "Meditation",
         "failure_rate": 65.0,
         "total_failures": 9,
         "total_days_tracked": 14
       }
     ],
     "habits": {...}
   }
"""

# Integration with Weekly Summary Generation:

"""
In your weekly summary generation code, after creating a WeekSummary:

from app.services.integration import generate_recommendations_for_week

# After creating/updating weekly summary
generate_recommendations_for_week(user_id, week_start_date, db)

Or use the helper:
from app.services.integration import get_weekly_summary_with_recommendations

result = get_weekly_summary_with_recommendations(user_id, week_start_date, db)
# Returns: {
#   "week_summary": WeekSummary,
#   "recommendations": [WeeklyRecommendation, ...],
#   "has_recommendations": bool
# }
"""
