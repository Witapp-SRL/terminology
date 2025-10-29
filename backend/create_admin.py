#!/usr/bin/env python3
"""
Script to create an initial admin user
"""
import sys
from database import SessionLocal, UserModel
from auth import get_password_hash
import uuid
from datetime import datetime, timezone

def create_admin_user(username="admin", email="admin@example.com", password="admin123", full_name="Administrator"):
    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(UserModel).filter(UserModel.username == username).first()
        if existing:
            print(f"User '{username}' already exists!")
            return False
        
        # Create admin user
        admin = UserModel(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            is_active=True,
            is_admin=True,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(admin)
        db.commit()
        
        print(f"✓ Admin user created successfully!")
        print(f"  Username: {username}")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"\n⚠️  Please change the password after first login!")
        
        return True
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        username = sys.argv[1]
        email = sys.argv[2] if len(sys.argv) > 2 else f"{username}@example.com"
        password = sys.argv[3] if len(sys.argv) > 3 else "admin123"
        full_name = sys.argv[4] if len(sys.argv) > 4 else "Administrator"
        create_admin_user(username, email, password, full_name)
    else:
        create_admin_user()
