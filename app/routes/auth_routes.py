from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_login import login_user, logout_user, login_required as flask_login_required
from app.services.auth_service import AuthService
from app.utils.jwt_utils import generate_token, generate_refresh_token
from app.utils.decorators import validate_json

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def home():
    """Root redirect to correct dashboard based on role"""
    from flask_login import current_user
    if current_user.is_authenticated:
        print(f"DEBUG: Authenticated user {current_user.email} accessing home with role {current_user.role}")
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif current_user.role == 'patient':
            return redirect(url_for('patient.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login route for Doctors and Patients (Email-based)"""
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
        else:
            email = request.form.get('email')
            password = request.form.get('password')

        if not email or not password:
            if request.is_json:
                return jsonify({'error': 'Missing email or password'}), 400
            flash('Email and password are required', 'danger')
            return render_template('auth/login.html')

        # Support for both admin username and email-based login
        if email == 'admin':
            user = AuthService.login_admin(email, password)
        else:
            user = AuthService.login_user(email, password)
        
        if not user:
            if request.is_json:
                return jsonify({'error': 'Invalid credentials'}), 401
            flash('Invalid email/username or password', 'danger')
            return render_template('auth/login.html')

        # Use Flask-Login to manage session
        login_user(user, remember=request.form.get('remember', False))
        print(f"DEBUG: User {user.username or user.email} logged in successfully with role: {user.role}")

        if request.is_json:
            return jsonify({
                'message': 'Login successful',
                'user': user.to_dict()
            }), 200

        # Redirect based on user role
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif user.role == 'patient':
            return redirect(url_for('patient.dashboard'))
        
        return redirect(url_for('auth.login'))

    return render_template('auth/login.html')

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login route for Admin (Username-based)"""
    from flask_login import current_user
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')

        if not username or not password:
            if request.is_json:
                return jsonify({'error': 'Missing username or password'}), 400
            flash('Username and password are required', 'danger')
            return render_template('auth/admin_login.html')

        user = AuthService.login_admin(username, password)
        
        if not user:
            if request.is_json:
                return jsonify({'error': 'Invalid username or password'}), 401
            flash('Invalid username or password', 'danger')
            return render_template('auth/admin_login.html')

        login_user(user, remember=request.form.get('remember', False))
        print(f"DEBUG: Admin {user.username} logged in successfully. Redirecting to admin dashboard.")

        if request.is_json:
            return jsonify({
                'message': 'Admin login successful',
                'user': user.to_dict()
            }), 200

        return redirect(url_for('admin.dashboard'))

    return render_template('auth/admin_login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration route supporting both HTML and API"""
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Basic validation
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role']
        for field in required_fields:
            if not data.get(field):
                if request.is_json:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
                flash(f'Missing required field: {field}', 'danger')
                return render_template('auth/register.html')
        
        # Role-specific validation
        if data.get('role') == 'doctor':
            if not data.get('specialization') or not data.get('license_number'):
                error_msg = 'Specialization and license number are required for doctors'
                if request.is_json:
                    return jsonify({'error': error_msg}), 400
                flash(error_msg, 'danger')
                return render_template('auth/register.html')

        if AuthService.check_email_exists(data.get('email')):
            if request.is_json:
                return jsonify({'error': 'Email already registered'}), 400
            flash('Email already registered', 'danger')
            return render_template('auth/register.html')
        
        if AuthService.check_username_exists(data.get('username')):
            if request.is_json:
                return jsonify({'error': 'Username already taken'}), 400
            flash('Username already taken', 'danger')
            return render_template('auth/register.html')
        
        try:
            user = AuthService.register_user(data)
            if request.is_json:
                return jsonify({'message': 'User registered successfully', 'user': user.to_dict()}), 201
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            if request.is_json:
                return jsonify({'error': f'Registration failed: {str(e)}'}), 500
            flash(f'Registration failed: {str(e)}', 'danger')
            return render_template('auth/register.html')

    return render_template('auth/register.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password request"""
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
        email = data.get('email')
        if not email:
            if request.is_json:
                return jsonify({'error': 'Email is required'}), 400
            flash('Email is required', 'danger')
            return render_template('auth/forgot_password.html')
            
        token = AuthService.generate_reset_token(email)
        
        message = 'If an account exists with that email, a reset token has been generated.'
        if token:
            info = f"Token generated (DEMO ONLY): {token}"
            if request.is_json:
                return jsonify({'message': message, 'token': token}), 200
            flash(message, 'info')
            flash(info, 'warning')
            return render_template('auth/forgot_password.html')
            
        if request.is_json:
            return jsonify({'message': message}), 200
        flash(message, 'info')
        return render_template('auth/forgot_password.html')
        
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token=None):
    """Reset password with token"""
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            token = data.get('token')
            new_password = data.get('new_password')
        else:
            token = request.form.get('token') or token
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password != confirm_password:
                flash('Passwords do not match', 'danger')
                return render_template('auth/reset_password.html', token=token)
        
        if not token or not new_password:
            if request.is_json:
                return jsonify({'error': 'Token and password are required'}), 400
            flash('Token and password are required', 'danger')
            return render_template('auth/reset_password.html', token=token)
            
        if AuthService.reset_password(token, new_password):
            if request.is_json:
                return jsonify({'message': 'Password reset successful'}), 200
            flash('Password reset successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            if request.is_json:
                return jsonify({'error': 'Invalid or expired token'}), 400
            flash('Invalid or expired token', 'danger')
            return render_template('auth/reset_password.html', token=token)
            
    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/logout', methods=['GET', 'POST'])
@flask_login_required
def logout():
    """Logout and clear session"""
    logout_user()
    session.clear()
    flash('Successfully logged out', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/api/profile', methods=['GET'])
@jwt_required()
def profile_api():
    """Get current user profile (API)"""
    current_user_id = get_jwt_identity()
    profile = AuthService.get_user_profile(current_user_id)
    if not profile: return jsonify({'error': 'User not found'}), 404
    return jsonify(profile), 200