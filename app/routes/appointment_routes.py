from flask import Blueprint, request, jsonify, session
from app.services.appointment_service import AppointmentService
from app.services.prescription_service import PrescriptionService
from app.utils.decorators import login_required, role_required

appointment_bp = Blueprint('appointment', __name__)

@appointment_bp.route('/', methods=['POST'])
@role_required(['patient'])
def create_appointment():
    """Book appointment with strict validation"""
    data = request.get_json() if request.is_json else request.form.to_dict()
    
    # Ensure patient_id is linked to the current user
    from app.models.patient import Patient
    patient = Patient.query.filter_by(user_id=session.get('user_id')).first()
    data['patient_id'] = patient.id

    try:
        appointment = AppointmentService.create_appointment(data)
        return jsonify({'message': 'Appointment requested', 'appointment': appointment.to_dict()}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@appointment_bp.route('/<int:appointment_id>', methods=['PATCH'])
@role_required(['doctor', 'admin'])
def update_status(appointment_id):
    """Approve, Reject, or Complete appointment"""
    data = request.get_json()
    status = data.get('status')
    user_role = session.get('user_role')
    
    try:
        appointment = AppointmentService.update_appointment_status(
            appointment_id=appointment_id,
            status=status,
            user_role=user_role,
            **data
        )
        return jsonify({'message': f'Status updated to {status}', 'appointment': appointment.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@appointment_bp.route('/<int:appointment_id>', methods=['DELETE'])
@role_required(['patient'])
def cancel_appointment(appointment_id):
    """Cancel pending appointment"""
    user_role = session.get('user_role')
    try:
        AppointmentService.update_appointment_status(
            appointment_id=appointment_id,
            status='cancelled',
            user_role=user_role,
            cancellation_reason=request.args.get('reason', 'Cancelled by patient')
        )
        return jsonify({'message': 'Appointment cancelled'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@appointment_bp.route('/prescribe', methods=['POST'])
@role_required(['doctor'])
def create_prescription():
    """Create prescription for an appointment"""
    data = request.get_json()
    try:
        prescription = PrescriptionService.create_prescription(data)
        return jsonify({'message': 'Prescription created', 'prescription': prescription.to_dict()}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400