from flask import Blueprint, request, jsonify, flash, redirect, url_for
from app.services.appointment_service import AppointmentService
from app.utils.decorators import login_required, role_required

appointment_bp = Blueprint('appointment', __name__)

@appointment_bp.route('/', methods=['POST'])
@login_required
def create_appointment():
    """Create a new appointment (supports Form and JSON)"""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
        
    try:
        appointment = AppointmentService.create_appointment(data)
        if request.is_json:
            return jsonify({'message': 'Appointment created', 'appointment': appointment.to_dict()}), 201
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('patient.dashboard'))
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('patient.dashboard'))

@appointment_bp.route('/doctor/<int:doctor_id>/slots')
@login_required
def get_slots(doctor_id):
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date is required'}), 400
    
    slots = AppointmentService.get_available_slots(doctor_id, date_str)
    return jsonify({'available_slots': slots}), 200

@appointment_bp.route('/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    """Cancel appointment"""
    reason = request.json.get('reason') if request.is_json else request.form.get('reason')
    try:
        AppointmentService.update_appointment_status(appointment_id, 'cancelled', reason)
        if request.is_json:
            return jsonify({'message': 'Appointment cancelled'}), 200
        flash('Appointment cancelled', 'info')
        return redirect(request.referrer or url_for('auth.home'))
    except Exception as e:
        return jsonify({'error': str(e)}), 400