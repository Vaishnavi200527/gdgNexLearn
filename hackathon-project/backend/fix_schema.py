from database import engine
from sqlalchemy import text

def fix_schema():
    print("Attempting to fix database schema...")
    with engine.connect() as connection:
        try:
            # SQLite syntax to add a column
            connection.execute(text("ALTER TABLE class_assignments ADD COLUMN due_date DATETIME"))
            connection.commit()
            print("Success: 'due_date' column added to 'class_assignments'.")
        except Exception as e:
            print(f"Note (class_assignments): {e}")
            
        try:
            # Add submitted_at to student_assignments
            connection.execute(text("ALTER TABLE student_assignments ADD COLUMN submitted_at DATETIME"))
            connection.commit()
            print("Success: 'submitted_at' column added to 'student_assignments'.")
        except Exception as e:
            print(f"Note (student_assignments submitted_at): {e}")

        try:
            # Add score to student_assignments (just in case)
            connection.execute(text("ALTER TABLE student_assignments ADD COLUMN score FLOAT"))
            connection.commit()
            print("Success: 'score' column added to 'student_assignments'.")
        except Exception as e:
            print(f"Note (student_assignments score): {e}")

        try:
            # Add score to student_quizzes
            connection.execute(text("ALTER TABLE student_quizzes ADD COLUMN score FLOAT"))
            connection.commit()
            print("Success: 'score' column added to 'student_quizzes'.")
        except Exception as e:
            print(f"Note (student_quizzes score): {e}")

        try:
            # Add submitted_at to student_quizzes
            connection.execute(text("ALTER TABLE student_quizzes ADD COLUMN submitted_at DATETIME"))
            connection.commit()
            print("Success: 'submitted_at' column added to 'student_quizzes'.")
        except Exception as e:
            print(f"Note (student_quizzes submitted_at): {e}")

        try:
            # Add submission_url to student_assignments
            connection.execute(text("ALTER TABLE student_assignments ADD COLUMN submission_url TEXT"))
            connection.commit()
            print("Success: 'submission_url' column added to 'student_assignments'.")
        except Exception as e:
            print(f"Note (student_assignments submission_url): {e}")

        try:
            # Add submission_notes to student_assignments
            connection.execute(text("ALTER TABLE student_assignments ADD COLUMN submission_notes TEXT"))
            connection.commit()
            print("Success: 'submission_notes' column added to 'student_assignments'.")
        except Exception as e:
            print(f"Note (student_assignments submission_notes): {e}")

if __name__ == "__main__":
    fix_schema()