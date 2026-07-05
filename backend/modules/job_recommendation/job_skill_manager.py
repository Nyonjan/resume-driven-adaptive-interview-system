from config.db_config import get_db_connection
from modules.job_recommendation.experience_filter import filter_jobs_by_experience

def build_filtered_job_skill_documents(user_id):
    """
    Step 3 of Job Recommendation Module:
    1. Filters jobs by candidate experience.
    2. Builds weighted skill documents for each eligible job role.
    3. Normalizes skill names to lowercase.
    
    Returns:
        list: [ { "job_id": id, "title": title, "skill_document": "..." }, ... ]
        dict: Error if resume not found.
    """
    # STEP 3.1 — Call Experience Filter
    eligible_jobs = filter_jobs_by_experience(user_id)

    # Check for errors from experience_filter
    if isinstance(eligible_jobs, dict) and "error" in eligible_jobs:
        return eligible_jobs
    
    # If no eligible jobs, return empty list
    if not eligible_jobs:
        return []

    job_id_map = {job['job_id']: job for job in eligible_jobs}
    job_ids = list(job_id_map.keys())
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Weight Mapping
    weight_map = {
        'fresher': 1,
        'junior': 2,
        'mid': 3,
        'senior': 4
    }

    try:
        # STEP 3.2 — Fetch ALL Required Skills for all eligible jobs in ONE query
        # Using %s dynamically for the IN clause
        placeholders = ', '.join(['%s'] * len(job_ids))
        query = f"""
            SELECT jrs.job_id, s.skill_name, jrs.required_level
            FROM job_required_skills jrs
            JOIN skills s ON jrs.skill_id = s.id
            WHERE jrs.job_id IN ({placeholders})
        """
        cursor.execute(query, job_ids)
        all_required_skills = cursor.fetchall()

        # Group skills by job_id
        skills_by_job = {}
        for skill_info in all_required_skills:
            jid = skill_info['job_id']
            if jid not in skills_by_job:
                skills_by_job[jid] = []
            skills_by_job[jid].append(skill_info)

        # STEP 3.4 & 3.5 — Build Weighted Job Skill Documents
        job_skill_docs = []
        for job_id, job in job_id_map.items():
            required_skills = skills_by_job.get(job_id, [])
            
            skill_terms = []
            for item in required_skills:
                # Normalize skill names to lowercase and join multi-word skills
                skill_name = item['skill_name'].lower().replace(" ", "_")
                req_level = item['required_level'].lower() if item['required_level'] else 'fresher'
                
                # STEP 3.3 — Map Level to Weight
                weight = weight_map.get(req_level, 1)
                
                # Repeat skill_name according to weight
                skill_terms.extend([skill_name] * weight)

            # Create space-separated string
            document_string = " ".join(skill_terms)

            job_skill_docs.append({
                "job_id": job_id,
                "title": job['title'],
                "skill_document": document_string
            })

        return job_skill_docs

    except Exception as e:
        print(f"Error building job skill documents: {str(e)}")
        return []
    finally:
        cursor.close()
        conn.close()
