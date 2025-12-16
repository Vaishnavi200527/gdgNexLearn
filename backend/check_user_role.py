from database import SessionLocal
import models

def check_user_role(email: str):
    db = SessionLocal()
    try:
        user = db.query(models.Users).filter(models.Users.email == email).first()
        if user:
            # Print user details
            print(f"User ID: {user.id}")
            print(f"User Name: {user.name}")
            print(f"User Email: {user.email}")
            print(f"User Role: {user.role}")
            print(f"User Role Type: {type(user.role)}")
            
            # Check if role is an enum or string
            if hasattr(user.role, 'value'):
                print(f"User Role Value: {user.role.value}")
            else:
                print(f"User Role (string): {user.role}")
        else:
            print(f"User with email '{email}' not found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_user_role("teacher@example.com")