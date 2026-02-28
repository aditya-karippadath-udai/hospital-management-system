from app.extensions import db
from app.models.appointment import Appointment
from app.models.doctor import Doctor, DoctorLeave
from app.models.patient import Patient
from datetime import datetime, time, timedelta, date
from sqlalchemy import and_

class AppointmentService:
    """Enhanced service for appointment management with strict validation and transaction safety"""
    
    @staticmethod
    def book_appointment(data):
        """Create a new appointment with strict validation and transaction safety"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            doctor_id = data['doctor_id']
            patient_id = data['patient_id']
            appointment_date = data['appointment_date']
            appointment_time = data['appointment_time']

            # Parse inputs
            if isinstance(appointment_date, str):
                appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            if isinstance(appointment_time, str):
                # Try multiple formats for flexibility
                for fmt in ('%H:%M:%S', '%H:%M'):
                    try:
                        appointment_time = datetime.strptime(appointment_time, fmt).time()
                        break
                    except ValueError: continue

            # 1. Prevent booking in the past
            now_dt = datetime.now()
            appointment_datetime = datetime.combine(appointment_date, appointment_time)
            
            if appointment_datetime < now_dt:
                logger.warning(f"Failed booking attempt for Patient {patient_id}: Past date {appointment_datetime}")
                raise ValueError("Appointments must be scheduled for a future date and time")

            # 2. Strict Availability Check
            available, message = AppointmentService.is_doctor_available(doctor_id, appointment_date, appointment_time)
            if not available:
                logger.warning(f"Failed booking attempt for Patient {patient_id}: {message}")
                raise ValueError(message)

            # 3. Concurrency Protection & Collision Check
            # Use row-level locking for the doctor to prevent race conditions during booking
            doctor_lock = Doctor.query.with_for_update().get(doctor_id)
            
            existing = Appointment.query.filter_by(
                doctor_id=doctor_id,
                appointment_date=appointment_date,
                appointment_time=appointment_time
            ).filter(Appointment.status.not_in(['cancelled', 'rejected'])).first()
            
            if existing:
                logger.warning(f"Failed booking attempt for Patient {patient_id}: Slot collision at {appointment_datetime}")
                raise ValueError("The selected time slot is already booked")

            # Calculate end time based on doctor's slot duration
            duration = data.get('duration', (doctor_lock.slot_duration if doctor_lock else 30) or 30)
            end_datetime = datetime.combine(appointment_date, appointment_time) + timedelta(minutes=duration)
            end_time = end_datetime.time()

            appointment = Appointment(
                doctor_id=doctor_id,
                patient_id=patient_id,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                end_time=end_time,
                duration=duration,
                reason=data['reason'],
                symptoms=data.get('symptoms', ''),
                appointment_type=data.get('appointment_type', 'regular'),
                consultation_fee=data.get('consultation_fee') or (doctor_lock.consultation_fee if doctor_lock else 0),
                status='pending'
            )
            
            db.session.add(appointment)
            db.session.commit()
            logger.info(f"Successful booking: Patient {patient_id} with Doctor {doctor_id} on {appointment_datetime}")
            return appointment
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Critical booking failure: {str(e)}")
            raise e

    @staticmethod
    def update_status(appointment_id, status, user_role, **kwargs):
        """Update appointment status with transition logic and transaction safety"""
        try:
            appointment = Appointment.query.get(appointment_id)
            if not appointment:
                raise ValueError("Appointment not found")
            
            # Role-based transition validation
            if status in ['confirmed', 'cancelled'] and user_role == 'doctor':
                # Doctor can confirm pending or cancel
                pass
            elif status == 'cancelled' and user_role == 'patient':
                if appointment.status != 'pending':
                    raise ValueError("Patients can only cancel pending appointments")
            elif status == 'completed' and user_role == 'doctor':
                pass
            
            appointment.status = status
            
            if status == 'confirmed':
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
    def get_patient_appointments(patient_id, status=None, upcoming=False):
        """Retrieve appointments for a specific patient"""
        query = Appointment.query.filter_by(patient_id=patient_id)
        if status:
            query = query.filter_by(status=status)
        if upcoming:
            query = query.filter(Appointment.appointment_date >= datetime.now().date())
        return query.order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()

    @staticmethod
    def get_doctor_appointments(doctor_id, status=None, upcoming=False):
        """Retrieve appointments for a specific doctor"""
        query = Appointment.query.filter_by(doctor_id=doctor_id)
        if status:
            query = query.filter_by(status=status)
        if upcoming:
            query = query.filter(Appointment.appointment_date >= datetime.now().date())
        return query.order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()

    @staticmethod
    def is_doctor_available(doctor_id, appointment_date, appointment_time):
        """
        Check if doctor is available at specific date and time with strict validation.
        Returns (bool, message)
        """
        doctor = Doctor.query.get(doctor_id)
        
        # 1. Validation: Basic Existence & Flag
        if not doctor:
            return False, "Doctor profile not found"
        if not doctor.is_available:
            return False, "Doctor is currently not accepting appointments"
            
        # 2. Validation: Schedule Configuration
        if not doctor.available_days or not doctor.available_time_start or not doctor.available_time_end:
            return False, "Doctor has not configured their consultation schedule"
        
        if (doctor.slot_duration or 0) <= 0:
            return False, "Doctor schedule configuration error (invalid slot duration)"

        # 3. Validation: Day of Week
        # Handle cases where available_days might be stored as a string instead of a list
        days = doctor.available_days
        if isinstance(days, str):
            import json
            try:
                days = json.loads(days)
            except:
                days = [days]
        
        day_name = appointment_date.strftime('%A')
        if day_name not in days:
            return False, f"Doctor is not available on {day_name}s"
        
        # 4. Validation: Working Hours
        if appointment_time < doctor.available_time_start or appointment_time >= doctor.available_time_end:
            return False, f"Time outside working hours ({doctor.available_time_start.strftime('%H:%M')} - {doctor.available_time_end.strftime('%H:%M')})"

        # 5. Validation: Doctor Leaves
        leave = DoctorLeave.query.filter(
            and_(
                DoctorLeave.doctor_id == doctor_id,
                DoctorLeave.start_date <= appointment_date,
                DoctorLeave.end_date >= appointment_date,
                DoctorLeave.is_approved == True
            )
        ).first()
        
        if leave:
            return False, f"Doctor is on leave from {leave.start_date} to {leave.end_date}"
        
        return True, "Available"