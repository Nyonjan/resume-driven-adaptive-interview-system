import sys
import os
import io
from unittest.mock import patch

# Adjust path to import backend modules correctly
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import app
from config.db_config import get_db_connection

# Get a real user_id from the database to run the test
def get_test_user_id():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception as e:
        print(f"Error fetching test user ID: {e}")
    return 1  # Default fallback if DB is not running or empty

test_user_id = get_test_user_id()
print(f"Using test user ID: {test_user_id}")

valid_resume_text = """
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
"""

invalid_document_text = """
Python for Beginners Tutorial Chapter 4
In this chapter, we will learn about object-oriented programming in Python, AI applications, and why C++ is different.
We'll build a simple class definition:
class Developer:
    def __init__(self, name):
        self.name = name

AI models are highly complex mathematical systems trained on GPUs.
Unlike Python, C++ requires manual memory management.
Let's write a simple example to show the difference.
"""

def run_api_tests():
    # Set testing mode
    app.config['TESTING'] = True
    client = app.test_client()

    print("\n=== TEST 1: Uploading a Valid Resume ===")
    with patch('api.resume_api.extract_text_from_pdf', return_value=valid_resume_text):
        # We send a dummy PDF file structure
        data = {
            'file': (io.BytesIO(b'%PDF-1.4 ... dummy pdf ...'), 'resume.pdf'),
            'user_id': str(test_user_id)
        }
        response = client.post('/api/resume/upload', data=data, content_type='multipart/form-data')
        print(f"Status Code: {response.status_code}")
        print(f"Response JSON: {response.get_json()}")
        assert response.status_code == 200, "Should succeed with status 200"
        assert response.get_json()['success'] is True, "Should return success: True"

    print("\n=== TEST 2: Uploading an Invalid Document ===")
    with patch('api.resume_api.extract_text_from_pdf', return_value=invalid_document_text):
        data = {
            'file': (io.BytesIO(b'%PDF-1.4 ... dummy pdf ...'), 'random_tutorial.pdf'),
            'user_id': str(test_user_id)
        }
        response = client.post('/api/resume/upload', data=data, content_type='multipart/form-data')
        print(f"Status Code: {response.status_code}")
        print(f"Response JSON: {response.get_json()}")
        assert response.status_code == 400, "Should fail with status 400"
        assert response.get_json()['success'] is False, "Should return success: False"
        assert "does not appear to be a resume" in response.get_json()['message'], "Should give a clear resume validation error message"

    print("\n=== All API Tests Passed! ===")

if __name__ == '__main__':
    run_api_tests()
