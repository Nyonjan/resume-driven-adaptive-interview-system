from flask import Blueprint, request, jsonify
from config.db_config import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

auth_api = Blueprint('auth_api', __name__)

# Route to handle user signup
@auth_api.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    full_name = data.get('fullName')
    email = data.get('email')
    password = data.get('password')

    if not full_name or not email or not password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    if len(password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400

    password_hash = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        return jsonify({'success': False, 'message': 'Email already exists'}), 400

    cursor.execute('INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)',
                   (full_name, email, password_hash))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'User signed up successfully'}), 200

# Route to handle user signin (login)
@auth_api.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Both email and password are required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()

    if user and check_password_hash(user[3], password):  # user[3] is the password_hash field
        user_info = {
            'id': user[0],        # User ID from database
            'fullName': user[1],  # full name
            'email': user[2],     # email
            'avatar': user[5] if len(user) > 5 else 'avatar1.png' # avatar
        }
        return jsonify({'success': True, 'message': 'Log In Successful', 'user': user_info}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 400

# Route to fetch user profile details
@auth_api.route('/profile', methods=['GET'])
def profile():
    email = request.args.get('email')
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT full_name, email, avatar FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            'success': True,
            'user': {
                'fullName': user[0],
                'email': user[1],
                'avatar': user[2]
            }
        }), 200
    else:
        return jsonify({'success': False, 'message': 'User not found'}), 404
