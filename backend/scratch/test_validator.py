import sys
import os

# Adjust path to import backend modules correctly
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.resume_parsing.resume_validator import validate_resume

# Define test cases
test_cases = {
    "valid_resume_1": """
    John Doe
    Email: john.doe@email.com | Phone: 123-456-7890
    
    PROFESSIONAL SUMMARY
    Dynamic Software Engineer with 5 years of experience in Python and C++.
    
    WORK EXPERIENCE
    Senior Python Developer at Tech Corp (2020 - Present)
    - Developed AI models and microservices.
    
    EDUCATION
    Bachelor of Science in Computer Science, University of Technology (2016-2020)
    
    SKILLS
    Python, AI, C++, SQL, Docker
    """,
    
    "random_doc_with_skills": """
    Python for Beginners Tutorial Chapter 4
    In this chapter, we will learn about object-oriented programming in Python, AI applications, and why C++ is different.
    We'll build a simple class definition:
    class Developer:
        def __init__(self, name):
            self.name = name
    
    AI models are highly complex mathematical systems trained on GPUs.
    Unlike Python, C++ requires manual memory management.
    Let's write a simple example to show the difference.
    """,
    
    "short_text": "I know python, ai, and c++.",
    
    "no_contact_but_rich_resume": """
    Jane Smith
    
    E D U C A T I O N
    Master of Science in Artificial Intelligence, Stanford University
    
    P R O F E S S I O N A L  E X P E R I E N C E
    Machine Learning Engineer Intern at AI Lab
    - Built deep learning models using PyTorch.
    
    S K I L L S
    Python, AI, Deep Learning, PyTorch
    """
}

for name, text in test_cases.items():
    is_valid, msg = validate_resume(text)
    print(f"[{name}]")
    print(f"  Length: {len(text)}")
    print(f"  Is Valid: {is_valid}")
    print(f"  Message: {msg}")
    print("-" * 50)
