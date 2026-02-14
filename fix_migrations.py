import sys
import os
from app import create_app
from app.extensions import db
from flask_migrate import migrate, upgrade

def fix_db():
    app = create_app()
    with app.app_context():
        print("Starting migration process...")
        try:
            # Generate migration
            migrate(message="Add resource tables and make email nullable")
            print("Migration generated successfully.")
            
            # Apply migration
            upgrade()
            print("Database upgraded successfully.")
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            # If we get a drift error, we might need more complex handling
            # but let's try the standard path first.

if __name__ == "__main__":
    fix_db()
