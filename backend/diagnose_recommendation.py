import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from modules.job_recommendation.job_recommender import recommend_jobs
import json

def diagnose():
    print("Diagnosing Job Recommendation for User ID: 1")
    try:
        result = recommend_jobs(1)
        print("Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Exception occurred: {str(e)}")

if __name__ == "__main__":
    diagnose()
