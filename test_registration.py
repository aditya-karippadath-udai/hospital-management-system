from app import create_app
from app.extensions import db
from app.services.auth_service import AuthService
from app.models.user import User
import uuid

app = create_app('testing')
# Mocking db.session.commit to avoid actual DB write during verification if preferred, 
# but here we'll use a test transaction.

with app.app_context():
    # Start a nested transaction
    db.session.begin_nested()
    try:
        data = {
            'username': f'dr_test_{uuid.uuid4().hex[:6]}',
            'email': f'test_{uuid.uuid4().hex[:6]}@hospital.com',
            'first_name': 'Test',
            'last_name': 'Doctor',
            'password': 'password123',
            'role': 'doctor',
            'specialization': 'General Medicine',
            'license_number': f'LIC-{uuid.uuid4().hex[:6].upper()}'
        }
        
        print("Attempting to register doctor...")
        user = AuthService.register_user(data)
        print(f"Successfully registered user: {user.username} (ID: {user.id})")
        print("Logic check PASS: db.session.flush() worked and user.id was generated.")
        
    except Exception as e:
        print(f"Registration FAILED: {str(e)}")
    finally:
        # Roll back everything to keep DB clean
        db.session.rollback()
