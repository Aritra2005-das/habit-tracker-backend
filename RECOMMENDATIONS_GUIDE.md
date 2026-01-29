# Intelligent Recommendation System Documentation

## Overview

The intelligent recommendation system analyzes user habit data and provides actionable insights and suggestions. It uses rule-based logic to identify patterns, detect issues, and recommend adjustments.

## Architecture

### Components

```
app/
├── schemas/
│   └── recommendation.py          # Response schemas for recommendations
├── services/
│   ├── failure_analysis.py        # Failure pattern analysis
│   ├── decision_engine.py         # Rule-based recommendation logic
│   ├── weekly_recommendations.py  # Weekly recommendation generation
│   └── integration.py             # Integration with weekly summaries
├── models/
│   └── weekly_recommendation.py   # Database model for storing recommendations
└── api/
    └── recommendations.py          # API endpoints
```

## Key Components

### 1. Failure Analysis Service (`failure_analysis.py`)

Analyzes habit failure patterns in the last 14 days.

**Main Classes:**
- `FailureAnalyzer`: Analyzes failure patterns and reasons

**Key Methods:**
```python
# Get failure patterns for a specific habit
analyzer.get_failure_patterns_for_habit(habit_id, user_id, days=14)
# Returns: {
#   "habit_id": 1,
#   "total_days_tracked": 14,
#   "total_failures": 4,
#   "failure_rate": 28.57,
#   "patterns": {"time": 2, "tired": 1, "forgot": 1},
#   "consecutive_failures": 1,
#   ...
# }

# Get failure patterns for all habits
analyzer.get_failure_patterns_for_user(user_id, days=14)

# Identify repeated failures (same failure type 2+ times)
analyzer.identify_repeated_failures(habit_id, user_id, days=14)

# Get habits with critical failure rates
analyzer.get_habits_with_critical_failures(user_id, threshold=50.0)
```

**Failure Pattern Detection:**
- Time constraints
- Tiredness/fatigue
- Motivation issues
- Forgot/forgot reminder
- Health issues
- Travel/commute
- Weather
- Other priorities
- Other/unspecified

### 2. Decision Engine (`decision_engine.py`)

Implements rule-based logic for generating recommendations.

**Main Class:**
- `DecisionEngine`: Generates intelligent recommendations

**Rules:**

1. **2 Bad Weeks Rule** (< 50% completion for 2 consecutive weeks)
   - Recommendation Type: `REDUCE_SCOPE`
   - Action: Suggest reducing habit frequency/difficulty
   - Example: "5x per week → 3x per week"

2. **Repeated Failure Rule** (Same failure pattern occurs 3+ times)
   - Recommendation Type: `REDESIGN_HABIT`
   - Action: Suggest redesigning to address barrier
   - Example: "If 'time constraint' occurs 3+ times, suggest time redesign"

3. **Stretch Opportunity Rule** (70%+ completion, stable trend)
   - Recommendation Type: `ADD_STRETCH`
   - Action: Suggest increasing difficulty/frequency
   - Example: "Add 1 more repetition or increase difficulty"

4. **New Habit Readiness Rule** (85%+ for 3 consecutive weeks)
   - Recommendation Type: `ENABLE_NEW_HABIT`
   - Action: Indicate user can add another habit
   - Message: "You're ready to add a new habit!"

**Key Methods:**
```python
# Generate all recommendations for a user
recommendations = engine.generate_recommendations(user_id)
# Returns: RecommendationResponse

# Generate recommendations for a specific habit
habit_recs = engine._generate_habit_recommendations(habit, user_id)
```

### 3. Weekly Recommendations Generator (`weekly_recommendations.py`)

Automatically generates recommendations after weekly summary calculation.

**Main Class:**
- `WeeklyRecommendationGenerator`: Creates weekly adjustment recommendations

**Key Methods:**
```python
# Generate recommendations for a completed week
generator.generate_weekly_recommendations(user_id, week_start_date)

# Get pending recommendations for a user
generator.get_pending_recommendations(user_id, limit=10)

# Mark recommendation as acted upon
generator.mark_recommendation_acted_upon(recommendation_id)

# Get recommendations for a specific week
generator.get_recommendations_by_week(user_id, week_start_date)
```

### 4. Recommendation Schemas (`schemas/recommendation.py`)

**Main Models:**
- `RecommendationType`: Enum of recommendation types
- `RecommendationPriority`: Priority levels (LOW, MEDIUM, HIGH, CRITICAL)
- `FailurePattern`: Failure pattern info
- `HabitRecommendation`: Individual habit recommendation
- `RecommendationResponse`: Complete response with all recommendations
- `WeeklyAdjustmentRecommendation`: Weekly auto-generated recommendation

## API Endpoints

### 1. Get User Recommendations
```
GET /api/v1/recommendations?user_id={user_id}

Response: RecommendationResponse
- habit_recommendations: List of recommendations for individual habits
- system_recommendations: General system-level insights
- total_habits_tracked: Count of active habits
- average_completion_rate: Average completion across all habits
- habits_needing_attention: Count of habits with recommendations
- next_steps: Prioritized action items
```

### 2. Get Habit-Specific Recommendations
```
GET /api/v1/recommendations/habit/{habit_id}?user_id={user_id}

Response: RecommendationResponse (filtered for this habit only)
```

### 3. Get Failure Analysis
```
GET /api/v1/recommendations/failure-analysis?user_id={user_id}&days={days}

Response: Detailed failure analysis
- top_failure_reasons: Most common failure types
- critical_habits: Habits with high failure rates
- habits: Detailed failure analysis per habit
```

## Data Models

### WeeklyRecommendation (Database Model)

Stores auto-generated recommendations for weekly reviews.

```python
class WeeklyRecommendation(BaseModel):
    user_id: int                    # User who receives recommendation
    habit_id: int                   # Habit the recommendation is about
    week_start_date: str           # Week start date (YYYY-MM-DD)
    recommendation_type: str       # Type of recommendation
    suggestion: str                # Short suggestion (max 500 chars)
    details: str                   # Detailed explanation (optional)
    is_acted_upon: int             # 0 = not acted, 1 = acted
    acted_upon_date: datetime      # When user acted on it (optional)
```

## Integration with Weekly Summaries

### Automatic Recommendation Generation

When a weekly summary is generated:

```python
from app.services.integration import generate_recommendations_for_week

# After creating weekly summary
generate_recommendations_for_week(user_id, week_start_date, db)
```

### Retrieve Summary with Recommendations

```python
from app.services.integration import get_weekly_summary_with_recommendations

result = get_weekly_summary_with_recommendations(user_id, week_start_date, db)
# Returns: {
#   "week_summary": WeekSummary object,
#   "recommendations": [WeeklyRecommendation, ...],
#   "has_recommendations": bool
# }
```

## Recommendation Examples

### Example 1: Scope Reduction

**Trigger:** 2 consecutive weeks < 50% completion

**Response:**
```json
{
  "habit_id": 1,
  "habit_name": "Morning Run",
  "recommendation_type": "reduce_scope",
  "title": "Consider Reducing Habit Scope",
  "description": "Your 'Morning Run' habit has had 2 consecutive weeks with low completion (< 50%). This suggests the current scope might be too ambitious.",
  "action_items": [
    "Reduce frequency from 5x per day to 3x per day",
    "Break the habit into smaller, more achievable steps",
    "Consider setting a specific time or trigger for the habit",
    "Review and remove any obstacles to completion"
  ],
  "priority": "high",
  "reason": "2 consecutive weeks below 50% completion threshold",
  "current_completion_rate": 35.5,
  "bad_weeks_count": 2,
  "suggested_reduction": "5x → 3x per day"
}
```

### Example 2: Habit Redesign

**Trigger:** Same failure pattern occurs 3+ times

**Response:**
```json
{
  "habit_id": 2,
  "habit_name": "Meditation",
  "recommendation_type": "redesign_habit",
  "title": "Redesign Habit for Better Success",
  "description": "Your 'Meditation' habit consistently fails due to 'time constraint' (occurred 4 times in the last 2 weeks). The habit design might not be compatible with your lifestyle.",
  "action_items": [
    "Address the 'time constraint' barrier directly",
    "Redesign the habit to work around time constraint",
    "Consider changing the time, location, or method",
    "Create a specific implementation plan for the new design",
    "Test the redesigned habit for 1-2 weeks"
  ],
  "priority": "high",
  "failure_count": 4,
  "failure_type": "time"
}
```

### Example 3: Stretch Goal

**Trigger:** 70%+ completion, stable trend (< 10% improvement)

**Response:**
```json
{
  "habit_id": 3,
  "habit_name": "Reading",
  "recommendation_type": "add_stretch",
  "title": "You're Ready for a Stretch Goal!",
  "description": "You've maintained excellent consistency with 'Reading' at 82% completion. Since your performance has plateaued, it's time to challenge yourself with a stretch goal.",
  "action_items": [
    "Increase frequency from 1x to 2x per day",
    "Or increase quality/duration of each completion",
    "Add a numerical target (e.g., '30 pages' instead of 'read')",
    "Track your progress on the stretch goal for 2-3 weeks"
  ],
  "priority": "medium",
  "stability_score": 82.0,
  "suggested_stretch": "1x → 2x per day"
}
```

### Example 4: New Habit Readiness

**Trigger:** 85%+ completion for 3 weeks

**System Recommendation:**
```
"🎉 You've demonstrated 85%+ completion for 3 weeks! You're ready to add a new habit to your routine."
```

## Configuration

### Thresholds (Customizable)

```python
# In DecisionEngine._check_two_bad_weeks()
BAD_WEEK_THRESHOLD = 50.0          # % completion

# In DecisionEngine._check_stretch_opportunity()
STRETCH_STABILITY_THRESHOLD = 70.0 # % completion
STRETCH_TREND_THRESHOLD = 10.0     # percentage points

# In DecisionEngine._check_ready_for_new_habit()
NEW_HABIT_THRESHOLD = 85.0         # % completion
NEW_HABIT_WEEKS = 3                # consecutive weeks

# In FailureAnalyzer.identify_repeated_failures()
REPEATED_FAILURE_COUNT = 2         # minimum occurrences
```

### Analysis Period

Default analysis window: **14 days** (configurable per call)

## Usage Examples

### Complete Workflow

```python
from sqlalchemy.orm import Session
from app.services.decision_engine import DecisionEngine
from app.services.failure_analysis import FailureAnalyzer

# Initialize services
db: Session = ...
engine = DecisionEngine(db)
analyzer = FailureAnalyzer(db)

# 1. Get all recommendations
recommendations = engine.generate_recommendations(user_id=1)

# 2. Check failure patterns
patterns = analyzer.get_failure_patterns_for_user(user_id=1, days=14)

# 3. Identify critical habits
critical = analyzer.get_habits_with_critical_failures(user_id=1)

# 4. Get top failure reasons
top_reasons = analyzer.get_top_failure_reasons_across_habits(user_id=1)

# 5. Use recommendations
for rec in recommendations.habit_recommendations:
    print(f"{rec.title} for {rec.habit_name}")
    for action in rec.action_items:
        print(f"  - {action}")
```

## Performance Considerations

- Analysis period: 14 days (optimal for pattern detection)
- Caching: Consider caching recommendations for 24 hours
- Database queries: Indexed on user_id, habit_id, date fields
- Recommendation generation: ~100-200ms per user with 5-10 habits

## Future Enhancements

1. **ML-based Recommendations**: Use historical data to predict habit success
2. **Personalization**: Learn individual failure patterns and success factors
3. **Adaptive Thresholds**: Adjust thresholds based on user baseline
4. **Social Comparison**: Compare with similar users (anonymized)
5. **Gamification**: Badge system for achieving milestones
6. **Predictive Alerts**: Alert users before likely failures
7. **A/B Testing**: Test different recommendation strategies

## Testing

### Test Recommendations Endpoint

```bash
# Get recommendations for user 1
curl "http://localhost:8000/api/v1/recommendations?user_id=1"

# Get habit-specific recommendations
curl "http://localhost:8000/api/v1/recommendations/habit/1?user_id=1"

# Get failure analysis (14 days)
curl "http://localhost:8000/api/v1/recommendations/failure-analysis?user_id=1&days=14"
```

## Troubleshooting

### No Recommendations Generated

**Possible Causes:**
- User has no habits
- Habits have no recent logs
- Thresholds not met

**Solution:** Check user habits and recent logs in database

### Slow Recommendation Generation

**Possible Causes:**
- Large number of habits (10+)
- Long analysis period (30+ days)
- Database queries not using indexes

**Solution:** Optimize query indexes, reduce analysis period, cache results

### Inaccurate Patterns

**Possible Causes:**
- Incomplete notes on failed logs
- Pattern keywords not matching local language
- Insufficient data (< 7 days)

**Solution:** Improve note consistency, customize pattern keywords

---

**Last Updated:** January 28, 2024
**Status:** Production Ready
