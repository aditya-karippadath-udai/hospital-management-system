from app.extensions import db
from app.models.user import User
from sqlalchemy import or_
from app.models.resource import Bed, Medicine, Ambulance
from datetime import date, timedelta

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

def seed_resources():
    """Seed initial hospital resources"""
    try:
        # Seed Beds
        if Bed.query.count() == 0:
            wards = ['General', 'ICU', 'Emergency', 'Pediatric']
            for i, ward in enumerate(wards * 3):
                bed = Bed(bed_number=f'B-{100+i}', ward=ward, is_occupied=(i % 3 == 0))
                db.session.add(bed)
            print("SUCCESS: Default beds seeded.")

        # Seed Medicines
        if Medicine.query.count() == 0:
            meds = [
                ('Paracetamol', 150, 5.50, date.today() + timedelta(days=365)),
                ('Amoxicillin', 8, 12.00, date.today() + timedelta(days=180)),
                ('Ibuprofen', 45, 8.25, date.today() + timedelta(days=500)),
                ('Insulin', 5, 25.00, date.today() + timedelta(days=30))
            ]
            for name, qty, price, expiry in meds:
                med = Medicine(name=name, stock_quantity=qty, price=price, expiry_date=expiry)
                db.session.add(med)
            print("SUCCESS: Default medicines seeded.")

        # Seed Ambulances
        if Ambulance.query.count() == 0:
            ambs = [('AMB-001', 'John Doe'), ('AMB-002', 'Jane Smith'), ('AMB-003', 'Mike Ross')]
            for num, driver in ambs:
                amb = Ambulance(vehicle_number=num, driver_name=driver, is_available=True)
                db.session.add(amb)
            print("SUCCESS: Default ambulances seeded.")

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"FAILURE: Error during resource seeding: {str(e)}")
