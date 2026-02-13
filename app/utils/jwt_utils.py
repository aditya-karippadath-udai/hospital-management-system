from flask_jwt_extended import get_jwt_identity
from app.models.user import User
from functools import wraps

def get_current_user():
    """Get current user from JWT token"""
    user_id = get_jwt_identity()
    if user_id:
        return User.query.get(user_id)
    return None

def get_current_user_role():
    """Get current user's role"""
    user = get_current_user()
    return user.role if user else None