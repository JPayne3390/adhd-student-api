# ADHD Student Productivity API
# Deploy to Vercel for free hosting and instant income generation

from flask import Flask, request, jsonify, render_template_string, redirect, session, url_for
from datetime import datetime, timedelta
import hashlib
import json
import os
import re
import msal
import requests as http_requests

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Microsoft Graph API Configuration
MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID', '')
MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET', '')
MICROSOFT_AUTHORITY = 'https://login.microsoftonline.com/common'
MICROSOFT_SCOPES = ['Files.ReadWrite.All', 'User.Read']
MICROSOFT_REDIRECT_URI = os.environ.get('MICROSOFT_REDIRECT_URI', 'http://localhost:5000/api/onedrive/callback')
GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'

# In-memory token storage (use Redis/DB in production)
token_cache = {}

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
        .api-example {
            background: #f5f5f5;
            padding: 2rem;
            border-radius: 10px;
            margin: 2rem 0;
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

@app.route('/api/focus-schedule', methods=['POST'])
def focus_schedule():
    """Generate personalized focus/break schedules"""
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

@app.route('/api/procrastination-buster', methods=['POST'])
def procrastination_buster():
    """Get personalized strategies to start tasks"""
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

# =============================================================================
# OneDrive Integration - Trash Search for ADHD File Organization
# =============================================================================

def get_msal_app():
    """Create MSAL confidential client application"""
    return msal.ConfidentialClientApplication(
        MICROSOFT_CLIENT_ID,
        authority=MICROSOFT_AUTHORITY,
        client_credential=MICROSOFT_CLIENT_SECRET
    )

def get_access_token(user_id):
    """Get access token for a user from cache"""
    return token_cache.get(user_id, {}).get('access_token')

@app.route('/api/onedrive/auth')
def onedrive_auth():
    """Initiate OneDrive OAuth2 authentication flow"""
    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        return jsonify({
            'error': 'OneDrive integration not configured',
            'setup_instructions': [
                '1. Register app at https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps',
                '2. Set MICROSOFT_CLIENT_ID environment variable',
                '3. Set MICROSOFT_CLIENT_SECRET environment variable',
                '4. Set MICROSOFT_REDIRECT_URI environment variable'
            ]
        }), 503

    msal_app = get_msal_app()
    auth_url = msal_app.get_authorization_request_url(
        scopes=MICROSOFT_SCOPES,
        redirect_uri=MICROSOFT_REDIRECT_URI
    )

    return redirect(auth_url)

@app.route('/api/onedrive/callback')
def onedrive_callback():
    """Handle OAuth2 callback from Microsoft"""
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'Authorization code not provided'}), 400

    msal_app = get_msal_app()
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=MICROSOFT_SCOPES,
        redirect_uri=MICROSOFT_REDIRECT_URI
    )

    if 'access_token' in result:
        # Get user info to create a user ID
        headers = {'Authorization': f'Bearer {result["access_token"]}'}
        user_info = http_requests.get(f'{GRAPH_API_ENDPOINT}/me', headers=headers).json()
        user_id = user_info.get('id', 'default_user')

        # Store token
        token_cache[user_id] = {
            'access_token': result['access_token'],
            'expires_at': datetime.now() + timedelta(seconds=result.get('expires_in', 3600))
        }

        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'OneDrive connected successfully. Use this user_id for trash search requests.'
        })

    return jsonify({'error': 'Failed to obtain access token', 'details': result.get('error_description')}), 400

@app.route('/api/onedrive/trash/search', methods=['POST'])
def search_onedrive_trash():
    """
    Search OneDrive trash for files deleted due to unclear naming.
    Returns files that likely need review without creating duplicates.
    """
    data = request.json or {}
    user_id = data.get('user_id') or request.headers.get('X-OneDrive-User-Id')
    api_key = request.headers.get('X-API-Key', 'free_trial')

    if not check_usage(api_key):
        return jsonify({'error': 'Daily limit reached'}), 429

    access_token = get_access_token(user_id)
    if not access_token:
        return jsonify({
            'error': 'Not authenticated with OneDrive',
            'action_required': 'Visit /api/onedrive/auth to connect your OneDrive account'
        }), 401

    # Get search parameters
    include_patterns = data.get('include_patterns', [])  # Additional patterns to search for
    exclude_extensions = data.get('exclude_extensions', ['.tmp', '.bak', '~'])
    max_results = min(data.get('max_results', 50), 100)  # Cap at 100

    headers = {'Authorization': f'Bearer {access_token}'}

    # Fetch deleted items from OneDrive recycle bin
    trash_url = f'{GRAPH_API_ENDPOINT}/me/drive/items/root/children?$filter=deleted ne null'

    # Alternative: Use the special folder for deleted items
    trash_response = http_requests.get(
        f'{GRAPH_API_ENDPOINT}/me/drive/special/deleted/children?$top={max_results}',
        headers=headers
    )

    if trash_response.status_code != 200:
        return jsonify({
            'error': 'Failed to fetch OneDrive trash',
            'details': trash_response.json() if trash_response.text else 'Unknown error'
        }), trash_response.status_code

    deleted_items = trash_response.json().get('value', [])

    # Also get current files to check for duplicates
    current_files_response = http_requests.get(
        f'{GRAPH_API_ENDPOINT}/me/drive/root/children?$top=500',
        headers=headers
    )

    current_file_hashes = set()
    current_file_names = set()

    if current_files_response.status_code == 200:
        current_files = current_files_response.json().get('value', [])
        for f in current_files:
            current_file_names.add(f.get('name', '').lower())
            # Use file hash if available for duplicate detection
            if 'file' in f and 'hashes' in f['file']:
                hashes = f['file']['hashes']
                if 'sha256Hash' in hashes:
                    current_file_hashes.add(hashes['sha256Hash'])
                elif 'quickXorHash' in hashes:
                    current_file_hashes.add(hashes['quickXorHash'])

    # Analyze deleted files for unclear naming patterns
    unclear_naming_files = []
    duplicate_files = []

    for item in deleted_items:
        name = item.get('name', '')
        extension = os.path.splitext(name)[1].lower()

        # Skip excluded extensions
        if extension in exclude_extensions:
            continue

        # Check for duplicate (already exists in drive)
        is_duplicate = False
        duplicate_reason = None

        # Check by name
        if name.lower() in current_file_names:
            is_duplicate = True
            duplicate_reason = 'File with same name exists'

        # Check by hash
        if 'file' in item and 'hashes' in item['file']:
            item_hashes = item['file']['hashes']
            for hash_type in ['sha256Hash', 'quickXorHash']:
                if hash_type in item_hashes and item_hashes[hash_type] in current_file_hashes:
                    is_duplicate = True
                    duplicate_reason = 'Identical file content exists'
                    break

        # Analyze if the name was unclear (likely why it was deleted)
        naming_analysis = analyze_filename_clarity(name, include_patterns)

        if naming_analysis['is_unclear']:
            file_info = {
                'id': item.get('id'),
                'name': name,
                'size': item.get('size'),
                'deleted_time': item.get('deleted', {}).get('dateTime'),
                'created_time': item.get('createdDateTime'),
                'modified_time': item.get('lastModifiedDateTime'),
                'web_url': item.get('webUrl'),
                'unclear_reasons': naming_analysis['reasons'],
                'suggested_actions': naming_analysis['suggestions'],
                'is_duplicate': is_duplicate,
                'duplicate_reason': duplicate_reason
            }

            if is_duplicate:
                duplicate_files.append(file_info)
            else:
                unclear_naming_files.append(file_info)

    track_usage(api_key)

    return jsonify({
        'success': True,
        'total_trash_items': len(deleted_items),
        'files_with_unclear_names': {
            'count': len(unclear_naming_files),
            'items': unclear_naming_files,
            'note': 'These files had unclear names and are NOT duplicates - safe to restore and rename'
        },
        'duplicate_files': {
            'count': len(duplicate_files),
            'items': duplicate_files,
            'note': 'These files already exist in your OneDrive - restoring would create duplicates'
        },
        'adhd_tips': [
            'Start by reviewing just 3 files to avoid overwhelm',
            'Create a "To Sort" folder for restored files',
            'Use descriptive names: [Project]_[Content]_[Date]',
            'Set a 10-minute timer to prevent hyperfocus on organizing'
        ]
    })

@app.route('/api/onedrive/trash/restore', methods=['POST'])
def restore_from_trash():
    """Restore a file from OneDrive trash with optional rename"""
    data = request.json or {}
    user_id = data.get('user_id') or request.headers.get('X-OneDrive-User-Id')
    file_id = data.get('file_id')
    new_name = data.get('new_name')  # Optional: rename on restore
    api_key = request.headers.get('X-API-Key', 'free_trial')

    if not check_usage(api_key):
        return jsonify({'error': 'Daily limit reached'}), 429

    if not file_id:
        return jsonify({'error': 'file_id is required'}), 400

    access_token = get_access_token(user_id)
    if not access_token:
        return jsonify({
            'error': 'Not authenticated with OneDrive',
            'action_required': 'Visit /api/onedrive/auth to connect your OneDrive account'
        }), 401

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Restore the file by removing the deleted property
    restore_url = f'{GRAPH_API_ENDPOINT}/me/drive/items/{file_id}/restore'

    restore_payload = {}
    if new_name:
        restore_payload['name'] = new_name

    restore_response = http_requests.post(restore_url, headers=headers, json=restore_payload)

    if restore_response.status_code in [200, 201, 204]:
        track_usage(api_key)
        return jsonify({
            'success': True,
            'message': f'File restored successfully{" and renamed to " + new_name if new_name else ""}',
            'file_id': file_id
        })

    return jsonify({
        'error': 'Failed to restore file',
        'details': restore_response.json() if restore_response.text else 'Unknown error'
    }), restore_response.status_code

def analyze_filename_clarity(filename, custom_patterns=None):
    """
    Analyze a filename to determine if it has unclear naming.
    Returns analysis with reasons and suggestions.
    """
    name_without_ext = os.path.splitext(filename)[0]
    extension = os.path.splitext(filename)[1]

    reasons = []
    suggestions = []

    # Pattern 1: Generic default names
    generic_patterns = [
        (r'^document\d*$', 'Generic "Document" name'),
        (r'^untitled\d*$', 'Untitled file'),
        (r'^new\s*(document|file|text|spreadsheet|presentation)?\d*$', 'Default "New" name'),
        (r'^book\d*$', 'Generic "Book" name (Excel default)'),
        (r'^presentation\d*$', 'Generic "Presentation" name'),
        (r'^slide\d*$', 'Generic "Slide" name'),
        (r'^sheet\d*$', 'Generic "Sheet" name'),
        (r'^copy\s*(of\s*)?', 'Copy of another file'),
        (r'^\(\d+\)$', 'Just a number in parentheses'),
        (r'^file\d*$', 'Generic "File" name'),
        (r'^temp\d*$', 'Temporary file indicator'),
        (r'^draft\d*$', 'Just "Draft" without description'),
        (r'^test\d*$', 'Test file name'),
        (r'^asdf+$', 'Keyboard mash name'),
        (r'^[a-z]$', 'Single letter name'),
        (r'^\d+$', 'Numbers only name'),
    ]

    name_lower = name_without_ext.lower().strip()

    for pattern, reason in generic_patterns:
        if re.match(pattern, name_lower, re.IGNORECASE):
            reasons.append(reason)

    # Pattern 2: Date-only names (no description)
    date_patterns = [
        r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$',  # MM/DD/YYYY or similar
        r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$',     # YYYY-MM-DD
        r'^\d{8}$',                             # YYYYMMDD
    ]

    for pattern in date_patterns:
        if re.match(pattern, name_lower):
            reasons.append('Date-only filename (no description of content)')
            suggestions.append('Add content description before or after the date')

    # Pattern 3: Very short names (likely not descriptive)
    if len(name_without_ext) <= 3 and not reasons:
        reasons.append('Very short filename (likely not descriptive)')

    # Pattern 4: All caps gibberish
    if name_without_ext.isupper() and len(name_without_ext) > 3:
        if not re.match(r'^[A-Z]+$', name_without_ext):  # Not a valid acronym
            reasons.append('ALL CAPS name (often indicates rushed naming)')

    # Pattern 5: Contains "copy" with numbers
    if re.search(r'copy\s*\(\d+\)|copy\s*\d+|\(\d+\)\s*copy', name_lower):
        reasons.append('Multiple copy indicator (file was duplicated multiple times)')

    # Pattern 6: Screenshot default names
    if re.match(r'^screenshot\s*\d*|^screen\s*shot|^capture\d*', name_lower):
        reasons.append('Default screenshot name')
        suggestions.append('Rename to describe what the screenshot shows')

    # Pattern 7: Download default names
    if re.match(r'^download\s*\(\d+\)|^downloaded?\d*', name_lower):
        reasons.append('Default download name')

    # Custom patterns from user
    if custom_patterns:
        for pattern in custom_patterns:
            try:
                if re.search(pattern, name_lower, re.IGNORECASE):
                    reasons.append(f'Matches custom pattern: {pattern}')
            except re.error:
                pass  # Invalid regex, skip

    # Generate suggestions based on file extension
    extension_suggestions = {
        '.docx': 'Try: [Subject]_[Assignment Type]_[Your Name]',
        '.doc': 'Try: [Subject]_[Assignment Type]_[Your Name]',
        '.xlsx': 'Try: [Project]_[Data Type]_[Date]',
        '.xls': 'Try: [Project]_[Data Type]_[Date]',
        '.pptx': 'Try: [Topic]_[Presentation Type]_[Date]',
        '.ppt': 'Try: [Topic]_[Presentation Type]_[Date]',
        '.pdf': 'Try: [Source]_[Document Type]_[Date]',
        '.txt': 'Try: [Topic]_notes_[Date]',
        '.jpg': 'Try: [Subject]_[What It Shows]_[Date]',
        '.png': 'Try: [Subject]_[What It Shows]_[Date]',
    }

    if extension.lower() in extension_suggestions and reasons:
        suggestions.append(extension_suggestions[extension.lower()])

    # Add general suggestions
    if reasons:
        suggestions.extend([
            'Be specific: What is this file actually about?',
            'Include project or class name for context',
            'Add date if the content is time-sensitive'
        ])

    return {
        'is_unclear': len(reasons) > 0,
        'reasons': reasons,
        'suggestions': list(set(suggestions))  # Remove duplicates
    }

def generate_task_breakdown(task, deadline, hours, energy_pattern):
    """Generate ADHD-optimized task breakdown"""
    days_until = (datetime.fromisoformat(deadline) - datetime.now()).days
    
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
            'why': 'Externalizing anxiety reduces its power'
        },
        'tired': {
            'name': 'Energy Investment',
            'action': 'Do the absolute easiest part while lying down if needed',
            'why': 'Any progress builds momentum'
        },
        'scattered': {
            'name': 'Focus Anchor',
            'action': 'Set 5 items related to task on desk, touch each one',
            'why': 'Physical objects ground scattered attention'
        }
    }
    
    if mood in mood_strategies:
        strategies.append(mood_strategies[mood])
    
    # Blocker-specific strategies
    if 'perfectionism' in blockers:
        strategies.append({
            'name': 'Terrible First Draft',
            'action': 'Set timer for 10 min and write the WORST possible version',
            'why': 'Removes pressure and gets you started'
        })
    
    if 'overwhelming' in blockers:
        strategies.append({
            'name': 'Microscope Method',
            'action': 'Zoom in on ONLY the first sentence/problem/step',
            'why': 'ADHD brains handle single focus better than big picture'
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
    
    if 0.2 <= break_time / work_time <= 0.3:
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

# Vercel serverless function handler
def handler(request, response):
    return app(request, response)

if __name__ == '__main__':
    app.run(debug=True)
