from app import create_app
from app.extensions import db
import sys

app = create_app()

def init_db():
    print("Initializing database tables...")
    try:
        with app.app_context():
            # This will create all tables based on the models that were imported in create_app
            db.create_all()
            print("Successfully created all tables in PostgreSQL!")
    except Exception as e:
        print(f"Error creating tables: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    init_db()
