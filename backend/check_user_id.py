import sqlite3

def get_user_id():
    # Connect to the database
    conn = sqlite3.connect('learning.db')
    cursor = conn.cursor()
    
    # Query for the user
    cursor.execute("SELECT id, name, email FROM users WHERE email='alice@example.com';")
    result = cursor.fetchone()
    
    if result:
        user_id, name, email = result
        print(f"User ID: {user_id}")
        print(f"Name: {name}")
        print(f"Email: {email}")
    else:
        print("User not found")
    
    conn.close()

if __name__ == "__main__":
    get_user_id()