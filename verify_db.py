from app import create_app
from app.extensions import db
from sqlalchemy import inspect

def check_tables():
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("Existing tables:")
        for table in tables:
            print(f"- {table}")
        
        required = ['beds', 'medicines', 'ambulances']
        missing = [t for t in required if t not in tables]
        
        if not missing:
            print("All required tables exist!")
            return True
        else:
            print(f"Missing tables: {missing}")
            return False

if __name__ == "__main__":
    check_tables()
