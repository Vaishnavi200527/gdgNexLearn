#!/usr/bin/env python3
"""
PDF Upload Router
Provides endpoints for uploading and processing PDF files for text-based learning
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import PyPDF2
import io
import json
from database import get_db
from services.pdf_processing import process_pdf_for_adaptive_learning
import models
import os
import uuid
from datetime import datetime
from auth_utils import get_current_teacher
import schemas

router = APIRouter(tags=["PDF Upload"])

STORAGE_PATH = os.path.join("storage", "assignments")
if not os.path.exists(STORAGE_PATH):
    os.makedirs(STORAGE_PATH)

@router.post("/create-adaptive-assignment")
async def create_adaptive_assignment(
    file: UploadFile = File(...),
    assignment_title: str = Form(...),
    description: str = Form(...),
    class_ids: str = Form(...), # Expecting a JSON string of a list of ints
    due_date: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_teacher)
):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files are allowed")

    # 1. Save the uploaded PDF
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(STORAGE_PATH, unique_filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    content_url = f"/storage/assignments/{unique_filename}"

    # 2. Process PDF to extract concepts
    try:
        # We need to read the file again for processing
        with open(file_path, "rb") as f:
            pdf_content = f.read()
        result = process_pdf_for_adaptive_learning(pdf_content)
        concepts_data = result.get("concepts", [])
    except Exception as e:
        raise HTTPException(500, f"PDF Processing failed: {str(e)}")

    if not concepts_data:
        raise HTTPException(400, "Could not extract any concepts from the PDF.")

    # In this simplified version, we'll create one assignment for the whole PDF
    # and link it to the first concept found.
    # A more advanced version might create multiple assignments or a new parent concept.
    
    first_concept_data = concepts_data[0]
    
    # 3. Get or create the main concept
    concept = db.query(models.Concepts).filter(
        models.Concepts.name.ilike(f"%{first_concept_data['name']}%")
    ).first()
    
    if not concept:
        concept = models.Concepts(
            name=first_concept_data['name'],
            description=first_concept_data.get('definition', '')
        )
        db.add(concept)
        db.commit()
        db.refresh(concept)
    
    # 4. Create the Assignment
    new_assignment = models.Assignments(
        title=assignment_title,
        description=description,
        content_url=content_url,
        teacher_id=current_user.id,
        concept_id=concept.id, # Link to the first extracted concept
        difficulty_level=3 # Default difficulty
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    
    # 5. Assign to classes and students
    try:
        list_of_class_ids = json.loads(class_ids)
    except json.JSONDecodeError:
        raise HTTPException(400, "class_ids must be a JSON array of integers.")

    due_date_obj = datetime.fromisoformat(due_date) if due_date else None
    
    for class_id in list_of_class_ids:
        # Check if class exists
        db_class = db.query(models.Classes).filter(models.Classes.id == class_id).first()
        if not db_class:
            # Maybe log a warning instead of raising an error
            print(f"Warning: Class with id {class_id} not found.")
            continue

        # Create ClassAssignment
        class_assignment = models.ClassAssignments(
            class_id=class_id,
            assignment_id=new_assignment.id,
            due_date=due_date_obj,
            assigned_at=datetime.utcnow()
        )
        db.add(class_assignment)

        # Get all students in the class and create StudentAssignments
        enrollments = db.query(models.ClassEnrollments).filter(models.ClassEnrollments.class_id == class_id).all()
        for enrollment in enrollments:
            student_assignment_exists = db.query(models.StudentAssignments).filter(
                models.StudentAssignments.student_id == enrollment.student_id,
                models.StudentAssignments.assignment_id == new_assignment.id
            ).first()
            if not student_assignment_exists:
                student_assignment = models.StudentAssignments(
                    student_id=enrollment.student_id,
                    assignment_id=new_assignment.id,
                    status=schemas.AssignmentStatus.ASSIGNED
                )
                db.add(student_assignment)

    db.commit()

    return {
        "message": "Assignment created and assigned successfully",
        "assignment_id": new_assignment.id,
        "content_url": content_url,
        "concepts_found": len(concepts_data)
    }


@router.post("/process-pdf")
async def process_pdf(
    file: UploadFile = File(...),
    assignment_title: str = Form(...),
    db: Session = Depends(get_db)
):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files are allowed")

    # Extract content from uploaded file
    content = await file.read()

    try:
        # Process PDF for text-based learning with detailed concept explanations
        result = process_pdf_for_adaptive_learning(content)
        
        # Extract concepts from the result
        concepts_data = result.get("concepts", [])

        # Process each concept and store in database
        processed_concepts = []
        for concept_data in concepts_data:
            # Create or update concept in database
            concept = db.query(models.Concepts).filter(
                models.Concepts.concept_name.ilike(f"%{concept_data['name']}%") |
                models.Concepts.concept_name.ilike(concept_data['name'])
            ).first()

            if not concept:
                # Create new concept with detailed information
                concept = models.Concepts(
                    concept_name=concept_data['name'],
                    description=concept_data['definition'],
                    id_slug=concept_data['name'].lower().replace(' ', '-').replace('_', '-')
                )

                db.add(concept)
                db.flush()  # Get ID without committing whole transaction
            else:
                # Update existing concept with detailed information
                concept.description = concept_data['definition']

                db.flush()

            # Create or update detailed explanation for this concept
            explanation = db.query(models.ConceptExplanations).filter(
                models.ConceptExplanations.concept_id == concept.id
            ).first()

            if not explanation:
                # Create new detailed explanation
                # Safely handle detailed_explanation field
                detailed_exp = concept_data.get('detailed_explanation', '')
                word_count = 0
                if isinstance(detailed_exp, str):
                    word_count = len(detailed_exp.split())

                explanation = models.ConceptExplanations(
                    concept_id=concept.id,
                    title=concept_data['name'],
                    definition=concept_data['definition'],
                    detailed_explanation=detailed_exp,
                    examples=concept_data.get('examples', []),
                    key_points=concept_data.get('key_points', []),
                    prerequisites=concept_data.get('prerequisites', []),
                    step_by_step_breakdown=[],  # We can add step-by-step breakdowns if needed
                    related_terms=concept_data.get('related_terms', []),
                    applications=concept_data.get('applications', []),
                    common_misconceptions=concept_data.get('misconceptions', []),
                    word_count=word_count
                )
                db.add(explanation)
            else:
                # Update existing explanation
                explanation.definition = concept_data['definition']
                explanation.detailed_explanation = concept_data.get('detailed_explanation', '')
                explanation.examples = concept_data.get('examples', [])
                explanation.key_points = concept_data.get('key_points', [])
                explanation.prerequisites = concept_data.get('prerequisites', [])
                explanation.related_terms = concept_data.get('related_terms', [])
                explanation.applications = concept_data.get('applications', [])
                explanation.common_misconceptions = concept_data.get('misconceptions', [])
                # Safely calculate word count
                detailed_exp = concept_data.get('detailed_explanation', '')
                if isinstance(detailed_exp, str):
                    explanation.word_count = len(detailed_exp.split())
                else:
                    explanation.word_count = 0

            processed_concepts.append({
                "id": concept.id,
                "name": concept.concept_name,
                "description": concept.description,
                "detailed_explanation": concept_data.get('detailed_explanation', ''),
                "key_points": concept_data.get('key_points', []),
                "prerequisites": concept_data.get('prerequisites', []),
                "related_terms": concept_data.get('related_terms', []),
                "examples": concept_data.get('examples', []),
                "applications": concept_data.get('applications', []),
                "misconceptions": concept_data.get('misconceptions', []),
                "sub_topics": concept_data.get('sub_topics', [])
            })

        db.commit()
        return {
            "assignment_title": assignment_title,
            "concepts": processed_concepts,
            "metadata": {
                "pages": result.get("metadata", {}).get("page_count", 1),
                "total_concepts": len(processed_concepts),
                "word_count": result["statistics"]["total_words"],
                "character_count": result["statistics"]["total_characters"]
            }
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"PDF Processing failed: {str(e)}")

@router.post("/process-pdf-detailed")
async def process_pdf_detailed(
    file: UploadFile = File(...),
    assignment_title: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Enhanced endpoint that returns more detailed concept explanations
    """
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files are allowed")

    # Extract content from uploaded file
    content = await file.read()

    try:
        # Process PDF for text-based learning with detailed concept explanations
        result = process_pdf_for_adaptive_learning(content)
        
        # Process concepts and store detailed explanations
        detailed_concepts = []
        for concept_data in result.get("concepts", []):
            # Create or update concept in database
            concept = db.query(models.Concepts).filter(
                models.Concepts.concept_name.ilike(f"%{concept_data['name']}%") |
                models.Concepts.concept_name.ilike(concept_data['name'])
            ).first()

            if not concept:
                # Create new concept
                concept = models.Concepts(
                    concept_name=concept_data['name'],
                    description=concept_data['definition'],
                    id_slug=concept_data['name'].lower().replace(' ', '-').replace('_', '-')
                )
                db.add(concept)
                db.flush()  # Get ID without committing whole transaction
            else:
                # Update existing concept
                concept.description = concept_data['definition']
                db.flush()

            # Create or update detailed explanation for this concept
            explanation = db.query(models.ConceptExplanations).filter(
                models.ConceptExplanations.concept_id == concept.id
            ).first()

            if not explanation:
                # Create new detailed explanation
                # Safely handle detailed_explanation field
                detailed_exp = concept_data.get('detailed_explanation', '')
                word_count = 0
                if isinstance(detailed_exp, str):
                    word_count = len(detailed_exp.split())

                explanation = models.ConceptExplanations(
                    concept_id=concept.id,
                    title=concept_data['name'],
                    definition=concept_data['definition'],
                    detailed_explanation=detailed_exp,
                    examples=concept_data.get('examples', []),
                    key_points=concept_data.get('key_points', []),
                    prerequisites=concept_data.get('prerequisites', []),
                    step_by_step_breakdown=[],  # We can add step-by-step breakdowns if needed
                    related_terms=concept_data.get('related_terms', []),
                    applications=concept_data.get('applications', []),
                    common_misconceptions=concept_data.get('misconceptions', []),
                    word_count=word_count
                )
                db.add(explanation)
            else:
                # Update existing explanation
                explanation.definition = concept_data['definition']
                explanation.detailed_explanation = concept_data.get('detailed_explanation', '')
                explanation.examples = concept_data.get('examples', [])
                explanation.key_points = concept_data.get('key_points', [])
                explanation.prerequisites = concept_data.get('prerequisites', [])
                explanation.related_terms = concept_data.get('related_terms', [])
                explanation.applications = concept_data.get('applications', [])
                explanation.common_misconceptions = concept_data.get('misconceptions', [])
                # Safely calculate word count
                detailed_exp = concept_data.get('detailed_explanation', '')
                if isinstance(detailed_exp, str):
                    explanation.word_count = len(detailed_exp.split())
                else:
                    explanation.word_count = 0

            detailed_concepts.append({
                "name": concept_data["name"],
                "definition": concept_data["definition"],
                "detailed_explanation": concept_data["detailed_explanation"],
                "examples": concept_data["examples"],
                "key_points": concept_data["key_points"],
                "prerequisites": concept_data["prerequisites"],
                "related_terms": concept_data["related_terms"],
                "applications": concept_data["applications"],
                "misconceptions": concept_data["misconceptions"],
                "sub_topics": concept_data["sub_topics"],
                "concept_id": concept.id,
                "explanation_id": explanation.id
            })

        db.commit()
        return {
            "assignment_title": assignment_title,
            "detailed_concepts": detailed_concepts,
            "text_content_preview": result["text_content"][:500] + "..." if len(result["text_content"]) > 500 else result["text_content"],
            "metadata": {
                "pages": result.get("metadata", {}).get("page_count", 1),
                "total_concepts": len(detailed_concepts),
                "word_count": result["statistics"]["total_words"],
                "character_count": result["statistics"]["total_characters"]
            }
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"PDF Processing failed: {str(e)}")

@router.get("/concept-explanations/{concept_id}")
async def get_concept_explanation(concept_id: int, db: Session = Depends(get_db)):
    """
    Retrieve detailed explanation for a specific concept
    """
    explanation = db.query(models.ConceptExplanations).filter(
        models.ConceptExplanations.concept_id == concept_id
    ).first()

    if not explanation:
        raise HTTPException(404, "Concept explanation not found")

    return {
        "concept_id": explanation.concept_id,
        "title": explanation.title,
        "definition": explanation.definition,
        "detailed_explanation": explanation.detailed_explanation,
        "examples": explanation.examples,
        "key_points": explanation.key_points,
        "prerequisites": explanation.prerequisites,
        "step_by_step_breakdown": explanation.step_by_step_breakdown,
        "related_terms": explanation.related_terms,
        "applications": explanation.applications,
        "common_misconceptions": explanation.common_misconceptions,
        "complexity_level": explanation.complexity_level,
        "word_count": explanation.word_count
    }
