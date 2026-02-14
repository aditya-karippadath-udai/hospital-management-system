from functools import wraps
from flask import request, jsonify, session, redirect, url_for, flash
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.services.role_service import RoleService

def login_required(f):
    """
    Decorator to ensure user is logged in.
    Supports both JWT (for API) and Session (for UI).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Check Session (UI/Web flow)
        if 'user_id' in session:
            return f(*args, **kwargs)
        
        # 2. Check JWT (API flow)
        try:
            verify_jwt_in_request(optional=True)
            if get_jwt_identity():
                return f(*args, **kwargs)
        except Exception:
            pass
            
        # If both fail, determine response type
        if request.path.startswith('/api'):
            return jsonify({'error': 'Authentication required'}), 401
        
        flash('Please login to access this page', 'warning')
        return redirect(url_for('auth.login'))
        
    return decorated_function

def role_required(allowed_roles):
    """
    Decorator to ensure user has required role.
    Works with both Session and JWT.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check Session first
            user_id = session.get('user_id')
            user_role = session.get('user_role')
            
            # If no session, try JWT
            if not user_id:
                try:
                    verify_jwt_in_request()
                    user_id = get_jwt_identity()
                    user_role = RoleService.get_user_role(user_id)
                except Exception:
                    pass
            
            if not user_id or user_role not in allowed_roles:
                if request.path.startswith('/api'):
                    return jsonify({'error': 'Permission denied'}), 403
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_json(required_fields):
    """Decorator to validate JSON request data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
            
            data = request.get_json()
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def paginate():
    """Decorator to handle pagination from query parameters"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 10))
                if page < 1: page = 1
                if per_page < 1: per_page = 10
            except ValueError:
                page = 1
                per_page = 10
            
            kwargs['page'] = page
            kwargs['per_page'] = per_page
            return f(*args, **kwargs)
        return decorated_function
    return decorator