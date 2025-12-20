import sqlite3

# Connect to the database
conn = sqlite3.connect('amep.db')
cursor = conn.cursor()

# Query for the specific user
cursor.execute("SELECT id, name, email, password_hash, role FROM users WHERE email = 'dishakulkarni2005@gmail.com'")
result = cursor.fetchall()

print("User information:")
for row in result:
    print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Password Hash: {row[3]}, Role: {row[4]}")

# Close the connection
conn.close()