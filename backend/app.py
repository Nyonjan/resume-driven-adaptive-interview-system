import os
from flask import Flask
from flask_cors import CORS

# Import blueprints
from api.auth_api import auth_api
from api.resume_api import resume_api
from api.job_api import job_api
from api.interview_api import interview_api
from api.job_routes import job_bp
from api.admin_api import admin_api
from api.user_api import user_api

app = Flask(__name__, static_folder='static', static_url_path='/static')


# Secret key for server-side session (use a strong random key in production)
app.secret_key = os.environ.get('SECRET_KEY', 'admin-secret-key-change-in-prod-2024')

# Enable CORS (allow credentials so session cookies travel with requests)
# We use supports_credentials=True to allow cookies
CORS(app, supports_credentials=True)

# ── Session Cookie Configuration (Required for cross-port/cross-origin cookies) ──
app.config.update(
    SESSION_COOKIE_SAMESITE='None',  # Allows cookies to be sent cross-site
    SESSION_COOKIE_SECURE=True,    # Required when SameSite is 'None'
    SESSION_COOKIE_HTTPONLY=True,  # Security best practice
)

# ── Register blueprints ──────────────────────────────────────────────────────
app.register_blueprint(auth_api,      url_prefix='/api/auth')
app.register_blueprint(resume_api,    url_prefix='/api/resume')
app.register_blueprint(job_api,       url_prefix='/api/job')
app.register_blueprint(interview_api, url_prefix='/api/interview')
app.register_blueprint(job_bp,        url_prefix='/api/job')
app.register_blueprint(admin_api,     url_prefix='/api/admin')
app.register_blueprint(user_api,      url_prefix='/api/user')

if __name__ == '__main__':
    app.run(debug=True)
