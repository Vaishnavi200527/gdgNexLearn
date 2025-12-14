import sys
import os
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from models import Base, Users, Classes, ClassEnrollments
from auth_utils import get_password_hash

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./amep.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_test_data():
    db = SessionLocal()
    try:
        # Create test teacher
        teacher = db.query(Users).filter(Users.email == "teacher@example.com").first()
        if not teacher:
            teacher = Users(
                name="Test Teacher",
                email="teacher@example.com",
                password_hash=get_password_hash("teacher123"),
                role="teacher"
            )
            db.add(teacher)
            db.commit()
            db.refresh(teacher)
            print("Test teacher created successfully!")
        
        # Create test student
        student = db.query(Users).filter(Users.email == "student@example.com").first()
        if not student:
            student = Users(
                name="Test Student",
                email="student@example.com",
                password_hash=get_password_hash("student123"),
                role="student"
            )
            db.add(student)
            db.commit()
            db.refresh(student)
            print("Test student created successfully!")
        
        # Create test class
        test_class = db.query(Classes).filter(Classes.name == "Test Class").first()
        if not test_class:
            test_class = Classes(
                name="Test Class",
                description="A test class",
                teacher_id=teacher.id
            )
            db.add(test_class)
            db.commit()
            db.refresh(test_class)
            print("Test class created successfully!")
            
            # Enroll student in class
            enrollment = ClassEnrollments(
                class_id=test_class.id,
                student_id=student.id
            )
            db.add(enrollment)
            db.commit()
            print("Student enrolled in class successfully!")
        
        print("\nTest data created successfully!")
        print("\nLogin Credentials:")
        print("Teacher: teacher@example.com / teacher123")
        print("Student: student@example.com / student123")
        if test_class:
            print(f"\nClass ID: {test_class.id}")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating test data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
