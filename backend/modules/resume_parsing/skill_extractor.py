import re
from config.db_config import get_db_connection

def load_skills_from_db():
    """
    Loads skills and their synonyms from the database.
    Returns a dictionary mapping synonym/skill_name (lowercase) to the standardized skill_name.
    """
    skill_map = {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Load primary skill names
        cursor.execute("SELECT skill_name FROM skills")
        for row in cursor.fetchall():
            name = row['skill_name']
            skill_map[name.lower()] = name
            
        # Load synonyms and link to primary skill
        query = """
            SELECT s.skill_name, sy.synonym 
            FROM skill_synonyms sy
            JOIN skills s ON sy.skill_id = s.id
        """
        cursor.execute(query)
        for row in cursor.fetchall():
            skill_map[row['synonym'].lower()] = row['skill_name']
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error loading skills from DB: {e}")
        
    return skill_map

def extract_skills(cleaned_text: str) -> list:
    """
    Extracts unique skills from text using rule-based matching against database entries.
    """
    if not cleaned_text:
        return []
    
    skill_map = load_skills_from_db()
    if not skill_map:
        return []
        
    extracted_skills = set()
    text_lower = cleaned_text.lower()
    
    # Sort by length descending to match long phrases (e.g., "Node.js") before short ones ("Node")
    sorted_synonyms = sorted(skill_map.keys(), key=len, reverse=True)
    
    for synonym in sorted_synonyms:
        # Normalize synonym to match NLP-cleaned text (removing symbols like . in Node.js)
        normalized_synonym = re.sub(r'[^a-z0-9\s]', '', synonym.lower()).strip()
        
        if not normalized_synonym:
            continue

        pattern = rf'\b{re.escape(normalized_synonym)}\b'
        if re.search(pattern, text_lower):
            extracted_skills.add(skill_map[synonym])
            
    return sorted(list(extracted_skills))

if __name__ == "__main__":
    test_text = "I am a Senior Developer with experience in Python, React.js, and Machine Learning."
    print("Found:", extract_skills(test_text))
