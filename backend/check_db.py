from database import SessionLocal
from models import Assignments, Concepts, StudentAssignments

db = SessionLocal()
assignments = db.query(Assignments).all()
print('Assignments:')
for a in assignments:
    print(f'ID: {a.id}, Title: {a.title}, Concept ID: {a.concept_id}, Content URL: {a.content_url}')

print('\nConcepts:')
concepts = db.query(Concepts).all()
for c in concepts:
    print(f'ID: {c.id}, Name: {c.name}')

print('\nStudent Assignments:')
student_assignments = db.query(StudentAssignments).all()
for sa in student_assignments:
    print(f'Student ID: {sa.student_id}, Assignment ID: {sa.assignment_id}, Status: {sa.status}')

db.close()
