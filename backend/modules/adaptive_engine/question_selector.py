import random
from config.db_config import get_db_connection
from mysql.connector import Error

def get_next_question(session_id):
    """
    Selects the next interview question based on the round-robin approach for skills
    and current difficulty levels.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 0. Check for an unanswered question in the current session (Reload case)
        check_unanswered_query = """
            SELECT q.*, iq.question_order, iq.skill_id as target_skill_id
            FROM interview_questions iq
            JOIN questions q ON iq.question_id = q.id
            WHERE iq.session_id = %s
            AND iq.question_id NOT IN (
                SELECT question_id FROM user_answers WHERE session_id = %s
            )
            ORDER BY iq.question_order DESC LIMIT 1
        """
        cursor.execute(check_unanswered_query, (session_id, session_id))
        unanswered = cursor.fetchone()

        if unanswered:
            # We found a question that was asked but not answered!
            found_question = unanswered
            target_skill_id = unanswered['target_skill_id']
            question_order = unanswered['question_order']
        else:
            # 1. Select the skill to ask next (Least questions asked per skill)
            # Criteria: questions_asked < max_questions
            skill_selection_query = """
                SELECT skill_id, current_difficulty, questions_asked, max_questions
                FROM session_skills
                WHERE session_id = %s AND questions_asked < max_questions
                ORDER BY questions_asked ASC
            """
            cursor.execute(skill_selection_query, (session_id,))
            eligible_skills = cursor.fetchall()

            if not eligible_skills:
                return False, "All planned questions for this session have been asked.", 404

            # Pick the first one (least questions asked) or randomize among those with same count
            min_asked = eligible_skills[0]['questions_asked']
            top_candidates = [s for s in eligible_skills if s['questions_asked'] == min_asked]
            selected_skill_ref = random.choice(top_candidates)
            
            target_skill_id = selected_skill_ref['skill_id']
            current_difficulty = selected_skill_ref['current_difficulty']

            # 2. Fetch an unasked question for this skill and difficulty
            difficulties = ['easy', 'medium', 'hard']
            search_order = [current_difficulty] + [d for d in difficulties if d != current_difficulty]
            
            found_question = None
            for difficulty in search_order:
                # Query questions excluding those already asked in this session
                question_query = """
                    SELECT q.* 
                    FROM questions q
                    WHERE q.skill_id = %s AND q.difficulty = %s
                    AND q.id NOT IN (
                        SELECT question_id FROM interview_questions WHERE session_id = %s
                    )
                    ORDER BY RAND() LIMIT 1
                """
                cursor.execute(question_query, (target_skill_id, difficulty, session_id))
                found_question = cursor.fetchone()
                if found_question:
                    break

            # 3. If no question found for THIS skill, try OTHER eligible skills
            if not found_question:
                for other_skill in [s for s in eligible_skills if s['skill_id'] != target_skill_id]:
                    target_skill_id = other_skill['skill_id']
                    for difficulty in difficulties:
                        cursor.execute(question_query, (target_skill_id, difficulty, session_id))
                        found_question = cursor.fetchone()
                        if found_question:
                            break
                    if found_question:
                        break

            if not found_question:
                return False, "No more unique questions found for any of the selected skills.", 404

            # Get current question order from session
            cursor.execute("SELECT current_question_index FROM interview_sessions WHERE id = %s", (session_id,))
            session_row = cursor.fetchone()
            question_order = (session_row['current_question_index'] if session_row else 0) + 1

            # 4. Record that this question was asked (using interview_questions)
            insert_tracking_query = """
                INSERT INTO interview_questions (session_id, question_id, skill_id, difficulty, question_order)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_tracking_query, (session_id, found_question['id'], target_skill_id, found_question['difficulty'], question_order))

            # 5. Increment questions_asked in session_skills
            update_skill_query = """
                UPDATE session_skills 
                SET questions_asked = questions_asked + 1 
                WHERE session_id = %s AND skill_id = %s
            """
            cursor.execute(update_skill_query, (session_id, target_skill_id))

            # 6. Update current_question_index in interview_sessions
            update_session_query = """
                UPDATE interview_sessions 
                SET current_question_index = %s 
                WHERE id = %s
            """
            cursor.execute(update_session_query, (question_order, session_id))

        # 7. Get Skill Name and User's Experience Level for this skill
        # We also need total_questions for tracking
        cursor.execute("SELECT user_id, total_questions FROM interview_sessions WHERE id = %s", (session_id,))
        session_data = cursor.fetchone()
        user_id = session_data['user_id'] if session_data else None
        total_questions = session_data['total_questions'] if session_data else 0

        skill_details_query = """
            SELECT s.skill_name, us.experience_level, us.id as user_skill_id
            FROM skills s
            LEFT JOIN user_skills us ON s.id = us.skill_id AND us.user_id = %s
            WHERE s.id = %s
        """
        cursor.execute(skill_details_query, (user_id, target_skill_id))
        details = cursor.fetchone()

        conn.commit()

        # Add metadata to question object
        found_question['skill_name'] = details['skill_name'] if details else "Unknown"
        found_question['experience_level'] = details['experience_level'] if details else "fresher"
        found_question['is_resume_skill'] = (details['user_skill_id'] is not None) if details else False
        found_question['current_question_index'] = question_order
        found_question['total_questions'] = total_questions

        return True, found_question, 200

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
