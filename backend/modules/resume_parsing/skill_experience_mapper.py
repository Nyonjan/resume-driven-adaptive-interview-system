import re

def map_skill_experience(experience_blocks: list, skills: list, total_experience: float) -> dict:
    """
    Maps skills to durations. Assignments are based on presence in job blocks;
    otherwise, total_experience is assigned.
    """
    skill_experience = {}
    
    # Pre-process blocks for faster case-insensitive matching
    processed_blocks = []
    for block in experience_blocks:
        processed_blocks.append({
            "duration": block.get("duration", 0),
            "text": block.get("block_text", "").lower()
        })

    for skill in skills:
        skill_lower = skill.lower()
        # Find all blocks containing the skill
        matched_durations = [
            block["duration"] for block in processed_blocks 
            if re.search(rf'\b{re.escape(skill_lower)}\b', block["text"])
        ]
        
        if matched_durations:
            # Sum durations from all matching blocks
            skill_experience[skill] = round(sum(matched_durations), 1)
        else:
            # Fallback to total experience if not found in specific blocks
            skill_experience[skill] = round(total_experience, 1)
            
    return skill_experience

if __name__ == "__main__":
    exp_blocks = [
        {"duration": 3.0, "block_text": "API, web applications, full stack"},
        {"duration": 2.0, "block_text": "e-commerce, database queries"}
    ]
    extracted_skills = ["python", "java", "api", "database"]
    total_exp = 5.0
    
    result = map_skill_experience(exp_blocks, extracted_skills, total_exp)
    import json
    print(json.dumps(result, indent=2))
