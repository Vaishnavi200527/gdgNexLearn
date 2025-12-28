import sqlite3
from auth_utils import verify_password, get_password_hash

def verify_user_password():
    # Connect to the database
    conn = sqlite3.connect('learning.db')
    cursor = conn.cursor()
    
    # Get the user's password hash
    cursor.execute("SELECT password_hash FROM users WHERE email='dishakulkarni2005@gmail.com';")
    result = cursor.fetchone()
    
    if result:
        stored_hash = result[0]
        print(f"Stored hash: {stored_hash[:50]}...")
        
        # Test if the password 'abcd1234' matches the hash
        test_password = "abcd1234"
        is_valid = verify_password(test_password, stored_hash)
        print(f"Password 'abcd1234' matches hash: {is_valid}")
        
        # Test a wrong password
        wrong_password = "password123"
        is_wrong = verify_password(wrong_password, stored_hash)
        print(f"Password 'password123' matches hash: {is_wrong}")
        
        # Let's also check what hash is generated for 'abcd1234'
        expected_hash = get_password_hash("abcd1234")
        print(f"Expected hash for 'abcd1234': {expected_hash[:50]}...")
        print(f"Hashes match: {stored_hash == expected_hash}")
    else:
        print("User not found")
    
    conn.close()

if __name__ == "__main__":
    verify_user_password()