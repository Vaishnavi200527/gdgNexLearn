import sqlite3

def check_database():
    try:
        conn = sqlite3.connect('learning.db')
        cursor = conn.cursor()
        
        # Check all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in database:", tables)
        
        # Check if users table exists and has data
        if ('users',) in tables:
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            print(f"Users table exists with {user_count} records")
            
            # Show user columns
            cursor.execute("PRAGMA table_info(users);")
            columns = cursor.fetchall()
            print("Users table columns:", columns)
            
            # Check for the specific user
            cursor.execute("SELECT id, email, name, role FROM users WHERE email='dishakulkarni2005@gmail.com';")
            user = cursor.fetchone()
            print("Disha user record:", user)
        else:
            print("Users table does not exist")
        
        conn.close()
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database()