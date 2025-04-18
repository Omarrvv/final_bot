"""
Authentication routes for the Egypt Tourism Chatbot.
Provides API endpoints for user registration, login, and token validation.
"""
import logging
import re
from flask import Blueprint, request, jsonify
from utils.auth import Auth, token_required

logger = logging.getLogger(__name__)

# Create Blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize Auth service
auth_service = Auth()


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json  # This could be None if request doesn't contain valid JSON!

    # Validate required fields
    required_fields = ['username', 'password', 'email']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Extract fields
    username = data['username']
    password = data['password']
    email = data['email']
    role = data.get('role', 'user')

    # Add email validation
    email_pattern = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
    if not email_pattern.match(email):
        return jsonify({"error": "Invalid email format"}), 400

    # Validate role
    if role not in ['user', 'admin']:
        return jsonify({"error": "Invalid role"}), 400

    # Register user
    try:
        result = auth_service.register_user(
            username=username,
            password=password,
            email=email,
            role=role
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": "Registration failed due to an internal error"}), 500

    if result['success']:
        return jsonify({
            "message": "User registered successfully",
            "user_id": result['user_id'],
            "token": result['token']
        }), 201
    else:
        return jsonify({"error": result.get('error', 'Registration failed')}), 400


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user."""
    data = request.json

    # Validate required fields
    required_fields = ['username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Extract fields
    username = data['username']
    password = data['password']

    # Login user
    result = auth_service.login_user(
        username=username,
        password=password
    )

    if result['success']:
        return jsonify({
            "message": "Login successful",
            "user_id": result['user_id'],
            "token": result['token'],
            "role": result['role']
        }), 200
    else:
        return jsonify({"error": result.get('error', 'Login failed')}), 401


@auth_bp.route('/validate', methods=['GET'])
@token_required
def validate_token():
    """Validate a token and get user info."""
    # Token validation is handled by the @token_required decorator
    user = request.user

    return jsonify({
        "valid": True,
        "user_id": user.get('sub'),
        "username": user.get('username'),
        "role": user.get('role')
    }), 200


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_user_profile():
    """Get current user profile information."""
    user = request.user
    username = user.get('username')

    # Get user from storage
    user_data = auth_service.get_user_by_username(username)
    if user_data:

        # Remove sensitive information
        profile = {
            "id": user_data.get('id'),
            "username": user_data.get('username'),
            "email": user_data.get('email'),
            "role": user_data.get('role'),
            "created_at": user_data.get('created_at'),
            "last_login": user_data.get('last_login')
        }

        return jsonify(profile), 200
    else:
        return jsonify({"error": "User not found"}), 404


def init_app(app):
    """Initialize authentication routes with the Flask app."""
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
