def categorize_skills(skill_experience: dict) -> dict:
    """
    Categorizes skills into technical_proficiency, frameworks_tools, and soft_skills.
    """
    categories = {
        "technical_proficiency": [],
        "frameworks_tools": [],
        "soft_skills": []
    }

    # Define common skill sets for categorization
    # This can be expanded or moved to a DB table later
    tech_keywords = [
        "python", "javascript", "sql", "java", "c++", "ruby", "php", "go", "rust",
        "postgresql", "mysql", "mongodb", "redis", "oracle", "sql server",
        "aws", "azure", "gcp", "cloud", "docker", "kubernetes", "linux",
        "django", "flask", "node.js", "express", "spring", "laravel",
        "data science", "machine learning", "ai", "artificial intelligence"
    ]
    
    framework_keywords = [
        "react", "angular", "vue", "svelte", "next.js", "remix", "bootstrap", "tailwind",
        "git", "github", "gitlab", "bitbucket", "jenkins", "terraform", "ansible",
        "jest", "cypress", "selenium", "graphql", "rest api", "soap",
        "trello", "jira", "confluence", "slack"
    ]

    soft_skill_keywords = [
        "communication", "teamwork", "leadership", "problem solving", "critical thinking",
        "adaptability", "time management", "creativity", "work ethic", "interpersonal",
        "agile", "scrum", "project management", "mentoring", "customer service"
    ]

    for skill, years in skill_experience.items():
        skill_lower = skill.lower()
        
        # Determine category based on keywords
        if any(kw in skill_lower for kw in soft_skill_keywords):
            categories["soft_skills"].append({"name": skill, "years": years})
        elif any(kw in skill_lower for kw in framework_keywords):
            categories["frameworks_tools"].append({"name": skill, "years": years})
        else:
            # Default to technical proficiency if not in other lists
            categories["technical_proficiency"].append({"name": skill, "years": years})

    return categories
