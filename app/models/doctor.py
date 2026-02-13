from app import db
from datetime import datetime

class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer)
    consultation_fee = db.Column(db.Float)
    available_days = db.Column(db.String(200))  # JSON string: ["Monday", "Wednesday", "Friday"]
    available_time_start = db.Column(db.Time)
    available_time_end = db.Column(db.Time)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    prescriptions = db.relationship('Prescription', backref='doctor', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': f"{self.user.first_name} {self.user.last_name}",
            'email': self.user.email,
            'specialization': self.specialization,
            'license_number': self.license_number,
            'qualification': self.qualification,
            'experience_years': self.experience_years,
            'consultation_fee': self.consultation_fee,
            'available_days': self.available_days,
            'available_time_start': str(self.available_time_start) if self.available_time_start else None,
            'available_time_end': str(self.available_time_end) if self.available_time_end else None,
            'is_available': self.is_available
        }