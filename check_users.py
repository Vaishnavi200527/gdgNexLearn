import sys
import os
sys.path.append('backend')

from backend.database import SessionLocal
from backend.models import Users

def check_users():
    db = SessionLocal()
    try:
        users = db.query(Users).all()
        print('Existing users:')
        if not users:
            print('No users found in database.')
        else:
            for user in users:
                print(f'ID: {user.id}, Name: {user.name}, Email: {user.email}, Role: {user.role}, Password: {user.password_hash}')
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
