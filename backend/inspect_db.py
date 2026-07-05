from config.db_config import get_db_connection
import json

def inspect_schema():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    tables = ['interview_sessions', 'session_skills', 'user_answers']
    schema = {}
    
    for table in tables:
        cursor.execute(f"DESCRIBE {table}")
        schema[table] = cursor.fetchall()
        
    print(json.dumps(schema, indent=2))
    conn.close()

if __name__ == "__main__":
    inspect_schema()
