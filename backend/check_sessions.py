from config.db_config import get_db_connection

def check_completed_sessions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, user_id, status FROM interview_sessions WHERE status = 'completed' LIMIT 5")
    rows = cursor.fetchall()
    print(rows)
    conn.close()

if __name__ == "__main__":
    check_completed_sessions()
