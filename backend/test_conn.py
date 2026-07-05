import sys
from config.db_config import get_db_connection
try:
    print("Attempting to connect...")
    sys.stdout.flush()
    conn = get_db_connection()
    print("Connection successful!")
    sys.stdout.flush()
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    print("Query executed!")
    sys.stdout.flush()
    conn.close()
    print("Connection closed.")
    sys.stdout.flush()
except Exception as e:
    print(f"Connection failed: {e}")
    sys.stdout.flush()
