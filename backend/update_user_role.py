import sqlite3

# Connect to the database
conn = sqlite3.connect('amep.db')
cursor = conn.cursor()

# Update the user's role to TEACHER
cursor.execute("UPDATE users SET role = 'TEACHER' WHERE email = 'dishakulkarni2005@gmail.com'")
conn.commit()

# Verify the update
cursor.execute("SELECT name, email, role FROM users WHERE email = 'dishakulkarni2005@gmail.com'")
result = cursor.fetchall()

print("Updated user information:")
for row in result:
    print(f"Name: {row[0]}, Email: {row[1]}, Role: {row[2]}")

# Close the connection
conn.close()