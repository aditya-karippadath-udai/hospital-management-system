from app.extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON


class Doctor(db.Model):
    """Doctor model for medical professionals"""
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    # Professional Information
    specialization = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer, default=0)
    consultation_fee = db.Column(db.Numeric(10, 2), default=0.00)
    bio = db.Column(db.Text)
    education = db.Column(JSON)
    certifications = db.Column(JSON)
    
    # Availability
    available_days = db.Column(JSON, default=list)
    available_time_start = db.Column(db.Time)
    available_time_end = db.Column(db.Time)
    slot_duration = db.Column(db.Integer, default=30)
    is_available = db.Column(db.Boolean, default=True)
    
    # Contact Information
    clinic_address = db.Column(db.Text)
    clinic_phone = db.Column(db.String(20))
    clinic_email = db.Column(db.String(120))
    
    # Department
    department = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy='dynamic', cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', backref='doctor', lazy='dynamic', cascade='all, delete-orphan')
    leaves = db.relationship('DoctorLeave', backref='doctor', lazy='dynamic', cascade='all, delete-orphan')
    ratings = db.relationship('DoctorRating', backref='doctor', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def average_rating(self):
        """Calculate average rating"""
        ratings = [r.rating for r in self.ratings]
        return sum(ratings) / len(ratings) if ratings else 0
    
    @property
    def total_appointments(self):
        """Get total appointments count"""
        return self.appointments.count()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.user.full_name if self.user else None,
            'email': self.user.email if self.user else None,
            'specialization': self.specialization,
            'license_number': self.license_number,
            'qualification': self.qualification,
            'experience_years': self.experience_years,
            'consultation_fee': float(self.consultation_fee) if self.consultation_fee else 0,
            'bio': self.bio,
            'education': self.education,
            'certifications': self.certifications,
            'available_days': self.available_days,
            'available_time_start': str(self.available_time_start) if self.available_time_start else None,
            'available_time_end': str(self.available_time_end) if self.available_time_end else None,
            'slot_duration': self.slot_duration,
            'is_available': self.is_available,
            'clinic_address': self.clinic_address,
            'clinic_phone': self.clinic_phone,
            'clinic_email': self.clinic_email,
            'department': self.department,
            'average_rating': float(self.average_rating),
            'total_appointments': self.total_appointments,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Doctor {self.user.full_name if self.user else self.id} - {self.specialization}>'


class DoctorLeave(db.Model):
    """Model for doctor leaves"""
    __tablename__ = 'doctor_leaves'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(200))
    is_approved = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'reason': self.reason,
            'is_approved': self.is_approved
        }


class DoctorRating(db.Model):
    """Model for doctor ratings by patients"""
    __tablename__ = 'doctor_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', ondelete='SET NULL'), nullable=True)
    
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('appointment_id', name='unique_appointment_rating'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.user.full_name if self.patient and self.patient.user else None,
            'appointment_id': self.appointment_id,
            'rating': self.rating,
            'review': self.review,
            'created_at': self.created_at.isoformat()
        }