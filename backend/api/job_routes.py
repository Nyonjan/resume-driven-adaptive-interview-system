from flask import Blueprint, request, jsonify

job_bp = Blueprint('job', __name__)

@job_bp.route('/recommend', methods=['GET'])
def recommend_jobs():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({
            "success": False,
            "message": "user_id is required"
        }), 400

    # 🔥 TEMP LOGIC (replace later with DB logic)
    jobs = [
        {
            "job_title": "Python Developer",
            "skill_match_percent": 80,
            "matched_skills": ["Python", "Flask"],
            "missing_skills": ["Docker", "AWS"]
        },
        {
            "job_title": "Backend Developer",
            "skill_match_percent": 65,
            "matched_skills": ["SQL", "API"],
            "missing_skills": ["System Design"]
        }
    ]

    return jsonify({
        "success": True,
        "recommended_jobs": jobs
    })