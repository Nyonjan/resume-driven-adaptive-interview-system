from config.db_config import get_db_connection
from mysql.connector import Error

def evaluate_performance(session_id, question_id, selected_option, response_time, confidence):
    """
    Evaluates user answer based on correctness, speed, and confidence.
    Adjusts difficulty level of the skill accordingly.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Fetch correct answer and skill_id
        cursor.execute("SELECT correct, skill_id, difficulty FROM questions WHERE id = %s", (question_id,))
        question = cursor.fetchone()
        if not question:
            return False, "Question not found", 404

        skill_id = question['skill_id']
        is_correct = 1 if (int(selected_option) == int(question['correct'])) else 0

        # 2. Compute speed score (Normalized response_time)
        # Assuming a target time of 60 seconds. Faster is better.
        speed_score = max(0, 1 - (float(response_time) / 60.0))

        # 3. Compute performance_score
        # score = 0.6*correct + 0.3*speed + 0.1*confidence
        performance_score = (0.6 * is_correct) + (0.3 * speed_score) + (0.1 * float(confidence))

        # 4. Store result in user_answers table
        insert_query = """
            INSERT INTO user_answers 
            (session_id, question_id, skill_id, selected_option, is_correct, response_time, confidence, performance_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            session_id, question_id, skill_id, selected_option, is_correct, response_time, confidence, performance_score
        ))

        # 5. Update session_skills (Adaptive Difficulty)
        cursor.execute("SELECT current_difficulty FROM session_skills WHERE session_id = %s AND skill_id = %s", (session_id, skill_id))
        skill_ref = cursor.fetchone()
        current_diff = skill_ref['current_difficulty'] if skill_ref else 'easy'

        new_diff = current_diff
        if performance_score > 0.7:
            # Increase difficulty
            if current_diff == 'easy': new_diff = 'medium'
            elif current_diff == 'medium': new_diff = 'hard'
        elif performance_score < 0.4:
            # Decrease difficulty
            if current_diff == 'hard': new_diff = 'medium'
            elif current_diff == 'medium': new_diff = 'easy'

        if new_diff != current_diff:
            cursor.execute("""
                UPDATE session_skills 
                SET current_difficulty = %s 
                WHERE session_id = %s AND skill_id = %s
            """, (new_diff, session_id, skill_id))

        # 6. Increment Skill Score (for general progress)
        cursor.execute("""
            UPDATE session_skills 
            SET skill_score = skill_score + %s 
            WHERE session_id = %s AND skill_id = %s
        """, (performance_score * 10, session_id, skill_id))

        conn.commit()

        return True, {
            'is_correct': bool(is_correct),
            'correct_option': question['correct'],
            'performance_score': round(performance_score, 2),
            'next_difficulty': new_diff
        }, 200

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
