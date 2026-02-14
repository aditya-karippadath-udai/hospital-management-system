from app import db
from app.models.appointment import Appointment
from app.models.doctor import Doctor, DoctorLeave
from app.models.patient import Patient
from datetime import datetime, time, timedelta, date
from sqlalchemy import and_


class AppointmentService:
    """Service for appointment management"""
    
    @staticmethod
    def create_appointment(data):
        """Create a new appointment"""
        appointment = Appointment(
            doctor_id=data['doctor_id'],
            patient_id=data['patient_id'],
            appointment_date=data['appointment_date'],
            appointment_time=data['appointment_time'],
            duration=data.get('duration', 30),
            reason=data['reason'],
            symptoms=data.get('symptoms', ''),
            appointment_type=data.get('appointment_type', 'regular'),
            consultation_fee=data.get('consultation_fee')
        )
        
        db.session.add(appointment)
        db.session.commit()
        return appointment
    
    @staticmethod
    def update_appointment_status(appointment_id, status, **kwargs):
        """Update appointment status"""
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return None
        
        appointment.status = status
        
        if status == 'confirmed':
            appointment.confirmed_at = datetime.utcnow()
        elif status == 'completed':
            appointment.completed_at = datetime.utcnow()
            if 'diagnosis' in kwargs:
                appointment.diagnosis = kwargs['diagnosis']
            if 'notes' in kwargs:
                appointment.notes = kwargs['notes']
        elif status == 'cancelled':
            appointment.cancelled_at = datetime.utcnow()
            if 'cancellation_reason' in kwargs:
                appointment.cancellation_reason = kwargs['cancellation_reason']
        
        db.session.commit()
        return appointment
    
    @staticmethod
    def cancel_appointment(appointment_id, reason):
        """Cancel an appointment"""
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return None
        
        if not appointment.can_be_cancelled:
            return None
        
        appointment.status = 'cancelled'
        appointment.cancellation_reason = reason
        appointment.cancelled_at = datetime.utcnow()
        
        db.session.commit()
        return appointment
    
    @staticmethod
    def get_appointments_by_doctor(doctor_id, status=None, start_date=None, end_date=None):
        """Get appointments for a specific doctor"""
        query = Appointment.query.filter_by(doctor_id=doctor_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if start_date:
            query = query.filter(Appointment.appointment_date >= start_date)
        
        if end_date:
            query = query.filter(Appointment.appointment_date <= end_date)
        
        return query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    
    @staticmethod
    def get_appointments_by_patient(patient_id, status=None):
        """Get appointments for a specific patient"""
        query = Appointment.query.filter_by(patient_id=patient_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    
    @staticmethod
    def get_appointment_by_id(appointment_id):
        """Get single appointment"""
        return Appointment.query.get(appointment_id)
    
    @staticmethod
    def is_doctor_available(doctor_id, appointment_date, appointment_time):
        """Check if doctor is available at specific date and time"""
        # Check if doctor exists
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
        
        # Check if time is within working hours
        if doctor.available_time_start and doctor.available_time_end:
            if appointment_time < doctor.available_time_start or appointment_time >= doctor.available_time_end:
                return False
        
        # Check existing appointments
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status='scheduled'
        ).first()
        
        return existing is None
    
    @staticmethod
    def get_available_slots(doctor_id, appointment_date):
        """Get available time slots for a doctor on a specific date"""
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            return []
        
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
            return []
        
        # Check if day is available
        if doctor.available_days:
            day_name = appointment_date.strftime('%A')
            if day_name not in doctor.available_days:
                return []
        
        # Get working hours
        start_time = doctor.available_time_start or time(9, 0)
        end_time = doctor.available_time_end or time(17, 0)
        slot_duration = doctor.slot_duration or 30
        
        # Get booked appointments
        booked_appointments = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            status='scheduled'
        ).all()
        
        booked_times = [app.appointment_time.strftime('%H:%M') for app in booked_appointments]
        
        # Generate available slots
        slots = []
        current_time = datetime.combine(appointment_date, start_time)
        end_datetime = datetime.combine(appointment_date, end_time)
        
        while current_time < end_datetime:
            time_str = current_time.strftime('%H:%M')
            if time_str not in booked_times:
                slots.append(time_str)
            current_time += timedelta(minutes=slot_duration)
        
        return slots
    
    @staticmethod
    def can_access_appointment(user, appointment):
        """Check if user can access appointment"""
        if user.role == 'admin':
            return True
        elif user.role == 'doctor' and appointment.doctor:
            return appointment.doctor.user_id == user.id
        elif user.role == 'patient' and appointment.patient:
            return appointment.patient.user_id == user.id
        
        return False
    
    @staticmethod
    def can_modify_appointment(user, appointment):
        """Check if user can modify appointment"""
        if user.role == 'admin':
            return True
        elif user.role == 'patient' and appointment.patient:
            return appointment.patient.user_id == user.id
        
        return False