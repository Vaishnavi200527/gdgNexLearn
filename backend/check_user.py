from database import SessionLocal
from models import Users
from auth_utils import verify_password

def check_user():
    db = SessionLocal()
    try:
        # Check if the user exists
        user = db.query(Users).filter(Users.email == "anderson@university.edu").first()
        if user:
            print(f"User found: {user.name}, email: {user.email}, role: {user.role}")
            # Test password verification
            password_correct = verify_password("password123", user.password_hash)
            print(f"Password 'password123' matches: {password_correct}")
        else:
            print("User with email 'anderson@university.edu' not found")
        
        # Show all users in the database
        print("\nAll users in the database:")
        all_users = db.query(Users).all()
        for u in all_users:
            print(f"- Name: {u.name}, Email: {u.email}, Role: {u.role}")
    finally:
        db.close()

if __name__ == "__main__":
    check_user()