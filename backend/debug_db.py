#!/usr/bin/env python3
"""
Debug script to check database connection and path
"""

from database import engine
import os
from sqlalchemy import inspect
import models

def debug_db():
    print("Debugging database connection...")
    
    # Check the engine URL
    print(f"Engine URL: {engine.url}")
    
    # Check the actual file path
    db_path = "amep.db"
    print(f"Expected database file exists: {os.path.exists(db_path)}")
    if os.path.exists(db_path):
        print(f"Database file size: {os.path.getsize(db_path)} bytes")
    
    # Check if we can connect directly with SQLite
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables in SQLite connection: {[table[0] for table in tables]}")
    
    # Check if users table exists in SQLite
    cursor.execute("SELECT COUNT(*) FROM users;")
    count = cursor.fetchone()[0]
    print(f"Users count in SQLite: {count}")
    
    conn.close()
    
    # Check SQLAlchemy inspector
    inspector = inspect(engine)
    try:
        table_names = inspector.get_table_names()
        print(f"Tables from SQLAlchemy inspector: {table_names}")
    except Exception as e:
        print(f"Error getting table names from SQLAlchemy: {e}")
    
    # Try to create a session and query
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Try to get the table directly
        result = db.execute("SELECT COUNT(*) FROM users;").fetchone()
        print(f"Direct SQL query result: {result[0]}")
    except Exception as e:
        print(f"Direct SQL query failed: {e}")
    
    db.close()

if __name__ == "__main__":
    debug_db()