def generate_professional_summary(full_name, total_experience, skills):
    """
    Generates a professional summary string.
    """
    if not skills:
        return f"{full_name} is a professional with {total_experience} years of experience."

    top_skills = skills[:3]
    skills_str = ", ".join(top_skills)
    
    summary = (
        f"{full_name} is a versatile professional with {total_experience}+ years of experience "
        f"specializing in {skills_str}. Strong background in building scalable solutions "
        f"with a proven track record of success in high-growth environments."
    )
    return summary
