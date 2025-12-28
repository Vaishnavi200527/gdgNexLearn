import sqlite3

# Connect to the database
conn = sqlite3.connect('amep.db')
cursor = conn.cursor()

# Update the user's role to TEACHER (uppercase to match enum)
cursor.execute("UPDATE users SET role = 'TEACHER' WHERE email = 'dishakulkarni2005@gmail.com'")

if cursor.rowcount > 0:
    conn.commit()
    print("User role updated successfully to TEACHER!")
    
    # Verify the update
    cursor.execute("SELECT id, name, email, role FROM users WHERE email = 'dishakulkarni2005@gmail.com'")
    result = cursor.fetchone()
    print(f"Updated user: ID {result[0]}, Name {result[1]}, Email {result[2]}, Role {result[3]}")
else:
    print("No user found with that email address.")

conn.close()