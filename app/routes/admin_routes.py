from flask import Blueprint, jsonify, render_template, request
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.utils.decorators import role_required, paginate

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@role_required(['admin'])
def dashboard():
    """Render Admin Dashboard or return JSON stats"""
    stats = {
        'total_users': User.query.count(),
        'total_doctors': Doctor.query.count(),
        'total_patients': Patient.query.count(),
        'total_appointments': Appointment.query.count()
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    if request.path.startswith('/api'):
        return jsonify({
            'statistics': stats,
            'recent_users': [u.to_dict() for u in recent_users]
        }), 200
        
    return render_template('admin_dashboard.html', stats=stats, recent_users=recent_users)

@admin_bp.route('/users')
@role_required(['admin'])
@paginate()
def list_users(page, per_page):
    """API or HTML list of users"""
    users_pagination = User.query.paginate(page=page, per_page=per_page)
    if request.path.startswith('/api'):
        return jsonify({
            'users': [u.to_dict() for u in users_pagination.items],
            'total': users_pagination.total,
            'pages': users_pagination.pages
        }), 200
    return render_template('admin_users.html', users=users_pagination.items)

@admin_bp.route('/doctors')
@role_required(['admin'])
def list_doctors():
    doctors = Doctor.query.all()
    return jsonify({'doctors': [d.to_dict() for d in doctors]}), 200