from config.db_config import get_db_connection
import json

def inspect_foreign_keys():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT 
        TABLE_NAME, 
        COLUMN_NAME, 
        CONSTRAINT_NAME, 
        REFERENCED_TABLE_NAME, 
        REFERENCED_COLUMN_NAME
    FROM
        INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE
        REFERENCED_TABLE_SCHEMA = 'interview_db' AND
        REFERENCED_TABLE_NAME = 'users';
    """
    cursor.execute(query)
    fks = cursor.fetchall()
    
    print("Foreign keys referencing 'users':")
    print(json.dumps(fks, indent=2))
    
    # Also check for tables referencing interview_sessions etc.
    query2 = """
    SELECT 
        TABLE_NAME, 
        COLUMN_NAME, 
        CONSTRAINT_NAME, 
        REFERENCED_TABLE_NAME, 
        REFERENCED_COLUMN_NAME
    FROM
        INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE
        REFERENCED_TABLE_SCHEMA = 'interview_db' AND
        REFERENCED_TABLE_NAME IN ('interview_sessions', 'resumes', 'user_skills');
    """
    cursor.execute(query2)
    fks2 = cursor.fetchall()
    print("\nForeign keys referencing user-related tables:")
    print(json.dumps(fks2, indent=2))
    
    conn.close()

if __name__ == "__main__":
    inspect_foreign_keys()
