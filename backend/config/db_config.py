import mysql.connector

def get_db_connection():
    # Connect to the MySQL database
    conn = mysql.connector.connect(
        host='localhost',        # Change this if you're using a remote server
        user='root',             # Replace with your MySQL username
        password='whiteshadow#123', # Replace with your MySQL password
        database='adaptive_interview'  # Your database name
    )
    return conn