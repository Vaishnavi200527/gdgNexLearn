#!/usr/bin/env python3
"""
Database Migration: Add Concept Explanations and PDF Documents Tables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from database import SQLALCHEMY_DATABASE_URL, Base
import models

def run_migration():
    """Create the new tables for concept explanations and PDF documents"""
    print("Running migration: Add Concept Explanations and PDF Documents tables...")
    
    # Create engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    try:
        # Create only the new tables
        print("Creating concept_explanations table...")
        models.ConceptExplanations.__table__.create(engine, checkfirst=True)
        
        print("Creating pdf_documents table...")
        models.PDFDocuments.__table__.create(engine, checkfirst=True)
        
        print("Migration completed successfully!")
        
        # Verify tables were created
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name IN ('concept_explanations', 'pdf_documents')
            """))
            created_tables = [row[0] for row in result]
            
        print(f"Created/verified tables: {created_tables}")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
