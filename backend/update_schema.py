#!/usr/bin/env python3
"""
Script to update the database schema with new columns from the refactored models
"""

import sqlite3
import sys
import os

# Add the backend directory to the path so we can import models
sys.path.append(os.path.join(os.path.dirname(__file__)))

from database import engine
import models  # Import models to register them with Base
from sqlalchemy import inspect

def update_schema():
    """Update database schema to match the current models"""
    
    print("Updating database schema to match current models...")
    
    # Create all tables based on current models
    from database import Base
    Base.metadata.create_all(bind=engine)
    
    print("Schema update completed!")
    
    # Verify the tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables in database: {tables}")
    
    # Check the users table structure
    if 'users' in tables:
        columns = inspector.get_columns('users')
        column_names = [col['name'] for col in columns]
        print(f"Users table columns: {column_names}")
    
    # Check the concepts table structure
    if 'concepts' in tables:
        columns = inspector.get_columns('concepts')
        column_names = [col['name'] for col in columns]
        print(f"Concepts table columns: {column_names}")
        
    # Check the quiz_questions table structure
    if 'quiz_questions' in tables:
        columns = inspector.get_columns('quiz_questions')
        column_names = [col['name'] for col in columns]
        print(f"QuizQuestions table columns: {column_names}")

if __name__ == "__main__":
    update_schema()