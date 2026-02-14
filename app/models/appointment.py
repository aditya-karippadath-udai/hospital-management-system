from app.extensions import db
from datetime import datetime
from sqlalchemy import Index


class Appointment(db.Model):
    """Appointment model for patient-doctor appointments"""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # Foreign Keys
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    
    # Appointment Details
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time)
    duration = db.Column(db.Integer, default=30)
    
    # Status (Pending / Confirmed / Cancelled)
    status = db.Column(db.String(20), default='pending', index=True)
    cancellation_reason = db.Column(db.String(200))
    rescheduled_from = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    
    # Consultation Details
    reason = db.Column(db.Text, nullable=False)
    symptoms = db.Column(db.Text)
    notes = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    
    # Type
    appointment_type = db.Column(db.String(20), default='regular')
    
    # Payment
    consultation_fee = db.Column(db.Numeric(10, 2))
    payment_status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(50))
    
    # Reminders
    reminder_sent = db.Column(db.Boolean, default=False)
    reminder_sent_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # Relationships
    prescription = db.relationship('Prescription', backref='appointment', uselist=False, cascade='all, delete-orphan')
    rating = db.relationship('DoctorRating', backref='appointment', uselist=False, cascade='all, delete-orphan')
    rescheduled_to = db.relationship('Appointment', backref=db.backref('original_appointment', remote_side=[id]))
    
    # Indexes
    __table_args__ = (
        Index('idx_appointment_doctor_date', 'doctor_id', 'appointment_date'),
        Index('idx_appointment_patient_date', 'patient_id', 'appointment_date'),
        Index('idx_appointment_date_status', 'appointment_date', 'status'),
        Index('idx_appointment_collision', 'doctor_id', 'appointment_date', 'appointment_time', unique=True),
    )
    
    def generate_appointment_number(self):
        """Generate unique appointment number"""
        import random
        import string
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"APT-{timestamp}-{random_str}"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.appointment_number:
            self.appointment_number = self.generate_appointment_number()
    
    @property
    def is_upcoming(self):
        """Check if appointment is upcoming"""
        today = datetime.now().date()
        now = datetime.now().time()
        return (self.appointment_date > today) or (
            self.appointment_date == today and self.appointment_time > now
        )
    
    @property
    def can_be_cancelled(self):
        """Check if appointment can be cancelled"""
        if self.status not in ['scheduled', 'confirmed']:
            return False
        
        if self.is_upcoming:
            appointment_datetime = datetime.combine(self.appointment_date, self.appointment_time)
            time_diff = (appointment_datetime - datetime.now()).total_seconds() / 3600
            return time_diff > 2
        
        return False
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'appointment_number': self.appointment_number,
            'doctor': {
                'id': self.doctor_id,
                'name': self.doctor.user.full_name if self.doctor and self.doctor.user else None,
                'specialization': self.doctor.specialization if self.doctor else None
            } if self.doctor else None,
            'patient': {
                'id': self.patient_id,
                'name': self.patient.user.full_name if self.patient and self.patient.user else None,
                'phone': self.patient.phone if self.patient else None
            } if self.patient else None,
            'appointment_date': self.appointment_date.isoformat(),
            'appointment_time': str(self.appointment_time),
            'end_time': str(self.end_time) if self.end_time else None,
            'duration': self.duration,
            'status': self.status,
            'cancellation_reason': self.cancellation_reason,
            'rescheduled_from': self.rescheduled_from,
            'reason': self.reason,
            'symptoms': self.symptoms,
            'notes': self.notes,
            'diagnosis': self.diagnosis,
            'appointment_type': self.appointment_type,
            'consultation_fee': float(self.consultation_fee) if self.consultation_fee else None,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'is_upcoming': self.is_upcoming,
            'can_be_cancelled': self.can_be_cancelled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None
        }
    
    def __repr__(self):
        return f'<Appointment {self.appointment_number} - {self.status}>'