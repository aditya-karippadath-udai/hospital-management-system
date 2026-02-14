from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from app.models.user import User


def generate_token(user_id):
    """Generate JWT access token"""
    return create_access_token(identity=user_id)


def generate_refresh_token(user_id):
    """Generate JWT refresh token"""
    return create_refresh_token(identity=user_id)


def get_current_user():
    """Get current user from JWT token"""
    user_id = get_jwt_identity()
    if user_id:
        return User.query.get(user_id)
    return None


def get_current_user_id():
    """Get current user ID from JWT token"""
    return get_jwt_identity()