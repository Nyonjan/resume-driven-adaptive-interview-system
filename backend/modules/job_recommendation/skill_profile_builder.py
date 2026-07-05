from config.db_config import get_db_connection

def build_candidate_skill_document(user_id):
    """
    Builds a weighted skill document for a candidate for later TF-IDF processing.
    Weights are: fresher=1, junior=2, mid=3, senior=4.
    Returns:
        dict: { "user_id": user_id, "skill_document": "skill1 skill1 skill2 ..." }
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # Return results as dictionaries for easier mapping

    # Weight Mapping
    weight_map = {
        'fresher': 1,
        'junior': 2,
        'mid': 3,
        'senior': 4
    }

    try:
        # STEP 1.1 & 1.3 - Fetch User Skills and Names in one JOIN
        query = """
            SELECT s.skill_name, us.experience_level 
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.id
            WHERE us.user_id = %s
        """
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()

        # STEP 1.4 - Build Weighted Skill Document
        skill_terms = []
        for row in results:
            skill_name = row['skill_name'].lower().replace(" ", "_")
            exp_level = row['experience_level'].lower() if row['experience_level'] else 'fresher'
            
            # STEP 1.2 - Map Level to Weight
            weight = weight_map.get(exp_level, 1)
            
            # Repeat skill_name based on weight
            skill_terms.extend([skill_name] * weight)

        # Create space-separated string
        document_string = " ".join(skill_terms)

        return {
            "user_id": user_id,
            "skill_document": document_string
        }

    except Exception as e:
        print(f"Error building skill document: {str(e)}")
        return {
            "user_id": user_id,
            "skill_document": ""
        }
    finally:
        cursor.close()
        conn.close()
