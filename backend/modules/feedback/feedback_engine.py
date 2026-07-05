from config.db_config import get_db_connection
from mysql.connector import Error

def generate_overall_summary(session_id):
    """
    Generates the overall performance summary for a completed interview session.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Fetch Session Info
        cursor.execute("SELECT * FROM interview_sessions WHERE id = %s", (session_id,))
        session = cursor.fetchone()
        if not session:
            return False, "Session not found", 404

        # 2. Fetch User Answers for the session
        query = """
            SELECT is_correct
            FROM user_answers
            WHERE session_id = %s
        """
        cursor.execute(query, (session_id,))
        answers = cursor.fetchall()

        if not answers:
            return False, "No answers found for this session", 404

        # 3. Overall Statistics
        total_attempted = len(answers)
        correct_count = sum(1 for a in answers if a['is_correct'])
        wrong_count = total_attempted - correct_count
        accuracy = (correct_count / total_attempted * 100) if total_attempted > 0 else 0
        
        rating = "Needs Improvement"
        if accuracy >= 80: rating = "Excellent"
        elif accuracy >= 60: rating = "Good"
        elif accuracy >= 40: rating = "Average"
        
        # Calculate duration if ended_at is present
        duration_str = "N/A"
        if session.get('started_at') and session.get('ended_at'):
            delta = session['ended_at'] - session['started_at']
            minutes = "0"
            seconds = "00"
            if delta.total_seconds() > 0:
                total_sec = int(delta.total_seconds())
                minutes = str(total_sec // 60)
                seconds = str(total_sec % 60).zfill(2)
            duration_str = f"{minutes}:{seconds} min"

        summary_data = {
            'total_attempted': total_attempted,
            'correct': correct_count,
            'wrong': wrong_count,
            'accuracy': round(accuracy, 1),
            'rating': rating,
            'duration': duration_str
        }

        return True, summary_data, 200

    except Error as e:
        return False, f"Database error: {str(e)}", 500
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def generate_skill_summary(session_id):
    """
    Generates the skill-wise performance summary for a completed session.
    Calculates total attempted, correct answers, wrong answers, and accuracy per skill.
    Assigns status: Strong (>= 75%), Moderate (50-74%), Weak (< 50%).
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                s.skill_name,
                COUNT(ua.id) as total_attempted,
                SUM(ua.is_correct) as correct_answers
            FROM user_answers ua
            JOIN skills s ON ua.skill_id = s.id
            WHERE ua.session_id = %s
            GROUP BY s.id, s.skill_name
        """
        cursor.execute(query, (session_id,))
        rows = cursor.fetchall()

        if not rows:
            return False, "No skill data found for this session", 404

        skill_results = []
        for row in rows:
            skill_name = row['skill_name']
            total = int(row['total_attempted'])
            correct = int(row['correct_answers']) if row['correct_answers'] else 0
            wrong = total - correct
            accuracy = (correct / total * 100) if total > 0 else 0
            accuracy_rounded = round(accuracy, 1)

            if accuracy >= 75:
                status = "Strong"
            elif accuracy >= 50:
                status = "Moderate"
            else:
                status = "Weak"

            skill_results.append({
                'skill_name': skill_name,
                'total_attempted': total,
                'correct': correct,
                'wrong': wrong,
                'accuracy': accuracy_rounded,
                'status': status
            })

        return True, skill_results, 200

    except Error as e:
        return False, f"Database error: {str(e)}", 500
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def generate_difficulty_summary(session_id):
    """
    Generates the difficulty-wise performance summary for a completed session.
    Also generates basic textual insights based on accuracy by difficulty level.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                q.difficulty,
                COUNT(ua.id) as total_attempted,
                SUM(ua.is_correct) as correct_answers
            FROM user_answers ua
            JOIN questions q ON ua.question_id = q.id
            WHERE ua.session_id = %s
            GROUP BY q.difficulty
        """
        cursor.execute(query, (session_id,))
        rows = cursor.fetchall()

        if not rows:
            return False, "No difficulty data found for this session", 404

        dist = {}
        # Pre-fill easy, medium, hard to ensure they exist in logic
        for level in ['easy', 'medium', 'hard']:
            dist[level] = {'total': 0, 'correct': 0, 'accuracy': 0, 'wrong': 0}

        results = []
        for row in rows:
            diff = row['difficulty'].lower()
            total = int(row['total_attempted'])
            correct = int(row['correct_answers']) if row['correct_answers'] else 0
            accuracy = (correct / total * 100) if total > 0 else 0
            
            dist[diff]['total'] = total
            dist[diff]['correct'] = correct
            dist[diff]['accuracy'] = round(accuracy, 1)
            dist[diff]['wrong'] = total - correct

            results.append({
                'difficulty': diff.capitalize(),
                'total_attempted': total,
                'correct': correct,
                'wrong': total - correct,
                'accuracy': round(accuracy, 1)
            })

        # Generate simple insights
        insights = []
        easy_acc = dist['easy']['accuracy']
        med_acc = dist['medium']['accuracy']
        hard_acc = dist['hard']['accuracy']

        # Examples of basic logic rules
        if dist['easy']['total'] > 0 and easy_acc >= 80:
            insights.append("High accuracy in easy questions indicates strong fundamentals.")
        elif dist['easy']['total'] > 0 and easy_acc < 50:
            insights.append("Low accuracy in easy questions suggests a need to brush up on basic concepts.")

        if dist['medium']['total'] > 0:
            if med_acc < 50 and easy_acc >= 50:
                insights.append("Significant drop in medium difficulty points to a need for more practice in applying concepts.")
            elif med_acc >= 70:
                insights.append("Solid performance in medium questions shows good practical understanding.")
        
        if dist['hard']['total'] > 0:
            if hard_acc < 40:
                insights.append("Struggling with hard questions indicates an opportunity to deepen your knowledge of advanced topics.")
            elif hard_acc >= 60:
                insights.append("Excellent performance on hard questions highlights strong problem-solving skills in complex scenarios.")

        if not insights:
            insights.append("Keep practicing to improve your consistency across all difficulty levels.")

        return True, {'difficulties': results, 'insights': insights}, 200

    except Error as e:
        return False, f"Database error: {str(e)}", 500
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_user_interview_history(user_id):
    """
    Fetches the interview session history for a specific user, including summary stats.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                s.id as session_id,
                s.started_at,
                s.ended_at,
                s.total_questions,
                s.interview_type,
                COUNT(ua.id) as attempted,
                SUM(ua.is_correct) as correct,
                GROUP_CONCAT(DISTINCT sk.skill_name SEPARATOR ', ') as skills_list
            FROM interview_sessions s
            LEFT JOIN user_answers ua ON s.id = ua.session_id
            LEFT JOIN session_skills ss ON s.id = ss.session_id
            LEFT JOIN skills sk ON ss.skill_id = sk.id
            WHERE s.user_id = %s AND s.status = 'completed'
            GROUP BY s.id
            ORDER BY s.started_at DESC
        """
        cursor.execute(query, (user_id,))
        sessions = cursor.fetchall()

        history = []
        for s in sessions:
            total_attempted = s['attempted']
            correct_count = s['correct'] if s['correct'] else 0
            accuracy = (correct_count / total_attempted * 100) if total_attempted > 0 else 0
            
            rating = "Needs Improvement"
            if accuracy >= 80: rating = "Excellent"
            elif accuracy >= 60: rating = "Good"
            elif accuracy >= 40: rating = "Average"

            history.append({
                'session_id': s['session_id'],
                'date': s['started_at'].strftime('%Y-%m-%d %H:%M') if s['started_at'] else 'N/A',
                'total_questions': s['total_questions'],
                'interview_type': s['interview_type'],
                'skills': s['skills_list'],
                'attempted': total_attempted,
                'correct': correct_count,
                'accuracy': round(accuracy, 1),
                'rating': rating
            })


        return True, history, 200

    except Error as e:
        return False, f"Database error: {str(e)}", 500
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_user_skill_analytics(user_id, limit=None):
    """
    Generates aggregate skill-wise performance analytics for a user.
    Can be limited to the N most recent completed sessions.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Base query for session IDs
        session_query = "SELECT id FROM interview_sessions WHERE user_id = %s AND status = 'completed' ORDER BY started_at DESC"
        if limit and limit > 0:
            session_query += f" LIMIT {limit}"
        
        cursor.execute(session_query, (user_id,))
        session_rows = cursor.fetchall()
        if not session_rows:
            return True, [], 200
            
        session_ids = [r['id'] for r in session_rows]
        placeholders = ', '.join(['%s'] * len(session_ids))

        query = f"""
            SELECT 
                s.skill_name,
                COUNT(ua.id) as total_attempted,
                SUM(ua.is_correct) as total_correct
            FROM user_answers ua
            JOIN skills s ON ua.skill_id = s.id
            WHERE ua.session_id IN ({placeholders})
            GROUP BY s.id, s.skill_name
            ORDER BY total_attempted DESC
        """
        cursor.execute(query, tuple(session_ids))
        rows = cursor.fetchall()

        analytics = []
        for row in rows:
            total = int(row['total_attempted'])
            correct = int(row['total_correct']) if row['total_correct'] else 0
            accuracy = (correct / total * 100) if total > 0 else 0
            
            if accuracy >= 75: status = "Strong"
            elif accuracy >= 50: status = "Moderate"
            else: status = "Weak"

            analytics.append({
                'skill_name': row['skill_name'],
                'total_attempted': total,
                'correct': correct,
                'accuracy': round(accuracy, 1),
                'status': status
            })

        return True, analytics, 200

    except Error as e:
        return False, f"Database error: {str(e)}", 500
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_user_difficulty_analytics(user_id, limit=None):
    """
    Aggregates performance by difficulty level across recent sessions.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        session_query = "SELECT id FROM interview_sessions WHERE user_id = %s AND status = 'completed' ORDER BY started_at DESC"
        if limit and limit > 0: session_query += f" LIMIT {limit}"
        cursor.execute(session_query, (user_id,))
        session_rows = cursor.fetchall()
        if not session_rows: return True, {}, 200
        session_ids = [r['id'] for r in session_rows]
        placeholders = ', '.join(['%s'] * len(session_ids))

        query = f"""
            SELECT 
                q.difficulty,
                COUNT(ua.id) as total_attempted,
                SUM(ua.is_correct) as correct_answers
            FROM user_answers ua
            JOIN questions q ON ua.question_id = q.id
            WHERE ua.session_id IN ({placeholders})
            GROUP BY q.difficulty
        """
        cursor.execute(query, tuple(session_ids))
        rows = cursor.fetchall()

        dist = {'easy': 0, 'medium': 0, 'hard': 0}
        for row in rows:
            diff = row['difficulty'].lower()
            total = int(row['total_attempted'])
            correct = int(row['correct_answers']) if row['correct_answers'] else 0
            accuracy = (correct / total * 100) if total > 0 else 0
            dist[diff] = round(accuracy, 1)

        return True, dist, 200
    except Error as e:
        return False, str(e), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_performance_trend(user_id, limit=10):
    """
    Returns a time-series of accuracy scores for recent sessions.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                s.id,
                s.started_at,
                COUNT(ua.id) as total,
                SUM(ua.is_correct) as correct
            FROM interview_sessions s
            JOIN user_answers ua ON s.id = ua.session_id
            WHERE s.user_id = %s AND s.status = 'completed'
            GROUP BY s.id
            ORDER BY s.started_at ASC
            LIMIT %s
        """
        cursor.execute(query, (user_id, limit or 10))
        rows = cursor.fetchall()

        trend = []
        for row in rows:
            acc = (row['correct'] / row['total'] * 100) if row['total'] > 0 else 0
            trend.append({
                'date': row['started_at'].strftime('%m/%d'),
                'accuracy': round(acc, 1)
            })

        return True, trend, 200
    except Error as e:
        return False, str(e), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_user_overview_stats(user_id):
    """
    Returns high-level overview statistics for the dashboard home.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Total interviews
        cursor.execute("SELECT COUNT(*) as count FROM interview_sessions WHERE user_id = %s AND status = 'completed'", (user_id,))
        total_interviews = cursor.fetchone()['count']

        # 2. Avg Accuracy
        cursor.execute("""
            SELECT 
                COUNT(ua.id) as total,
                SUM(ua.is_correct) as correct
            FROM user_answers ua
            JOIN interview_sessions s ON ua.session_id = s.id
            WHERE s.user_id = %s AND s.status = 'completed'
        """, (user_id,))
        res = cursor.fetchone()
        avg_accuracy = (res['correct'] / res['total'] * 100) if res['total'] and res['total'] > 0 else 0

        # 3. Most Practiced Skill
        cursor.execute("""
            SELECT s.skill_name, COUNT(ua.id) as count
            FROM user_answers ua
            JOIN skills s ON ua.skill_id = s.id
            JOIN interview_sessions ises ON ua.session_id = ises.id
            WHERE ises.user_id = %s
            GROUP BY s.id, s.skill_name
            ORDER BY count DESC LIMIT 1
        """, (user_id,))
        skill_res = cursor.fetchone()
        top_skill = skill_res['skill_name'] if skill_res else "None"

        # 4. Readiness Score (weighted average of recent sessions)
        # For simplicity, we'll use the avg accuracy of the last 3 sessions
        cursor.execute("""
            SELECT s.id, COUNT(ua.id) as total, SUM(ua.is_correct) as correct
            FROM interview_sessions s
            JOIN user_answers ua ON s.id = ua.session_id
            WHERE s.user_id = %s AND s.status = 'completed'
            GROUP BY s.id
            ORDER BY s.started_at DESC LIMIT 3
        """, (user_id,))
        recent_sessions = cursor.fetchall()
        
        readiness_score = 0
        if recent_sessions:
            total_r = sum(s['total'] for s in recent_sessions)
            correct_r = sum(s['correct'] for s in recent_sessions)
            readiness_score = (correct_r / total_r * 100) if total_r > 0 else 0

        return True, {
            'total_interviews': total_interviews,
            'avg_accuracy': round(avg_accuracy, 1),
            'top_skill': top_skill,
            'readiness_score': round(readiness_score, 1)
        }, 200

    except Error as e:
        return False, str(e), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

