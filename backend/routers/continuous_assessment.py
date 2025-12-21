from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from services.continuous_assessment import ContinuousAssessmentService, get_continuous_assessment_service
from database import get_db
from auth_utils import get_current_student
import models
import schemas

router = APIRouter(tags=["Continuous Assessment"])

@router.post("/generate-checks")
async def generate_understanding_checks(
    concept_id: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    """
    Generate understanding checks for a specific concept.
    
    Args:
        concept_id: ID of the concept to generate checks for
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of understanding check questions
    """
    try:
        service = get_continuous_assessment_service(db)
        questions = service.generate_understanding_checks(concept_id, current_user.id)
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating understanding checks: {str(e)}")

@router.post("/evaluate-response")
async def evaluate_understanding_response(
    question_id: str = Body(..., embed=True),
    student_answer: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    """
    Evaluate student's response to an understanding check.
    
    Args:
        question_id: ID of the question being answered
        student_answer: Student's answer to the question
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Evaluation result with feedback
    """
    try:
        service = get_continuous_assessment_service(db)
        result = service.evaluate_understanding_check(current_user.id, question_id, student_answer)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating response: {str(e)}")

@router.post("/adapt-content")
async def adapt_content_based_on_responses(
    concept_id: int = Body(..., embed=True),
    responses: List[Dict[str, Any]] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_student)
):
    """
    Adapt content delivery based on student responses to understanding checks.
    
    Args:
        concept_id: ID of the concept being assessed
        responses: List of student responses to understanding checks
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Adaptation recommendations for content delivery
    """
    try:
        service = get_continuous_assessment_service(db)
        adaptation = service.adapt_content_based_on_responses(current_user.id, concept_id, responses)
        return adaptation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adapting content: {str(e)}")