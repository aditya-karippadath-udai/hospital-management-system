from app import db
from datetime import datetime

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    diagnosis = db.Column(db.Text, nullable=False)
    medicines = db.Column(db.Text, nullable=False)  # JSON string: [{"name": "Medicine", "dosage": "1x/day", "duration": "7 days"}]
    tests = db.Column(db.Text)  # JSON string: [{"name": "Blood Test", "instructions": "Fasting"}]
    notes = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'doctor_name': f"{self.doctor.user.first_name} {self.doctor.user.last_name}",
            'patient_id': self.patient_id,
            'patient_name': f"{self.patient.user.first_name} {self.patient.user.last_name}",
            'appointment_id': self.appointment_id,
            'diagnosis': self.diagnosis,
            'medicines': self.medicines,
            'tests': self.tests,
            'notes': self.notes,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'created_at': self.created_at.isoformat()
        }