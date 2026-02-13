from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.user import User
from datetime import datetime, time, timedelta
import json

class AppointmentService:
    @staticmethod
    def is_doctor_available(doctor_id, appointment_date, appointment_time):
        # Check if doctor has any appointment at this time
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status='scheduled'
        ).first()
        
        return existing is None
    
    @staticmethod
    def get_available_slots(doctor_id, date):
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            return []
        
        # Get doctor's working hours
        start_time = doctor.available_time_start or time(9, 0)  # Default 9 AM
        end_time = doctor.available_time_end or time(17, 0)    # Default 5 PM
        
        # Get all booked appointments for this date
        booked_appointments = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=date,
            status='scheduled'
        ).all()
        
        booked_times = [app.appointment_time.strftime('%H:%M') for app in booked_appointments]
        
        # Generate all possible slots (30-minute intervals)
        slots = []
        current_time = datetime.combine(date, start_time)
        end_datetime = datetime.combine(date, end_time)
        
        while current_time < end_datetime:
            time_str = current_time.strftime('%H:%M')
            if time_str not in booked_times:
                slots.append(time_str)
            current_time += timedelta(minutes=30)
        
        return slots
    
    @staticmethod
    def can_access_appointment(user_id, appointment):
        user = User.query.get(user_id)
        
        if user.role == 'admin':
            return True
        elif user.role == 'doctor':
            return appointment.doctor.user_id == user_id
        elif user.role == 'patient':
            return appointment.patient.user_id == user_id
        
        return False
    
    @staticmethod
    def can_modify_appointment(user_id, appointment):
        user = User.query.get(user_id)
        
        # Only patients and admins can modify/cancel appointments
        if user.role == 'admin':
            return True
        elif user.role == 'patient':
            return appointment.patient.user_id == user_id
        
        return False