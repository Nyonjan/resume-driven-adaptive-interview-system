from flask import Blueprint, request, jsonify
from config.db_config import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

user_api = Blueprint('user_api', __name__)

# Route to update user avatar
@user_api.route('/update-avatar', methods=['POST'])
def update_avatar():
    data = request.get_json()
    user_id = data.get('user_id')
    avatar = data.get('avatar')

    if not user_id or not avatar:
        return jsonify({'success': False, 'message': 'User ID and avatar filename are required'}), 400

    # Basic validation of avatar filename (optional but recommended)
    allowed_avatars = ['avatar1.png', 'avatar2.png', 'avatar3.png']
    if avatar not in allowed_avatars:
        return jsonify({'success': False, 'message': 'Invalid avatar selection'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Update avatar
        cursor.execute('UPDATE users SET avatar = %s WHERE id = %s', (avatar, user_id))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Avatar updated successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Route to change user password
@user_api.route('/change-password', methods=['POST'])
def change_password():
    data = request.get_json()
    user_id = data.get('user_id')
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not user_id or not current_password or not new_password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current password hash
        cursor.execute('SELECT password_hash FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Verify current password
        if not check_password_hash(user[0], current_password):
            conn.close()
            return jsonify({'success': False, 'message': 'Incorrect current password'}), 401

        # Hash new password
        new_password_hash = generate_password_hash(new_password)

        # Update password
        cursor.execute('UPDATE users SET password_hash = %s WHERE id = %s', (new_password_hash, user_id))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Password changed successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
