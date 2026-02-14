from flask import Blueprint, jsonify, render_template, request, session
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.utils.decorators import role_required
from datetime import datetime

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/dashboard')
@role_required(['doctor'])
def dashboard():
    """Doctor Dashboard"""
    user_id = session.get('user_id')
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404
        
    today = datetime.now().date()
    today_appointments = Appointment.query.filter_by(
        doctor_id=doctor.id, 
        appointment_date=today
    ).order_by(Appointment.appointment_time).all()
    
    stats = {
        'total_appointments': Appointment.query.filter_by(doctor_id=doctor.id).count(),
        'today_appointments': len(today_appointments),
        'upcoming_appointments': Appointment.query.filter_by(doctor_id=doctor.id).filter(Appointment.appointment_date > today).count(),
        'completed_appointments': Appointment.query.filter_by(doctor_id=doctor.id, status='completed').count()
    }
    
    if request.path.startswith('/api'):
        return jsonify({
            'doctor': doctor.to_dict(),
            'statistics': stats,
            'today_appointments': [a.to_dict() for a in today_appointments]
        }), 200
        
    return render_template('doctor_dashboard.html', doctor=doctor, stats=stats, appointments=today_appointments)

@doctor_bp.route('/appointments')
@role_required(['doctor'])
def my_appointments():
    user_id = session.get('user_id')
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    return jsonify({'appointments': [a.to_dict() for a in appointments]}), 200