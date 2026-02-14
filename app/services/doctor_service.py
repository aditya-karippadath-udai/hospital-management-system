from app.extensions import db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from datetime import datetime

class DoctorService:
    @staticmethod
    def get_dashboard_stats(doctor_id):
        """Aggregate stats for doctor dashboard"""
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            return None
            
        return {
            'total_appointments': doctor.appointments.count(),
            'pending_requests': doctor.appointments.filter_by(status='pending').count(),
            'upcoming_today': doctor.appointments.filter(
                Appointment.appointment_date == datetime.now().date(),
                Appointment.status == 'approved'
            ).count(),
            'completed_total': doctor.appointments.filter_by(status='completed').count()
        }

    # Appointment updates are now handled by AppointmentService.update_status

    @staticmethod
    def get_patient_history(patient_id):
        """Get all past appointments and prescriptions for a patient"""
        return Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.appointment_date.desc()).all()

    @staticmethod
    def get_doctor_by_id(doctor_id):
        """Get doctor details by ID"""
        return Doctor.query.get(doctor_id)

    @staticmethod
    def update_availability(doctor_id, data):
        """Update doctor's availability and consulting hours with safety"""
        try:
            doctor = Doctor.query.get(doctor_id)
            if not doctor:
                raise ValueError("Doctor not found")
                
            if 'available_days' in data:
                doctor.available_days = data['available_days']
            if 'available_time_start' in data:
                doctor.available_time_start = datetime.strptime(data['available_time_start'], '%H:%M').time()
            if 'available_time_end' in data:
                doctor.available_time_end = datetime.strptime(data['available_time_end'], '%H:%M').time()
            if 'consultation_fee' in data:
                doctor.consultation_fee = data['consultation_fee']
            if 'is_available' in data:
                doctor.is_available = data['is_available']
                
            db.session.commit()
            return doctor
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def add_rating(doctor_id, patient_id, appointment_id, rating_value, review=None):
        """Add a review and rating for a doctor with safety"""
        try:
            from app.models.doctor import DoctorRating
            
            # Check if already rated
            existing = DoctorRating.query.filter_by(appointment_id=appointment_id).first()
            if existing:
                raise ValueError("Appointment already rated")
                
            rating = DoctorRating(
                doctor_id=doctor_id,
                patient_id=patient_id,
                appointment_id=appointment_id,
                rating=rating_value,
                review=review
            )
            db.session.add(rating)
            db.session.commit()
            return rating
        except Exception as e:
            db.session.rollback()
            raise e
