from config.db_config import get_db_connection

def filter_jobs_by_experience(user_id):
    """
    Filters job roles based on the candidate's total experience stored in the resumes table.
    Requirement: min_experience <= user_total_experience AND (max_experience IS NULL OR user_total_experience <= max_experience)
    Returns:
        list: A list of eligible job dictionaries or an empty list if none match.
        dict: Error dictionary if resume is not found.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Fetch total_experience from resumes table
        cursor.execute("SELECT total_experience FROM resumes WHERE user_id = %s", (user_id,))
        resume_row = cursor.fetchone()

        if not resume_row:
            return {"error": "Resume not found for the given User ID."}

        user_total_experience = resume_row['total_experience']

        # 2. Query job_roles table for matching jobs
        # Logic: min_experience <= user_total_experience AND (max_experience IS NULL OR user_total_experience <= max_experience)
        query = """
            SELECT id AS job_id, title, min_experience, max_experience 
            FROM job_roles
            WHERE min_experience <= %s
              AND (max_experience IS NULL OR %s <= max_experience)
        """
        cursor.execute(query, (user_total_experience, user_total_experience))
        eligible_jobs = cursor.fetchall()

        # 3. Return the list (fetchall returns list of dicts because of dictionary=True)
        return eligible_jobs

    except Exception as e:
        print(f"Error filtering jobs by experience: {str(e)}")
        return []
    finally:
        cursor.close()
        conn.close()
