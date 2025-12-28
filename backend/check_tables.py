import sqlite3

# Connect to the database
conn = sqlite3.connect('amep.db')
cursor = conn.cursor()

# Check all tables in the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check if users table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
result = cursor.fetchone()
if result:
    print("\nUsers table exists!")
    # Check how many users are in the table
    cursor.execute("SELECT COUNT(*) FROM users;")
    count = cursor.fetchone()[0]
    print(f"Number of users in table: {count}")
else:
    print("\nUsers table does NOT exist!")

conn.close()