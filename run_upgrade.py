import sys
import os
from app import create_app
from flask_migrate import upgrade

# Redirect output to a file
log_file = open("upgrade_log.txt", "w")
sys.stdout = log_file
sys.stderr = log_file

def do_upgrade():
    app = create_app()
    with app.app_context():
        print("Starting upgrade process...")
        try:
            # Apply migration
            print("Calling upgrade()...")
            upgrade()
            print("Database upgraded successfully.")
        except Exception as e:
            print(f"Error during upgrade: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    try:
        do_upgrade()
    finally:
        log_file.close()
