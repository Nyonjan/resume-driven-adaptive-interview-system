import math
from modules.job_recommendation.tfidf_calculator import compute_tfidf

def calculate_cosine_similarity(vec_a, vec_b):
    """
    Computes the cosine similarity between two vectors.
    Formula: (A . B) / (||A|| * ||B||)
    """
    # 1. Compute Dot Product
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    
    # 2. Compute Magnitudes (Euclidean Norm)
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    
    # 3. Handle zero magnitudes to avoid division by zero
    if mag_a == 0 or mag_b == 0:
        return 0.0
        
    # 4. Compute Similarity
    return dot_product / (mag_a * mag_b)

def recommend_jobs(user_id, top_n=5):
    """
    Job Recommendation Module:
    1. Fetches TF-IDF vectors for candidate and jobs.
    2. Calculates cosine similarity between candidate and each job.
    3. Calculates matched and missing skills for each job.
    4. Sorts jobs by similarity score descending.
    5. Returns Top N results.
    """
    # STEP 9.1 — Get TF-IDF Vectors
    tfidf_result = compute_tfidf(user_id)
    
    # Handle error from previous steps
    if isinstance(tfidf_result, dict) and "error" in tfidf_result:
        return tfidf_result
        
    tfidf_vectors = tfidf_result["tfidf_vectors"]
    job_metadata = tfidf_result["job_metadata"]
    vocabulary = tfidf_result["vocabulary"]
    
    # STEP 9.2 — Separate Candidate and Jobs
    # candidate is always at index 0
    candidate_vector = tfidf_vectors[0]
    job_vectors = tfidf_vectors[1:]
    
    # Get candidate skills (non-zero entries in candidate vector)
    candidate_skills = set()
    for i, val in enumerate(candidate_vector):
        if val > 0:
            candidate_skills.add(vocabulary[i])

    # STEP 9.3 & 9.4 — Compute Similarity and Store Results
    recommendations = []
    
    # job_vectors and job_metadata follow the same order
    for i, job_vector in enumerate(job_vectors):
        score = calculate_cosine_similarity(candidate_vector, job_vector)
        
        # Calculate skill matches
        job_skills = set()
        for j, val in enumerate(job_vector):
            if val > 0:
                job_skills.add(vocabulary[j])
        
        matched_skills = list(candidate_skills.intersection(job_skills))
        missing_skills = list(job_skills.difference(candidate_skills))
        
        # New: Compute skill match percentage
        total_req = len(job_skills)
        skill_match_percent = round((len(matched_skills) / total_req * 100), 0) if total_req > 0 else 0
        
        recommendations.append({
            "job_id": job_metadata[i]["job_id"],
            "job_title": job_metadata[i]["title"],
            "skill_match_percent": int(skill_match_percent),
            "similarity_score": round(score, 4),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills
        })
        
    # STEP 9.5 — Sort by Similarity (Primary) and Skill Match (Secondary)
    recommendations.sort(key=lambda x: (x["similarity_score"], x["skill_match_percent"]), reverse=True)
    
    # FINAL RETURN FORMAT
    return {
        "recommended_jobs": recommendations[:top_n]
    }
