from config.db_config import get_db_connection
from mysql.connector import Error

def initialize_interview_session(user_id, selected_skills, mode):
    """
    Initializes a new interview session and sets up initial skill tracking.
    
    Args:
        user_id (int): ID of the user starting the interview.
        selected_skills (list): List of skill names or IDs to include.
        mode (str): Interview mode ('quick', 'standard', 'deep').
        
    Returns:
        tuple: (success (bool), data or error_message (dict/str), status_code (int))
    """
    # Map mode to questions PER SKILL
    per_skill_map = {
        'quick': 5,
        'standard': 10,
        'deep': 20
    }
    questions_per_skill = per_skill_map.get(mode.lower(), 10)
    total_questions = questions_per_skill * len(selected_skills)

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. End any existing in-progress sessions for this user
        cursor.execute("UPDATE interview_sessions SET status = 'completed', ended_at = CURRENT_TIMESTAMP WHERE user_id = %s AND status = 'in_progress'", (user_id,))
        
        # 2. Create Interview Session
        session_query = """
            INSERT INTO interview_sessions (user_id, total_questions, status)
            VALUES (%s, %s, 'in_progress')
        """
        cursor.execute(session_query, (user_id, total_questions))
        session_id = cursor.lastrowid

        # 2. Add Selected Skills to Session
        skill_ids = []
        for s in selected_skills:
            if isinstance(s, int) or (isinstance(s, str) and s.isdigit()):
                skill_ids.append(int(s))
            else:
                # Lookup ID by name
                cursor.execute("SELECT id FROM skills WHERE skill_name = %s", (s,))
                row = cursor.fetchone()
                if row:
                    skill_ids.append(row['id'])

        if not skill_ids:
            return False, "No valid skills found", 400

        # Check for 'max_questions' column presence
        cursor.execute("SHOW COLUMNS FROM session_skills LIKE 'max_questions'")
        has_max_questions = cursor.fetchone() is not None

        # 3. Insert skill tracking for this session
        if has_max_questions:
            skill_session_query = """
                INSERT INTO session_skills (session_id, skill_id, current_difficulty, max_questions)
                VALUES (%s, %s, 'easy', %s)
            """
            for s_id in skill_ids:
                cursor.execute(skill_session_query, (session_id, s_id, questions_per_skill))
        else:
            skill_session_query = """
                INSERT INTO session_skills (session_id, skill_id, current_difficulty)
                VALUES (%s, %s, 'easy')
            """
            for s_id in skill_ids:
                cursor.execute(skill_session_query, (session_id, s_id))

        conn.commit()

        return True, {
            'session_id': session_id,
            'total_questions': total_questions,
            'questions_per_skill': questions_per_skill
        }, 201

    except Error as e:
        if conn:
            conn.rollback()
        return False, f"Database error: {str(e)}", 500
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def end_interview_session(session_id):
    """
    Marks an interview session as completed and records the end time.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Check if session exists
        cursor.execute("SELECT status FROM interview_sessions WHERE id = %s", (session_id,))
        session = cursor.fetchone()

        if not session:
            return False, "Interview session not found", 404

        # 2. If already completed, just return success (idempotent)
        if session['status'] == 'completed':
            return True, "Session already completed", 200

        # 3. Update session status and ended_at
        update_query = """
            UPDATE interview_sessions 
            SET status = 'completed', ended_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        cursor.execute(update_query, (session_id,))
        conn.commit()

        return True, "Interview session ended successfully", 200

    except Error as e:
        if conn:
            conn.rollback()
        return False, f"Database error: {str(e)}", 500
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
