from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from services import teacher_interventions
from database import get_db
from auth_utils import get_current_teacher
import models
import schemas

router = APIRouter(tags=["Teacher Dashboard"])

@router.get("/class-overview")
async def get_class_dashboard(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    """
    Get comprehensive class dashboard with mastery, engagement, and performance metrics.
    
    Returns:
        Dict containing class dashboard data
    """
    try:
        dashboard_data = teacher_interventions.get_class_dashboard(current_user.id, db)
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard data: {str(e)}")

@router.get("/struggling-students")
async def get_struggling_students(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    """
    Get list of students who need intervention.
    
    Returns:
        List of struggling students with details
    """
    try:
        struggling_students = teacher_interventions.detect_struggling_students(current_user.id, db)
        return struggling_students
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving struggling students: {str(e)}")

@router.get("/student-insights/{student_id}")
async def get_student_insights(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    """
    Get detailed insights for a specific student.
    
    Args:
        student_id: ID of the student to get insights for
        
    Returns:
        Detailed insights for the student
    """
    try:
        # Verify the student is in one of the teacher's classes
        teacher_classes = db.query(models.Classes).filter(models.Classes.teacher_id == current_user.id).all()
        class_ids = [cls.id for cls in teacher_classes]
        
        if not class_ids:
            raise HTTPException(status_code=403, detail="No classes found for this teacher")
        
        student_enrolled = db.query(models.ClassEnrollments).filter(
            models.ClassEnrollments.class_id.in_(class_ids),
            models.ClassEnrollments.student_id == student_id
        ).first()
        
        if not student_enrolled:
            raise HTTPException(status_code=403, detail="Student not enrolled in any of your classes")
        
        insights = teacher_interventions.get_detailed_student_insights(student_id, db)
        return insights
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving student insights: {str(e)}")

@router.get("/concept-analytics")
async def get_concept_analytics(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    """
    Get analytics on concept mastery across all classes.
    
    Returns:
        Dict with concept mastery analytics
    """
    try:
        analytics = teacher_interventions.get_class_performance_analytics(current_user.id, db)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving concept analytics: {str(e)}")

@router.get("/engagement-trends")
async def get_engagement_trends(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    """
    Get student engagement trends over time.
    
    Args:
        days: Number of days to analyze (default: 30)
        
    Returns:
        Dict with engagement trend data
    """
    try:
        trends = teacher_interventions.get_student_engagement_trends(current_user.id, db, days)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving engagement trends: {str(e)}")

@router.get("/intervention-summary")
async def get_intervention_summary(
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    """
    Get summary of interventions performed by the teacher.
    
    Returns:
        Dict with intervention summary data
    """
    try:
        summary = teacher_interventions.get_class_intervention_summary(current_user.id, db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving intervention summary: {str(e)}")