from app.extensions import db
from app.models.doctor import Doctor, DoctorRating
from app.models.patient import Patient
from app.models.appointment import Appointment
from datetime import datetime

class PatientService:
    @staticmethod
    def get_dashboard_stats(patient_id):
        """Aggregate stats for patient dashboard"""
        patient = Patient.query.get(patient_id)
        if not patient:
            return None
            
        return {
            'total_appointments': patient.appointments.count(),
            'upcoming_appointments': patient.appointments.filter(
                Appointment.appointment_date >= datetime.now().date(),
                Appointment.status.in_(['pending', 'approved'])
            ).count(),
            'completed_appointments': patient.appointments.filter_by(status='completed').count()
        }

    @staticmethod
    def list_doctors(specialization=None):
        """List doctors with optional filtering (only active ones)"""
        from app.models.user import User
        query = Doctor.query.join(User).filter(User.is_active == True)
        if specialization:
            query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
        return query.all()

    @staticmethod
    def book_appointment(patient_id, doctor_id, date_str, time_str, reason):
        """Create a new appointment request"""
        try:
            # Convert strings to date/time objects
            appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            appt_time = datetime.strptime(time_str, '%H:%M').time()
            
            appointment = Appointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                appointment_date=appt_date,
                appointment_time=appt_time,
                reason=reason,
                status='pending'
            )
            db.session.add(appointment)
            db.session.commit()
            return appointment
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def rate_doctor(patient_id, doctor_id, appointment_id, rating, review=None):
        """Add a rating for a doctor"""
        try:
            # Check if rating already exists for this appointment
            existing = DoctorRating.query.filter_by(appointment_id=appointment_id).first()
            if existing:
                existing.rating = rating
                existing.review = review
            else:
                new_rating = DoctorRating(
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    appointment_id=appointment_id,
                    rating=rating,
                    review=review
                )
                db.session.add(new_rating)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
