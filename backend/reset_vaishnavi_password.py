import sqlite3
import sys
import os

# Add current directory to path to import auth_utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from auth_utils import get_password_hash
except ImportError:
    # Fallback if running directly and import fails
    import bcrypt
    def get_password_hash(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def reset_password():
    db_path = 'amep.db'
    email = "2005vaishnavikumbhar@gmail.com"
    password = "Kumbhar123"
    
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id, name, role FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    hashed_pw = get_password_hash(password)
    
    if user:
        print(f"Found user: {user}")
        cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (hashed_pw, email))
        print(f"Updated password for {email} to '{password}'")
    else:
        print(f"User {email} not found. Creating new student user...")
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Vaishnavi", email, hashed_pw, "student")
        )
        print(f"Created user {email} with password '{password}' and role 'student'")
        
    conn.commit()
    conn.close()
    print("Database updated successfully.")

if __name__ == "__main__":
    reset_password()