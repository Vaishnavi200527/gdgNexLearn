import numpy as np
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import schemas
import models
from datetime import datetime, timedelta
from services import ai_content_generation

class ContinuousAssessmentService:
    def __init__(self, db: Session):
        self.db = db
    
    def generate_understanding_checks(self, concept_id: int, student_id: int) -> List[Dict[str, Any]]:
        """
        Generate micro-assessments to check student understanding after concept delivery.
        """
        # Get concept information
        concept = self.db.query(models.Concepts).filter(models.Concepts.id == concept_id).first()
        if not concept:
            return []
        
        # Prepare concept data for AI generation
        concept_data = {
            "concept": concept.name,
            "definition": concept.description,
            "key_points": [],  # Would be populated from PDF extraction in a full implementation
            "prerequisites": [],
            "difficulty": "medium"
        }
        
        # Generate micro-questions using AI
        try:
            questions = ai_content_generation.generate_micro_questions(concept_data)
            return [
                {
                    "question_id": f"check_{concept_id}_{i}",
                    "question_text": questions["mcq"]["question"],
                    "options": questions["mcq"]["options"],
                    "correct_answer": questions["mcq"]["answer"],
                    "question_type": "multiple_choice"
                },
                {
                    "question_id": f"check_{concept_id}_{i+1}",
                    "question_text": questions["fill_blank"]["question"],
                    "correct_answer": questions["fill_blank"]["answer"],
                    "question_type": "fill_in_blank"
                }
            ]
        except Exception as e:
            print(f"Error generating understanding checks: {e}")
            # Fallback to template-based questions
            return self._generate_template_questions(concept)
    
    def _generate_template_questions(self, concept: models.Concepts) -> List[Dict[str, Any]]:
        """
        Generate template-based questions when AI generation fails.
        """
        return [
            {
                "question_id": f"check_{concept.id}_1",
                "question_text": f"What is the main idea of {concept.name}?",
                "options": [f"Main idea of {concept.name}", "Irrelevant concept", "Opposite concept", "Partial concept"],
                "correct_answer": f"Main idea of {concept.name}",
                "question_type": "multiple_choice"
            },
            {
                "question_id": f"check_{concept.id}_2",
                "question_text": f"The key principle of {concept.name} is _____.",
                "correct_answer": f"key principle of {concept.name}",
                "question_type": "fill_in_blank"
            }
        ]
    
    def evaluate_understanding_check(self, student_id: int, question_id: str, student_answer: str) -> Dict[str, Any]:
        """
        Evaluate student's response to an understanding check.
        """
        # Extract concept_id from question_id
        try:
            concept_id = int(question_id.split('_')[1])
        except (IndexError, ValueError):
            return {"error": "Invalid question ID"}
        
        # Get the question details (in a real implementation, this would be stored in the database)
        concept = self.db.query(models.Concepts).filter(models.Concepts.id == concept_id).first()
        if not concept:
            return {"error": "Concept not found"}
        
        # For demonstration, we'll assume the correct answer is stored somewhere
        # In a real implementation, this would be retrieved from the database
        correct_answer = f"correct answer for {concept.name}"  # Placeholder
        
        # Simple string matching for evaluation
        is_correct = student_answer.lower().strip() == correct_answer.lower().strip()
        confidence = "high" if is_correct else "low"
        
        # Store the result in the database
        assessment_result = models.EngagementLogs(
            student_id=student_id,
            engagement_type=schemas.EngagementType.ASSIGNMENT,  # Using ASSIGNMENT type for understanding checks
            value=1 if is_correct else 0,
            metadata_json=f'{{"question_id": "{question_id}", "concept_id": {concept_id}, "correct": {is_correct}}}'
        )
        self.db.add(assessment_result)
        self.db.commit()
        
        return {
            "is_correct": is_correct,
            "confidence": confidence,
            "feedback": "Good job!" if is_correct else f"Try reviewing the concept of {concept.name}."
        }
    
    def adapt_content_based_on_responses(self, student_id: int, concept_id: int, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Adapt content delivery based on student responses to understanding checks.
        """
        # Calculate accuracy
        correct_count = sum(1 for r in responses if r.get("is_correct", False))
        total_count = len(responses)
        accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
        
        # Determine next steps based on accuracy
        if accuracy >= 80:
            # Student understands the concept well, move to next concept
            next_step = "advance"
            explanation_type = "compact"
        elif accuracy >= 60:
            # Student has moderate understanding, provide standard explanation
            next_step = "review"
            explanation_type = "standard"
        else:
            # Student is struggling, provide simplified explanation
            next_step = "reteach"
            explanation_type = "simple"
        
        return {
            "student_id": student_id,
            "concept_id": concept_id,
            "accuracy": accuracy,
            "next_step": next_step,
            "recommended_explanation_type": explanation_type,
            "feedback": self._generate_feedback_message(accuracy, next_step)
        }
    
    def _generate_feedback_message(self, accuracy: float, next_step: str) -> str:
        """
        Generate a feedback message based on student performance.
        """
        if accuracy >= 80:
            return "Great job! You have a strong understanding of this concept."
        elif accuracy >= 60:
            return "Good effort! Let's review a few key points to strengthen your understanding."
        else:
            return "It looks like you're having some trouble with this concept. Let's go through it again with a simpler explanation."

def get_continuous_assessment_service(db: Session) -> ContinuousAssessmentService:
    """
    Factory function to create a ContinuousAssessmentService instance.
    """
    return ContinuousAssessmentService(db)