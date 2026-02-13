from app import db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from datetime import datetime

class AuthService:
    @staticmethod
    def create_user(data):
        user = User(
            email=data['email'],
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create role-specific profile
        if data['role'] == 'doctor':
            doctor = Doctor(
                user_id=user.id,
                specialization=data.get('specialization', 'General'),
                license_number=data.get('license_number', ''),
                qualification=data.get('qualification', ''),
                experience_years=data.get('experience_years', 0),
                consultation_fee=data.get('consultation_fee', 0)
            )
            db.session.add(doctor)
        elif data['role'] == 'patient':
            patient = Patient(
                user_id=user.id,
                phone=data.get('phone', ''),
                address=data.get('address', '')
            )
            db.session.add(patient)
        
        db.session.commit()
        return user
    
    @staticmethod
    def validate_login(email, password):
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
            return user
        return None