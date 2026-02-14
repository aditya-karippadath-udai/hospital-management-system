import sys
import os
from app import create_app
from app.extensions import db
from flask_migrate import migrate, upgrade

# Redirect output to a file
log_file = open("migration_log.txt", "w")
sys.stdout = log_file
sys.stderr = log_file

def fix_db():
    app = create_app()
    with app.app_context():
        print("Starting migration process...")
        try:
            # Generate migration
            print("Calling migrate()...")
            migrate(message="Add resource tables and make email nullable")
            print("Migration generated successfully.")
            
            # Apply migration
            print("Calling upgrade()...")
            upgrade()
            print("Database upgraded successfully.")
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    try:
        fix_db()
    finally:
        log_file.close()
