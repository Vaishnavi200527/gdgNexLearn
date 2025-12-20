import numpy as np
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import schemas
import models
from datetime import datetime, timedelta

class BayesianKnowledgeTracer:
    def __init__(self, init_prior=0.5, learn_rate=0.3, guess_rate=0.1, slip_rate=0.1):
        self.init_prior = init_prior
        self.learn_rate = learn_rate
        self.guess_rate = guess_rate
        self.slip_rate = slip_rate
    
    def update_mastery(self, prev_mastery, correctness):
        """
        Update mastery probability using Bayesian Knowledge Tracing
        """
        # Probability of getting question right given knowledge
        p_correct_given_knowledge = 1 - self.slip_rate
        
        # Probability of getting question right given no knowledge
        p_correct_given_no_knowledge = self.guess_rate
        
        # Update using Bayes' theorem
        if correctness:
            # Correct answer
            numerator = prev_mastery * p_correct_given_knowledge
            denominator = (prev_mastery * p_correct_given_knowledge) + ((1 - prev_mastery) * p_correct_given_no_knowledge)
        else:
            # Incorrect answer
            numerator = prev_mastery * (1 - p_correct_given_knowledge)
            denominator = (prev_mastery * (1 - p_correct_given_knowledge)) + ((1 - prev_mastery) * (1 - p_correct_given_no_knowledge))
        
        if denominator == 0:
            return prev_mastery
            
        new_mastery = numerator / denominator
        # Apply learning rate
        new_mastery = min(1.0, new_mastery + self.learn_rate * (1 - new_mastery))
        
        return new_mastery

# Initialize BKT model
bkt_model = BayesianKnowledgeTracer()

def get_adaptive_assignments(student_id: int, db: Session) -> List[schemas.AdaptiveAssignmentResponse]:
    """
    Get adaptive assignments based on student's mastery levels using BKT model.
    Returns empty list for students who haven't completed any assignments yet.
    """
    # Get student's current mastery levels
    mastery_records = db.query(models.StudentMastery).filter(
        models.StudentMastery.student_id == student_id
    ).all()
    
    # For students who haven't completed any assignments, return empty list
    if not mastery_records:
        return []
    
    # For students with existing mastery records, return assignments based on lowest mastery concepts
    assignments = []
    
    # Sort by mastery score to find weakest concepts
    sorted_mastery = sorted(mastery_records, key=lambda x: x.mastery_score)
    weakest_concept = sorted_mastery[0] if sorted_mastery else None
    
    if weakest_concept and weakest_concept.mastery_score < 70:
        # Focus on weak areas
        assignments = [
            schemas.AdaptiveAssignmentResponse(
                assignment_id=weakest_concept.concept_id * 10 + 1,
                title=f"Reinforcement: {weakest_concept.concept.name}",
                description=f"Additional practice for {weakest_concept.concept.name}",
                difficulty_level=max(1, int(weakest_concept.mastery_score / 20)),
                estimated_time=30
            )
        ]
    else:
        # Advance to next level
        assignments = [
            schemas.AdaptiveAssignmentResponse(
                assignment_id=2,
                title="Intermediate Challenge",
                description="Apply your knowledge in new contexts",
                difficulty_level=3,
                estimated_time=45
            )
        ]
    
    return assignments

def update_mastery_score(student_id: int, concept_id: int, score: float, db: Session):
    """
    Update student's mastery score for a concept after assignment submission using BKT.
    """
    # Get current mastery record
    mastery_record = db.query(models.StudentMastery).filter(
        models.StudentMastery.student_id == student_id,
        models.StudentMastery.concept_id == concept_id
    ).first()
    
    # Convert percentage score to correctness (1 if >= 70%, 0 otherwise)
    correctness = 1 if score >= 70 else 0
    
    if mastery_record:
        # Update existing mastery using BKT
        prev_mastery = mastery_record.mastery_score / 100.0
        new_mastery = bkt_model.update_mastery(prev_mastery, correctness)
        mastery_record.mastery_score = new_mastery * 100
    else:
        # Create new mastery record
        initial_mastery = 0.5 if correctness else 0.2
        new_mastery = bkt_model.update_mastery(initial_mastery, correctness)
        mastery_record = models.StudentMastery(
            student_id=student_id,
            concept_id=concept_id,
            mastery_score=new_mastery * 100
        )
        db.add(mastery_record)
    
    db.commit()
    print(f"Updated mastery for student {student_id} in concept {concept_id} to {new_mastery * 100:.2f}%")

def recommend_learning_path(student_id: int, db: Session) -> List[dict]:
    """
    Recommend a personalized learning path based on student's mastery levels and goals.
    """
    # Get student's current mastery levels
    mastery_records = db.query(models.StudentMastery).filter(
        models.StudentMastery.student_id == student_id
    ).all()
    
    # Get student's concept progress
    progress_records = db.query(models.ConceptProgress).filter(
        models.ConceptProgress.student_id == student_id
    ).all()
    
    # Get all concepts
    all_concepts = db.query(models.Concepts).all()
    
    # Build recommendation
    recommendations = []
    
    if not mastery_records:
        # New student - recommend foundational concepts
        foundational_concepts = [c for c in all_concepts if "basic" in c.name.lower() or "intro" in c.name.lower()]
        if not foundational_concepts:
            foundational_concepts = all_concepts[:3]  # First 3 concepts as fallback
        
        for concept in foundational_concepts:
            recommendations.append({
                "concept_id": concept.id,
                "concept_name": concept.name,
                "reason": "Foundational skill for beginners",
                "priority": "high",
                "estimated_time": 60
            })
    else:
        # Existing student - analyze gaps and suggest next steps
        # 1. Find weak areas (mastery < 70%)
        weak_areas = [m for m in mastery_records if m.mastery_score < 70]
        
        for mastery in weak_areas:
            concept = next((c for c in all_concepts if c.id == mastery.concept_id), None)
            if concept:
                recommendations.append({
                    "concept_id": concept.id,
                    "concept_name": concept.name,
                    "reason": f"Reinforce weak area (current mastery: {mastery.mastery_score:.1f}%)",
                    "priority": "high",
                    "estimated_time": 90
                })
        
        # 2. Find next concepts to learn (prerequisites met)
        mastered_concepts = [m for m in mastery_records if m.mastery_score >= 70]
        mastered_concept_ids = [m.concept_id for m in mastered_concepts]
        
        # Simple prerequisite logic (in a real system, this would be more complex)
        for concept in all_concepts:
            if concept.id not in mastered_concept_ids and concept.id not in [r["concept_id"] for r in recommendations]:
                # Check if prerequisites are met (simplified)
                # In a real system, you'd have a prerequisites table
                prereq_met = True  # Simplified for demo
                
                if prereq_met:
                    recommendations.append({
                        "concept_id": concept.id,
                        "concept_name": concept.name,
                        "reason": "Next logical concept to learn",
                        "priority": "medium",
                        "estimated_time": 120
                    })
        
        # 3. Advanced topics for highly mastered concepts
        advanced_concepts = [m for m in mastery_records if m.mastery_score >= 90]
        
        for mastery in advanced_concepts:
            # Suggest related advanced topics
            related_advanced = [c for c in all_concepts 
                              if c.id != mastery.concept_id and 
                                 c.name.lower().find(mastery.concept.name.lower()[:4]) != -1]
            
            for concept in related_advanced[:2]:  # Max 2 related advanced topics
                if concept.id not in [r["concept_id"] for r in recommendations]:
                    recommendations.append({
                        "concept_id": concept.id,
                        "concept_name": concept.name,
                        "reason": f"Advanced extension of mastered concept ({mastery.mastery_score:.1f}% mastery)",
                        "priority": "low",
                        "estimated_time": 150
                    })
    
    # Sort by priority (high first) then by estimated time
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda x: (priority_order[x["priority"]], x["estimated_time"]))
    
    return recommendations

def get_student_learning_profile(student_id: int, db: Session) -> Dict[str, Any]:
    """
    Build a comprehensive learning profile for a student based on their interactions and performance.
    """
    # Get student's mastery records
    mastery_records = db.query(models.StudentMastery).filter(
        models.StudentMastery.student_id == student_id
    ).all()
    
    # Get student's engagement logs from the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    engagement_logs = db.query(models.EngagementLogs).filter(
        models.EngagementLogs.student_id == student_id,
        models.EngagementLogs.timestamp >= thirty_days_ago
    ).all()
    
    # Get student's assignment submissions
    assignment_submissions = db.query(models.StudentAssignments).filter(
        models.StudentAssignments.student_id == student_id
    ).all()
    
    # Calculate learning metrics
    total_assignments = len(assignment_submissions)
    completed_assignments = len([s for s in assignment_submissions if s.status == schemas.AssignmentStatus.SUBMITTED])
    graded_assignments = [s for s in assignment_submissions if s.score is not None]
    
    avg_score = np.mean([s.score for s in graded_assignments]) if graded_assignments else 0
    completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
    
    # Calculate engagement metrics
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
    
    # Determine learning pace
    if avg_daily_engagement > 120:  # More than 2 hours per day
        learning_pace = "fast"
    elif avg_daily_engagement > 60:  # 1-2 hours per day
        learning_pace = "moderate"
    else:
        learning_pace = "slow"
    
    # Determine preferred difficulty level based on performance
    if avg_score >= 85:
        preferred_difficulty = "advanced"
    elif avg_score >= 70:
        preferred_difficulty = "intermediate"
    else:
        preferred_difficulty = "beginner"
    
    return {
        "student_id": student_id,
        "learning_pace": learning_pace,
        "preferred_difficulty": preferred_difficulty,
        "avg_score": round(avg_score, 2),
        "completion_rate": round(completion_rate, 2),
        "total_engagement_minutes": round(total_engagement_time, 2),
        "avg_daily_engagement_minutes": round(avg_daily_engagement, 2),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "total_assignments": total_assignments,
        "completed_assignments": completed_assignments
    }

def adjust_content_difficulty(student_id: int, db: Session) -> Dict[str, Any]:
    """
    Adjust content difficulty based on student's learning profile and recent performance.
    """
    # Get student's learning profile
    profile = get_student_learning_profile(student_id, db)
    
    # Get recent assignment scores (last 5 assignments)
    recent_assignments = db.query(models.StudentAssignments).filter(
        models.StudentAssignments.student_id == student_id,
        models.StudentAssignments.score.isnot(None)
    ).order_by(models.StudentAssignments.submitted_at.desc()).limit(5).all()
    
    # Calculate recent performance trend
    if len(recent_assignments) >= 2:
        recent_scores = [a.score for a in recent_assignments]
        trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]  # Slope of trend line
        
        if trend > 5:  # Improving significantly
            difficulty_adjustment = "increase"
        elif trend < -5:  # Declining significantly
            difficulty_adjustment = "decrease"
        else:
            difficulty_adjustment = "maintain"
    else:
        difficulty_adjustment = "maintain"
    
    # Adjust based on overall performance
    if profile["avg_score"] >= 90 and difficulty_adjustment == "maintain":
        difficulty_adjustment = "increase"
    elif profile["avg_score"] <= 60 and difficulty_adjustment == "maintain":
        difficulty_adjustment = "decrease"
    
    return {
        "student_id": student_id,
        "current_difficulty": profile["preferred_difficulty"],
        "recommended_adjustment": difficulty_adjustment,
        "reasoning": f"Based on average score of {profile['avg_score']}% and recent performance trend"
    }

def analyze_learning_speed(student_id: int, db: Session) -> Dict[str, Any]:
    """
    Analyze student's learning speed based on engagement patterns and mastery progression.
    """
    # Get engagement logs from the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    engagement_logs = db.query(models.EngagementLogs).filter(
        models.EngagementLogs.student_id == student_id,
        models.EngagementLogs.timestamp >= thirty_days_ago
    ).all()
    
    # Get mastery records with timestamps
    mastery_records = db.query(models.StudentMastery).filter(
        models.StudentMastery.student_id == student_id
    ).all()
    
    # Calculate learning speed metrics
    total_engagement_time = sum([log.value for log in engagement_logs])
    avg_daily_engagement = total_engagement_time / 30 if total_engagement_time > 0 else 0
    
    # Calculate mastery progression rate
    if len(mastery_records) >= 2:
        # Sort by concept_id to get a progression (simplified)
        sorted_records = sorted(mastery_records, key=lambda x: x.concept_id)
        mastery_scores = [record.mastery_score for record in sorted_records]
        
        if len(mastery_scores) >= 2:
            # Calculate average improvement per concept
            improvements = [mastery_scores[i] - mastery_scores[i-1] for i in range(1, len(mastery_scores))]
            avg_improvement = np.mean(improvements) if improvements else 0
            
            # Determine learning speed category
            if avg_improvement > 10:  # Rapid improvement
                learning_speed = "rapid"
            elif avg_improvement > 5:  # Fast improvement
                learning_speed = "fast"
            elif avg_improvement > 0:  # Moderate improvement
                learning_speed = "moderate"
            else:  # Slow or no improvement
                learning_speed = "slow"
        else:
            learning_speed = "undetermined"
    else:
        learning_speed = "undetermined"
    
    # Determine content pacing recommendation
    if learning_speed == "rapid":
        pacing_recommendation = "accelerate"
    elif learning_speed == "slow":
        pacing_recommendation = "decelerate"
    else:
        pacing_recommendation = "maintain"
    
    return {
        "student_id": student_id,
        "learning_speed": learning_speed,
        "avg_daily_engagement_minutes": round(avg_daily_engagement, 2),
        "mastery_progression_rate": round(avg_improvement, 2) if 'avg_improvement' in locals() else 0,
        "pacing_recommendation": pacing_recommendation,
        "analysis_timestamp": datetime.utcnow().isoformat()
    }

def adjust_content_pacing(student_id: int, db: Session) -> Dict[str, Any]:
    """
    Dynamically adjust content pacing based on student's learning speed analysis.
    """
    # Analyze learning speed
    speed_analysis = analyze_learning_speed(student_id, db)
    
    # Get student's learning profile
    profile = get_student_learning_profile(student_id, db)
    
    # Determine pacing adjustment
    if speed_analysis["pacing_recommendation"] == "accelerate":
        pacing_factor = 1.5  # Increase pace by 50%
        content_density = "high"
    elif speed_analysis["pacing_recommendation"] == "decelerate":
        pacing_factor = 0.7  # Decrease pace by 30%
        content_density = "low"
    else:
        pacing_factor = 1.0  # Maintain current pace
        content_density = "medium"
    
    # Adjust estimated time for assignments based on pacing factor
    # Get current assignments for the student
    student_assignments = db.query(models.StudentAssignments).filter(
        models.StudentAssignments.student_id == student_id
    ).all()
    
    adjusted_assignments = []
    for sa in student_assignments:
        assignment = db.query(models.Assignments).filter(models.Assignments.id == sa.assignment_id).first()
        if assignment:
            adjusted_time = int(30 * pacing_factor)  # Base time adjusted by pacing factor
            adjusted_assignments.append({
                "assignment_id": assignment.id,
                "title": assignment.title,
                "original_estimated_time": 30,
                "adjusted_estimated_time": adjusted_time,
                "pacing_factor": pacing_factor
            })
    
    return {
        "student_id": student_id,
        "learning_speed": speed_analysis["learning_speed"],
        "pacing_recommendation": speed_analysis["pacing_recommendation"],
        "content_density": content_density,
        "pacing_factor": pacing_factor,
        "adjusted_assignments": adjusted_assignments,
        "reasoning": f"Based on {speed_analysis['learning_speed']} learning speed and {profile['learning_pace']} engagement pace"
    }