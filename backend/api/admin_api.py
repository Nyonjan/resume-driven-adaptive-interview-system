from flask import Blueprint, request, jsonify, session, send_from_directory
from config.db_config import get_db_connection
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import csv
import io
import os
import json
import time

# Path to the site config JSON and uploads folder
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_CONFIG_PATH = os.path.join(_BASE, 'data', 'site_config.json')
UPLOADS_FOLDER   = os.path.join(_BASE, 'static', 'uploads')
ALLOWED_EXTS     = {'jpg', 'jpeg', 'png', 'webp', 'gif'}

def _read_config():
    try:
        with open(SITE_CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def _write_config(data):
    with open(SITE_CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)

admin_api = Blueprint('admin_api', __name__)

# ─── Helper: require admin session ──────────────────────────────────────────

def admin_required(f):
    """Decorator that blocks the route if no valid admin session exists."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Unauthorized. Admin login required.'}), 401
        return f(*args, **kwargs)
    return decorated


def serialize_data(data):
    """Helper to convert datetime objects to ISO strings for JSON serialization."""
    if isinstance(data, list):
        return [serialize_data(i) for i in data]
    if isinstance(data, dict):
        return {k: serialize_data(v) for k, v in data.items()}
    if hasattr(data, 'isoformat'):
        return data.isoformat()
    return data


# ─── POST /api/admin/login ───────────────────────────────────────────────────

@admin_api.route('/login', methods=['POST'])
def admin_login():
    """
    Authenticate an admin by username + password.
    Expects JSON: { "username": "...", "password": "..." }
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required.'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, password_hash, full_name FROM admins WHERE username = %s',
            (username,)
        )
        admin = cursor.fetchone()
        conn.close()
    except Exception as e:
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

    if admin and check_password_hash(admin[2], password):
        # Store admin info in server-side session
        session['admin_logged_in'] = True
        session['admin_id']        = admin[0]
        session['admin_username']  = admin[1]
        session['admin_full_name'] = admin[3]

        return jsonify({
            'success': True,
            'message': 'Login successful.',
            'admin': {
                'id':       admin[0],
                'username': admin[1],
                'fullName': admin[3]
            }
        }), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid username or password.'}), 401


# ─── POST /api/admin/logout ──────────────────────────────────────────────────

@admin_api.route('/logout', methods=['POST'])
@admin_required
def admin_logout():
    """Clear the admin session."""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'}), 200


# ─── GET /api/admin/me ───────────────────────────────────────────────────────

@admin_api.route('/me', methods=['GET'])
@admin_required
def admin_me():
    """Return the currently authenticated admin's info."""
    return jsonify({
        'success': True,
        'admin': {
            'id':       session.get('admin_id'),
            'username': session.get('admin_username'),
            'fullName': session.get('admin_full_name')
        }
    }), 200

@admin_api.route('/me', methods=['PUT'])
@admin_required
def update_admin_profile():
    """Update the logged-in admin's profile (name, password)."""
    data = request.get_json()
    admin_id = session.get('admin_id')
    full_name = data.get('fullName', '').strip()
    new_password = data.get('password', '')

    if not full_name:
        return jsonify({'success': False, 'message': 'Full Name is required.'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if new_password:
            # Update both name and password
            pw_hash = generate_password_hash(new_password)
            cursor.execute(
                'UPDATE admins SET full_name = %s, password_hash = %s WHERE id = %s',
                (full_name, pw_hash, admin_id)
            )
        else:
            # Update name only
            cursor.execute(
                'UPDATE admins SET full_name = %s WHERE id = %s',
                (full_name, admin_id)
            )
        
        conn.commit()
        conn.close()

        # Update session data
        session['admin_full_name'] = full_name
        
        return jsonify({'success': True, 'message': 'Profile updated successfully.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
# ─── GET /api/admin/users ───────────────────────────────────────────────────

@admin_api.route('/users', methods=['GET'])
@admin_required
def list_users():
    """List all registered users."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, full_name, email, avatar, created_at FROM users ORDER BY created_at DESC')
        users = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'users': serialize_data(users)}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── GET /api/admin/stats ───────────────────────────────────────────────────

@admin_api.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    """Get global platform statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Total Users
        cursor.execute('SELECT COUNT(*) as count FROM users')
        total_users = cursor.fetchone()['count']

        # 2. Active Sessions (in_progress)
        cursor.execute("SELECT COUNT(*) as count FROM interview_sessions WHERE status = 'in_progress'")
        active_sessions = cursor.fetchone()['count']

        # 3. Completed Sessions
        cursor.execute("SELECT COUNT(*) as count FROM interview_sessions WHERE status = 'completed'")
        completed_sessions = cursor.fetchone()['count']

        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'totalUsers': total_users,
                'activeSessions': active_sessions,
                'completedSessions': completed_sessions
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── ANALYTICS ───────────────────────────────────────────────────────────────

@admin_api.route('/analytics', methods=['GET'])
@admin_required
def get_detailed_analytics():
    """Aggregate detailed platform analytics for charts."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Skill Popularity (Top 8)
        cursor.execute('''
            SELECT s.skill_name, COUNT(us.user_id) as user_count
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.id
            GROUP BY s.id
            ORDER BY user_count DESC
            LIMIT 8
        ''')
        skill_popularity = cursor.fetchall()

        # 2. Average Scores by Skill Category
        cursor.execute('''
            SELECT s.category, AVG(ua.performance_score) as avg_score
            FROM user_answers ua
            JOIN interview_sessions isess ON ua.session_id = isess.id
            JOIN questions q ON ua.question_id = q.id
            JOIN skills s ON q.skill_id = s.id
            WHERE ua.performance_score IS NOT NULL
            GROUP BY s.category
            ORDER BY avg_score DESC
        ''')
        category_performance = cursor.fetchall()

        # 3. Interview Activity (Last 7 Days)
        cursor.execute('''
            SELECT DATE(started_at) as date, COUNT(*) as count
            FROM interview_sessions
            WHERE started_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(started_at)
            ORDER BY date ASC
        ''')
        activity_trend = cursor.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'skillPopularity': skill_popularity,
            'categoryPerformance': serialize_data(category_performance),
            'activityTrend': serialize_data(activity_trend)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_api.route('/skills', methods=['GET'])
@admin_required
def get_all_skills():
    """List all available skills along with their synonyms."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Use GROUP_CONCAT to get synonyms as a comma-separated string
        query = '''
            SELECT s.id, s.skill_name, s.category, 
                   GROUP_CONCAT(sy.synonym SEPARATOR ', ') as synonyms
            FROM skills s
            LEFT JOIN skill_synonyms sy ON s.id = sy.skill_id
            GROUP BY s.id
            ORDER BY s.skill_name ASC
        '''
        cursor.execute(query)
        skills = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'skills': skills}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_api.route('/skills', methods=['POST'])
@admin_required
def add_skill():
    """Add a new skill to the platform, optionally with synonyms."""
    data = request.get_json()
    name = data.get('skill_name', '').strip()
    category = data.get('category', '').strip()
    synonyms = data.get('synonyms', []) # Optional list of strings

    if not name or not category:
        return jsonify({'success': False, 'message': 'Skill name and category are required.'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO skills (skill_name, category) VALUES (%s, %s)',
            (name, category)
        )
        new_id = cursor.lastrowid

        # Add synonyms if provided
        if synonyms and isinstance(synonyms, list):
            for syn in synonyms:
                syn = syn.strip()
                if syn:
                    cursor.execute(
                        'INSERT INTO skill_synonyms (skill_id, synonym) VALUES (%s, %s)',
                        (new_id, syn)
                    )
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'id': new_id, 'message': 'Skill added successfully.'}), 201
    except Exception as e:
        if 'Duplicate entry' in str(e):
            return jsonify({'success': False, 'message': f'Skill "{name}" already exists.'}), 409
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_api.route('/skills/<int:skill_id>/synonyms', methods=['POST'])
@admin_required
def add_synonym(skill_id):
    """Add a synonym/alias for a specific skill."""
    data = request.get_json()
    synonym = data.get('synonym', '').strip()

    if not synonym:
        return jsonify({'success': False, 'message': 'Synonym is required.'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO skill_synonyms (skill_id, synonym) VALUES (%s, %s)',
            (skill_id, synonym)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Synonym added successfully.'}), 201
    except Exception as e:
        if 'Duplicate entry' in str(e):
            return jsonify({'success': False, 'message': f'Synonym "{synonym}" already exists for this skill.'}), 409
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_api.route('/synonyms/<int:syn_id>', methods=['DELETE'])
@admin_required
def delete_synonym(syn_id):
    """Remove a specific synonym."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM skill_synonyms WHERE id = %s', (syn_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Synonym removed.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── GET /api/admin/questions ───────────────────────────────────────────────

@admin_api.route('/questions', methods=['GET'])
@admin_required
def list_questions():
    """Retrieve filtered list of questions."""
    skill_id = request.args.get('skill_id')
    difficulty = request.args.get('difficulty')
    exp_level = request.args.get('experience_level')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = '''
            SELECT q.*, s.skill_name 
            FROM questions q
            JOIN skills s ON q.skill_id = s.id
            WHERE 1=1
        '''
        params = []
        if skill_id:
            query += ' AND q.skill_id = %s'
            params.append(skill_id)
        if difficulty:
            query += ' AND q.difficulty = %s'
            params.append(difficulty)
        if exp_level:
            query += ' AND q.experience_level = %s'
            params.append(exp_level)
            
        query += ' ORDER BY q.id DESC'
        
        cursor.execute(query, tuple(params))
        questions = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'questions': serialize_data(questions)}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── POST /api/admin/questions ──────────────────────────────────────────────

@admin_api.route('/questions', methods=['POST'])
@admin_required
def add_question():
    """Add a new question to the bank."""
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            INSERT INTO questions 
            (skill_id, experience_level, difficulty, question, option1, option2, option3, option4, correct)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(query, (
            data['skill_id'], data['experience_level'], data['difficulty'],
            data['question'], data['option1'], data['option2'],
            data['option3'], data['option4'], data['correct']
        ))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return jsonify({'success': True, 'id': new_id, 'message': 'Question added successfully'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_api.route('/questions/csv', methods=['POST'])
@admin_required
def upload_questions_csv():
    """Bulk upload questions from a CSV file. skill_id is passed as a form field."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded.'}), 400

    file = request.files['file']
    skill_id = request.form.get('skill_id', '').strip()

    if not skill_id:
        return jsonify({'success': False, 'message': 'Please select a skill before uploading.'}), 400

    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'message': 'Invalid file. Please upload a .csv file.'}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.reader(stream)

        conn = get_db_connection()
        cursor = conn.cursor()

        count = 0
        errors = []
        insert_query = '''
            INSERT INTO questions 
            (skill_id, experience_level, difficulty, question, option1, option2, option3, option4, correct)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''

        valid_exp = {'fresher', 'junior', 'mid', 'senior'}
        valid_diff = {'easy', 'medium', 'hard'}

        for i, row in enumerate(reader, start=1):
            # Skip empty rows and likely header rows
            if not row or len(row) < 8:
                continue
            if row[0].strip().lower() in ('experience_level', 'exp', 'level'):
                continue  # skip header if present

            exp_level  = row[0].strip().lower()
            difficulty = row[1].strip().lower()
            question   = row[2].strip()
            opt1       = row[3].strip()
            opt2       = row[4].strip()
            opt3       = row[5].strip()
            opt4       = row[6].strip()
            correct    = row[7].strip()

            if exp_level not in valid_exp:
                errors.append(f"Row {i}: invalid experience_level '{exp_level}'")
                continue
            if difficulty not in valid_diff:
                errors.append(f"Row {i}: invalid difficulty '{difficulty}'")
                continue
            if not correct.isdigit() or int(correct) not in range(1, 5):
                errors.append(f"Row {i}: correct must be 1-4, got '{correct}'")
                continue

            cursor.execute(insert_query, (
                skill_id, exp_level, difficulty, question,
                opt1, opt2, opt3, opt4, int(correct)
            ))
            count += 1

        conn.commit()
        conn.close()

        msg = f'Successfully imported {count} question(s).'
        if errors:
            msg += f' Skipped {len(errors)} row(s) with errors: ' + '; '.join(errors[:3])
            if len(errors) > 3:
                msg += f' ... and {len(errors)-3} more.'

        return jsonify({'success': True, 'message': msg, 'imported': count}), 201

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing CSV: {str(e)}'}), 500


# ─── PUT /api/admin/questions/<id> ───────────────────────────────────────────

@admin_api.route('/questions/<int:qid>', methods=['PUT', 'PATCH'])
@admin_required
def update_question(qid):
    """Update existing question."""
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            UPDATE questions 
            SET skill_id=%s, experience_level=%s, difficulty=%s, question=%s, 
                option1=%s, option2=%s, option3=%s, option4=%s, correct=%s
            WHERE id=%s
        '''
        cursor.execute(query, (
            data['skill_id'], data['experience_level'], data['difficulty'],
            data['question'], data['option1'], data['option2'],
            data['option3'], data['option4'], data['correct'], qid
        ))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Question updated successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── DELETE /api/admin/questions/<id> ────────────────────────────────────────

@admin_api.route('/questions/<int:qid>', methods=['DELETE'])
@admin_required
def delete_question(qid):
    """Remove a question from the bank."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM questions WHERE id = %s', (qid,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Question deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── GET /api/admin/users/<id> ───────────────────────────────────────────────

@admin_api.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user_detail(user_id):
    """Aggregate all information for a specific user."""
    try:
        conn = get_db_connection()
        # Use simple cursor first to check user existence
        cursor = conn.cursor(dictionary=True)
        
        # 1. Basic User Info
        cursor.execute('SELECT id, full_name, email, avatar, created_at FROM users WHERE id = %s', (user_id,))
        user_basic = cursor.fetchone()
        
        if not user_basic:
            conn.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # 2. Resume Info
        cursor.execute('SELECT extracted_text, total_experience FROM resumes WHERE user_id = %s', (user_id,))
        resume_data = cursor.fetchone()

        # 3. Skills
        cursor.execute('''
            SELECT s.skill_name as name, s.category, us.years_experience as years, us.experience_level as level
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.id
            WHERE us.user_id = %s
        ''', (user_id,))
        skills = cursor.fetchall()

        # 4. Interview History + Scores
        cursor.execute('''
            SELECT 
                s.id, 
                s.status, 
                s.started_at, 
                s.ended_at,
                (SELECT AVG(performance_score) FROM user_answers WHERE session_id = s.id) as avg_score
            FROM interview_sessions s
            WHERE s.user_id = %s
            ORDER BY s.started_at DESC
        ''', (user_id,))
        history = cursor.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'user': serialize_data({
                'id': user_basic['id'],
                'fullName': user_basic['full_name'],
                'email': user_basic['email'],
                'joinedAt': user_basic['created_at'],
                'avatar': user_basic['avatar'],
                'resume': resume_data['extracted_text'] if resume_data else None,
                'totalExperience': resume_data['total_experience'] if resume_data else 0,
                'skills': skills,
                'history': history
            })
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── DELETE /api/admin/users/<id> ───────────────────────────────────────────

@admin_api.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """
    Permanently delete a user and all their associated data.
    This includes resumes, skills, interview sessions, and answers.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Delete user answers (via interview sessions)
        cursor.execute('''
            DELETE FROM user_answers 
            WHERE session_id IN (SELECT id FROM interview_sessions WHERE user_id = %s)
        ''', (user_id,))
        
        # 2. Delete interview sessions
        cursor.execute('DELETE FROM interview_sessions WHERE user_id = %s', (user_id,))
        
        # 3. Delete resumes
        cursor.execute('DELETE FROM resumes WHERE user_id = %s', (user_id,))
        
        # 4. Delete user skills
        cursor.execute('DELETE FROM user_skills WHERE user_id = %s', (user_id,))
        
        # 5. Finally, delete the user record
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'User not found.'}), 404
            
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'User {user_id} and all related data have been deleted.'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── GET  /api/admin/hero-image ─────────────────────────────────────────

@admin_api.route('/hero-image', methods=['GET'])
def get_hero_image():
    """Public endpoint — returns current hero image URL (no auth needed)."""
    cfg = _read_config()
    url = cfg.get('hero_image_url')
    return jsonify({'success': True, 'hero_image_url': url}), 200


# ─── SITE SETTINGS (GENERAL) ───────────────────────────

@admin_api.route('/settings', methods=['GET'])
@admin_required
def get_site_settings():
    """Returns all site configuration settings."""
    cfg = _read_config()
    return jsonify({'success': True, 'settings': cfg}), 200

@admin_api.route('/settings/public', methods=['GET'])
def get_public_settings():
    """Public endpoint for user-facing site configuration."""
    cfg = _read_config()
    # Filter to only include safe, non-sensitive data
    public_keys = {
        'site_name', 'site_tagline', 'contact_email', 'hero_image_url',
        'audience_1_image_url', 'audience_2_image_url', 'audience_3_image_url',
        'advantage_1_image_url', 'advantage_2_image_url', 'advantage_3_image_url'
    }
    public_cfg = {k: cfg.get(k) for k in public_keys if k in cfg}
    
    # Defaults if not set
    if not public_cfg.get('site_name'): public_cfg['site_name'] = 'Interview Me'
    if not public_cfg.get('site_tagline'): public_cfg['site_tagline'] = 'Personalized Interview Practice Based on Resume and Performance.'
    
    return jsonify({'success': True, 'settings': public_cfg}), 200

@admin_api.route('/settings', methods=['POST'])
@admin_required
def update_site_settings():
    """Updates general site configuration settings."""
    data = request.get_json()
    cfg = _read_config()
    
    # Update allowed keys only
    allowed_keys = {'site_name', 'site_tagline', 'contact_email', 'interview_q_count'}
    for key in allowed_keys:
        if key in data:
            cfg[key] = data[key]
            
    _write_config(cfg)
    return jsonify({'success': True, 'message': 'Site settings updated successfully.'}), 200


# ─── POST /api/admin/upload-image ─────────────────────────────────────────

@admin_api.route('/upload-image', methods=['POST'])
@admin_required
def upload_site_image():
    """Admin uploads a new image for a specific site slot."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected.'}), 400

    config_key = request.form.get('config_key')
    valid_keys = {
        'hero_image_url', 'audience_1_image_url', 'audience_2_image_url', 'audience_3_image_url',
        'advantage_1_image_url', 'advantage_2_image_url', 'advantage_3_image_url'
    }
    if config_key not in valid_keys:
        return jsonify({'success': False, 'message': 'Invalid config key for image upload.'}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTS:
        return jsonify({'success': False, 'message': f'Unsupported file type. Allowed: {ALLOWED_EXTS}'}), 400

    try:
        os.makedirs(UPLOADS_FOLDER, exist_ok=True)
        filename = f"{config_key.replace('_url', '')}_{int(time.time())}.{ext}"
        save_path = os.path.join(UPLOADS_FOLDER, filename)
        file.save(save_path)

        # Build URL client will use
        image_url = f'http://127.0.0.1:5000/static/uploads/{filename}'

        cfg = _read_config()
        cfg[config_key] = image_url
        _write_config(cfg)

        return jsonify({'success': True, 'image_url': image_url, 'message': 'Image updated successfully.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ─── DELETE /api/admin/upload-image ───────────────────────────────────────

@admin_api.route('/upload-image', methods=['DELETE'])
@admin_required
def reset_site_image():
    """Resets a site image back to the default."""
    data = request.get_json()
    config_key = data.get('config_key')
    valid_keys = {
        'hero_image_url', 'audience_1_image_url', 'audience_2_image_url', 'audience_3_image_url',
        'advantage_1_image_url', 'advantage_2_image_url', 'advantage_3_image_url'
    }
    if config_key not in valid_keys:
        return jsonify({'success': False, 'message': 'Invalid config key.'}), 400

    cfg = _read_config()
    cfg[config_key] = None
    _write_config(cfg)
    return jsonify({'success': True, 'message': 'Image reset to default.'}), 200

# ─── JOBS MANAGEMENT ───────────────────────────────────────────────────────

@admin_api.route('/jobs', methods=['GET'])
@admin_required
def get_all_jobs():
    """List all job roles and their required skills."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get jobs
        cursor.execute('SELECT * FROM job_roles ORDER BY id DESC')
        jobs = cursor.fetchall()
        
        # Get skills for each job
        for job in jobs:
            cursor.execute('''
                SELECT s.id, s.skill_name, jrs.required_level
                FROM job_required_skills jrs
                JOIN skills s ON jrs.skill_id = s.id
                WHERE jrs.job_id = %s
            ''', (job['id'],))
            job['skills'] = cursor.fetchall()
            
        conn.close()
        return jsonify({'success': True, 'jobs': jobs}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_api.route('/jobs', methods=['POST'])
@admin_required
def create_job():
    """Create a new job role with associated skills."""
    data = request.get_json()
    title = data.get('title')
    min_exp = data.get('min_experience', 0)
    max_exp = data.get('max_experience')
    skill_assignments = data.get('skills', []) # List of {skill_id: 1, level: 'mid'}

    if not title:
        return jsonify({'success': False, 'message': 'Job title is required.'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Insert Job
        cursor.execute(
            'INSERT INTO job_roles (title, min_experience, max_experience) VALUES (%s, %s, %s)',
            (title, min_exp, max_exp)
        )
        job_id = cursor.lastrowid
        
        # 2. Insert Skills
        for sa in skill_assignments:
            cursor.execute(
                'INSERT INTO job_required_skills (job_id, skill_id, required_level) VALUES (%s, %s, %s)',
                (job_id, sa['skill_id'], sa['level'])
            )
            
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'id': job_id, 'message': 'Job role created successfully.'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_api.route('/jobs/<int:job_id>', methods=['DELETE'])
@admin_required
def delete_job(job_id):
    """Remove a job role."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Skills will be deleted automatically if ON DELETE CASCADE is set, 
        # otherwise we do it manually.
        cursor.execute('DELETE FROM job_required_skills WHERE job_id = %s', (job_id,))
        cursor.execute('DELETE FROM job_roles WHERE id = %s', (job_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Job role deleted.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
