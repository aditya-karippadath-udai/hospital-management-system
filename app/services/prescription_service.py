from app.extensions import db
from app.models.prescription import Prescription, PrescriptionItem
from app.models.appointment import Appointment
from datetime import datetime

class PrescriptionService:
    @staticmethod
    def create_prescription(data):
        """Create a prescription and mark appointment as completed"""
        try:
            # Validate appointment
            appointment = Appointment.query.get(data['appointment_id'])
            if not appointment:
                raise ValueError("Appointment not found")
            
            if appointment.status == 'completed':
                raise ValueError("Prescription already exists for this appointment")

            prescription = Prescription(
                doctor_id=appointment.doctor_id,
                patient_id=appointment.patient_id,
                appointment_id=appointment.id,
                diagnosis=data['diagnosis'],
                symptoms=data.get('symptoms'),
                clinical_notes=data.get('clinical_notes'),
                medicines=data.get('medicines', []),
                tests=data.get('tests', []),
                advice=data.get('advice')
            )
            
            db.session.add(prescription)
            
            # Update appointment status
            appointment.status = 'completed'
            appointment.completed_at = datetime.utcnow()
            appointment.diagnosis = data['diagnosis']
            
            db.session.commit()
            return prescription
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def get_patient_prescriptions(patient_id):
        """Get all prescriptions for a patient"""
        return Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.created_at.desc()).all()

    @staticmethod
    def get_prescription_by_id(prescription_id):
        """Get single prescription details"""
        return Prescription.query.get(prescription_id)
