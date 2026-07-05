from flask import Blueprint, request, jsonify
from modules.adaptive_engine.session_manager import initialize_interview_session, end_interview_session
from modules.adaptive_engine.question_selector import get_next_question
from modules.adaptive_engine.evaluator import evaluate_performance
from modules.feedback.feedback_engine import (
    generate_overall_summary, 
    generate_skill_summary, 
    generate_difficulty_summary,
    get_user_interview_history,
    get_user_skill_analytics,
    get_user_difficulty_analytics,
    get_performance_trend,
    get_user_overview_stats
)

interview_api = Blueprint('interview_api', __name__)


@interview_api.route('/start', methods=['POST'])
def start_interview():
    """Initializes a new interview session."""
    data = request.get_json()
    user_id = data.get('user_id')
    selected_skills = data.get('selected_skills')
    mode = data.get('mode')

    if not user_id or not selected_skills or not mode:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    success, result, status_code = initialize_interview_session(user_id, selected_skills, mode)
    
    if success:
        return jsonify({
            'success': True,
            **result,
            'message': 'Interview session initialized'
        }), status_code
    else:
        return jsonify({
            'success': False,
            'message': result
        }), status_code

@interview_api.route('/next-question/<int:session_id>', methods=['GET'])
def fetch_next_question(session_id):
    """Retrieves the next adaptive question for the session."""
    success, result, status_code = get_next_question(session_id)
    
    if success:
        return jsonify({
            'success': True,
            'question': result
        }), status_code
    else:
        return jsonify({
            'success': False,
            'message': result
        }), status_code

@interview_api.route('/submit-answer', methods=['POST'])
def handle_submit_answer():
    """Evaluates the user's answer and updates session state using performance scoring."""
    data = request.get_json()
    session_id = data.get('session_id')
    question_id = data.get('question_id')
    selected_option = data.get('selected_option')
    response_time = data.get('response_time', 30)
    confidence = data.get('confidence', 0.5)

    if not all([session_id, question_id, selected_option]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    success, result, status_code = evaluate_performance(session_id, question_id, selected_option, response_time, confidence)
    
    if success:
        return jsonify({
            'success': True,
            **result,
            'message': 'Answer submitted and evaluated'
        }), status_code
    else:
        return jsonify({
            'success': False,
            'message': result
        }), status_code

@interview_api.route('/end', methods=['POST'])
def finalize_session():
    """Ends the interview session."""
    data = request.get_json()
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'success': False, 'message': 'Missing session_id'}), 400

    success, result, status_code = end_interview_session(session_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': result
        }), status_code
    else:
        return jsonify({
            'success': False,
            'message': result
        }), status_code

@interview_api.route('/results/<int:session_id>', methods=['GET'])
def get_interview_results(session_id):
    """Retrieves the overall performance summary for a completed session."""
    success, result, status_code = generate_overall_summary(session_id)
    
    if success:
        return jsonify({
            'success': True,
            'data': result
        }), status_code
    else:
        return jsonify({
            'success': False,
            'message': result
        }), status_code

@interview_api.route('/results/<int:session_id>/skills', methods=['GET'])
def get_interview_skills_summary(session_id):
    """Retrieves the skill-wise performance summary for a completed session."""
    success, result, status_code = generate_skill_summary(session_id)
    
    if success:
        return jsonify({
            'success': True,
            'data': result
        }), status_code
    else:
        return jsonify({
            'success': False,
            'message': result
        }), status_code

@interview_api.route('/results/<int:session_id>/difficulty', methods=['GET'])
def get_interview_difficulty_summary(session_id):
    """Retrieves the difficulty-wise performance summary for a completed session."""
    success, result, status_code = generate_difficulty_summary(session_id)
    
    if success:
        return jsonify({
            'success': True,
            'data': result
        }), status_code
    else:
        return jsonify({
            'success': False,
            'message': result
        }), status_code

@interview_api.route('/history/<int:user_id>', methods=['GET'])
def get_user_history(user_id):
    """Retrieves the interview history for a specific user."""
    success, result, status_code = get_user_interview_history(user_id)
    
    if success:
        return jsonify({
            'success': True,
            'data': result
        }), status_code
    else:
        return jsonify({
            'success': False,
            'message': result
        }), status_code

@interview_api.route('/analytics/<int:user_id>', methods=['GET'])
def get_skill_analytics(user_id):
    """Retrieves comprehensive aggregate analytics for a specific user."""
    filter_val = request.args.get('filter')
    limit = None
    if filter_val == 'latest': limit = 1
    elif filter_val == 'last5': limit = 5
    elif filter_val == 'last10': limit = 10
    
    # 1. Skill Analytics
    s_success, s_result, _ = get_user_skill_analytics(user_id, limit)
    
    # 2. Difficulty Analytics
    d_success, d_result, _ = get_user_difficulty_analytics(user_id, limit)
    
    # 3. Trend Analytics (Always uses a reasonable history, e.g., 10)
    t_success, t_result, _ = get_performance_trend(user_id, 10)
    
    if s_success and d_success and t_success:
        return jsonify({
            'success': True,
            'data': {
                'skills': s_result,
                'difficulty': d_result,
                'trend': t_result
            }
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to load some analytics components'
        }), 500

@interview_api.route('/overview/<int:user_id>', methods=['GET'])
def get_overview_stats(user_id):
    """Retrieves high-level summary stats for the dashboard overview."""
    success, result, status_code = get_user_overview_stats(user_id)
    
    if success:
        return jsonify({
            'success': True,
            'data': result
        }), status_code
    else:
        return jsonify({
            'success': False,
            'message': result
        }), status_code


