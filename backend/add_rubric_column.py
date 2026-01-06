import sqlite3
import os

# Connect to the database
db_path = "learning.db"
if not os.path.exists(db_path):
    print(f"Database file {db_path} does not exist. Please start the server first to create it.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if the column already exists
    cursor.execute("PRAGMA table_info(projects)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'evaluation_rubric' in columns:
        print("Column 'evaluation_rubric' already exists in the projects table.")
    else:
        # Add the evaluation_rubric column to the projects table
        cursor.execute("ALTER TABLE projects ADD COLUMN evaluation_rubric TEXT DEFAULT '[]'")
        print("Column 'evaluation_rubric' added to the projects table successfully.")
    
    conn.commit()
    print("Database updated successfully.")
    
except sqlite3.Error as e:
    print(f"An error occurred: {e}")
    conn.rollback()
    
finally:
    conn.close()