from flask import Blueprint, request, jsonify
from modules.job_recommendation.job_recommender import recommend_jobs

job_api = Blueprint('job_api', __name__)

@job_api.route('/recommend', methods=['GET'])
def get_recommendations():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "message": "User ID is required"}), 400
        
    try:
        # Call the recommendation engine
        result = recommend_jobs(int(user_id))
        
        # Handle errors from the recommender (e.g., "Resume not found")
        if isinstance(result, dict) and "error" in result:
            return jsonify({"success": False, "message": result["error"]}), 404
            
        return jsonify({
            "success": True,
            "recommended_jobs": result["recommended_jobs"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
