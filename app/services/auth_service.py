from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.extensions import db
from datetime import datetime
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

class AuthService:
    @staticmethod
    def register_user(data):
        """Register a new user and create specific profile with rollback support"""
        try:
            # Create base user
            user = User(
                username=data['username'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                role=data.get('role', 'patient')
            )
            user.set_password(data['password'])
            db.session.add(user)
            db.session.flush()  # Get user.id without committing
            
            # Create profile based on role
            if user.role == 'doctor':
                # Validate doctor-specific fields
                if not data.get('specialization') or not data.get('license_number'):
                    raise ValueError("Specialization and license number are required for doctors")
                
                doctor = Doctor(
                    user_id=user.id,
                    specialization=data['specialization'],
                    license_number=data['license_number']
                )
                db.session.add(doctor)
            elif user.role == 'patient':
                patient = Patient(user_id=user.id)
                db.session.add(patient)
                
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def login_user(email, password):
        """Validate user credentials"""
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            return user
        return None

    @staticmethod
    def check_email_exists(email):
        return User.query.filter_by(email=email).first() is not None

    @staticmethod
    def check_username_exists(username):
        return User.query.filter_by(username=username).first() is not None

    @staticmethod
    def get_user_profile(user_id):
        """Get user with role-specific details"""
        user = User.query.get(user_id)
        if not user:
            return None
            
        profile = user.to_dict()
        if user.role == 'doctor' and user.doctor_profile:
            profile['doctor_details'] = user.doctor_profile.to_dict()
        elif user.role == 'patient' and user.patient_profile:
            profile['patient_details'] = user.patient_profile.to_dict()
            
        return profile

    @staticmethod
    def generate_reset_token(email):
        """Generate a password reset token for a given email"""
        user = User.query.filter_by(email=email).first()
        if not user:
            return None
        
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(email, salt='password-reset-salt')

    @staticmethod
    def verify_reset_token(token, expires_sec=3600):
        """Verify the password reset token"""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(
                token,
                salt='password-reset-salt',
                max_age=expires_sec
            )
            return email
        except (SignatureExpired, BadTimeSignature):
            return None

    @staticmethod
    def reset_password(token, new_password):
        """Reset the user's password using the token"""
        email = AuthService.verify_reset_token(token)
        if not email:
            return False
            
        user = User.query.filter_by(email=email).first()
        if not user:
            return False
            
        user.set_password(new_password)
        db.session.commit()
        return True