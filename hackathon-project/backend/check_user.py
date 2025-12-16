import sqlite3

# Connect to the database
conn = sqlite3.connect('amep.db')
cursor = conn.cursor()

# Query for the specific user
cursor.execute("SELECT name, email, role FROM users WHERE email = 'dishakulkarni2005@gmail.com'")
result = cursor.fetchall()

print("User information:")
for row in result:
    print(f"Name: {row[0]}, Email: {row[1]}, Role: {row[2]}")

# Close the connection
conn.close()