from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON


class Prescription(db.Model):
    """Prescription model for medical prescriptions"""
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_number = db.Column(db.String(20), unique=True, nullable=False)
    
    # Foreign Keys
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', ondelete='SET NULL'), nullable=True)
    
    # Prescription Details
    diagnosis = db.Column(db.Text, nullable=False)
    symptoms = db.Column(db.Text)
    clinical_notes = db.Column(db.Text)
    
    # Medicines
    medicines = db.Column(JSON, nullable=False, default=list)
    
    # Tests
    tests = db.Column(JSON, default=list)
    
    # Vital Signs
    vital_signs = db.Column(JSON, default=dict)
    
    # Follow-up
    follow_up_date = db.Column(db.Date)
    follow_up_instructions = db.Column(db.Text)
    
    # Additional Information
    advice = db.Column(db.Text)
    dietary_restrictions = db.Column(JSON, default=list)
    lifestyle_changes = db.Column(JSON, default=list)
    
    # Digital Signature
    is_signed = db.Column(db.Boolean, default=False)
    signed_at = db.Column(db.DateTime)
    digital_signature = db.Column(db.Text)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_printed = db.Column(db.Boolean, default=False)
    printed_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prescription_items = db.relationship('PrescriptionItem', backref='prescription', lazy='dynamic', cascade='all, delete-orphan')
    
    def generate_prescription_number(self):
        """Generate unique prescription number"""
        import random
        import string
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"PRS{timestamp}{random_str}"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.prescription_number:
            self.prescription_number = self.generate_prescription_number()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'prescription_number': self.prescription_number,
            'doctor': {
                'id': self.doctor_id,
                'name': self.doctor.user.full_name if self.doctor and self.doctor.user else None,
                'specialization': self.doctor.specialization if self.doctor else None,
                'license_number': self.doctor.license_number if self.doctor else None
            } if self.doctor else None,
            'patient': {
                'id': self.patient_id,
                'name': self.patient.user.full_name if self.patient and self.patient.user else None,
                'age': self.patient.age if self.patient else None,
                'gender': self.patient.gender if self.patient else None,
                'blood_group': self.patient.blood_group if self.patient else None
            } if self.patient else None,
            'appointment_id': self.appointment_id,
            'appointment_number': self.appointment.appointment_number if self.appointment else None,
            'diagnosis': self.diagnosis,
            'symptoms': self.symptoms,
            'clinical_notes': self.clinical_notes,
            'medicines': self.medicines,
            'tests': self.tests,
            'vital_signs': self.vital_signs,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'follow_up_instructions': self.follow_up_instructions,
            'advice': self.advice,
            'dietary_restrictions': self.dietary_restrictions,
            'lifestyle_changes': self.lifestyle_changes,
            'is_signed': self.is_signed,
            'signed_at': self.signed_at.isoformat() if self.signed_at else None,
            'is_active': self.is_active,
            'is_printed': self.is_printed,
            'printed_at': self.printed_at.isoformat() if self.printed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Prescription {self.prescription_number}>'


class PrescriptionItem(db.Model):
    """Model for individual prescription items"""
    __tablename__ = 'prescription_items'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False)
    
    # Medicine Details
    medicine_name = db.Column(db.String(200), nullable=False)
    medicine_type = db.Column(db.String(50))
    dosage = db.Column(db.String(100))
    frequency = db.Column(db.String(100))
    duration = db.Column(db.String(50))
    duration_days = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    instructions = db.Column(db.Text)
    timing = db.Column(JSON, default=list)
    with_food = db.Column(db.Boolean, default=True)
    
    # Additional
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'prescription_id': self.prescription_id,
            'medicine_name': self.medicine_name,
            'medicine_type': self.medicine_type,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'duration': self.duration,
            'duration_days': self.duration_days,
            'quantity': self.quantity,
            'instructions': self.instructions,
            'timing': self.timing,
            'with_food': self.with_food
        }