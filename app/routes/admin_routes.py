from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.utils.decorators import role_required, validate_json

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@role_required(['admin'])
def dashboard():
    # Get statistics
    total_users = User.query.count()
    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return jsonify({
        'statistics': {
            'total_users': total_users,
            'total_doctors': total_doctors,
            'total_patients': total_patients,
            'total_appointments': total_appointments
        },
        'recent_users': [user.to_dict() for user in recent_users]
    }), 200

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@role_required(['admin'])
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    users = User.query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'users': [user.to_dict() for user in users.items],
        'total': users.total,
        'pages': users.pages,
        'current_page': users.page
    }), 200

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin'])
@validate_json(['role', 'is_active'])
def update_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    user.role = data.get('role', user.role)
    user.is_active = data.get('is_active', user.is_active)
    
    db.session.commit()
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin'])
def delete_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Soft delete by deactivating
    user.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'User deactivated successfully'}), 200

@admin_bp.route('/doctors/pending', methods=['GET'])
@jwt_required()
@role_required(['admin'])
def get_pending_doctors():
    # This would require a 'status' field in Doctor model
    pending_doctors = Doctor.query.filter_by(is_approved=False).all()
    
    return jsonify({
        'pending_doctors': [doctor.to_dict() for doctor in pending_doctors]
    }), 200