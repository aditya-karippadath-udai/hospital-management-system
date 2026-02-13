from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    # Personal Information
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    blood_group = db.Column(db.String(5))
    
    # Contact Information
    phone = db.Column(db.String(20))
    alternative_phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    
    # Emergency Contact
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relation = db.Column(db.String(50))
    
    # Medical Information
    blood_group = db.Column(db.String(5))
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    allergies = db.Column(JSON, default=list)  # Store allergies as JSON array
    chronic_diseases = db.Column(JSON, default=list)  # Store chronic diseases as JSON array
    current_medications = db.Column(JSON, default=list)  # Store current medications as JSON array
    medical_history = db.Column(JSON, default=dict)  # Store medical history as JSON
    family_history = db.Column(JSON, default=dict)  # Store family history as JSON
    
    # Insurance Information
    insurance_provider = db.Column(db.String(100))
    insurance_policy_number = db.Column(db.String(50))
    insurance_expiry_date = db.Column(db.Date)
    
    # Preferences
    preferred_language = db.Column(db.String(50), default='English')
    communication_preference = db.Column(db.String(20), default='email')  # email, sms, phone
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    bills = db.relationship('Bill', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        if self.date_of_birth:
            today = datetime.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    def bmi(self):
        """Calculate BMI"""
        if self.height and self.weight:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 2)
        return None
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.user.full_name if self.user else None,
            'email': self.user.email if self.user else None,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'age': self.age,
            'gender': self.gender,
            'blood_group': self.blood_group,
            'phone': self.phone,
            'alternative_phone': self.alternative_phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code,
            'emergency_contact': {
                'name': self.emergency_contact_name,
                'phone': self.emergency_contact_phone,
                'relation': self.emergency_contact_relation
            },
            'medical_info': {
                'height': self.height,
                'weight': self.weight,
                'bmi': self.bmi,
                'allergies': self.allergies,
                'chronic_diseases': self.chronic_diseases,
                'current_medications': self.current_medications
            },
            'insurance': {
                'provider': self.insurance_provider,
                'policy_number': self.insurance_policy_number,
                'expiry_date': self.insurance_expiry_date.isoformat() if self.insurance_expiry_date else None
            },
            'preferences': {
                'language': self.preferred_language,
                'communication': self.communication_preference
            },
            'total_appointments': self.appointments.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Patient {self.user.full_name if self.user else self.id}>'