from flask import Blueprint, jsonify, render_template, request, session
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.utils.decorators import role_required

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/dashboard')
@role_required(['patient'])
def dashboard():
    """Patient Dashboard"""
    user_id = session.get('user_id')
    patient = Patient.query.filter_by(user_id=user_id).first()
    
    if not patient:
        return jsonify({'error': 'Patient profile not found'}), 404
        
    upcoming_appointments = Appointment.query.filter_by(
        patient_id=patient.id
    ).filter(Appointment.status != 'cancelled').order_by(Appointment.appointment_date).all()
    
    stats = {
        'total_appointments': Appointment.query.filter_by(patient_id=patient.id).count(),
        'upcoming_appointments': len([a for a in upcoming_appointments if a.is_upcoming]),
        'completed_appointments': Appointment.query.filter_by(patient_id=patient.id, status='completed').count()
    }
    
    if request.path.startswith('/api'):
        return jsonify({
            'patient': patient.to_dict(),
            'statistics': stats,
            'upcoming_appointments': [a.to_dict() for a in upcoming_appointments]
        }), 200
        
    return render_template('patient_dashboard.html', patient=patient, stats=stats, appointments=upcoming_appointments)

@patient_bp.route('/doctors')
@role_required(['patient'])
def browse_doctors():
    doctors = Doctor.query.all()
    if request.path.startswith('/api'):
        return jsonify({'doctors': [d.to_dict() for d in doctors]}), 200
    return render_template('patient_doctors.html', doctors=doctors)