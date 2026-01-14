from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from typing import List, Dict, Any, Optional

import schemas, models
from database import get_db
from auth_utils import get_current_user

# For social sharing
import urllib.parse
import os
from jinja2 import Environment, FileSystemLoader

router = APIRouter(
    prefix="/api/quizzes",
    tags=["quizzes"],
)

@router.post("/", response_model=schemas.QuizResponse)
def create_quiz(
    quiz: schemas.QuizCreate,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_user),
):
    if current_user.role != models.UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Only teachers can create quizzes")

    db_quiz = models.Quiz(
        title=quiz.title,
        description=quiz.description,
        teacher_id=current_user.id,
    )
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)

    for question in quiz.questions:
        db_question = models.QuizQuestion(
            quiz_id=db_quiz.id,
            question_text=question.question_text,
            options=question.options,
            correct_answer=question.correct_answer,
        )
        db.add(db_question)
    
    db.commit()
    db.refresh(db_quiz)

    return db_quiz

@router.post("/assign", status_code=status.HTTP_201_CREATED)
def assign_quiz_to_classes(
    assignment: schemas.ClassQuizCreate,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_user),
):
    if current_user.role != models.UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Only teachers can assign quizzes")

    # 1. Verify the quiz exists
    db_quiz = db.query(models.Quiz).filter(models.Quiz.id == assignment.quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # 2. Verify the class exists
    db_class = db.query(models.Classes).filter(models.Classes.id == assignment.class_id).first()
    if not db_class:
        raise HTTPException(status_code=404, detail=f"Class with id {assignment.class_id} not found")

    # 3. Create the ClassQuiz link
    db_class_quiz = models.ClassQuizzes(
        class_id=assignment.class_id,
        quiz_id=assignment.quiz_id,
        due_date=assignment.due_date
    )
    db.add(db_class_quiz)
    
    # 4. Get all students in the class
    enrollments = db.query(models.ClassEnrollments).filter(models.ClassEnrollments.class_id == assignment.class_id).all()
    student_ids = [enrollment.student_id for enrollment in enrollments]

    # 5. Create a StudentQuiz entry for each student
    for student_id in student_ids:
        db_student_quiz = models.StudentQuizzes(
            student_id=student_id,
            quiz_id=assignment.quiz_id,
            class_id=assignment.class_id,
            status="assigned"
        )
        db.add(db_student_quiz)

    db.commit()
    
    return {"message": f"Quiz {assignment.quiz_id} assigned to class {assignment.class_id} and {len(student_ids)} students."}

@router.get("/student", response_model=List[schemas.StudentQuizResponse])
def get_student_quizzes(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_user),
):
    if current_user.role != models.UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can view their quizzes")

    student_quizzes = db.query(models.StudentQuizzes).filter(models.StudentQuizzes.student_id == current_user.id).all()
    return student_quizzes

@router.get("/{quiz_id}", response_model=schemas.QuizForStudentResponse)
def get_quiz_for_student(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_user),
):
    if current_user.role != models.UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can view quizzes")

    # Check if the student is assigned to this quiz
    student_quiz = db.query(models.StudentQuizzes).filter(
        models.StudentQuizzes.student_id == current_user.id,
        models.StudentQuizzes.quiz_id == quiz_id
    ).first()

    if not student_quiz:
        raise HTTPException(status_code=403, detail="You are not assigned to this quiz")

    db_quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return db_quiz

@router.post("/{quiz_id}/submit", response_model=schemas.StudentQuizResponse)
async def submit_quiz(
    quiz_id: int,
    submission: schemas.StudentQuizSubmission,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_user),
):
    if current_user.role != models.UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can submit quizzes")

    # Check if the student is assigned to this quiz
    student_quiz = db.query(models.StudentQuizzes).filter(
        models.StudentQuizzes.student_id == current_user.id,
        models.StudentQuizzes.quiz_id == quiz_id
    ).first()

    if not student_quiz:
        raise HTTPException(status_code=403, detail="You are not assigned to this quiz")

    if student_quiz.status == "submitted":
        raise HTTPException(status_code=400, detail="You have already submitted this quiz")

    db_quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Grade the quiz and store attempts
    score = 0
    total_questions = len(db_quiz.questions)
    concept_attempts = {}  # Track attempts per concept

    for question in db_quiz.questions:
        student_answer = submission.answers.get(str(question.id))
        is_correct = student_answer == question.correct_answer if student_answer else False

        if is_correct:
            score += 1

        # Store attempt
        attempt = models.Attempt(
            student_id=current_user.id,
            question_id=question.id,
            is_correct=is_correct
        )
        db.add(attempt)

        # Group attempts by concept
        concept_id = question.concept_id
        if concept_id not in concept_attempts:
            concept_attempts[concept_id] = []
        concept_attempts[concept_id].append(is_correct)

    percentage_score = (score / total_questions) * 100 if total_questions > 0 else 0

    # Update the student_quiz record
    student_quiz.score = percentage_score
    student_quiz.status = "submitted"
    student_quiz.submitted_at = datetime.utcnow()

    # Recalculate mastery for each concept
    for concept_id, attempts in concept_attempts.items():
        # Get all attempts for this student and concept
        all_attempts = db.query(models.Attempt).join(models.Question).filter(
            models.Attempt.student_id == current_user.id,
            models.Question.concept_id == concept_id
        ).all()

        total_correct = sum(1 for a in all_attempts if a.is_correct)
        total_attempts_count = len(all_attempts)

        # Calculate mastery score
        mastery_score = (total_correct / total_attempts_count) * 100 if total_attempts_count > 0 else 0

        # Update or create mastery record
        mastery_record = db.query(models.MasteryScores).filter(
            models.MasteryScores.student_id == current_user.id,
            models.MasteryScores.concept_id == concept_id
        ).first()

        if mastery_record:
            mastery_record.mastery_score = mastery_score
        else:
            mastery_record = models.MasteryScores(
                student_id=current_user.id,
                concept_id=concept_id,
                mastery_score=mastery_score
            )
            db.add(mastery_record)

    # Generate detailed question reviews
    question_reviews = []
    for question in db_quiz.questions:
        student_answer = submission.answers.get(str(question.id))
        is_correct = student_answer == question.correct_answer if student_answer else False

        # Get concept name and id if available
        concept_name = None
        concept_id = None
        if hasattr(question, 'concept_id') and question.concept_id:
            concept = db.query(models.Concept).filter(models.Concept.id == question.concept_id).first()
            concept_name = concept.concept_name if concept else None
            concept_id = question.concept_id

        question_reviews.append(schemas.QuestionReviewItem(
            question_id=question.id,
            question_text=question.question_text,
            student_answer=student_answer,
            correct_answer=question.correct_answer,
            is_correct=is_correct,
            explanation=None,  # Could be enhanced with AI explanations
            concept_name=concept_name,
            concept_id=concept_id
        ))

    # Generate concept review for weak areas
    concept_review = await generate_concept_review(current_user.id, quiz_id, concept_attempts, db)

    # Store the concept review and question reviews in the student quiz record
    if concept_review:
        student_quiz.concept_review = concept_review
    student_quiz.question_reviews = question_reviews

    db.commit()
    db.refresh(student_quiz)

    return student_quiz

@router.get("/{quiz_id}/submissions", response_model=List[schemas.QuizSubmissionResponse])
def get_quiz_submissions(
    quiz_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_user)
):
    """
    Get all submissions for a specific quiz.
    Teachers can see all submissions for their quizzes.
    Students can only see their own submissions.
    """
    # Check if quiz exists
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # If user is a student, they can only see their own submissions
    if current_user.role == models.UserRole.STUDENT:
        submissions = db.query(models.StudentQuizzes).filter(
            models.StudentQuizzes.quiz_id == quiz_id,
            models.StudentQuizzes.student_id == current_user.id
        ).offset(skip).limit(limit).all()
    # If user is a teacher, they can see all submissions for their quizzes
    elif current_user.role == models.UserRole.TEACHER and quiz.teacher_id == current_user.id:
        submissions = db.query(models.StudentQuizzes).filter(
            models.StudentQuizzes.quiz_id == quiz_id
        ).options(
            joinedload(models.StudentQuizzes.student)
        ).offset(skip).limit(limit).all()
    else:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to view these submissions"
        )
    
    return submissions

@router.get("/{quiz_id}/submissions/{submission_id}", response_model=schemas.QuizSubmissionDetailResponse)
def get_quiz_submission(
    quiz_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_user)
):
    """
    Get detailed information about a specific quiz submission.
    Teachers can see any submission for their quizzes.
    Students can only see their own submissions.
    """
    # Check if quiz exists
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Get the submission with related data
    submission = db.query(models.StudentQuizzes).options(
        joinedload(models.StudentQuizzes.student),
        joinedload(models.StudentQuizzes.quiz).joinedload(models.Quiz.questions)
    ).filter(
        models.StudentQuizzes.id == submission_id,
        models.StudentQuizzes.quiz_id == quiz_id
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Check permissions
    if current_user.role == models.UserRole.STUDENT and submission.student_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to view this submission"
        )
    
    if current_user.role == models.UserRole.TEACHER and quiz.teacher_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to view this submission"
        )
    
    # Get question statistics if user is a teacher
    question_stats = {}
    if current_user.role == models.UserRole.TEACHER:
        question_stats = get_question_statistics(quiz_id, db)
    
    # Add question statistics to the response
    submission.question_stats = question_stats
    
    return submission

@router.get("/{quiz_id}/submissions/{submission_id}/print")
async def get_quiz_submission_html(
    quiz_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_user)
):
    """
    Get HTML version of the quiz submission for display.
    """
    # Get the submission data
    submission = get_quiz_submission(quiz_id, submission_id, db, current_user)
    
    # Render the HTML template
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("quiz_submission.html")
    html_content = template.render(submission=submission, now=datetime.utcnow())
    
    return {"html": html_content}

@router.post("/{quiz_id}/submissions/{submission_id}/share/email")
async def share_quiz_submission_email(
    quiz_id: int,
    submission_id: int,
    email_data: schemas.ShareQuizSubmissionEmail,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_user)
):
    """
    Share quiz submission results via email.
    """
    # Get the submission data
    submission = get_quiz_submission(quiz_id, submission_id, db, current_user)
    
    # Email configuration (should be in your settings/config)
    conf = ConnectionConfig(
        MAIL_USERNAME=os.getenv("SMTP_USERNAME"),
        MAIL_PASSWORD=os.getenv("SMTP_PASSWORD"),
        MAIL_FROM=os.getenv("SMTP_FROM", "noreply@yourapp.com"),
        MAIL_PORT=int(os.getenv("SMTP_PORT", 587)),
        MAIL_SERVER=os.getenv("SMTP_SERVER"),
        MAIL_TLS=True,
        MAIL_SSL=False
    )
    
    # Render the email template
    env = Environment(loader=FileSystemLoader("templates/email"))
    template = env.get_template("quiz_results.html")
    html_content = template.render(
        submission=submission,
        message=email_data.message,
        sender_name=current_user.full_name or current_user.email
    )
    
    # Send the email
    message = MessageSchema(
        subject=f"Quiz Results: {submission.quiz.title}",
        recipients=email_data.recipient_emails,
        body=html_content,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)
    
    return {"message": "Quiz results shared successfully"}

@router.get("/{quiz_id}/submissions/{submission_id}/share/social")
async def get_social_share_links(
    quiz_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_user)
):
    """
    Get social share links for the quiz submission.
    """
    # Get the submission data
    submission = get_quiz_submission(quiz_id, submission_id, db, current_user)
    
    # Base URL for your application
    base_url = os.getenv("FRONTEND_URL", "https://yourapp.com")
    share_text = f"I scored {submission.score}% on {submission.quiz.title}!"
    
    # Generate share links for different platforms
    social_links = {
        "twitter": f"https://twitter.com/intent/tweet?text={urllib.parse.quote(share_text)}&url={base_url}/quizzes/{quiz_id}/submissions/{submission_id}",
        "facebook": f"https://www.facebook.com/sharer/sharer.php?u={base_url}/quizzes/{quiz_id}/submissions/{submission_id}&quote={urllib.parse.quote(share_text)}",
        "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={base_url}/quizzes/{quiz_id}/submissions/{submission_id}",
        "whatsapp": f"https://wa.me/?text={urllib.parse.quote(share_text + ' ' + base_url + '/quizzes/' + str(quiz_id) + '/submissions/' + str(submission_id))}",
        "email": f"mailto:?subject=My Quiz Results&body={urllib.parse.quote(share_text + '\n\nView my results: ' + base_url + '/quizzes/' + str(quiz_id) + '/submissions/' + str(submission_id))}"
    }
    
    return social_links

@router.get("/{quiz_id}/statistics", response_model=schemas.QuizStatisticsResponse)
def get_quiz_statistics(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_user)
):
    """
    Get detailed statistics for a quiz.
    Only the teacher who created the quiz can view these statistics.
    """
    # Check if quiz exists and get the quiz with related data
    quiz = db.query(models.Quiz).options(
        joinedload(models.Quiz.questions)
    ).filter(
        models.Quiz.id == quiz_id
    ).first()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Check if the current user is the teacher who created the quiz
    if quiz.teacher_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to view these statistics"
        )
    
    # Get all submissions for this quiz
    submissions = db.query(models.StudentQuizzes).filter(
        models.StudentQuizzes.quiz_id == quiz_id,
        models.StudentQuizzes.status == "submitted"
    ).all()
    
    # Calculate basic statistics
    total_submissions = len(submissions)
    average_score = sum(s.score for s in submissions) / total_submissions if total_submissions > 0 else 0
    passing_submissions = sum(1 for s in submissions if s.score >= quiz.passing_score)
    passing_rate = (passing_submissions / total_submissions) * 100 if total_submissions > 0 else 0
    
    # Get score distribution
    score_distribution = {str(i*10): 0 for i in range(11)}  # 0-100 in 10-point increments
    for submission in submissions:
        score_bucket = str((submission.score // 10) * 10)
        if score_bucket in score_distribution:
            score_distribution[score_bucket] += 1
    
    # Get question statistics
    question_stats = get_question_statistics(quiz_id, db)
    
    # Get time spent statistics
    time_spent = []
    for submission in submissions:
        if submission.started_at and submission.submitted_at:
            time_spent.append((submission.submitted_at - submission.started_at).total_seconds() / 60)  # in minutes
    
    avg_time_spent = sum(time_spent) / len(time_spent) if time_spent else 0
    
    # Get performance by question type (if applicable)
    question_type_stats = {}
    for question in quiz.questions:
        if question.question_type not in question_type_stats:
            question_type_stats[question.question_type] = {
                "total": 0,
                "correct": 0
            }
        question_type_stats[question.question_type]["total"] += 1
        if question.id in question_stats:
            question_type_stats[question.question_type]["correct"] += question_stats[question.id]["correct_attempts"]
    
    # Calculate accuracy by question type
    for q_type in question_type_stats:
        total = question_type_stats[q_type]["total"] * total_submissions
        correct = question_type_stats[q_type]["correct"]
        question_type_stats[q_type]["accuracy"] = (correct / total) * 100 if total > 0 else 0
    
    return {
        "quiz_id": quiz_id,
        "total_submissions": total_submissions,
        "average_score": average_score,
        "passing_rate": passing_rate,
        "score_distribution": score_distribution,
        "question_statistics": question_stats,
        "average_time_spent_minutes": avg_time_spent,
        "question_type_statistics": question_type_stats,
        "difficulty_analysis": {
            "easiest_questions": sorted(
                question_stats.items(),
                key=lambda x: x[1]["difficulty"],
                reverse=True
            )[:5],  # Top 5 easiest questions
            "hardest_questions": sorted(
                question_stats.items(),
                key=lambda x: x[1]["difficulty"]
            )[:5]  # Top 5 hardest questions
        }
    }

def get_question_statistics(quiz_id: int, db: Session) -> Dict[int, Dict[str, Any]]:
    """
    Helper function to get statistics for each question in a quiz.
    Returns a dictionary with question_id as key and statistics as value.
    """
    # Get all submissions for this quiz
    submissions = db.query(models.StudentQuizzes).filter(
        models.StudentQuizzes.quiz_id == quiz_id,
        models.StudentQuizzes.status == "submitted"
    ).all()
    
    # Get all questions for this quiz
    quiz = db.query(models.Quiz).options(
        joinedload(models.Quiz.questions)
    ).filter(models.Quiz.id == quiz_id).first()
    
    if not quiz:
        return {}
    
    # Initialize statistics
    question_stats = {}
    for question in quiz.questions:
        question_stats[question.id] = {
            "total_attempts": 0,
            "correct_attempts": 0,
            "incorrect_attempts": 0,
            "answer_distribution": {},
            "difficulty": 0.0,
            "discrimination_index": 0.0,
            "point_biserial": 0.0
        }
    
    # Process each submission
    for submission in submissions:
        submission_answers = submission.answers or {}
        
        for question_id, answer in submission_answers.items():
            if int(question_id) in question_stats:
                question_stats[int(question_id)]["total_attempts"] += 1
                
                # Get the correct answer for this question
                question = next((q for q in quiz.questions if q.id == int(question_id)), None)
                if question:
                    is_correct = str(answer) == str(question.correct_answer)
                    
                    if is_correct:
                        question_stats[int(question_id)]["correct_attempts"] += 1
                    else:
                        question_stats[int(question_id)]["incorrect_attempts"] += 1
                    
                    # Update answer distribution
                    answer_key = str(answer)
                    if answer_key not in question_stats[int(question_id)]["answer_distribution"]:
                        question_stats[int(question_id)]["answer_distribution"][answer_key] = 0
                    question_stats[int(question_id)]["answer_distribution"][answer_key] += 1
    
    # Calculate difficulty for each question (percentage of students who got it right)
    for question_id, stats in question_stats.items():
        if stats["total_attempts"] > 0:
            stats["difficulty"] = stats["correct_attempts"] / stats["total_attempts"]
    
    # Calculate discrimination index and point-biserial correlation
    if len(submissions) > 1:
        # Sort submissions by total score
        sorted_submissions = sorted(submissions, key=lambda x: x.score)
        
        # Get top and bottom 27% of students
        n = len(sorted_submissions)
        n_group = max(1, int(n * 0.27))  # 27% as per Kelley's criterion
        
        high_group = sorted_submissions[-n_group:]
        low_group = sorted_submissions[:n_group]
        
        # Calculate discrimination index for each question
        for question_id in question_stats:
            # Count correct answers in high and low groups
            high_correct = 0
            low_correct = 0
            
            for submission in high_group:
                submission_answers = submission.answers or {}
                answer = submission_answers.get(str(question_id))
                question = next((q for q in quiz.questions if q.id == question_id), None)
                
                if question and str(answer) == str(question.correct_answer):
                    high_correct += 1
            
            for submission in low_group:
                submission_answers = submission.answers or {}
                answer = submission_answers.get(str(question_id))
                question = next((q for q in quiz.questions if q.id == question_id), None)
                
                if question and str(answer) == str(question.correct_answer):
                    low_correct += 1
            
            # Calculate discrimination index
            question_stats[question_id]["discrimination_index"] = (high_correct - low_correct) / n_group
            
            # Calculate point-biserial correlation (simplified)
            p = question_stats[question_id]["difficulty"]
            q = 1 - p
            if p > 0 and q > 0:
                point_biserial = (high_correct - low_correct) / (n_group * (p * q) ** 0.5)
                question_stats[question_id]["point_biserial"] = point_biserial if not math.isnan(point_biserial) else 0.0
    
    return question_stats

async def generate_concept_review(student_id: int, quiz_id: int, concept_attempts: dict, db: Session) -> dict:
    """
    Generate detailed concept review for weak areas based on quiz performance.
    Provides simplified explanations, real-world examples, and structured learning content.
    """
    from services.ai_content_generation import call_gemini_api
    from services.concept_explanation_storage import ConceptExplanationStorage

    weak_concepts = []

    # Identify weak concepts (those with low performance)
    for concept_id, attempts in concept_attempts.items():
        if not attempts:
            continue

        correct_count = sum(1 for attempt in attempts if attempt)
        accuracy = correct_count / len(attempts)

        # Consider concepts weak if accuracy < 60%
        if accuracy < 0.6:
            concept = db.query(models.Concept).filter(models.Concept.id == concept_id).first()
            if concept:
                weak_concepts.append({
                    'concept_id': concept_id,
                    'concept_name': concept.concept_name,
                    'accuracy': accuracy,
                    'attempts': len(attempts)
                })

    if not weak_concepts:
        return None

    # Get quiz details for PDF extraction
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        return None

    # Try to get PDF content from class assignments
    pdf_text = ""
    try:
        # Find class assignment that has this quiz
        class_quiz = db.query(models.ClassQuizzes).filter(
            models.ClassQuizzes.quiz_id == quiz_id
        ).first()

        if class_quiz:
            # Get assignments for this class that might have PDFs
            assignments = db.query(models.Assignments).join(models.ClassAssignments).filter(
                models.ClassAssignments.class_id == class_quiz.class_id
            ).all()

            for assignment in assignments:
                if assignment.content_url and weak_concepts:
                    try:
                        pdf_text = extract_pdf_text(assignment.content_url)
                        if pdf_text:
                            break  # Use the first PDF we find
                    except Exception as e:
                        continue
    except Exception as e:
        pass

    # If no PDF text, get from concept explanations
    if not pdf_text:
        storage = ConceptExplanationStorage(db)
        for concept in weak_concepts:
            explanation_obj = db.query(models.ConceptExplanations).filter(
                models.ConceptExplanations.concept_id == concept['concept_id']
            ).first()

            if explanation_obj and explanation_obj.detailed_explanation:
                pdf_text = explanation_obj.detailed_explanation
                break

    # Generate detailed AI explanations for weak concepts
    concept_reviews = []
    for concept in weak_concepts[:3]:  # Limit to top 3 weak concepts
        try:
            mastery_score = int(concept['accuracy'] * 100)

            prompt = f"""
            You are an AI tutor helping a student review a concept they struggled with in a quiz.
            The student got {mastery_score}% accuracy on questions about "{concept['concept_name']}".

            **Context from their material:**
            {pdf_text[:2000] if pdf_text else "No specific material provided"}

            **Instructions:**
            Provide a detailed, simplified explanation to help them understand this concept better.
            Structure the response clearly with headings and use simple language.
            Include real-world examples specific to this concept.

            **Response Format (JSON only):**
            {{
              "title": "Clear heading for the concept review (e.g., 'Understanding {concept['concept_name']}')",
              "key_points": ["3-5 key points they should remember, written simply"],
              "explanation": "A clear, step-by-step explanation of the concept in simple language",
              "real_world_examples": ["2-3 specific real-world examples showing how this concept applies"],
              "common_mistakes": ["2-3 common mistakes to avoid, explained simply"],
              "practice_tip": "One specific, actionable tip for practicing this concept"
            }}
            """

            response = await call_gemini_api(prompt, expect_json=True)
            if isinstance(response, dict):
                concept_reviews.append({
                    'concept_name': concept['concept_name'],
                    'accuracy': concept['accuracy'],
                    **response
                })
            else:
                # Fallback if AI fails
                concept_reviews.append({
                    'concept_name': concept['concept_name'],
                    'accuracy': concept['accuracy'],
                    'title': f'Understanding {concept["concept_name"]}',
                    'key_points': ['Focus on understanding the core principles', 'Practice with similar examples', 'Review related concepts'],
                    'explanation': f'You had {int(concept["accuracy"]*100)}% accuracy on {concept["concept_name"]}. This concept is fundamental and needs more practice. Review the material and try similar questions.',
                    'real_world_examples': [f'In everyday life, {concept["concept_name"]} helps us make decisions about similar situations.', f'At work, understanding {concept["concept_name"]} can improve your performance in related tasks.'],
                    'common_mistakes': ['Rushing through questions without understanding', 'Not reading the question carefully', 'Missing key details in the explanation'],
                    'practice_tip': 'Try explaining this concept to someone else in simple terms'
                })

        except Exception as e:
            # Simple fallback
            concept_reviews.append({
                'concept_name': concept['concept_name'],
                'accuracy': concept['accuracy'],
                'title': f'Understanding {concept["concept_name"]}',
                'key_points': ['Review the basic principles', 'Practice with examples', 'Ask for help if needed'],
                'explanation': f'You struggled with {concept["concept_name"]} (only {int(concept["accuracy"]*100)}% correct). Take time to review this topic and practice with similar problems.',
                'real_world_examples': [f'{concept["concept_name"]} is used in many real-world situations.', f'Understanding {concept["concept_name"]} helps in making better decisions.'],
                'common_mistakes': ['Not understanding fundamentals', 'Careless errors in application'],
                'practice_tip': 'Work through additional practice problems and explain your answers'
            })

    return {
        'weak_concepts_count': len(weak_concepts),
        'weak_concepts_list': [{'name': wc['concept_name'], 'accuracy': wc['accuracy']} for wc in weak_concepts],
        'concept_reviews': concept_reviews,
        'recommendation': f"You struggled with {len(weak_concepts)} concept{'s' if len(weak_concepts) != 1 else ''}. Focus on reviewing these areas before your next quiz."
    }

def extract_pdf_text(pdf_path: str) -> str:
    """
    Extract text content from a PDF file for concept review.
    """
    try:
        import pdfplumber
        import requests
        import io
        import os

        if pdf_path.startswith("http://") or pdf_path.startswith("https://"):
            response = requests.get(pdf_path)
            response.raise_for_status()
            pdf_file = io.BytesIO(response.content)
        else:
            # It's a local file path
            full_path = os.path.join(os.path.dirname(__file__), '..', pdf_path.lstrip('/'))
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"PDF file not found at {full_path}")
            pdf_file = open(full_path, "rb")

        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages[:5]:  # Limit to first 5 pages for performance
                text += page.extract_text() + "\n"

        if not (pdf_path.startswith("http://") or pdf_path.startswith("https://")):
             pdf_file.close()

        return text.strip()
    except Exception as e:
        return ""
