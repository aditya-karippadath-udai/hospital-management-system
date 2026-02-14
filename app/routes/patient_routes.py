from flask import Blueprint, jsonify, render_template, request, session, abort, flash, redirect, url_for
from flask_login import current_user, login_required
from app.services.patient_service import PatientService
from app.services.doctor_service import DoctorService
from app.services.appointment_service import AppointmentService
from app.services.prescription_service import PrescriptionService
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from datetime import datetime

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/dashboard')
@login_required
def dashboard():
    """Patient Dashboard View"""
    if current_user.role != 'patient':
        abort(403)
        
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        flash('Patient profile not found.', 'warning')
        return redirect(url_for('auth.home'))
        
    stats = PatientService.get_dashboard_stats(patient.id)
    upcoming_appointments = patient.appointments.filter(
        Appointment.appointment_date >= datetime.now().date(),
        Appointment.status.in_(['pending', 'approved'])
    ).order_by(Appointment.appointment_date).limit(5).all()
    
    if request.path.startswith('/api') or request.is_json:
        return jsonify({
            'statistics': stats,
            'upcoming_appointments': [a.to_dict() for a in upcoming_appointments]
        }), 200
        
    return render_template('patient/patient_dashboard.html', patient=patient, stats=stats, appointments=upcoming_appointments)

@patient_bp.route('/doctors', methods=['GET'])
@login_required
def list_doctors():
    """List all active doctors"""
    if current_user.role != 'patient': abort(403)
    
    specialization = request.args.get('specialization')
    doctors = PatientService.list_doctors(specialization=specialization)
    
    if request.path.startswith('/api') or request.is_json:
        return jsonify({'doctors': [d.to_dict() for d in doctors]}), 200
        
    return render_template('patient/patient_doctors.html', doctors=doctors, specialization=specialization)

@patient_bp.route('/doctors/<int:doctor_id>', methods=['GET'])
@login_required
def doctor_profile(doctor_id):
    """View detailed doctor profile"""
    if current_user.role != 'patient': abort(403)
    
    doctor = DoctorService.get_doctor_by_id(doctor_id)
    if not doctor:
        if request.is_json: return jsonify({'error': 'Doctor not found'}), 404
        flash('Doctor not found', 'danger')
        return redirect(url_for('patient.list_doctors'))
        
    if request.path.startswith('/api') or request.is_json:
        return jsonify({'doctor': doctor.to_dict()}), 200
        
    return render_template('patient/doctor_profile.html', doctor=doctor)

@patient_bp.route('/book/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def book_appointment(doctor_id):
    """Book an appointment with a doctor"""
    if current_user.role != 'patient': abort(403)
    
    doctor = DoctorService.get_doctor_by_id(doctor_id)
    if not doctor:
        flash('Doctor not found', 'danger')
        return redirect(url_for('patient.list_doctors'))
        
    if request.method == 'POST':
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        
        # Determine if JSON or Form
        if request.is_json:
            data = request.get_json()
        else:
            data = {
                'doctor_id': doctor_id,
                'patient_id': patient.id,
                'appointment_date': request.form.get('appointment_date'),
                'appointment_time': request.form.get('appointment_time'),
                'reason': request.form.get('reason', 'General Checkup')
            }
            
        try:
            appointment = PatientService.book_appointment(
                patient_id=patient.id,
                doctor_id=doctor_id,
                date_str=data['appointment_date'],
                time_str=data['appointment_time'],
                reason=data.get('reason', 'General Checkup')
            )
            if request.is_json:
                return jsonify({'message': 'Appointment booked', 'appointment': appointment.to_dict()}), 201
            
            flash('Appointment booked! Waiting for doctor approval.', 'success')
            return redirect(url_for('patient.my_appointments'))
        except Exception as e:
            if request.is_json: return jsonify({'error': str(e)}), 400
            flash(f'Booking failed: {str(e)}', 'danger')
            
    return render_template('patient/book_appointment.html', 
                           doctor=doctor, 
                           today=datetime.now().strftime('%Y-%m-%d'))

@patient_bp.route('/appointments', methods=['GET'])
@login_required
def my_appointments():
    """View patient's appointments"""
    if current_user.role != 'patient': abort(403)
    
    status = request.args.get('status')
    upcoming = request.args.get('upcoming', 'false').lower() == 'true'
    
    appointments = AppointmentService.get_appointments(
        user_id=current_user.id, 
        role='patient', 
        status=status,
        upcoming=upcoming
    )
    
    if request.path.startswith('/api') or request.is_json:
        return jsonify({'appointments': [a.to_dict() for a in appointments]}), 200
        
    return render_template('patient/patient_appointments.html', appointments=appointments)

@patient_bp.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    """Cancel a pending appointment"""
    if current_user.role != 'patient': abort(403)
    
    try:
        AppointmentService.update_appointment_status(
            appointment_id=appointment_id,
            status='cancelled',
            user_role='patient',
            cancellation_reason='Cancelled by patient'
        )
        flash('Appointment cancelled successfully', 'success')
    except Exception as e:
        flash(f'Cancellation failed: {str(e)}', 'danger')
        
    return redirect(url_for('patient.my_appointments'))

@patient_bp.route('/prescriptions', methods=['GET'])
@login_required
def my_prescriptions():
    """View patient medical history"""
    if current_user.role != 'patient': abort(403)
    
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    prescriptions = PrescriptionService.get_patient_prescriptions(patient.id)
    
    if request.path.startswith('/api') or request.is_json:
        return jsonify({'prescriptions': [p.to_dict() for p in prescriptions]}), 200
        
    return render_template('patient/patient_prescriptions.html', prescriptions=prescriptions)

@patient_bp.route('/doctor/<int:doctor_id>/rate', methods=['POST'])
@login_required
def rate_doctor(doctor_id):
    """Add rating for a doctor"""
    if current_user.role != 'patient': abort(403)
    
    data = request.get_json()
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    try:
        rating = DoctorService.add_rating(
            doctor_id=doctor_id,
            patient_id=patient.id,
            appointment_id=data['appointment_id'],
            rating_value=data['rating'],
            review=data.get('review')
        )
        return jsonify({'message': 'Rating added successfully', 'rating': rating.to_dict()}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400