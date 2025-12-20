from sqlalchemy.orm import Session
from typing import List, Dict
import schemas
import models
from datetime import datetime, timedelta
import numpy as np

def detect_struggling_students(teacher_id: int, db: Session) -> List[Dict]:
    """
    Identify students who need intervention based on mastery scores or confusion index.
    """
    # Get all students taught by this teacher
    teacher_classes = db.query(models.Classes).filter(models.Classes.teacher_id == teacher_id).all()
    class_ids = [cls.id for cls in teacher_classes]
    
    if not class_ids:
        return []
    
    # Get students enrolled in these classes
    student_enrollments = db.query(models.ClassEnrollments).filter(
        models.ClassEnrollments.class_id.in_(class_ids)
    ).all()
    student_ids = [enrollment.student_id for enrollment in student_enrollments]
    
    if not student_ids:
        return []
    
    struggling_students = []
    
    for student_id in student_ids:
        # Get student's mastery records
        mastery_records = db.query(models.StudentMastery).filter(
            models.StudentMastery.student_id == student_id
        ).all()
        
        # Calculate average mastery score
        if mastery_records:
            avg_mastery = np.mean([record.mastery_score for record in mastery_records])
            
            # Flag students with low average mastery
            if avg_mastery < 60:
                student = db.query(models.Users).filter(models.Users.id == student_id).first()
                if student:
                    struggling_students.append({
                        "student_id": student_id,
                        "student_name": student.name,
                        "avg_mastery_score": round(avg_mastery, 2),
                        "reason": "Low average mastery score"
                    })
        
        # Check for recent confusion indicators in engagement logs
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_engagement_logs = db.query(models.EngagementLogs).filter(
            models.EngagementLogs.student_id == student_id,
            models.EngagementLogs.timestamp >= thirty_days_ago
        ).all()
        
        # Calculate confusion index based on engagement patterns
        if recent_engagement_logs:
            values = [log.value for log in recent_engagement_logs]
            if values:
                mean_value = np.mean(values)
                std_value = np.std(values) if len(values) > 1 else 0
                
                # High variability in engagement might indicate confusion
                if std_value > 0 and mean_value > 0:
                    cv = std_value / mean_value  # Coefficient of variation
                    if cv > 1.0:  # High variability threshold
                        student = db.query(models.Users).filter(models.Users.id == student_id).first()
                        if student:
                            # Check if student is already flagged
                            existing_entry = next((s for s in struggling_students if s["student_id"] == student_id), None)
                            if existing_entry:
                                existing_entry["reason"] += "; High engagement variability indicating confusion"
                            else:
                                struggling_students.append({
                                    "student_id": student_id,
                                    "student_name": student.name,
                                    "confusion_indicator": round(cv, 2),
                                    "reason": "High engagement variability indicating confusion"
                                })
    
    return struggling_students

def get_class_dashboard(teacher_id: int, db: Session) -> Dict:
    """
    Get class-wide dashboard with mastery, engagement, soft skills, and leaderboard data.
    """
    # Get teacher's classes
    teacher_classes = db.query(models.Classes).filter(models.Classes.teacher_id == teacher_id).all()
    class_ids = [cls.id for cls in teacher_classes]
    
    if not class_ids:
        return {
            "class_mastery_summary": {},
            "engagement_metrics": {
                "active_students": 0,
                "avg_daily_engagement": 0.0,
                "high_confusion_cases": 0
            },
            "soft_skill_summary": {},
            "leaderboard": [],
            "struggling_students": []
        }
    
    # Get students in these classes
    student_enrollments = db.query(models.ClassEnrollments).filter(
        models.ClassEnrollments.class_id.in_(class_ids)
    ).all()
    student_ids = [enrollment.student_id for enrollment in student_enrollments]
    
    # Get mastery data
    mastery_records = db.query(models.StudentMastery).filter(
        models.StudentMastery.student_id.in_(student_ids)
    ).all()
    
    # Calculate class mastery summary
    concept_mastery = {}
    for record in mastery_records:
        if record.concept_id not in concept_mastery:
            concept_mastery[record.concept_id] = {
                "concept_name": "Unknown Concept",  # Will be updated below
                "scores": []
            }
        concept_mastery[record.concept_id]["scores"].append(record.mastery_score)
    
    # Get concept names
    concept_ids = list(concept_mastery.keys())
    concepts = db.query(models.Concepts).filter(models.Concepts.id.in_(concept_ids)).all()
    for concept in concepts:
        if concept.id in concept_mastery:
            concept_mastery[concept.id]["concept_name"] = concept.name
    
    # Calculate averages
    class_mastery_summary = {}
    for concept_id, data in concept_mastery.items():
        if data["scores"]:
            class_mastery_summary[data["concept_name"]] = {
                "avg_score": round(np.mean(data["scores"]), 2),
                "min_score": round(min(data["scores"]), 2),
                "max_score": round(max(data["scores"]), 2),
                "student_count": len(data["scores"])
            }
    
    # Get engagement metrics
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    engagement_logs = db.query(models.EngagementLogs).filter(
        models.EngagementLogs.student_id.in_(student_ids),
        models.EngagementLogs.timestamp >= thirty_days_ago
    ).all()
    
    active_students = len(set(log.student_id for log in engagement_logs))
    
    # Calculate average daily engagement
    if engagement_logs:
        daily_engagement = {}
        for log in engagement_logs:
            date = log.timestamp.date()
            if date not in daily_engagement:
                daily_engagement[date] = 0
            daily_engagement[date] += log.value
        
        avg_daily_engagement = np.mean(list(daily_engagement.values())) if daily_engagement else 0.0
    else:
        avg_daily_engagement = 0.0
    
    # Count high confusion cases
    high_confusion_cases = 0
    for student_id in student_ids:
        student_logs = [log for log in engagement_logs if log.student_id == student_id]
        if student_logs:
            values = [log.value for log in student_logs]
            if values:
                mean_value = np.mean(values)
                std_value = np.std(values) if len(values) > 1 else 0
                
                if std_value > 0 and mean_value > 0:
                    cv = std_value / mean_value
                    if cv > 1.0:
                        high_confusion_cases += 1
    
    engagement_metrics = {
        "active_students": active_students,
        "avg_daily_engagement": round(avg_daily_engagement, 2),
        "high_confusion_cases": high_confusion_cases
    }
    
    # Get soft skill summary (simplified)
    soft_skill_scores = db.query(models.SoftSkillScores).filter(
        models.SoftSkillScores.student_id.in_(student_ids)
    ).all()
    
    skill_averages = {}
    for score in soft_skill_scores:
        if score.skill not in skill_averages:
            skill_averages[score.skill] = []
        skill_averages[score.skill].append(score.score)
    
    soft_skill_summary = {
        skill: round(np.mean(scores), 2) 
        for skill, scores in skill_averages.items()
    }
    
    # Generate leaderboard (simplified)
    student_xp_records = db.query(models.StudentXP).filter(
        models.StudentXP.student_id.in_(student_ids)
    ).all()
    
    leaderboard = []
    for record in student_xp_records:
        student = db.query(models.Users).filter(models.Users.id == record.student_id).first()
        if student:
            leaderboard.append({
                "student_id": record.student_id,
                "student_name": student.name,
                "total_xp": record.total_xp,
                "rank": 0  # Will be set below
            })
    
    # Sort by XP and assign ranks
    leaderboard.sort(key=lambda x: x["total_xp"], reverse=True)
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
    
    # Get struggling students
    struggling_students = detect_struggling_students(teacher_id, db)
    
    dashboard = {
        "class_mastery_summary": class_mastery_summary,
        "engagement_metrics": engagement_metrics,
        "soft_skill_summary": soft_skill_summary,
        "leaderboard": leaderboard[:10],  # Top 10 students
        "struggling_students": struggling_students
    }
    
    return dashboard

def get_detailed_student_insights(student_id: int, db: Session) -> Dict:
    """
    Get detailed insights for a specific student.
    """
    # Get student info
    student = db.query(models.Users).filter(models.Users.id == student_id).first()
    if not student:
        return {}
    
    # Get mastery records
    mastery_records = db.query(models.StudentMastery).filter(
        models.StudentMastery.student_id == student_id
    ).all()
    
    # Get engagement logs from last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    engagement_logs = db.query(models.EngagementLogs).filter(
        models.EngagementLogs.student_id == student_id,
        models.EngagementLogs.timestamp >= thirty_days_ago
    ).all()
    
    # Get assignments
    assignments = db.query(models.StudentAssignments).filter(
        models.StudentAssignments.student_id == student_id
    ).all()
    
    # Calculate insights
    total_assignments = len(assignments)
    completed_assignments = len([a for a in assignments if a.status == schemas.AssignmentStatus.SUBMITTED])
    graded_assignments = [a for a in assignments if a.score is not None]
    
    avg_score = np.mean([a.score for a in graded_assignments]) if graded_assignments else 0
    
    # Engagement metrics
    total_engagement_time = sum([log.value for log in engagement_logs])
    avg_daily_engagement = total_engagement_time / 30 if total_engagement_time > 0 else 0
    
    # Identify strengths and weaknesses
    strengths = []
    weaknesses = []
    
    for record in mastery_records:
        concept = db.query(models.Concepts).filter(models.Concepts.id == record.concept_id).first()
        if concept:
            if record.mastery_score >= 80:
                strengths.append({
                    "concept": concept.name,
                    "mastery_score": record.mastery_score
                })
            elif record.mastery_score < 60:
                weaknesses.append({
                    "concept": concept.name,
                    "mastery_score": record.mastery_score
                })
    
    return {
        "student_id": student_id,
        "student_name": student.name,
        "email": student.email,
        "total_assignments": total_assignments,
        "completed_assignments": completed_assignments,
        "completion_rate": round((completed_assignments / total_assignments * 100) if total_assignments > 0 else 0, 2),
        "avg_score": round(avg_score, 2),
        "total_engagement_minutes": round(total_engagement_time, 2),
        "avg_daily_engagement_minutes": round(avg_daily_engagement, 2),
        "strengths": strengths[:5],  # Top 5 strengths
        "weaknesses": weaknesses[:5],  # Top 5 weaknesses
        "recent_engagement_trend": "increasing" if avg_daily_engagement > 0 else "stable"
    }

def get_class_performance_analytics(teacher_id: int, db: Session) -> Dict:
    """
    Get comprehensive analytics for all classes taught by the teacher.
    """
    # Get teacher's classes
    teacher_classes = db.query(models.Classes).filter(models.Classes.teacher_id == teacher_id).all()
    class_ids = [cls.id for cls in teacher_classes]
    
    if not class_ids:
        return {}
    
    # Get students in these classes
    student_enrollments = db.query(models.ClassEnrollments).filter(
        models.ClassEnrollments.class_id.in_(class_ids)
    ).all()
    student_ids = [enrollment.student_id for enrollment in student_enrollments]
    
    # Get mastery data
    mastery_records = db.query(models.StudentMastery).filter(
        models.StudentMastery.student_id.in_(student_ids)
    ).all()
    
    # Calculate concept analytics
    concept_data = {}
    for record in mastery_records:
        concept = db.query(models.Concepts).filter(models.Concepts.id == record.concept_id).first()
        if concept:
            if concept.id not in concept_data:
                concept_data[concept.id] = {
                    "concept_name": concept.name,
                    "mastery_scores": []
                }
            concept_data[concept.id]["mastery_scores"].append(record.mastery_score)
    
    # Calculate statistics
    analytics = {}
    for concept_id, data in concept_data.items():
        scores = data["mastery_scores"]
        if scores:
            analytics[data["concept_name"]] = {
                "avg_mastery": round(sum(scores) / len(scores), 2),
                "min_mastery": round(min(scores), 2),
                "max_mastery": round(max(scores), 2),
                "student_count": len(scores),
                "mastery_distribution": {
                    "beginner": len([s for s in scores if s < 60]),
                    "intermediate": len([s for s in scores if 60 <= s < 80]),
                    "advanced": len([s for s in scores if s >= 80])
                }
            }
    
    return analytics

def get_student_engagement_trends(teacher_id: int, db: Session, days: int = 30) -> Dict:
    """
    Get student engagement trends over time.
    """
    # Get teacher's classes
    teacher_classes = db.query(models.Classes).filter(models.Classes.teacher_id == teacher_id).all()
    class_ids = [cls.id for cls in teacher_classes]
    
    if not class_ids:
        return {}
    
    # Get students in these classes
    student_enrollments = db.query(models.ClassEnrollments).filter(
        models.ClassEnrollments.class_id.in_(class_ids)
    ).all()
    student_ids = [enrollment.student_id for enrollment in student_enrollments]
    
    # Get engagement logs from specified number of days
    since_date = datetime.utcnow() - timedelta(days=days)
    engagement_logs = db.query(models.EngagementLogs).filter(
        models.EngagementLogs.student_id.in_(student_ids),
        models.EngagementLogs.timestamp >= since_date
    ).all()
    
    # Group by date
    daily_engagement = {}
    for log in engagement_logs:
        date_str = log.timestamp.strftime("%Y-%m-%d")
        if date_str not in daily_engagement:
            daily_engagement[date_str] = 0
        daily_engagement[date_str] += log.value
    
    # Sort by date
    sorted_dates = sorted(daily_engagement.keys())
    trend_data = {
        "dates": sorted_dates,
        "engagement_values": [daily_engagement[date] for date in sorted_dates]
    }
    
    return trend_data

def get_class_intervention_summary(teacher_id: int, db: Session) -> Dict:
    """
    Get summary of interventions performed by the teacher.
    """
    # Get all interventions by this teacher
    interventions = db.query(models.TeacherInterventions).filter(
        models.TeacherInterventions.teacher_id == teacher_id
    ).all()
    
    # Group by concept
    concept_interventions = {}
    for intervention in interventions:
        concept_name = "General"  # Default
        if intervention.concept_id:
            concept = db.query(models.Concepts).filter(models.Concepts.id == intervention.concept_id).first()
            if concept:
                concept_name = concept.name
        
        if concept_name not in concept_interventions:
            concept_interventions[concept_name] = 0
        concept_interventions[concept_name] += 1
    
    # Get recent interventions (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_interventions = db.query(models.TeacherInterventions).filter(
        models.TeacherInterventions.teacher_id == teacher_id,
        models.TeacherInterventions.timestamp >= seven_days_ago
    ).count()
    
    return {
        "total_interventions": len(interventions),
        "recent_interventions": recent_interventions,
        "interventions_by_concept": concept_interventions
    }