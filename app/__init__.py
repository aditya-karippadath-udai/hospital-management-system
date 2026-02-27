from flask import Flask, jsonify, request, render_template, redirect, url_for
from app.extensions import db, migrate, jwt
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    from app.config import config
    app.config.from_object(config.get(config_name, config['default']))
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    from app.extensions import login_manager
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Import models to ensure they are registered with SQLAlchemy
    from app import models
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Global template context
    from datetime import datetime
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    @app.template_filter('currency_inr')
    def currency_inr_filter(value):
        """Format value as INR (₹) with Indian numbering system"""
        try:
            if value is None: return "₹0.00"
            amount = float(value)
            s, temp = "%.2f" % amount, ""
            res, k = s.split(".")
            res = res[::-1]
            for i in range(len(res)):
                if i == 3 or (i > 3 and (i - 3) % 2 == 0):
                    temp += ","
                temp += res[i]
            res = temp[::-1].strip(",")
            return "₹" + res + "." + k
        except (ValueError, TypeError):
            return f"₹{value}"
    
    @app.teardown_request
    def shutdown_session(exception=None):
        if exception:
            db.session.rollback()
    
    # Run seeding logic within app context
    with app.app_context():
        from app.utils.seed import seed_admin
        seed_admin()
    
    # Add root redirect
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    return app


def register_blueprints(app):
    """Register all blueprints"""
    from app.routes.auth_routes import auth_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.doctor_routes import doctor_bp
    from app.routes.patient_routes import patient_bp
    from app.routes.appointment_routes import appointment_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(appointment_bp, url_prefix='/appointments')


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith('/api'):
            return jsonify({'error': 'Forbidden', 'message': 'You do not have permission to access this resource'}), 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api'):
            return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        if request.path.startswith('/api'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500