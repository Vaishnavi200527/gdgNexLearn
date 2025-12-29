#!/usr/bin/env python3
"""
Script to explicitly create all database tables
"""

import sys
import os

# Add the backend directory to the path so we can import models
sys.path.append(os.path.join(os.path.dirname(__file__)))

from database import engine, Base
import models  # This should register all models with Base
from sqlalchemy import inspect

def create_tables():
    """Create all tables based on models"""
    
    print("Creating database tables...")
    
    # Print all mapped classes to verify models are loaded
    print(f"Mapped classes: {[mapper.class_.__name__ for mapper in Base.registry.mappers]}")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("Tables created!")
    
    # Verify the tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables in database: {tables}")
    
    # Show detailed info about each table
    for table in tables:
        columns = inspector.get_columns(table)
        column_names = [col['name'] for col in columns]
        print(f"{table} columns: {column_names}")

if __name__ == "__main__":
    create_tables()