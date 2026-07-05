from modules.job_recommendation.skill_profile_builder import build_candidate_skill_document
from modules.job_recommendation.job_skill_manager import build_filtered_job_skill_documents

def build_corpus(user_id):
    """
    Step 4 of Job Recommendation Module:
    Prepares a corpus of documents for TF-IDF analysis.
    The first document (index 0) is always the candidate's skill document.
    Subsequent documents are the skill documents for eligible jobs.
    
    Returns:
        dict: {
            "documents": ["candidate_doc", "job1_doc", "job2_doc", ...],
            "job_metadata": [{"job_id": 1, "title": "..."}, ...]
        }
        dict: Error if resume not found.
    """
    # 1. Fetch Candidate Skill Document
    candidate_result = build_candidate_skill_document(user_id)
    
    # Validation: TF-IDF cannot work with an empty candidate document
    if not candidate_result or not candidate_result.get("skill_document"):
        return {"error": "Candidate skill document is empty. Cannot perform recommendation."}

    # 2. Fetch Eligible Job Skill Documents
    job_docs_result = build_filtered_job_skill_documents(user_id)

    # 3. Validate Results
    # Check for "Resume not found" error from job_skill_manager (via experience_filter)
    if isinstance(job_docs_result, dict) and "error" in job_docs_result:
        return job_docs_result
    
    # If no eligible jobs, return empty document list and metadata
    if not job_docs_result:
        return {
            "documents": [],
            "job_metadata": []
        }

    # 4. Build Corpus List
    documents = []
    job_metadata = []

    # Add Candidate document as the first element (Index 0)
    documents.append(candidate_result.get("skill_document", ""))

    # Append job documents and track metadata
    for job in job_docs_result:
        documents.append(job.get("skill_document", ""))
        job_metadata.append({
            "job_id": job.get("job_id"),
            "title": job.get("title")
        })

    return {
        "documents": documents,
        "job_metadata": job_metadata
    }
