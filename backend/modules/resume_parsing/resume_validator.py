import re

def validate_resume(text: str) -> tuple[bool, str]:
    """
    Validates if the provided text looks like a valid resume.
    Returns (is_valid, error_message).
    """
    if not text or len(text.strip()) < 150:
        return False, "The uploaded document is too short to be a valid resume."
        
    if len(text) > 100000:
        return False, "The uploaded document is too long to be a resume. Please upload a standard 1-3 page resume."

    # Define standard resume categories and their keywords
    categories = {
        "experience": [
            "EXPERIENCE", "WORK HISTORY", "PROFESSIONAL EXPERIENCE", 
            "EMPLOYMENT", "WORK EXP", "WORK EXPERIENCE", "PROFESSIONAL BACKGROUND",
            "CAREER HISTORY"
        ],
        "education": [
            "EDUCATION", "ACADEMIC", "ACADEMIC BACKGROUND", "ACADEMIC PROFILE", 
            "QUALIFICATIONS", "EDUCATIONAL QUALIFICATIONS"
        ],
        "skills": [
            "SKILLS", "TECHNICAL SKILLS", "EXPERTISE", "CORE COMPETENCIES", 
            "KEY SKILLS", "TECHNOLOGIES", "PROFESSIONAL SKILLS"
        ],
        "projects": [
            "PROJECTS", "PERSONAL PROJECTS", "ACADEMIC PROJECTS", "SELECTED PROJECTS",
            "PROJECT EXPERIENCE"
        ],
        "summary": [
            "SUMMARY", "PROFESSIONAL SUMMARY", "PROFILE", "OBJECTIVE", "ABOUT ME"
        ]
    }

    def get_flexible_pattern(keyword):
        # Handles potential phantom spaces in PDF extraction like "W O R K"
        return r'\b' + r'\s*'.join(list(re.escape(keyword))) + r'\b'

    matched_categories = set()
    for cat_name, keywords in categories.items():
        for kw in keywords:
            pattern = rf'{get_flexible_pattern(kw)}'
            if re.search(pattern, text, re.IGNORECASE):
                matched_categories.add(cat_name)
                break  # Category matched, move to next

    # Check for contact information (Email and Phone patterns)
    # Email pattern:
    email_pattern = r'[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}'
    has_email = bool(re.search(email_pattern, text))

    # Phone pattern (flexible for international/local formats):
    # A sequence of 7 to 15 digits with spaces/dashes/parentheses
    phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{10}\b'
    has_phone = bool(re.search(phone_pattern, text))

    # Let's count how many signals we have
    score = len(matched_categories)
    if has_email:
        score += 1
    if has_phone:
        score += 1

    # We require a minimum score of 2.
    # If the score is less than 2, it is definitely not a resume.
    # If the score is 2, let's require at least one of them to be 'experience', 'education', or 'skills'
    # to prevent false positives from random documents that happen to have an email or phone pattern and some word like "projects".
    if score < 2:
        return False, "The document does not appear to be a resume. A valid resume should contain standard sections such as Education, Experience, or Skills."
        
    if score == 2:
        # Check if the matched categories include a core section
        core_categories = {"experience", "education", "skills"}
        if not (matched_categories & core_categories):
            return False, "The document does not appear to be a resume. A valid resume should contain standard sections such as Education, Experience, or Skills."

    return True, ""
