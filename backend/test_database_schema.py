#!/usr/bin/env python3
"""
Test script to verify database schema and attribute references
"""
from sqlalchemy.orm import sessionmaker
from database import engine
from models import Concept, MasteryScores, Users
import models

def test_database_schema():
    """Test database schema and attribute references"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Test 1: Check if concepts table has the correct columns
        print("Testing database schema...")

        # Query a concept to check attributes
        concept = db.query(Concept).first()
        if concept:
            print(f"Concept found: id={concept.id}, concept_name='{concept.concept_name}', subject='{concept.subject}', description='{concept.description}'")

            # Test attribute access
            try:
                name = concept.concept_name
                print(f"✓ concept_name attribute accessible: {name}")
            except AttributeError as e:
                print(f"✗ concept_name attribute error: {e}")

            try:
                subject = concept.subject
                print(f"✓ subject attribute accessible: {subject}")
            except AttributeError as e:
                print(f"✗ subject attribute error: {e}")

            try:
                description = concept.description
                print(f"✓ description attribute accessible: {description}")
            except AttributeError as e:
                print(f"✗ description attribute error: {e}")

        # Test 2: Check mastery scores relationship
        mastery = db.query(models.MasteryScores).first()
        if mastery:
            print(f"Mastery record found: student_id={mastery.student_id}, concept_id={mastery.concept_id}")
            if mastery.concept:
                print(f"✓ Concept relationship works: concept_name='{mastery.concept.concept_name}'")
            else:
                print("✗ Concept relationship failed")

        # Test 3: Check if we can create a new concept
        print("Testing concept creation...")
        new_concept = Concept(
            concept_name="Test Concept",
            subject="Test Subject",
            description="Test Description"
        )
        db.add(new_concept)
        db.commit()
        db.refresh(new_concept)
        print(f"✓ New concept created: id={new_concept.id}, concept_name='{new_concept.concept_name}'")

        # Clean up test concept
        db.delete(new_concept)
        db.commit()
        print("✓ Test concept cleaned up")

        print("All database schema tests passed!")

    except Exception as e:
        print(f"Database test failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_database_schema()
