from app.extensions import db
from app.models.appointment import Appointment
from app.models.doctor import Doctor, DoctorLeave
from app.models.patient import Patient
from datetime import datetime, time, timedelta, date
from sqlalchemy import and_

class AppointmentService:
    """Enhanced service for appointment management with strict validation"""
    
    @staticmethod
    def create_appointment(data):
        """Create a new appointment with validation"""
        try:
            doctor_id = data['doctor_id']
            patient_id = data['patient_id']
            appointment_date = data['appointment_date']
            appointment_time = data['appointment_time']

            # 1. Prevent booking in the past
            # Convert string to date/time if necessary
            if isinstance(appointment_date, str):
                appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            if isinstance(appointment_time, str):
                appointment_time = datetime.strptime(appointment_time, '%H:%M').time()

            appointment_datetime = datetime.combine(appointment_date, appointment_time)
            if appointment_datetime < datetime.now():
                raise ValueError("Cannot book appointments in the past")

            # 2. Check Doctor Availability
            if not AppointmentService.is_doctor_available(doctor_id, appointment_date, appointment_time):
                raise ValueError("Doctor is not available at the selected time")

            # 3. Prevent Double Booking (Strict check for 'scheduled' or 'confirmed' status)
            existing = Appointment.query.filter_by(
                doctor_id=doctor_id,
                appointment_date=appointment_date,
                appointment_time=appointment_time
            ).filter(Appointment.status.in_(['scheduled', 'confirmed'])).first()
            
            if existing:
                raise ValueError("This time slot is already booked")

            appointment = Appointment(
                doctor_id=doctor_id,
                patient_id=patient_id,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                duration=data.get('duration', 30),
                reason=data['reason'],
                symptoms=data.get('symptoms', ''),
                appointment_type=data.get('appointment_type', 'regular'),
                consultation_fee=data.get('consultation_fee'),
                status='pending'  # Initial status for fresher-level flow
            )
            
            db.session.add(appointment)
            db.session.commit()
            return appointment
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def update_appointment_status(appointment_id, status, user_role, **kwargs):
        """Update appointment status with transition logic"""
        try:
            appointment = Appointment.query.get(appointment_id)
            if not appointment:
                raise ValueError("Appointment not found")
            
            # Role-based transition validation
            if status in ['approved', 'rejected'] and user_role != 'doctor':
                raise ValueError("Only doctors can approve or reject appointments")
            
            if status == 'cancelled' and user_role == 'patient' and appointment.status != 'pending':
                raise ValueError("Patients can only cancel pending appointments")

            appointment.status = status
            
            if status == 'approved':
                appointment.confirmed_at = datetime.utcnow()
            elif status == 'completed':
                appointment.completed_at = datetime.utcnow()
                if 'diagnosis' in kwargs:
                    appointment.diagnosis = kwargs['diagnosis']
            elif status == 'cancelled':
                appointment.cancelled_at = datetime.utcnow()
                if 'cancellation_reason' in kwargs:
                    appointment.cancellation_reason = kwargs['cancellation_reason']
            
            db.session.commit()
            return appointment
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def is_doctor_available(doctor_id, appointment_date, appointment_time):
        """Check if doctor is available at specific date and time"""
        doctor = Doctor.query.get(doctor_id)
        if not doctor or not doctor.is_available:
            return False
        
        # Check if doctor has leave
        leave = DoctorLeave.query.filter(
            and_(
                DoctorLeave.doctor_id == doctor_id,
                DoctorLeave.start_date <= appointment_date,
                DoctorLeave.end_date >= appointment_date,
                DoctorLeave.is_approved == True
            )
        ).first()
        
        if leave:
            return False
        
        # Check if day is in available days
        if doctor.available_days:
            day_name = appointment_date.strftime('%A')
            if day_name not in doctor.available_days:
                return False
        
        # Check working hours
        if doctor.available_time_start and doctor.available_time_end:
            if appointment_time < doctor.available_time_start or appointment_time >= doctor.available_time_end:
                return False
        
        return True

    @staticmethod
    def get_appointments(user_id, role, status=None, upcoming=False):
        """Filterable appointment Retrieval"""
        if role == 'doctor':
            doctor = Doctor.query.filter_by(user_id=user_id).first()
            query = Appointment.query.filter_by(doctor_id=doctor.id)
        else:
            patient = Patient.query.filter_by(user_id=user_id).first()
            query = Appointment.query.filter_by(patient_id=patient.id)
            
        if status:
            query = query.filter_by(status=status)
            
        if upcoming:
            today = datetime.now().date()
            query = query.filter(Appointment.appointment_date >= today)
            
        return query.order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()