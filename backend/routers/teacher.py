from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import schemas
import models
import database
from services import ai_content_generation, teacher_interventions
import asyncio
from auth_utils import get_current_teacher

router = APIRouter(
    tags=["teacher"]
)

get_db = database.get_db

@router.get("/ai/assignments", response_model=List[schemas.AIGeneratedAssignment])
def get_ai_assignments(concept_id: int, api_key: Optional[str] = None, db: Session = Depends(get_db)):
    # Get AI-suggested assignments for a concept
    assignments = ai_content_generation.generate_assignments(concept_id, db, api_key)
    return assignments

@router.post("/assignments/create")
def create_assignment(
    assignments: List[schemas.AssignmentCreate], 
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    # Teacher selects AI-generated assignment(s) to assign
    created_assignments = []
    for assignment in assignments:
        db_assignment = models.Assignments(**assignment.dict(), teacher_id=current_user.id)
        db.add(db_assignment)
        db.commit()
        db.refresh(db_assignment)
        created_assignments.append(db_assignment)
    
    return created_assignments

@router.get("/ai/projects", response_model=List[schemas.AIGeneratedProject])
def get_ai_projects(skill_area: str, api_key: Optional[str] = None, db: Session = Depends(get_db)):
    # Get AI-suggested projects for a skill area
    projects = ai_content_generation.generate_projects(skill_area, db, api_key)
    return projects

@router.post("/projects/create")
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    # Create a project
    db_project = models.Projects(**project.dict(), teacher_id=current_user.id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.post("/softskills/score")
def record_soft_skill_score(
    score: schemas.SoftSkillScoreCreate,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    # Record a soft skill score (teacher or peer assessment)
    # Verify the evaluator is authorized (teacher of the student's class or peer)
    db_score = models.SoftSkillScores(**score.dict())
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    return db_score

@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    # Get teacher dashboard data
    dashboard_data = teacher_interventions.get_class_dashboard(current_user.id, db)
    return dashboard_data

@router.post("/intervene")
def record_intervention(
    intervention: schemas.TeacherInterventionCreate,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    # Record a teacher intervention for a student
    db_intervention = models.TeacherInterventions(**intervention.dict(), teacher_id=current_user.id)
    db.add(db_intervention)
    db.commit()
    db.refresh(db_intervention)
    
    return {"message": "Intervention recorded", "intervention": db_intervention}

@router.get("/interventions")
def get_interventions(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    # Get all interventions by this teacher
    interventions = db.query(models.TeacherInterventions).filter(
        models.TeacherInterventions.teacher_id == current_user.id
    ).all()
    return interventions

@router.post("/ai/generate-quiz", response_model=schemas.GeneratedQuiz)
async def generate_quiz(topic: str, difficulty: int = 3, question_count: int = 5, api_key: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Generate quiz questions using the Gemini API.
    
    Args:
        topic: The topic for the quiz
        difficulty: Difficulty level (1-5)
        question_count: Number of questions to generate (1-10)
        api_key: Optional Gemini API key. If not provided, will use from environment.
        
    Returns:
        GeneratedQuiz: A quiz with questions and answers
    """
    # Validate inputs
    difficulty = max(1, min(5, difficulty))  # Clamp difficulty between 1-5
    question_count = max(1, min(10, question_count))  # Clamp between 1-10 questions
    
    # Map numeric difficulty to string for the API
    difficulty_map = {
        1: "beginner",
        2: "easy",
        3: "medium",
        4: "hard",
        5: "expert"
    }
    difficulty_str = difficulty_map.get(difficulty, "medium")
    
    try:
        # Generate quiz questions using our new function
        questions_data = await ai_content_generation.generate_quiz_questions(
            topic=topic,
            num_questions=question_count,
            difficulty=difficulty_str,
            api_key=api_key
        )
        
        # Transform to our schema format
        questions = []
        for q_data in questions_data:
            question = schemas.QuizQuestion(
                id=q_data.get("id", 0),
                type=q_data.get("type", "Multiple Choice"),
                question=q_data.get("question", ""),
                options=q_data.get("options"),
                correct_answer=q_data.get("correct_answer", "")
            )
            questions.append(question)
        
        # Create the quiz schema
        quiz = schemas.GeneratedQuiz(
            topic=topic,
            difficulty=difficulty,
            questions=questions
        )
        
        return quiz
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating quiz: {str(e)}"
        )

@router.get("/classes", response_model=List[schemas.ClassResponse])
async def get_teacher_classes(
    current_user: models.Users = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Get all classes for the current teacher
    """
    classes = db.query(models.Classes).filter(
        models.Classes.teacher_id == current_user.id
    ).all()
    return classes

@router.get("/students", response_model=List[schemas.UserResponse])
def get_all_students(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    """Get all students in the system"""
    students = db.query(models.Users).filter(models.Users.role == models.UserRole.STUDENT).all()
    return students

@router.get("/teachers", response_model=List[schemas.UserResponse])
def get_all_teachers(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    """Get all teachers in the system"""
    teachers = db.query(models.Users).filter(models.Users.role == models.UserRole.TEACHER).all()
    return teachers

@router.post("/assignments/class/{class_id}", status_code=status.HTTP_201_CREATED)
async def assign_to_class(
    class_id: int, 
    assignment_data: schemas.ClassAssignmentAssignment,
    db: Session = Depends(get_db)
):
    # Check if class exists
    db_class = db.query(models.Classes).filter(models.Classes.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class with id {class_id} not found"
        )
    
    # Check if assignment exists
    assignment = db.query(models.Assignments).filter(
        models.Assignments.id == assignment_data.assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment with id {assignment_data.assignment_id} not found"
        )
    
    # Create class assignment
    db_class_assignment = models.ClassAssignments(
        class_id=class_id,
        assignment_id=assignment_data.assignment_id,
        assigned_at=datetime.utcnow()
    )
    
    # Get all students in the class
    class_enrollments = db.query(models.ClassEnrollments).filter(
        models.ClassEnrollments.class_id == class_id
    ).all()
    
    # Assign to each student
    for enrollment in class_enrollments:
        student_assignment = models.StudentAssignments(
            student_id=enrollment.student_id,
            assignment_id=assignment_data.assignment_id,
            status=schemas.AssignmentStatus.ASSIGNED
        )
        db.add(student_assignment)
    
    db.add(db_class_assignment)
    db.commit()
    db.refresh(db_class_assignment)
    
    return {"message": f"Assignment {assignment.title} assigned to class {db_class.name}"}

@router.get("/classes/{class_id}/assignments", response_model=List[schemas.ClassAssignmentResponse])
async def get_class_assignments(class_id: int, db: Session = Depends(get_db)):
    # Get all assignments for the class with their details
    assignments = db.query(
        models.Assignments,
        models.ClassAssignments.assigned_at,
        models.ClassAssignments.due_date
    ).join(
        models.ClassAssignments,
        models.Assignments.id == models.ClassAssignments.assignment_id
    ).filter(
        models.ClassAssignments.class_id == class_id
    ).all()
    
    return [
        {
            **assignment[0].__dict__,
            "assigned_at": assignment[1],
            "due_date": assignment[2],
            "class_id": class_id
        }
        for assignment in assignments
    ]

@router.get("/assignments/{assignment_id}/submissions", response_model=List[schemas.AssignmentSubmissionResponse])
async def get_assignment_submissions(
    assignment_id: int,
    class_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.StudentAssignments).filter(
        models.StudentAssignments.assignment_id == assignment_id
    )
    
    if class_id:
        # Get only submissions from students in the specified class
        query = query.join(
            models.ClassEnrollments,
            models.StudentAssignments.student_id == models.ClassEnrollments.student_id
        ).filter(
            models.ClassEnrollments.class_id == class_id
        )
    
    submissions = query.all()
    return submissions

# Project submission endpoints for teachers
@router.get("/projects/{project_id}/submissions", response_model=List[schemas.ProjectSubmissionResponse])
async def get_project_submissions(
    project_id: int,
    class_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    """
    Get all submissions for a specific project
    Teachers can view all student submissions for projects they created or assigned
    """
    query = db.query(models.ProjectSubmissions).filter(
        models.ProjectSubmissions.project_id == project_id
    )
    
    if class_id:
        # Filter by specific class
        query = query.filter(models.ProjectSubmissions.class_id == class_id)
    
    # Verify teacher has access to this project/class
    project = db.query(models.Projects).filter(models.Projects.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    submissions = query.all()
    return submissions

@router.get("/classes/{class_id}/projects/{project_id}/submissions", response_model=List[schemas.ProjectSubmissionResponse])
async def get_class_project_submissions(
    class_id: int,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    """
    Get all submissions for a specific project in a specific class
    """
    # Verify teacher has access to this class
    class_obj = db.query(models.Classes).filter(models.Classes.id == class_id).first()
    if not class_obj or class_obj.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this class"
        )
    
    submissions = db.query(models.ProjectSubmissions).filter(
        models.ProjectSubmissions.project_id == project_id,
        models.ProjectSubmissions.class_id == class_id
    ).all()
    
    return submissions

@router.put("/projects/submissions/{submission_id}/grade")
async def grade_project_submission(
    submission_id: int,
    grade_data: dict,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    """
    Grade a project submission and update status to GRADED
    """
    submission = db.query(models.ProjectSubmissions).filter(
        models.ProjectSubmissions.id == submission_id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Update submission with grade and status
    submission.score = grade_data.get("score")
    submission.status = schemas.AssignmentStatus.GRADED
    
    db.commit()
    db.refresh(submission)
    
    return {"message": "Project graded successfully", "submission": submission}