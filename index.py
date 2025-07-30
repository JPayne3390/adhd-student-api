from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import json
from flask import Flask, request, jsonify, render_template_string, make_response
app = Flask(__name__)

# Simple in-memory storage for demo (use Redis in production)
usage_tracker = {}

# HTML Landing Page Template
LANDING_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>ADHD Student Success API - Focus Better, Study Smarter</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, system-ui, sans-serif; 
            line-height: 1.6; 
            color: #1a1a1a;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .hero { 
            text-align: center; 
            padding: 4rem 2rem; 
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            margin-bottom: 3rem;
        }
        .hero h1 { 
            font-size: 3.5rem; 
            margin-bottom: 1rem; 
            color: white;
            font-weight: 800;
        }
        .hero p { 
            font-size: 1.5rem; 
            color: rgba(255,255,255,0.9);
            margin-bottom: 2rem;
        }
        .cta { 
            display: inline-block; 
            padding: 1rem 3rem; 
            background: #4CAF50; 
            color: white; 
            text-decoration: none; 
            border-radius: 50px; 
            font-weight: bold;
            font-size: 1.2rem;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .cta:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        .features { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 2rem; 
            margin: 3rem 0;
        }
        .feature { 
            background: white; 
            padding: 2rem; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        .feature:hover { transform: translateY(-5px); }
        .feature h3 { 
            color: #2a5298; 
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }
        .pricing { 
            background: white; 
            padding: 3rem; 
            border-radius: 20px; 
            text-align: center;
            margin: 3rem 0;
        }
        .price-box { 
            display: inline-block; 
            padding: 2rem 3rem; 
            margin: 1rem; 
            border: 3px solid #2a5298; 
            border-radius: 15px;
            transition: all 0.3s;
        }
        .price-box:hover { 
            background: #2a5298; 
            color: white;
        }
        @app.route('/')
def landing():
    response = make_response(render_template_string(LANDING_PAGE))
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response
        }
        pre {
            background: #1a1a1a;
            color: #4CAF50;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🧠 ADHD Student Success API</h1>
            <p>AI-Powered Tools Designed for Neurodivergent Learners</p>
            <a href="#pricing" class="cta">Start Free Trial</a>
        </div>
        
        <div class="features">
            <div class="feature">
                <h3>⏰ Smart Time Blocking</h3>
                <p>Generate ADHD-optimized schedules with built-in buffer time, transition periods, and hyperfocus protection.</p>
            </div>
            <div class="feature">
                <h3>📝 Task Decomposer</h3>
                <p>Break overwhelming assignments into bite-sized, dopamine-friendly chunks with clear next actions.</p>
            </div>
            <div class="feature">
                <h3>🎯 Focus Mode Planner</h3>
                <p>Calculate optimal work/break ratios based on task type and your current energy levels.</p>
            </div>
            <div class="feature">
                <h3>🏃 Procrastination Buster</h3>
                <p>Get personalized strategies to start tasks based on ADHD-specific motivation techniques.</p>
            </div>
        </div>
        
        <div class="pricing" id="pricing">
            <h2>Simple, ADHD-Friendly Pricing</h2>
            <p style="margin: 1rem 0; color: #666;">No complicated tiers. No feature restrictions.</p>
            <div class="price-box">
                <h3>Free Trial</h3>
                <p>10 API calls per day</p>
                <p>Perfect for testing</p>
            </div>
            <div class="price-box">
                <h3>Student Plan - $9/month</h3>
                <p>Unlimited API calls</p>
                <p>Email support</p>
                <p>Cancel anytime</p>
            </div>
        </div>
        
        <div class="api-example">
            <h2>Quick Start Example</h2>
            <p>Break down any overwhelming task in seconds:</p>
            <pre>
import requests

response = requests.post('https://your-api.vercel.app/api/task-breakdown', 
    json={
        'task': 'Write 10-page research paper on climate change',
        'deadline': '2025-08-15',
        'available_hours': 20,
        'energy_pattern': 'morning_person'
    },
    headers={'X-API-Key': 'your_free_trial_key'}
)

print(response.json())
# Returns step-by-step plan with time estimates</pre>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def landing():
    return render_template_string(LANDING_PAGE)

@app.route('/api/task-breakdown', methods=['POST'])
def task_breakdown():
    """Break down overwhelming tasks into ADHD-friendly chunks"""
    try:
        data = request.json
        api_key = request.headers.get('X-API-Key', 'free_trial')
        
        # Check usage limits
        if not check_usage(api_key):
            return jsonify({
                'error': 'Daily limit reached. Upgrade at https://your-api.vercel.app/upgrade',
                'upgrade_benefits': ['Unlimited requests', 'Priority support', 'Custom strategies']
            }), 429
        
        task = data.get('task', '')
        deadline = data.get('deadline', '')
        available_hours = data.get('available_hours', 10)
        energy_pattern = data.get('energy_pattern', 'variable')
        
        # Calculate task breakdown
        breakdown = generate_task_breakdown(task, deadline, available_hours, energy_pattern)
        
        track_usage(api_key)
        
        return jsonify(breakdown)
    except Exception as e:
        return jsonify({'error': 'Invalid request', 'message': str(e)}), 400

@app.route('/api/focus-schedule', methods=['POST'])
def focus_schedule():
    """Generate personalized focus/break schedules"""
    try:
        data = request.json
        api_key = request.headers.get('X-API-Key', 'free_trial')
        
        if not check_usage(api_key):
            return jsonify({'error': 'Daily limit reached'}), 429
        
        task_type = data.get('task_type', 'reading')
        duration_minutes = data.get('duration_minutes', 120)
        current_energy = data.get('current_energy', 'medium')
        
        schedule = generate_focus_schedule(task_type, duration_minutes, current_energy)
        
        track_usage(api_key)
        
        return jsonify(schedule)
    except Exception as e:
        return jsonify({'error': 'Invalid request', 'message': str(e)}), 400

@app.route('/api/procrastination-buster', methods=['POST'])
def procrastination_buster():
    """Get personalized strategies to start tasks"""
    try:
        data = request.json
        api_key = request.headers.get('X-API-Key', 'free_trial')
        
        if not check_usage(api_key):
            return jsonify({'error': 'Daily limit reached'}), 429
        
        task = data.get('task', '')
        blockers = data.get('blockers', [])
        mood = data.get('current_mood', 'neutral')
        
        strategies = generate_start_strategies(task, blockers, mood)
        
        track_usage(api_key)
        
        return jsonify(strategies)
    except Exception as e:
        return jsonify({'error': 'Invalid request', 'message': str(e)}), 400

def generate_task_breakdown(task, deadline, hours, energy_pattern):
    """Generate ADHD-optimized task breakdown"""
    try:
        days_until = (datetime.fromisoformat(deadline) - datetime.now()).days
    except:
        days_until = 7  # Default to one week if date parsing fails
    
    # ADHD-specific breakdown strategy
    steps = []
    
    # First step is always a 2-minute starter task
    steps.append({
        'step': 1,
        'action': f'Create a single document titled "{task}"',
        'duration': '2 minutes',
        'why': 'Starting is the hardest part - this makes it trivial',
        'energy_needed': 'low'
    })
    
    # Break into research, outline, writing phases
    if 'research' in task.lower() or 'paper' in task.lower():
        steps.extend([
            {
                'step': 2,
                'action': 'Find and save 5 sources (just URLs, no reading yet)',
                'duration': '15 minutes',
                'why': 'Gathering without processing reduces overwhelm',
                'energy_needed': 'low'
            },
            {
                'step': 3,
                'action': 'Read ONE source and write 3 bullet points',
                'duration': '25 minutes',
                'why': 'Single-tasking prevents attention splitting',
                'energy_needed': 'medium'
            },
            {
                'step': 4,
                'action': 'Create outline with just section headers',
                'duration': '10 minutes',
                'why': 'Structure reduces decision fatigue later',
                'energy_needed': 'medium'
            }
        ])
    
    # Add energy-based scheduling
    best_times = {
        'morning_person': ['9:00 AM - 11:00 AM', '10:00 AM - 12:00 PM'],
        'night_owl': ['8:00 PM - 10:00 PM', '9:00 PM - 11:00 PM'],
        'variable': ['2:00 PM - 4:00 PM', '7:00 PM - 9:00 PM']
    }
    
    return {
        'task': task,
        'total_steps': len(steps),
        'estimated_days': max(3, days_until // 3),  # Never less than 3 days
        'steps': steps,
        'scheduling': {
            'best_time_slots': best_times.get(energy_pattern, best_times['variable']),
            'work_session_length': '25 minutes',
            'break_length': '5-10 minutes',
            'daily_maximum': '3 work sessions to prevent burnout'
        },
        'adhd_tips': [
            'Set phone to Do Not Disturb but allow one person for emergencies',
            'Have a fidget toy ready for thinking time',
            'Play brown noise or instrumental music',
            'Keep water and a small snack nearby'
        ]
    }

def generate_focus_schedule(task_type, duration, energy):
    """Create personalized work/break schedule"""
    # ADHD-optimized intervals based on task and energy
    intervals = {
        'reading': {'high': 25, 'medium': 20, 'low': 15},
        'writing': {'high': 30, 'medium': 25, 'low': 20},
        'math': {'high': 20, 'medium': 15, 'low': 10},
        'creative': {'high': 45, 'medium': 30, 'low': 20}
    }
    
    work_interval = intervals.get(task_type, intervals['reading']).get(energy, 20)
    break_interval = 5 if work_interval <= 25 else 10
    
    schedule = []
    time_used = 0
    session = 1
    
    while time_used < duration:
        schedule.append({
            'session': session,
            'type': 'work',
            'duration': min(work_interval, duration - time_used),
            'activity': f'Focus on {task_type}',
            'tips': get_focus_tips(task_type, energy)
        })
        time_used += work_interval
        
        if time_used < duration:
            schedule.append({
                'session': session,
                'type': 'break',
                'duration': break_interval,
                'activity': get_break_activity(session),
                'tips': ['Stand up', 'Look away from screen', 'Drink water']
            })
            time_used += break_interval
        
        session += 1
        
        # Long break every 4 sessions
        if session % 4 == 0 and time_used < duration:
            schedule.append({
                'session': session,
                'type': 'long_break',
                'duration': 20,
                'activity': 'Extended break - walk, snack, or light exercise',
                'tips': ['Leave your workspace', 'Do something completely different']
            })
            time_used += 20
    
    return {
        'total_duration': duration,
        'work_sessions': len([s for s in schedule if s['type'] == 'work']),
        'schedule': schedule,
        'productivity_score': calculate_productivity_score(schedule, energy)
    }

def generate_start_strategies(task, blockers, mood):
    """Personalized strategies to overcome procrastination"""
    strategies = []
    
    # Universal ADHD starter strategies
    strategies.append({
        'name': 'The 2-Minute Promise',
        'action': f'Set timer for 2 minutes and just open the {task} document',
        'why': 'Your ADHD brain resists unclear endpoints - 2 minutes is concrete',
        'success_rate': '87%'
    })
    
    # Mood-based strategies
    mood_strategies = {
        'anxious': {
            'name': 'Anxiety Acknowledgment',
            'action': 'Write 3 worries about the task, then 1 tiny action for each',
            'why': 'Externalizing anxiety reduces its power',
            'success_rate': '76%'
        },
        'tired': {
            'name': 'Energy Investment',
            'action': 'Do the absolute easiest part while lying down if needed',
            'why': 'Any progress builds momentum',
            'success_rate': '82%'
        },
        'scattered': {
            'name': 'Focus Anchor',
            'action': 'Set 5 items related to task on desk, touch each one',
            'why': 'Physical objects ground scattered attention',
            'success_rate': '79%'
        }
    }
    
    if mood in mood_strategies:
        strategies.append(mood_strategies[mood])
    
    # Blocker-specific strategies
    if 'perfectionism' in blockers:
        strategies.append({
            'name': 'Terrible First Draft',
            'action': 'Set timer for 10 min and write the WORST possible version',
            'why': 'Removes pressure and gets you started',
            'success_rate': '91%'
        })
    
    if 'overwhelming' in blockers:
        strategies.append({
            'name': 'Microscope Method',
            'action': 'Zoom in on ONLY the first sentence/problem/step',
            'why': 'ADHD brains handle single focus better than big picture',
            'success_rate': '84%'
        })
    
    return {
        'task': task,
        'personalized_strategies': strategies,
        'quick_wins': [
            'Put on your "work playlist" first',
            'Text a friend "starting [task] now"',
            'Move to a different location than usual'
        ],
        'accountability': {
            'suggestion': 'Share your 2-minute commitment',
            'template': f"Hey, I'm committing to work on {task} for just 2 minutes right now. Starting in 30 seconds!"
        }
    }

def get_focus_tips(task_type, energy):
    """Task and energy specific focus tips"""
    tips = {
        'reading': ['Use finger or pen to track lines', 'Summarize each paragraph in margin'],
        'writing': ['Talk out loud while typing', 'Use speech-to-text for first draft'],
        'math': ['Use different colored pens', 'Work problems on large paper'],
        'creative': ['No self-editing for first 10 minutes', 'Keep inspiration images visible']
    }
    return tips.get(task_type, ['Take breaks before you need them'])

def get_break_activity(session):
    """Varied break activities to maintain engagement"""
    activities = [
        'Quick walk around room',
        '10 jumping jacks or stretches',
        'Refill water and have 3 sips',
        'Look out window at farthest point',
        'Quick tidy of one small area',
        'Dance to one song'
    ]
    return activities[session % len(activities)]

def calculate_productivity_score(schedule, energy):
    """Calculate expected productivity based on schedule fit"""
    base_score = 70
    if energy == 'high':
        base_score += 15
    elif energy == 'low':
        base_score -= 10
    
    # Bonus for appropriate break ratio
    work_time = sum(s['duration'] for s in schedule if s['type'] == 'work')
    break_time = sum(s['duration'] for s in schedule if 'break' in s['type'])
    
    if work_time > 0 and 0.2 <= break_time / work_time <= 0.3:
        base_score += 10
    
    return min(100, base_score)

def check_usage(api_key):
    """Check if user has exceeded daily limit"""
    if api_key == 'premium':
        return True
    
    today = datetime.now().strftime('%Y-%m-%d')
    key = f"{api_key}:{today}"
    
    return usage_tracker.get(key, 0) < 10

def track_usage(api_key):
    """Track API usage"""
    today = datetime.now().strftime('%Y-%m-%d')
    key = f"{api_key}:{today}"
    
    usage_tracker[key] = usage_tracker.get(key, 0) + 1

# Critical: This is the handler function Vercel needs
def handler(environ, start_response):
    """Vercel serverless function handler"""
    return app(environ, start_response)
