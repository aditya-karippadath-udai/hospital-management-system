from app import create_app
from app.extensions import db
from sqlalchemy import inspect

def verify_column():
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        columns = inspector.get_columns('appointments')
        for column in columns:
            if column['name'] == 'appointment_number':
                print(f"Column: {column['name']}")
                print(f"Type: {column['type']}")
                if hasattr(column['type'], 'length'):
                    print(f"Length: {column['type'].length}")
                return column['type'].length == 50
        return False

if __name__ == "__main__":
    verify_column()
