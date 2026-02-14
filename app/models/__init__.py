from app.extensions import db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.prescription import Prescription

# This ensures all models are imported and registered with SQLAlchemy's metadata
__all__ = ['User', 'Doctor', 'Patient', 'Appointment', 'Prescription']
