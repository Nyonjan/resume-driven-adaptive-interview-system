from config.db_config import get_db_connection

def verify_deletion_logic(user_id):
    """
    Simulate the deletion logic to check if it would work correctly.
    This script performs a DRY RUN (using a transaction that is rolled back).
    """
    try:
        conn = get_db_connection()
        conn.autocommit = False # Ensure we use transactions
        cursor = conn.cursor()
        
        print(f"Verifying deletion logic for user_id: {user_id}")
        
        # 1. Count records before
        cursor.execute("SELECT COUNT(*) FROM user_answers WHERE session_id IN (SELECT id FROM interview_sessions WHERE user_id = %s)", (user_id,))
        answers_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM interview_sessions WHERE user_id = %s", (user_id,))
        sessions_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM resumes WHERE user_id = %s", (user_id,))
        resumes_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_skills WHERE user_id = %s", (user_id,))
        skills_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE id = %s", (user_id,))
        user_exists = cursor.fetchone()[0]
        
        print(f"Records found: Answers={answers_count}, Sessions={sessions_count}, Resumes={resumes_count}, Skills={skills_count}, UserExists={user_exists}")
        
        if not user_exists:
            print("User does not exist. Skipping simulation.")
            conn.close()
            return

        # 2. Perform deletions
        cursor.execute("DELETE FROM user_answers WHERE session_id IN (SELECT id FROM interview_sessions WHERE user_id = %s)", (user_id,))
        cursor.execute("DELETE FROM interview_sessions WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM resumes WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM user_skills WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        # 3. Verify counts after (should be 0)
        cursor.execute("SELECT COUNT(*) FROM users WHERE id = %s", (user_id,))
        if cursor.fetchone()[0] == 0:
            print("Success: User and related data deleted in transaction.")
        else:
            print("Failure: User still exists after deletion.")
            
        # 4. Rollback to keep data intact
        conn.rollback()
        print("Transaction rolled back successfully.")
        conn.close()
        
    except Exception as e:
        print(f"Error during verification: {e}")

if __name__ == "__main__":
    # I'll try to find a real user ID first
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            verify_deletion_logic(row[0])
        else:
            print("No users found in database to test with.")
    except Exception as e:
        print(f"Could not find a user: {e}")
