#!/usr/bin/env python3
"""
Migration to add description column and make subject nullable in concepts table
"""

from sqlalchemy import create_engine, text
import os
DATABASE_URL = "sqlite:///./amep.db"

def add_description_column():
    """Add description column and make subject nullable in concepts table"""
    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            # Check if description column exists
            result = conn.execute(text("""
                PRAGMA table_info(concepts)
            """))

            columns = [row[1] for row in result.fetchall()]

            if 'description' not in columns:
                print("Adding description column to concepts table...")
                conn.execute(text("""
                    ALTER TABLE concepts ADD COLUMN description TEXT
                """))
                conn.commit()
                print("Description column added successfully.")
            else:
                print("Description column already exists.")

            # Make subject column nullable (SQLite doesn't support ALTER COLUMN directly)
            # We need to recreate the table to make subject nullable
            print("Making subject column nullable by recreating table...")

            # Get existing data
            existing_data = conn.execute(text("SELECT id, subject, concept_name FROM concepts")).fetchall()

            # Drop the table
            conn.execute(text("DROP TABLE concepts"))

            # Recreate the table with subject nullable and description column
            conn.execute(text("""
                CREATE TABLE concepts (
                    id INTEGER PRIMARY KEY,
                    subject TEXT,
                    concept_name TEXT NOT NULL,
                    description TEXT
                )
            """))

            # Reinsert the data
            for row in existing_data:
                conn.execute(text("""
                    INSERT INTO concepts (id, subject, concept_name, description)
                    VALUES (?, ?, ?, NULL)
                """), (row[0], row[1], row[2]))

            conn.commit()
            print("Subject column made nullable and description column added successfully.")

    except Exception as e:
        print(f"Error in migration: {e}")
    finally:
        engine.dispose()

if __name__ == "__main__":
    add_description_column()
