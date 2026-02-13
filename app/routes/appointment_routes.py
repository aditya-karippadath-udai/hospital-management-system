from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.services.appointment_service import AppointmentService
from app.utils.decorators import role_required, validate_json
from datetime import datetime

appointment_bp = Blueprint('appointments', __name__)

@appointment_bp.route('', methods=['GET'])
@jwt_required()
def get_appointments():
    current_user_id = get_jwt_identity()
    user_role = request.user_role  # This would be set by a middleware
    
    if user_role == 'patient':
        patient = Patient.query.filter_by(user_id=current_user_id).first()
        appointments = Appointment.query.filter_by(patient_id=patient.id)
    elif user_role == 'doctor':
        doctor = Doctor.query.filter_by(user_id=current_user_id).first()
        appointments = Appointment.query.filter_by(doctor_id=doctor.id)
    else:
        appointments = Appointment.query
    
    # Apply filters
    date = request.args.get('date')
    status = request.args.get('status')
    doctor_id = request.args.get('doctor_id')
    
    if date:
        appointments = appointments.filter_by(appointment_date=datetime.strptime(date, '%Y-%m-%d').date())
    if status:
        appointments = appointments.filter_by(status=status)
    if doctor_id:
        appointments = appointments.filter_by(doctor_id=doctor_id)
    
    appointments = appointments.order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    
    return jsonify({
        'appointments': [app.to_dict() for app in appointments]
    }), 200

@appointment_bp.route('', methods=['POST'])
@jwt_required()
@role_required(['patient'])
@validate_json(['doctor_id', 'appointment_date', 'appointment_time', 'reason'])
def create_appointment():
    current_user_id = get_jwt_identity()
    patient = Patient.query.filter_by(user_id=current_user_id).first()
    
    data = request.get_json()
    
    # Check doctor availability
    doctor = Doctor.query.get(data['doctor_id'])
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404
    
    if not AppointmentService.is_doctor_available(doctor.id, data['appointment_date'], data['appointment_time']):
        return jsonify({'error': 'Doctor not available at this time'}), 400
    
    appointment = Appointment(
        doctor_id=data['doctor_id'],
        patient_id=patient.id,
        appointment_date=datetime.strptime(data['appointment_date'], '%Y-%m-%d').date(),
        appointment_time=datetime.strptime(data['appointment_time'], '%H:%M').time(),
        reason=data['reason'],
        notes=data.get('notes', '')
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment created successfully',
        'appointment': appointment.to_dict()
    }), 201

@appointment_bp.route('/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    # Check permissions
    current_user_id = get_jwt_identity()
    if not AppointmentService.can_access_appointment(current_user_id, appointment):
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(appointment.to_dict()), 200

@appointment_bp.route('/<int:appointment_id>', methods=['PUT'])
@jwt_required()
def update_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    # Check permissions
    current_user_id = get_jwt_identity()
    if not AppointmentService.can_modify_appointment(current_user_id, appointment):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if 'appointment_date' in data:
        appointment.appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
    if 'appointment_time' in data:
        appointment.appointment_time = datetime.strptime(data['appointment_time'], '%H:%M').time()
    if 'reason' in data:
        appointment.reason = data['reason']
    if 'notes' in data:
        appointment.notes = data['notes']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment updated successfully',
        'appointment': appointment.to_dict()
    }), 200

@appointment_bp.route('/<int:appointment_id>', methods=['DELETE'])
@jwt_required()
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    # Check permissions
    current_user_id = get_jwt_identity()
    if not AppointmentService.can_modify_appointment(current_user_id, appointment):
        return jsonify({'error': 'Unauthorized'}), 403
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    return jsonify({'message': 'Appointment cancelled successfully'}), 200

@appointment_bp.route('/available-slots', methods=['GET'])
def get_available_slots():
    doctor_id = request.args.get('doctor_id')
    date = request.args.get('date')
    
    if not doctor_id or not date:
        return jsonify({'error': 'doctor_id and date are required'}), 400
    
    available_slots = AppointmentService.get_available_slots(
        doctor_id,
        datetime.strptime(date, '%Y-%m-%d').date()
    )
    
    return jsonify({
        'doctor_id': doctor_id,
        'date': date,
        'available_slots': available_slots
    }), 200