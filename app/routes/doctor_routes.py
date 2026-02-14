from flask import Blueprint, jsonify, render_template, request, session, abort, flash, redirect, url_for
from flask_login import current_user, login_required
from app.services.appointment_service import AppointmentService
from app.services.doctor_service import DoctorService
from app.services.prescription_service import PrescriptionService
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.patient import Patient
from datetime import datetime

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/dashboard')
@login_required
def dashboard():
    """Enhanced Doctor Dashboard"""
    if current_user.role != 'doctor':
        abort(403)
        
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('auth.login'))

    stats = DoctorService.get_dashboard_stats(doctor.id)
    today = datetime.now().date()
    
    # Today's Agenda
    today_appointments = Appointment.query.filter_by(
        doctor_id=doctor.id, 
        appointment_date=today
    ).filter(Appointment.status.in_(['approved', 'confirmed', 'scheduled'])).order_by(Appointment.appointment_time.asc()).all()
    
    if request.path.startswith('/api') or request.is_json:
        return jsonify({
            'statistics': stats,
            'today_appointments': [a.to_dict() for a in today_appointments]
        }), 200
        
    return render_template('doctor/doctor_dashboard.html', 
                           stats=stats, 
                           doctor=doctor, 
                           today_appointments=today_appointments)

@doctor_bp.route('/appointments', methods=['GET'])
@login_required
def incoming_appointments():
    """Manage appointment requests and schedule"""
    if current_user.role != 'doctor': abort(403)
    
    status = request.args.get('status', 'pending')
    appointments = AppointmentService.get_appointments(
        user_id=current_user.id,
        role='doctor',
        status=status
    )
    
    if request.path.startswith('/api') or request.is_json:
        return jsonify({'appointments': [a.to_dict() for a in appointments]}), 200
        
    return render_template('doctor/doctor_appointments.html', appointments=appointments)

@doctor_bp.route('/appointments/<int:appointment_id>/status/<string:status>', methods=['POST'])
@login_required
def update_status(appointment_id, status):
    """Accept, reject, or complete an appointment"""
    if current_user.role != 'doctor': abort(403)
    
    if DoctorService.update_appointment_status(appointment_id, status):
        flash(f'Appointment {status} successfully', 'success')
    else:
        flash('Error updating appointment status', 'danger')
        
    return redirect(url_for('doctor.incoming_appointments', status='pending'))

@doctor_bp.route('/patient/<int:patient_id>/history')
@login_required
def patient_history(patient_id):
    """View patient medical history for consultations"""
    if current_user.role != 'doctor': abort(403)
    patient = Patient.query.get_or_404(patient_id)
    history = DoctorService.get_patient_history(patient_id)
    return render_template('doctor/patient_history.html', patient=patient, history=history)

@doctor_bp.route('/appointments/<int:appointment_id>/prescribe', methods=['GET', 'POST'])
@login_required
def create_prescription_view(appointment_id):
    """Prescription creation flow"""
    if current_user.role != 'doctor': abort(403)
    
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.doctor.user_id != current_user.id:
        abort(403)
        
    if request.method == 'POST':
        # Collect medicine data from forms
        med_names = request.form.getlist('med_name[]')
        med_dosages = request.form.getlist('med_dosage[]')
        med_freqs = request.form.getlist('med_freq[]')
        
        medicines = []
        for n, d, f in zip(med_names, med_dosages, med_freqs):
            if n: medicines.append({'name': n, 'dosage': d, 'frequency': f})
            
        data = {
            'appointment_id': appointment_id,
            'diagnosis': request.form.get('diagnosis'),
            'symptoms': request.form.get('symptoms'),
            'clinical_notes': request.form.get('clinical_notes'),
            'medicines': medicines,
            'advice': request.form.get('advice')
        }
        
        try:
            PrescriptionService.create_prescription(data)
            flash('Prescription saved and appointment completed', 'success')
            return redirect(url_for('doctor.dashboard'))
        except Exception as e:
            flash(f'Error saving prescription: {str(e)}', 'danger')
            
    return render_template('doctor/create_prescription.html', appointment=appointment)

@doctor_bp.route('/availability', methods=['GET', 'POST'])
@login_required
def manage_availability():
    """Toggle availability and manage working hours"""
    if current_user.role != 'doctor': abort(403)
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        data = {
            'is_available': 'is_available' in request.form,
            'available_time_start': request.form.get('available_time_start'),
            'available_time_end': request.form.get('available_time_end'),
            'available_days': request.form.getlist('available_days[]'),
            'consultation_fee': request.form.get('consultation_fee')
        }
        
        try:
            # Handle list strings if from API
            if request.is_json:
                data = request.get_json()
                
            DoctorService.update_availability(doctor.id, data)
            
            # Additional toggle for boolean availability
            doctor.is_available = data['is_available']
            from app.extensions import db
            db.session.commit()
            
            if not request.is_json:
                flash('Availability settings updated', 'success')
                return redirect(url_for('doctor.dashboard'))
            return jsonify({'message': 'Availability updated'}), 200
        except Exception as e:
            if request.is_json: return jsonify({'error': str(e)}), 400
            flash(f'Error updating availability: {str(e)}', 'danger')
            
    return render_template('doctor/doctor_availability.html', doctor=doctor)