import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy.orm import Session
from database import SessionLocal
import models
import auth_utils

def debug_authentication():
    print("Debugging authentication process...")
    
    # Create database session
    db: Session = SessionLocal()
    
    try:
        # Get the user from the database
        email = "dishakulkarni2005@gmail.com"
        user = auth_utils.get_user(db, email=email)
        
        if user:
            print(f"User found: {user.name} ({user.email})")
            print(f"Role: {user.role}")
            print(f"Password hash in DB: {user.password_hash[:50]}...")
            
            # Try to verify the password
            password_to_test = "abcd1234"
            is_valid = auth_utils.verify_password(password_to_test, user.password_hash)
            print(f"Password '{password_to_test}' verification: {is_valid}")
            
            # Test with wrong password
            wrong_password = "password123"
            is_wrong = auth_utils.verify_password(wrong_password, user.password_hash)
            print(f"Password '{wrong_password}' verification: {is_wrong}")
            
            # Check role value
            print(f"Role type: {type(user.role)}")
            print(f"Role value: {user.role}")
            print(f"Role value (if enum): {user.role.value if hasattr(user.role, 'value') else user.role}")
        else:
            print("User not found in database")
            
    except Exception as e:
        print(f"Error during authentication debug: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_authentication()