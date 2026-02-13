from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.models.user import User
from app.utils.decorators import role_required
from datetime import datetime

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@role_required(['doctor'])
def dashboard():
    current_user_id = get_jwt_identity()
    doctor = Doctor.query.filter_by(user_id=current_user_id).first()
    
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404
    
    # Today's appointments
    today = datetime.now().date()
    today_appointments = Appointment.query.filter_by(
        doctor_id=doctor.id,
        appointment_date=today
    ).count()
    
    # Total patients
    total_patients = len(set([app.patient_id for app in doctor.appointments]))
    
    # Upcoming appointments
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date >= today,
        Appointment.status == 'scheduled'
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).limit(5).all()
    
    return jsonify({
        'statistics': {
            'today_appointments': today_appointments,
            'total_patients': total_patients,
            'total_appointments': len(doctor.appointments)
        },
        'upcoming_appointments': [app.to_dict() for app in upcoming_appointments],
        'profile': doctor.to_dict()
    }), 200

@doctor_bp.route('/appointments', methods=['GET'])
@jwt_required()
@role_required(['doctor'])
def get_appointments():
    current_user_id = get_jwt_identity()
    doctor = Doctor.query.filter_by(user_id=current_user_id).first()
    
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404
    
    date = request.args.get('date')
    status = request.args.get('status')
    
    query = Appointment.query.filter_by(doctor_id=doctor.id)
    
    if date:
        query = query.filter_by(appointment_date=datetime.strptime(date, '%Y-%m-%d').date())
    
    if status:
        query = query.filter_by(status=status)
    
    appointments = query.order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    
    return jsonify({
        'appointments': [app.to_dict() for app in appointments]
    }), 200

@doctor_bp.route('/appointments/<int:appointment_id>/status', methods=['PUT'])
@jwt_required()
@role_required(['doctor'])
def update_appointment_status(appointment_id):
    current_user_id = get_jwt_identity()
    doctor = Doctor.query.filter_by(user_id=current_user_id).first()
    
    appointment = Appointment.query.get(appointment_id)
    
    if not appointment or appointment.doctor_id != doctor.id:
        return jsonify({'error': 'Appointment not found'}), 404
    
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['completed', 'cancelled', 'no-show']:
        return jsonify({'error': 'Invalid status'}), 400
    
    appointment.status = status
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment status updated',
        'appointment': appointment.to_dict()
    }), 200

@doctor_bp.route('/patients', methods=['GET'])
@jwt_required()
@role_required(['doctor'])
def get_patients():
    current_user_id = get_jwt_identity()
    doctor = Doctor.query.filter_by(user_id=current_user_id).first()
    
    # Get unique patients who have appointments with this doctor
    patient_ids = set([app.patient_id for app in doctor.appointments])
    patients = Patient.query.filter(Patient.id.in_(patient_ids)).all()
    
    return jsonify({
        'patients': [patient.to_dict() for patient in patients]
    }), 200

@doctor_bp.route('/prescriptions', methods=['POST'])
@jwt_required()
@role_required(['doctor'])
def create_prescription():
    current_user_id = get_jwt_identity()
    doctor = Doctor.query.filter_by(user_id=current_user_id).first()
    
    data = request.get_json()
    
    prescription = Prescription(
        doctor_id=doctor.id,
        patient_id=data['patient_id'],
        appointment_id=data.get('appointment_id'),
        diagnosis=data['diagnosis'],
        medicines=data['medicines'],
        tests=data.get('tests'),
        notes=data.get('notes'),
        follow_up_date=datetime.strptime(data['follow_up_date'], '%Y-%m-%d').date() if data.get('follow_up_date') else None
    )
    
    db.session.add(prescription)
    db.session.commit()
    
    return jsonify({
        'message': 'Prescription created successfully',
        'prescription': prescription.to_dict()
    }), 201