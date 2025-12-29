#!/usr/bin/env python3
"""
Migration script to add IRT parameters and prerequisite fields to Concepts table
and IRT parameters to QuizQuestions table
"""

import sqlite3
import sys
import os

# Add the backend directory to the path so we can import models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import engine
import models
from sqlalchemy import inspect

def add_irt_prerequisites_columns():
    """Add IRT parameters and prerequisite fields to the database tables"""
    
    # Check if columns already exist
    inspector = inspect(engine)
    columns = inspector.get_columns('concepts')
    column_names = [col['name'] for col in columns]
    
    # Check for missing columns in concepts table
    missing_concept_columns = []
    if 'id_slug' not in column_names:
        missing_concept_columns.append('id_slug')
    if 'prerequisite_ids' not in column_names:
        missing_concept_columns.append('prerequisite_ids')
    if 'irt_difficulty' not in column_names:
        missing_concept_columns.append('irt_difficulty')
    if 'discrimination_index' not in column_names:
        missing_concept_columns.append('discrimination_index')
    
    # Check quiz_questions table
    quiz_columns = inspector.get_columns('quiz_questions')
    quiz_column_names = [col['name'] for col in quiz_columns]
    
    missing_quiz_columns = []
    if 'irt_difficulty' not in quiz_column_names:
        missing_quiz_columns.append('irt_difficulty')
    if 'discrimination_index' not in quiz_column_names:
        missing_quiz_columns.append('discrimination_index')
    
    # Connect to database
    conn = sqlite3.connect('amep.db')
    cursor = conn.cursor()
    
    try:
        # Add missing columns to concepts table
        for col in missing_concept_columns:
            if col == 'id_slug':
                cursor.execute("ALTER TABLE concepts ADD COLUMN id_slug TEXT")
            elif col == 'prerequisite_ids':
                cursor.execute("ALTER TABLE concepts ADD COLUMN prerequisite_ids TEXT")
            elif col == 'irt_difficulty':
                cursor.execute("ALTER TABLE concepts ADD COLUMN irt_difficulty REAL DEFAULT 0.0")
            elif col == 'discrimination_index':
                cursor.execute("ALTER TABLE concepts ADD COLUMN discrimination_index REAL DEFAULT 1.0")
        
        # Add missing columns to quiz_questions table
        for col in missing_quiz_columns:
            if col == 'irt_difficulty':
                cursor.execute("ALTER TABLE quiz_questions ADD COLUMN irt_difficulty REAL DEFAULT 0.0")
            elif col == 'discrimination_index':
                cursor.execute("ALTER TABLE quiz_questions ADD COLUMN discrimination_index REAL DEFAULT 1.0")
        
        conn.commit()
        print("Migration completed successfully!")
        print(f"Added columns to concepts table: {missing_concept_columns}")
        print(f"Added columns to quiz_questions table: {missing_quiz_columns}")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Columns may already exist: {e}")
        else:
            print(f"Error during migration: {e}")
    except Exception as e:
        print(f"Unexpected error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_irt_prerequisites_columns()