import csv
import os
import sys
from mysql.connector import Error

# Add the parent directory to sys.path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.db_config import get_db_connection

# ==========================================
# CONFIGURATION: Set your CSV file path here
# ==========================================
CSV_FILE_PATH = r"d:\resume-driven-adaptive-interview\doc\sql_question.csv"
# ==========================================

def load_skill_map(cursor):
    """Fetches all skills from DB and returns a map of skill_name -> id"""
    cursor.execute("SELECT id, skill_name FROM skills")
    return {row[1].lower(): row[0] for row in cursor.fetchall()}

def validate_row(row, skill_map):
    """Validates CSV row and returns a tuple of (is_valid, reason, processed_data)"""
    valid_exp_levels = {'fresher', 'junior', 'mid', 'senior'}
    valid_difficulties = {'easy', 'medium', 'hard'}
    
    try:
        # Support both 'skill' (name) and 'skill_id' (direct integer)
        if 'skill' in row:
            skill_name = row['skill'].strip().lower()
            if skill_name not in skill_map:
                return False, f"Skill '{skill_name}' not found in database", None
            skill_id = skill_map[skill_name]
        elif 'skill_id' in row:
            try:
                skill_id = int(row['skill_id'].strip())
            except ValueError:
                return False, f"Invalid skill_id: {row['skill_id']}", None
        else:
            return False, "Missing 'skill' or 'skill_id' column", None

        exp_level = row['experience_level'].strip().lower()
        difficulty = row['difficulty'].strip().lower()
        question = row['question'].strip()
        options = [row[f'option{i}'].strip() for i in range(1, 5)]
        correct = row['correct'].strip()
        
        # 2. ENUM validation
        if exp_level not in valid_exp_levels:
            return False, f"Invalid experience level: {exp_level}", None
            
        if difficulty not in valid_difficulties:
            return False, f"Invalid difficulty: {difficulty}", None
            
        # 3. Correct option validation
        try:
            correct_int = int(correct)
            if not (1 <= correct_int <= 4):
                return False, f"Correct option must be between 1 and 4, got {correct}", None
        except ValueError:
            return False, f"Correct option must be an integer, got {correct}", None
            
        # 4. Empty check
        if not question or any(not opt for opt in options):
            return False, "Empty question or options", None
            
        return True, "Valid", (skill_id, exp_level, difficulty, question, options[0], options[1], options[2], options[3], correct_int)
        
    except KeyError as e:
        return False, f"Missing column: {str(e)}", None

def import_questions(csv_file_path):
    """Main function to parse CSV and bulk insert into MySQL"""
    if not os.path.exists(csv_file_path):
        print(f"Error: File not found at '{csv_file_path}'")
        print("Please update the 'CSV_FILE_PATH' variable at the top of this script.")
        return

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Load skill mapping
        print("Fetching skill mapping from database...")
        skill_map = load_skill_map(cursor)
        
        valid_rows = []
        skipped_count = 0
        success_count = 0
        
        # 2. Read CSV
        print(f"Reading CSV file: {csv_file_path}")
        with open(csv_file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                is_valid, reason, data = validate_row(row, skill_map)
                if is_valid:
                    valid_rows.append(data)
                else:
                    print(f"Skipping row {i}: {reason}")
                    skipped_count += 1
        
        # 3. Bulk Insert
        if valid_rows:
            print(f"Inserting {len(valid_rows)} valid questions into database...")
            insert_query = """
                INSERT INTO questions (skill_id, experience_level, difficulty, question, option1, option2, option3, option4, correct)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(insert_query, valid_rows)
            conn.commit()
            success_count = len(valid_rows)
            print("Bulk insert successful!")
        else:
            print("No valid rows found to insert.")

        print(f"Import Summary: {success_count} success, {skipped_count} skipped.")

    except Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    import_questions(CSV_FILE_PATH)
