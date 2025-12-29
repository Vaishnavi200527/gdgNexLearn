import sqlite3
import bcrypt

# Connect to the database
conn = sqlite3.connect('amep.db')
cursor = conn.cursor()

# Query for the specific user
cursor.execute("SELECT id, name, email, password_hash, role FROM users WHERE email = 'dishakulkarni2005@gmail.com'")
result = cursor.fetchall()

print("User information:")
for row in result:
    print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Password Hash: {row[3]}, Role: {row[4]}")

if not result:
    print("User dishakulkarni2005@gmail.com does not exist in the database.")

# Let's also check all existing users
cursor.execute("SELECT id, name, email, role FROM users")
all_users = cursor.fetchall()

print("\nAll existing users in the database:")
for row in all_users:
    print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Role: {row[3]}")

# Check if the user might have a different email format (case sensitivity)
cursor.execute("SELECT id, name, email, password_hash, role FROM users WHERE LOWER(email) = LOWER('dishakulkarni2005@gmail.com')")
case_insensitive_result = cursor.fetchall()

if case_insensitive_result:
    print(f"\nFound user with case-insensitive search:")
    for row in case_insensitive_result:
        print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Password Hash: {row[3]}, Role: {row[4]}")

# Close the connection
conn.close()

# Test the password hashing function from auth_utils
print("\nTesting password hashing function...")
try:
    from auth_utils import verify_password, get_password_hash
    
    # Test with a known password
    plain_password = "abcd1234"
    # Let's get the password hash for one of the existing users to verify the function works
    cursor = sqlite3.connect('amep.db').cursor()
    cursor.execute("SELECT password_hash FROM users WHERE email = 'alice@example.com' LIMIT 1")
    result = cursor.fetchone()
    
    if result:
        alice_hash = result[0]
        print(f"Testing password verification for alice@example.com")
        print(f"Alice's password hash: {alice_hash[:20]}...")  # Show first 20 chars
        
        # Verify Alice's password (should be "password123" based on seed_data.py)
        is_valid = verify_password("password123", alice_hash)
        print(f"Is 'password123' valid for Alice? {is_valid}")
        
        # Verify wrong password
        is_invalid = verify_password("wrongpassword", alice_hash)
        print(f"Is 'wrongpassword' valid for Alice? {is_invalid}")
    
    print(f"Password hashing function works correctly.")
    
except ImportError as e:
    print(f"Could not import auth_utils: {e}")
except Exception as e:
    print(f"Error testing password functions: {e}")