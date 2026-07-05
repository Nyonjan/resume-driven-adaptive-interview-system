import sys
import os

# Add the parent directory to sys.path so we can import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.db_config import get_db_connection
from werkzeug.security import generate_password_hash

def fix_admin_password():
    username = 'admin1'
    plain_password = 'admin123'
    hashed_password = generate_password_hash(plain_password)
    
    print(f"Update: Setting hashed password for '{username}'...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM admins WHERE username = %s", (username,))
        result = cursor.fetchone()
        
        if result:
            # Update existing user
            cursor.execute(
                "UPDATE admins SET password_hash = %s WHERE username = %s",
                (hashed_password, username)
            )
            print(f"Successfully updated password for admin: {username}")
        else:
            # Insert if doesn't exist (safety)
            cursor.execute(
                "INSERT INTO admins (username, password_hash, full_name) VALUES (%s, %s, %s)",
                (username, hashed_password, 'Admin User')
            )
            print(f"Created new admin user: {username}")
            
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating database: {e}")
        return False

if __name__ == "__main__":
    fix_admin_password()
