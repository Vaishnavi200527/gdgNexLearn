import sqlite3
import bcrypt

def create_user():
    # Connect to the database
    conn = sqlite3.connect('amep.db')
    cursor = conn.cursor()
    
    # Hash the password using bcrypt (to match auth_utils.py)
    password = "abcd1234"
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Insert the new user
    try:
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role) 
            VALUES (?, ?, ?, ?)
        """, ("Disha Kulkarni", "dishakulkarni2005@gmail.com", password_hash, "TEACHER"))
        
        conn.commit()
        print("User dishakulkarni2005@gmail.com created successfully!")
        
        # Verify the user was added
        cursor.execute("SELECT id, name, email, role FROM users WHERE email = 'dishakulkarni2005@gmail.com'")
        result = cursor.fetchone()
        print(f"Created user: ID {result[0]}, Name {result[1]}, Email {result[2]}, Role {result[3]}")
        
    except sqlite3.IntegrityError:
        print("User already exists in the database!")
    
    conn.close()

if __name__ == "__main__":
    create_user()