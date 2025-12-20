import sqlite3
from auth_utils import get_password_hash

# Connect to the database
conn = sqlite3.connect('amep.db')
cursor = conn.cursor()

# Set a new password for the user
new_password = "teacher123"  # Using a known test password
hashed_password = get_password_hash(new_password)

# Update the user's password
cursor.execute("UPDATE users SET password_hash = ? WHERE email = 'dishakulkarni2005@gmail.com'", (hashed_password,))
conn.commit()

# Verify the update
cursor.execute("SELECT id, name, email, password_hash, role FROM users WHERE email = 'dishakulkarni2005@gmail.com'")
result = cursor.fetchall()

print("Updated user information:")
for row in result:
    print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Password Hash: {row[3]}, Role: {row[4]}")

# Close the connection
conn.close()

print(f"\nPassword successfully reset for dishakulkarni2005@gmail.com")
print(f"New password: {new_password}")