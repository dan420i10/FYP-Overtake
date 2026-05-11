"""
Migration script to hash plain text passwords in the database
Run this once to update existing passwords
"""
from app import create_app
from extensions import db
from models import User
import bcrypt

def hash_existing_passwords():
    """Hash all plain text passwords in the database"""
    app = create_app()
    
    with app.app_context():
        # Get all users
        users = User.query.all()
        
        for user in users:
            # Check if password is already hashed (bcrypt hashes start with $2)
            if not user.password.startswith('$2'):
                print(f"Hashing password for user: {user.email}")
                user.set_password(user.password)
                db.session.commit()
        
        print("All passwords have been hashed successfully!")

if __name__ == '__main__':
    hash_existing_passwords()
