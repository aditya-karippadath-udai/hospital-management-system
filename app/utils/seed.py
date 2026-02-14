from app.extensions import db
from app.models.user import User
from sqlalchemy import or_

def seed_admin():
    """Seed default admin user if not exists using professional transaction handling"""
    try:
        # Check if an admin already exists by username OR email
        admin = User.query.filter(
            or_(User.email == 'admin@hms.com', User.username == 'admin')
        ).first()
        
        if not admin:
            # Create the default admin account
            admin = User(
                email='admin@hms.com',
                username='admin',
                first_name='System',
                last_name='Administrator',
                role='admin',
                is_active=True
            )
            # Ensure password is hashed properly using the model's method
            admin.set_password('1234')
            
            db.session.add(admin)
            db.session.commit()
            print("SUCCESS: Default admin user 'admin' created.")
        else:
            print("INFO: Default admin user already exists. Skipping insertion.")
            
    except Exception as e:
        # Clean up the session state on failure
        db.session.rollback()
        print(f"FAILURE: Error during admin seeding: {str(e)}")
