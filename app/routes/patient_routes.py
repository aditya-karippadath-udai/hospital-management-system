from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.models.doctor import Doctor
from app.models.user import User
from app.utils.decorators import role_required

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@role_required(['patient'])
def dashboard():
    current_user_id = get_jwt_identity()
    patient = Patient.query.filter_by(user_id=current_user_id).first()
    
    if not patient:
        return jsonify({'error': 'Patient profile not found'}), 404
    
    # Upcoming appointments
    upcoming_appointments = Appointment.query.filter_by(
        patient_id=patient.id,
        status='scheduled'
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).limit(5).all()
    
    # Recent prescriptions
    recent_prescriptions = Prescription.query.filter_by(
        patient_id=patient.id
    ).order_by(Prescription.created_at.desc()).limit(5).all()
    
    return jsonify({
        'profile': patient.to_dict(),
        'statistics': {
            'total_appointments': len(patient.appointments),
            'total_prescriptions': len(patient.prescriptions)
        },
        'upcoming_appointments': [app.to_dict() for app in upcoming_appointments],
        'recent_prescriptions': [presc.to_dict() for presc in recent_prescriptions]
    }), 200

@patient_bp.route('/appointments', methods=['GET'])
@jwt_required()
@role_required(['patient'])
def get_appointments():
    current_user_id = get_jwt_identity()
    patient = Patient.query.filter_by(user_id=current_user_id).first()
    
    status = request.args.get('status')
    
    query = Appointment.query.filter_by(patient_id=patient.id)
    
    if status:
        query = query.filter_by(status=status)
    
    appointments = query.order_by(Appointment.appointment_date.desc()).all()
    
    return jsonify({
        'appointments': [app.to_dict() for app in appointments]
    }), 200

@patient_bp.route('/prescriptions', methods=['GET'])
@jwt_required()
@role_required(['patient'])
def get_prescriptions():
    current_user_id = get_jwt_identity()
    patient = Patient.query.filter_by(user_id=current_user_id).first()
    
    prescriptions = Prescription.query.filter_by(
        patient_id=patient.id
    ).order_by(Prescription.created_at.desc()).all()
    
    return jsonify({
        'prescriptions': [presc.to_dict() for presc in prescriptions]
    }), 200

@patient_bp.route('/profile', methods=['PUT'])
@jwt_required()
@role_required(['patient'])
def update_profile():
    current_user_id = get_jwt_identity()
    patient = Patient.query.filter_by(user_id=current_user_id).first()
    user = User.query.get(current_user_id)
    
    data = request.get_json()
    
    # Update user info
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'email' in data:
        user.email = data['email']
    
    # Update patient info
    if 'phone' in data:
        patient.phone = data['phone']
    if 'address' in data:
        patient.address = data['address']
    if 'emergency_contact' in data:
        patient.emergency_contact = data['emergency_contact']
    if 'medical_history' in data:
        patient.medical_history = data['medical_history']
    if 'allergies' in data:
        patient.allergies = data['allergies']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated successfully',
        'user': user.to_dict(),
        'patient': patient.to_dict()
    }), 200