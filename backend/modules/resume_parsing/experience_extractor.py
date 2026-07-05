import re
from datetime import datetime

def extract_experience_blocks(raw_text: str) -> list:
    """
    Extract experience date ranges and calculate duration.
    Focuses on sections like "Experience" or "Work History" to avoid Education date conflicts.
    Handles headers with phantom spaces (e.g., "W O R K E X P").
    """
    if not raw_text:
        return []

    # Identify the start of the experience section
    start_keywords = [
        "EXPERIENCE", "WORK HISTORY", "PROFESSIONAL EXPERIENCE", 
        "EMPLOYMENT", "WORK EXP", "WORK EXPERIENCE", "PROFESSIONAL BACKGROUND"
    ]
    
    # Regex helper for headers with potential spaces between characters (e.g., "W O R K")
    def get_flexible_pattern(keyword):
        return r'\b' + r'\s*'.join(list(re.escape(keyword))) + r'\b'

    earliest_start = len(raw_text)
    found_start = False
    search_start_from = 0
    
    # Find the earliest occurrence of a start keyword
    for kw in start_keywords:
        pattern = rf'\b{get_flexible_pattern(kw)}\b'
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match and match.start() < earliest_start:
            earliest_start = match.start()
            search_start_from = match.end()
            found_start = True
    
    start_pos = earliest_start if found_start else 0

    # Identify the end of the section (the next header)
    end_keywords = [
        "EDUCATION", "SKILLS", "PROJECTS", "CERTIFICATIONS", 
        "VOLUNTEER", "INTERESTS", "LANGUAGES", "ACHIEVEMENTS"
    ]
    
    end_pos = len(raw_text)
    if found_start:
        search_area = raw_text[search_start_from:] 
        earliest_end_found = len(search_area)
        found_end = False
        
        for kw in end_keywords:
            pattern = rf'\b{get_flexible_pattern(kw)}\b'
            match = re.search(pattern, search_area, re.IGNORECASE)
            if match and match.start() < earliest_end_found:
                earliest_end_found = match.start()
                found_end = True
        
        if found_end:
            end_pos = search_start_from + earliest_end_found

    target_text = raw_text[start_pos:end_pos]

    current_year = datetime.now().year
    present_pattern = r'(?:Present|Current|Now|Ongoing|Till\s+Now|To\s+Date)'
    month_names = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
    date_pattern = rf'(?:{month_names}\s+\d{{4}}|\d{{4}}|\d{{2}}/\d{{4}})'
    range_pattern = rf'({date_pattern})\s*(?:-|–|—|to)\s*({date_pattern}|{present_pattern})'

    matches = re.finditer(range_pattern, target_text, re.IGNORECASE)
    experience_blocks = []

    def parse_date_info(date_str):
        year_match = re.search(r'\d{4}', date_str)
        year = int(year_match.group()) if year_match else None
        month = 1
        mm_match = re.search(r'(\d{1,2})/\d{4}', date_str)
        if mm_match:
            month = int(mm_match.group(1))
        else:
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            for i, m in enumerate(months, 1):
                if re.search(rf'{m}', date_str, re.IGNORECASE):
                    month = i
                    break
        return year, month

    for match in matches:
        start_raw = match.group(1)
        end_raw = match.group(2)

        start_year, start_month = parse_date_info(start_raw)

        if re.search(present_pattern, end_raw, re.IGNORECASE):
            end_year = current_year
            end_month = datetime.now().month
        else:
            end_year, end_month = parse_date_info(end_raw)

        if start_year and end_year:
            # Check for explicit month patterns for higher precision
            has_start_m = any(m in start_raw for m in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']) or '/' in start_raw
            has_end_m = any(m in end_raw for m in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']) or '/' in end_raw or re.search(present_pattern, end_raw, re.IGNORECASE)
            
            if not has_start_m and not has_end_m:
                # Use plain year difference if no month is explicitly detected
                duration = float(end_year - start_year)
            else:
                total_months = (end_year - start_year) * 12 + (end_month - start_month)
                duration = round(max(0.1, total_months / 12.0), 1)

            start_idx = max(0, match.start() - 120)
            end_idx = min(len(target_text), match.end() + 120)
            context = target_text[start_idx:end_idx].strip()

            experience_blocks.append({
                "start_year": start_year,
                "end_year": end_year,
                "duration": max(0.1, duration),
                "block_text": context
            })

    return experience_blocks

if __name__ == "__main__":
    test_resume = """
    G I U L I A G O N Z A L E Z 
    E D U C A T I O N 2014 - 2016 ... 2010 - 2014 
    S K I L L S ... Python, SQL
    W O R K E X P E R I E N C E 
    Python Developer DoorDash September 2017 - current
    Worked on building new Angular components ... determined solutions for the user experience
    Python Developer Intern Knewton April 2016 - April 2017
    P R O J E C T S ...
    """
    
    print("\nExtracting experience with Section Detection...")
    results = extract_experience_blocks(test_resume)
    import json
    print(json.dumps(results, indent=2))
    print(f"\nFound {len(results)} blocks.")
