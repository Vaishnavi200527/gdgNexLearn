from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import schemas
import models
import database
from services import adaptive_learning, engagement_tracking, gamification, ai_content_generation
from services.concept_explanation_storage import ConceptExplanationStorage
from sqlalchemy import and_
import auth_utils
from auth_utils import get_current_student, get_current_user, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
import requests
import pdfplumber
import io
import os
import json
from services.ai_content_generation import call_gemini_api
import logging

# Suppress pdfminer warnings
logging.getLogger("pdfminer").setLevel(logging.ERROR)

router = APIRouter(
    tags=["student"]
)

def extract_pdf_text(pdf_path: str) -> str:
    """
    Extract text content from a PDF file, which can be a URL or a local file path.
    """
    try:
        if pdf_path.startswith("http://") or pdf_path.startswith("https://"):
            response = requests.get(pdf_path)
            response.raise_for_status()
            pdf_file = io.BytesIO(response.content)
        else:
            # It's a local file path
            # The path is relative to the backend directory, so we need to adjust it
            full_path = os.path.join(os.path.dirname(__file__), '..', pdf_path.lstrip('/'))
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"PDF file not found at {full_path}")
            pdf_file = open(full_path, "rb")

        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        if not (pdf_path.startswith("http://") or pdf_path.startswith("https://")):
             pdf_file.close()
             
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

# --- MOCK AI Generation Functions ---
# In a real application, these would be in a separate 'ai_services.py' file and call an external AI API like Gemini.

async def generate_ai_explanation(concept_name: str, pdf_text: str, mastery_score: int, detail_level: str) -> dict:
    """
    Generates a personalized explanation by calling the Gemini API.
    """
    if mastery_score < 40:
        persona = "a friendly and patient tutor for a beginner. Use simple words and lots of analogies."
        learning_level = "Beginner"
    elif mastery_score < 75:
        persona = "a helpful colleague. Assume some basic knowledge but explain the core ideas clearly with practical examples."
        learning_level = "Intermediate"
    else:
        persona = "an expert mentor. Focus on advanced nuances, edge cases, and performance considerations."
        learning_level = "Advanced"

    prompt = f"""
    You are an AI-powered tutor. Your role is to act as {persona}.
    Your task is to provide a personalized, engaging, and friendly explanation of a concept for a student.

    **Student's Current Learning Level:** {learning_level} ({mastery_score}% mastery)
    **Concept to Explain:** {concept_name}
    **Source Material (from their assignment PDF):**
    ---
    {pdf_text[:4000]}
    ---

    **Instructions:**
    1.  **Analyze the Source Material:** Base your explanation on the provided text.
    2.  **Personalize for the Student:** Tailor the depth, tone, and examples to the student's learning level.
        - For Beginners: Be very encouraging, use simple analogies, break things down step-by-step, and define all key terms.
        - For Intermediate Learners: Focus on connecting ideas, practical applications, and common pitfalls.
        - For Advanced Learners: Discuss nuances, best practices, performance, and connections to other advanced topics.
    3.  **Be Engaging and Friendly:** Use a conversational and encouraging tone. Use emojis where appropriate to make it more engaging.
    4.  **Structure Your Response:** Return ONLY a valid JSON object with the following structure. Do NOT include any text outside the JSON object.

    **JSON Structure to Return:**
    {{
      "title": "A personalized and catchy title for the explanation",
      "definition": "A clear, concise definition of the concept, adapted for the student's level.",
      "detailed_explanation": "A detailed, multi-paragraph explanation. Use markdown for formatting (e.g., **bold**, *italics*). This should be the core of the explanation.",
      "key_points": [
        "A list of 3-5 key takeaways or summary points.",
        "Each point should be a string."
      ],
      "examples": [
        {{
          "title": "A descriptive title for the first example (e.g., 'A Simple Analogy')",
          "code": "A code snippet or a real-world scenario that illustrates the concept. Use markdown for code blocks if applicable."
        }},
        {{
          "title": "A descriptive title for a second, more practical example",
          "code": "Another code snippet or scenario, perhaps more complex depending on the student's level."
        }}
      ],
      "related_terms": [
        "A list of 3-5 related concepts or terms that the student might also want to explore.",
        "Each term should be a string."
      ]
    }}
    """

    try:
        response = await call_gemini_api(prompt, expect_json=True)
        # The call_gemini_api should ideally handle JSON parsing. 
        # If it returns a string, we attempt to parse it.
        if isinstance(response, str):
            return json.loads(response)
        return response
    except Exception as e:
        # Fallback to a simpler, non-AI response if the API call fails
        return {
            "title": f"Understanding {concept_name}",
            "definition": "Could not generate AI explanation. Here is the raw text:",
            "detailed_explanation": pdf_text[:1500],
            "key_points": [],
            "examples": [],
            "related_terms": []
        }

async def generate_ai_quiz(concept_name: str, pdf_text: str, mastery_score: int, question_count: int = 10) -> list:
    """
    Generates a personalized quiz by calling the Gemini API.
    """
    if mastery_score < 40:
        difficulty = "Easy"
    elif mastery_score < 75:
        difficulty = "Medium"
    else:
        difficulty = "Hard"

    prompt = f"""
    You are an AI that generates educational content.
    Your task is to create a personalized, multiple-choice quiz about a specific concept, based on provided text and a student's mastery level.

    **Student's Mastery Level:** {difficulty} ({mastery_score}%)
    **Concept for Quiz:** {concept_name}
    **Number of Questions:** {question_count}
    **Source Material:**
    ---
    {pdf_text[:4000]}
    ---

    **Instructions:**
    1.  **Create {question_count} Multiple-Choice Questions:** The questions must be based *only* on the source material provided.
    2.  **Adapt Difficulty:**
        - For **Easy** level: Focus on definitions, key terms, and straightforward facts from the text.
        - For **Medium** level: Focus on comprehension, application of concepts, and interpreting information from the text.
        - For **Hard** level: Focus on analysis, synthesis, evaluation, and making inferences based on the text.
    3.  **Provide Four Options:** For each question, provide four distinct options (A, B, C, D).
    4.  **Indicate Correct Answer:** Clearly identify the correct answer for each question.
    5.  **Strict JSON Output:** Return ONLY a valid JSON array of objects. Do not include any text, notes, or markdown outside of the JSON array.

    **JSON Structure to Return:**
    [
      {{
        "question": "The text of the first question goes here.",
        "type": "multiple_choice",
        "options": [
          "Option A",
          "Option B",
          "Option C",
          "Option D"
        ],
        "correct_answer": "Option B"
      }},
      {{
        "question": "The text of the second question goes here.",
        "type": "multiple_choice",
        "options": [
          "Option A",
          "Option B",
          "Option C",
          "Option D"
        ],
        "correct_answer": "Option C"
      }}
    ]
    """

    try:
        response = await call_gemini_api(prompt, expect_json=True)
        if isinstance(response, list):
            return response
        # Handle cases where the API might wrap the list in a dict
        if isinstance(response, dict) and 'questions' in response and isinstance(response['questions'], list):
            return response['questions']
        
        # If the response is not in the expected format, try to parse it if it's a string
        if isinstance(response, str):
            try:
                # The response might be a JSON string that needs parsing
                parsed_response = json.loads(response)
                if isinstance(parsed_response, list):
                    return parsed_response
            except json.JSONDecodeError:
                pass # Fall through to the fallback if parsing fails

        # Fallback for unexpected structure
        raise TypeError("Unexpected response format from AI")

    except Exception as e:
        # Fallback to mock questions if the API call fails
        questions = []
        for i in range(question_count):
            questions.append({
                "question": f"Mock Fallback Question {i+1} for '{concept_name}' at {difficulty} level. What is its main purpose?",
                "type": "multiple_choice",
                "options": [f"Option A", f"Option B (Correct)", f"Option C", f"Option D"],
                "correct_answer": f"Option B (Correct)"
            })
        return questions

# --- End of MOCK AI Functions ---

get_db = database.get_db

@router.post("/signup", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(models.Users).filter(models.Users.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user (in a real app, hash the password)
    new_user = models.Users(
        name=user.name,
        email=user.email,
        password_hash=user.password,  # In production, hash this!
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=schemas.Token)
def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    # Verify password hash
    db_user = db.query(models.Users).filter(models.Users.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Handle role serialization
    role_value = db_user.role.value if hasattr(db_user.role, "value") else db_user.role
    
    # Create access token
    access_token_expires = timedelta(minutes=1440) # 24 hours for development
    access_token = create_access_token(
        data={"sub": db_user.email, "role": role_value},
        expires_delta=access_token_expires
    )
    
    return schemas.Token(
        access_token=access_token, 
        token_type="bearer",
        role=role_value
    )

@router.get("/mastery", response_model=List[schemas.MasteryResponse])
def get_mastery(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    # Get student mastery records
    student_id = current_user.id
<<<<<<< HEAD
    mastery_records = db.query(models.MasteryScores).filter(
        models.MasteryScores.student_id == student_id
    ).all()
=======
    
    # Eager load the concept relationship to avoid N+1 queries
    mastery_records = db.query(models.StudentMastery)\
        .join(models.StudentMastery.concept)\
        .filter(models.StudentMastery.student_id == student_id)\
        .all()
    
>>>>>>> 31d1d287acc7d6db0c326025d7fac1f9462033ea
    
    results = []
    for record in mastery_records:
        result = {
            "concept_id": record.concept_id,
<<<<<<< HEAD
            "concept_name": record.concept.concept_name if record.concept else "Unknown",
            "mastery_score": record.mastery_score,
=======
            "concept_name": record.concept.name if record.concept else "Unknown",
            "mastery_score": float(record.mastery_score),  # Ensure it's a float
>>>>>>> 31d1d287acc7d6db0c326025d7fac1f9462033ea
            "level": int(record.mastery_score / 20) + 1
        }
        results.append(result)
    
    return results

@router.get("/learning-profile", response_model=schemas.StudentLearningProfile)
def get_learning_profile(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    """
    Get student's comprehensive learning profile.
    """
    profile = adaptive_learning.get_student_learning_profile(current_user.id, db)
    return profile

@router.get("/content-adjustment", response_model=schemas.ContentDifficultyAdjustment)
def get_content_adjustment(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    """
    Get recommended content difficulty adjustment based on student's performance.
    """
    adjustment = adaptive_learning.adjust_content_difficulty(current_user.id, db)
    return adjustment

@router.get("/learning-speed-analysis", response_model=dict)
def get_learning_speed_analysis(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    """
    Get analysis of student's learning speed.
    """
    analysis = adaptive_learning.analyze_learning_speed(current_user.id, db)
    return analysis

@router.get("/content-pacing-adjustment", response_model=dict)
def get_content_pacing_adjustment(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    """
    Get dynamic content pacing adjustment based on learning speed.
    """
    adjustment = adaptive_learning.adjust_content_pacing(current_user.id, db)
    return adjustment

@router.get("/assignments/adaptive", response_model=List[schemas.AdaptiveAssignmentResponse])
def get_adaptive_assignments(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    # Get adaptive assignments based on student's mastery levels and class enrollment
    student_id = current_user.id

    # Get student's mastery scores
    mastery_records = db.query(models.MasteryScores).filter(
        models.MasteryScores.student_id == student_id
    ).all()

    # Create a dictionary of concept_id -> mastery_score
    mastery_dict = {record.concept_id: record.mastery_score for record in mastery_records}

    # First get classes the student is enrolled in
    enrolled_classes = db.query(models.Classes.id)\
        .join(models.ClassEnrollments)\
        .filter(models.ClassEnrollments.student_id == student_id)\
        .all()

    class_ids = [c.id for c in enrolled_classes]

    # Get assignments assigned to those classes
    class_assignments = db.query(models.Assignments)\
        .join(models.ClassAssignments)\
        .filter(models.ClassAssignments.class_id.in_(class_ids))\
        .all()

    # Convert to adaptive assignment response format with difficulty adjustment
    adaptive_assignments = []
    for assignment in class_assignments:
        # Get mastery score for this concept
        mastery_score = mastery_dict.get(assignment.concept_id, 0)

        # Adjust difficulty based on mastery
        # If mastery < 60: keep original difficulty (needs practice)
        # If mastery 60-80: increase difficulty slightly
        # If mastery > 80: no assignment needed (mastered)
        if mastery_score > 80:
            continue  # Skip assignments for mastered concepts

        adjusted_difficulty = assignment.difficulty_level or 1
        if mastery_score >= 60 and mastery_score <= 80:
            adjusted_difficulty = min(5, adjusted_difficulty + 1)  # Increase difficulty slightly

        adaptive_assignments.append(schemas.AdaptiveAssignmentResponse(
            assignment_id=assignment.id,
            title=assignment.title,
            description=assignment.description,
            difficulty_level=adjusted_difficulty,
            estimated_time=30  # Default value
        ))

    return adaptive_assignments

@router.get("/assignments/{assignment_id}/info", response_model=schemas.AssignmentResponse)
def get_assignment_by_id(
    assignment_id: int, 
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_user)
):
    # Get specific assignment by ID
    assignment = db.query(models.Assignments).filter(models.Assignments.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

@router.get("/assignments/{assignment_id}/concepts")
async def get_assignment_concepts(
    assignment_id: int,
    detail_level: str = 'medium',
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    """
    Get AI-powered, personalized concept explanations for an assignment.
    """
    if detail_level not in ['basic', 'medium', 'comprehensive']:
        raise HTTPException(400, "detail_level must be 'basic', 'medium', or 'comprehensive'")
    
    assignment = db.query(models.Assignments).join(models.Assignments.concept).filter(models.Assignments.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if not assignment.concept_id or not assignment.concept:
        raise HTTPException(404, detail="No concept associated with this assignment")
    
    concept = assignment.concept

    # Get student's mastery for this concept
    mastery_record = db.query(models.StudentMastery).filter(
        models.StudentMastery.student_id == current_user.id,
        models.StudentMastery.concept_id == concept.id
    ).first()
    mastery_score = mastery_record.mastery_score if mastery_record else 0

    # Extract text from PDF if content_url is available
    pdf_text = ""
    if assignment.content_url:
        try:
            pdf_text = extract_pdf_text(assignment.content_url)
        except Exception as e:
            # If PDF extraction fails, fall back to stored explanation
            pass

    # If no PDF text, get base explanation text from storage
    if not pdf_text:
        storage = ConceptExplanationStorage(db)
        explanation_obj = db.query(models.ConceptExplanations).filter(models.ConceptExplanations.concept_id == concept.id).first()

        if not explanation_obj:
            return {"success": False, "message": "No base explanation material found to generate AI explanation."}

        pdf_text = explanation_obj.detailed_explanation or explanation_obj.definition or "No content available"

    # Generate personalized explanation using AI
    try:
        explanation = await generate_ai_explanation(
            concept_name=concept.name,
            pdf_text=pdf_text,
            mastery_score=mastery_score,
            detail_level=detail_level
        )
    except Exception as e:
        raise HTTPException(500, detail=f"AI explanation generation failed: {str(e)}")
    
    return {
        "success": True,
        "assignment_id": assignment_id,
        "assignment_title": assignment.title,
        "concept_id": assignment.concept_id,
        "concept_name": concept.name,
        "detail_level": detail_level,
        "explanation": explanation,
        "mastery_score": mastery_score
    }

@router.post("/engagement")
def log_engagement(engagement: schemas.EngagementLogCreate, db: Session = Depends(get_db)):
    # Log engagement and optionally award XP
    engagement_tracking.log_engagement(engagement, db)
    return {"message": "Engagement logged successfully"}

@router.get("/projects", response_model=List[schemas.ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    # Get projects that the student is part of through class enrollment
    student_id = current_user.id
    student_projects = db.query(models.Projects)\
        .join(models.ClassProjects)\
        .join(models.Classes)\
        .join(models.ClassEnrollments)\
        .filter(models.ClassEnrollments.student_id == student_id)\
        .all()
    return student_projects

@router.get("/leaderboard", response_model=List[schemas.LeaderboardEntry])
def get_leaderboard(db: Session = Depends(get_db)):
    # Get class/global leaderboard
    leaderboard = gamification.get_leaderboard(db)
    return leaderboard

@router.get("/badges", response_model=List[schemas.BadgeDisplay])
def get_badges(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    # Get student's badges and achievements
    student_id = current_user.id
    badges = gamification.get_student_badges(student_id, db)
    return badges

@router.get("/assignments", response_model=List[schemas.StudentAssignmentDetail])
async def get_student_assignments(
    status: Optional[schemas.AssignmentStatus] = None,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    # Get all assignments for the student with their status
    student_id = current_user.id
    query = db.query(models.StudentAssignments).filter(models.StudentAssignments.student_id == student_id)
    
    if status:
        query = query.filter(models.StudentAssignments.status == status)
    
    student_assignments = query.all()
    
    result = []
    for sa in student_assignments:
        assignment = db.query(models.Assignments).filter(models.Assignments.id == sa.assignment_id).first()
        if not assignment: continue
        
        # Find due date based on the class the student is enrolled in
        due_date = None
        student_classes = db.query(models.ClassEnrollments.class_id).filter(
            models.ClassEnrollments.student_id == student_id
        ).all()
        student_class_ids = [c.class_id for c in student_classes]
        
        if student_class_ids:
            class_assignment = db.query(models.ClassAssignments).filter(
                models.ClassAssignments.assignment_id == sa.assignment_id,
                models.ClassAssignments.class_id.in_(student_class_ids)
            ).first()
            if class_assignment:
                due_date = class_assignment.due_date
        
        # Add to result list
        result.append({
            "id": assignment.id,
            "concept_id": assignment.concept_id,
            "teacher_id": assignment.teacher_id,
            "difficulty_level": assignment.difficulty_level if assignment.difficulty_level else 1,
            "content_url": assignment.content_url,
            "title": assignment.title,
            "description": assignment.description,
            "status": sa.status,
            "score": sa.score,
            "submitted_at": sa.submitted_at,
            "due_date": due_date
        })
    
    return result

@router.get("/assignments/{assignment_id}", response_model=schemas.StudentAssignmentDetail)
async def get_assignment_details(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    # Get assignment details with student's submission status
    student_id = current_user.id
    assignment = db.query(
        models.Assignments,
        models.StudentAssignments.status,
        models.StudentAssignments.score,
        models.StudentAssignments.submitted_at,
        models.ClassAssignments.due_date
    ).join(
        models.StudentAssignments,
        and_(
            models.Assignments.id == models.StudentAssignments.assignment_id,
            models.StudentAssignments.student_id == student_id
        )
    ).outerjoin(
        models.ClassAssignments,
        models.Assignments.id == models.ClassAssignments.assignment_id
    ).filter(
        models.Assignments.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or not assigned to student"
        )
    
    return {
        **assignment[0].__dict__,
        "status": assignment[1],
        "score": assignment[2],
        "submitted_at": assignment[3],
        "due_date": assignment[4]
    }

@router.post("/assignments/{assignment_id}/submit", status_code=status.HTTP_200_OK)
async def submit_assignment(
    assignment_id: int,
    submission: schemas.AssignmentSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    # Check if assignment exists and is assigned to student
    student_id = current_user.id
    
    student_assignment = db.query(models.StudentAssignments).filter(
        models.StudentAssignments.assignment_id == assignment_id,
        models.StudentAssignments.student_id == student_id
    ).first()
    
    if not student_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or not assigned to student"
        )
    
    # Update submission details
    student_assignment.status = schemas.AssignmentStatus.SUBMITTED
    student_assignment.submission_url = submission.submission_url
    student_assignment.submission_notes = submission.submission_notes
    student_assignment.submitted_at = datetime.utcnow()
    
    # Log engagement
    engagement_log = models.EngagementLogs(
        student_id=student_id,
        engagement_type=schemas.EngagementType.ASSIGNMENT,
        value=1,  # Count as one engagement
        metadata_json=f"{{'assignment_id': {assignment_id}, 'action': 'submission'}}"
    )
    
    db.add(engagement_log)
    db.commit()
    db.refresh(student_assignment)
    
    # Update student progress, XP, streaks, badges
    gamification.update_after_submission(student_id, assignment_id, db)
    
    # TODO: Send notification to teacher
    
    return {"message": "Assignment submitted successfully", "assignment_id": assignment_id}

@router.get("/assignments/{assignment_id}/status", response_model=schemas.StudentAssignmentDetail)
async def get_assignment_status(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    # Get assignment status for student
    student_id = current_user.id
    assignment = db.query(
        models.Assignments,
        models.StudentAssignments.status,
        models.StudentAssignments.score,
        models.StudentAssignments.submitted_at,
        models.ClassAssignments.due_date
    ).join(
        models.StudentAssignments,
        and_(
            models.Assignments.id == models.StudentAssignments.assignment_id,
            models.StudentAssignments.student_id == student_id
        )
    ).outerjoin(
        models.ClassAssignments,
        models.Assignments.id == models.ClassAssignments.assignment_id
    ).filter(
        models.Assignments.id == assignment_id
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or not assigned to student"
        )

    return {
        **assignment[0].__dict__,
        "status": assignment[1],
        "score": assignment[2],
        "submitted_at": assignment[3],
        "due_date": assignment[4]
    }

<<<<<<< HEAD
@router.get("/homework/adaptive", response_model=List[schemas.AdaptiveHomeworkResponse])
def get_adaptive_homework(
=======
@router.get("/assignments/{assignment_id}/quiz")
async def get_assignment_quiz(
    assignment_id: int,
>>>>>>> 31d1d287acc7d6db0c326025d7fac1f9462033ea
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    """
<<<<<<< HEAD
    Generate adaptive homework based on student's mastery levels.
    Returns questions from concepts where mastery is below 80%.
    """
    student_id = current_user.id

    # Get student's mastery scores
    mastery_records = db.query(models.MasteryScores).filter(
        models.MasteryScores.student_id == student_id
    ).all()

    # Find concepts where mastery is below 80%
    weak_concepts = []
    for record in mastery_records:
        if record.mastery_score < 80:
            weak_concepts.append(record.concept_id)

    # If no weak concepts, return empty list (student has mastered everything)
    if not weak_concepts:
        return []

    # Get questions from weak concepts, prioritizing based on mastery level
    # Lower mastery = higher priority
    concept_priorities = {record.concept_id: record.mastery_score for record in mastery_records}
    weak_concepts.sort(key=lambda x: concept_priorities.get(x, 0))  # Sort by lowest mastery first

    homework_questions = []
    questions_per_concept = 3  # Limit questions per concept

    for concept_id in weak_concepts:
        # Get questions for this concept
        questions = db.query(models.Question).filter(
            models.Question.concept_id == concept_id
        ).limit(questions_per_concept).all()

        for question in questions:
            homework_questions.append({
                "question_id": question.id,
                "concept_id": concept_id,
                "concept_name": question.concept.concept_name if question.concept else "Unknown",
                "question_text": question.question_text,
                "difficulty": question.difficulty,
                "mastery_level": concept_priorities.get(concept_id, 0)
            })

    return homework_questions
=======
    Generate a personalized quiz for the assignment based on student's mastery level
    """
    student_id = current_user.id

    # Check if assignment exists and is assigned to student
    student_assignment = db.query(models.StudentAssignments).filter(
        models.StudentAssignments.assignment_id == assignment_id,
        models.StudentAssignments.student_id == student_id
    ).first()

    if not student_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found or not assigned to student"
        )

    # Get assignment details
    assignment = db.query(models.Assignments).filter(models.Assignments.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Get student's mastery level for the concept
    mastery_record = db.query(models.StudentMastery).filter(
        models.StudentMastery.student_id == student_id,
        models.StudentMastery.concept_id == assignment.concept_id
    ).first()
    mastery_score = mastery_record.mastery_score if mastery_record else 0

    # Extract text from PDF if content_url is available
    pdf_text = ""
    if assignment.content_url:
        try:
            pdf_text = extract_pdf_text(assignment.content_url)
        except Exception as e:
            # If PDF extraction fails, fall back to stored explanation
            pass

    # If no PDF text, get base explanation text from storage
    if not pdf_text:
        explanation_obj = db.query(models.ConceptExplanations).filter(
            models.ConceptExplanations.concept_id == assignment.concept_id
        ).first()
        if not explanation_obj or not explanation_obj.detailed_explanation:
            raise HTTPException(404, detail="No source material found to generate quiz")

        pdf_text = explanation_obj.detailed_explanation or explanation_obj.definition or "No content available"

    # Generate quiz questions using AI (mocked here)
    try:
        questions = await generate_ai_quiz(
            concept_name=assignment.concept.name,
            pdf_text=pdf_text,
            mastery_score=mastery_score,
            question_count=10  # As requested
        )
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to generate AI quiz: {str(e)}")

    return {
        "assignment_id": assignment_id,
        "assignment_title": assignment.title,
        "concept_name": assignment.concept.name if assignment.concept else "General Programming",
        "difficulty": "adaptive",
        "mastery_score": mastery_score,
        "questions": questions
    }

@router.post("/assignments/{assignment_id}/quiz/submit", response_model=Dict[str, Any])
async def submit_quiz_answers(
    assignment_id: int,
    submission: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    """
    Submit quiz answers and calculate score.
    """
    student_id = current_user.id
    
    try:
        # Extract data from submission
        questions = submission.get("questions", [])
        user_answers = submission.get("answers", [])

        if not questions or not user_answers:
            error_msg = "Invalid submission format. 'questions' and 'answers' are required."
            raise HTTPException(status_code=400, detail=error_msg)

        # Check if assignment exists and is assigned to student
        student_assignment = db.query(models.StudentAssignments).filter(
            models.StudentAssignments.assignment_id == assignment_id,
            models.StudentAssignments.student_id == student_id
        ).first()
        
        if not student_assignment:
            error_msg = f"Assignment {assignment_id} not found or not assigned to student {student_id}"
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )

        # Calculate score from the current submission, regardless of attempt number
        total_questions = len(questions)
        correct_answers = 0
        user_answers_map = {ans['questionIndex']: ans['answer'] for ans in user_answers}

        for i, question_data in enumerate(questions):
            user_answer = user_answers_map.get(i)
            correct_answer = question_data.get("correct_answer")

            if user_answer is not None and correct_answer is not None:
                if str(user_answer).strip().lower() == str(correct_answer).strip().lower():
                    correct_answers += 1

        score = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0

        # Check if this quiz has already been submitted and graded.
        # Only the first attempt updates the score and mastery.
        is_first_attempt = student_assignment.score is None

        if not is_first_attempt:
            return {
                "assignment_id": assignment_id,
                "score": score,
                "correct": correct_answers,
                "total": total_questions,
                "passed": score >= 70,
                "message": "Quiz re-attempted. This score is for practice and does not replace your first attempt."
            }

        # Get assignment details with concept relationship loaded
        assignment = db.query(models.Assignments).options(
            joinedload(models.Assignments.concept)
        ).filter(models.Assignments.id == assignment_id).first()
        
        if not assignment:
            error_msg = f"Assignment {assignment_id} not found in database"
            raise HTTPException(status_code=404, detail=error_msg)

        # Update the student's assignment record with the score and status
        student_assignment.score = score
        student_assignment.status = schemas.AssignmentStatus.GRADED
        student_assignment.submitted_at = datetime.utcnow()

        # Update student mastery score based on this quiz performance
        if not assignment.concept_id:
            pass
        else:
            # Get or create the mastery record
            mastery_record = db.query(models.StudentMastery).filter(
                models.StudentMastery.student_id == student_id,
                models.StudentMastery.concept_id == assignment.concept_id
            ).first()

            if mastery_record:
                # Update existing mastery using a weighted average
                old_score = mastery_record.mastery_score
                new_score = (old_score * 0.4) + (score * 0.6)  # 60% weight to new score
                mastery_record.mastery_score = min(100, new_score)
            else:
                # Create a new mastery record with the current quiz score
                new_mastery = models.StudentMastery(
                    student_id=student_id,
                    concept_id=assignment.concept_id,
                    mastery_score=float(score)
                )
                db.add(new_mastery)

        # Log engagement for the submission
        engagement_log = models.EngagementLogs(
            student_id=student_id,
            engagement_type=schemas.EngagementType.ASSIGNMENT,
            value=1,
            metadata_json=json.dumps({
                "assignment_id": assignment_id,
                "action": "quiz_submission",
                "score": score,
                "concept_id": assignment.concept_id,
                "is_first_attempt": is_first_attempt
            })
        )
        db.add(engagement_log)

        # Award XP for completing the quiz (50-100 XP based on score)
        xp_earned = 50 + int(score / 2)
        gamification.award_xp(student_id, xp_earned, db)

        # Commit all changes to the database
        db.commit()

        return {
            "assignment_id": assignment_id,
            "score": score,
            "correct": correct_answers,
            "total": total_questions,
            "passed": score >= 70,
            "message": "Quiz submitted successfully! Your mastery has been updated.",
            "mastery_updated": assignment.concept_id is not None
        }

    except Exception as e:
        db.rollback()
        error_msg = f"Error processing quiz submission: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your submission. Please try again."
        )
>>>>>>> 31d1d287acc7d6db0c326025d7fac1f9462033ea
