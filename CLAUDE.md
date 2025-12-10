# CLAUDE.md - AI Assistant Guide

## Project Overview

This is the **ADHD Student Productivity API** - a Flask-based REST API providing AI-powered tools designed for neurodivergent learners. The API helps students with ADHD manage tasks, maintain focus, and overcome procrastination through specialized strategies.

## Codebase Structure

```
adhd-student-api/
├── api.py              # Main Flask application (all routes and logic)
├── requirements.txt    # Python dependencies
└── CLAUDE.md          # This file
```

This is a single-file Flask application designed for simplicity and easy deployment to Vercel.

## Technology Stack

- **Framework**: Flask 2.3.2
- **Language**: Python 3.x
- **Deployment Target**: Vercel (serverless)
- **Storage**: In-memory dictionary (demo purposes; use Redis in production)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Landing page with HTML marketing content |
| `/api/task-breakdown` | POST | Break down tasks into ADHD-friendly chunks |
| `/api/focus-schedule` | POST | Generate personalized focus/break schedules |
| `/api/procrastination-buster` | POST | Get strategies to overcome procrastination |

### Authentication

All API endpoints use an `X-API-Key` header. Free trial users get 10 API calls per day; premium users (`api_key='premium'`) have unlimited access.

## Key Functions

- `generate_task_breakdown()` - Creates step-by-step task plans with ADHD-optimized timing
- `generate_focus_schedule()` - Builds work/break schedules based on task type and energy level
- `generate_start_strategies()` - Provides personalized procrastination-busting strategies
- `check_usage()` / `track_usage()` - Rate limiting logic

## Development Workflow

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the development server
python api.py
```

The server runs on `http://localhost:5000` with debug mode enabled.

### Testing Endpoints

```bash
# Test task breakdown
curl -X POST http://localhost:5000/api/task-breakdown \
  -H "Content-Type: application/json" \
  -H "X-API-Key: free_trial" \
  -d '{"task": "Write essay", "deadline": "2025-12-20", "available_hours": 10}'

# Test focus schedule
curl -X POST http://localhost:5000/api/focus-schedule \
  -H "Content-Type: application/json" \
  -d '{"task_type": "writing", "duration_minutes": 60, "current_energy": "medium"}'

# Test procrastination buster
curl -X POST http://localhost:5000/api/procrastination-buster \
  -H "Content-Type: application/json" \
  -d '{"task": "Start homework", "blockers": ["overwhelming"], "current_mood": "anxious"}'
```

## Code Conventions

### API Response Format

All endpoints return JSON with descriptive fields including:
- Action items with durations and explanations (`why` field)
- ADHD-specific tips and strategies
- Energy level considerations

### Rate Limiting

- Free tier: 10 requests/day per API key
- Premium tier: Unlimited
- Usage tracked by `{api_key}:{date}` key in memory

### Energy Patterns

Valid values for energy-related parameters:
- `high`, `medium`, `low` (for current_energy)
- `morning_person`, `night_owl`, `variable` (for energy_pattern)

### Task Types

Supported task types for focus scheduling:
- `reading`, `writing`, `math`, `creative`

### Mood Values

Supported mood values for procrastination buster:
- `anxious`, `tired`, `scattered`, `neutral`

## Production Considerations

1. **Storage**: Replace in-memory `usage_tracker` dict with Redis or database
2. **Authentication**: Implement proper API key validation and user management
3. **Error Handling**: Add comprehensive try/except blocks and input validation
4. **Logging**: Add structured logging for monitoring
5. **CORS**: Configure CORS headers if frontend is on different domain

## Deployment

Designed for Vercel serverless deployment. The `handler()` function at the bottom of `api.py` serves as the Vercel entry point.

## Notes for AI Assistants

- This is a focused, single-file application - avoid over-engineering
- The ADHD-specific strategies are research-based; preserve the explanatory `why` fields
- Time intervals (Pomodoro-style) are intentionally shorter than standard for ADHD optimization
- The landing page HTML is embedded in the Python file for simplicity
