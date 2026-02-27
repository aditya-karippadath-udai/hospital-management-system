from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        # Check current column length
        result = db.session.execute(text("SELECT character_maximum_length FROM information_schema.columns WHERE table_name = 'prescriptions' AND column_name = 'prescription_number'"))
        row = result.fetchone()
        if row:
            print(f"Current prescription_number length in DB: {row[0]}")
        else:
            print("Could not find column in DB")
            
        # Try to alter table directly if not updated
        if row and row[0] < 50:
            print("Attempting to alter table directly...")
            db.session.execute(text("ALTER TABLE prescriptions ALTER COLUMN prescription_number TYPE VARCHAR(50)"))
            db.session.commit()
            print("Successfully altered table directly.")
            
            # Verify again
            result = db.session.execute(text("SELECT character_maximum_length FROM information_schema.columns WHERE table_name = 'prescriptions' AND column_name = 'prescription_number'"))
            print(f"New prescription_number length in DB: {result.fetchone()[0]}")
        
    except Exception as e:
        print(f"Error checking/altering DB: {str(e)}")
