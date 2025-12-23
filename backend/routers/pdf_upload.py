#!/usr/bin/env python3
"""
PDF Upload Router
Provides endpoints for uploading and processing PDF files for adaptive learning
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import PyPDF2
import io
from database import get_db
from services.ai_content_generation import extract_concept_from_pdf
from services.adaptive_learning import get_adaptive_assignments
import models

router = APIRouter(tags=["PDF Upload"])

@router.post("/process-pdf")
async def process_pdf(
    file: UploadFile = File(...),
    assignment_title: str = Form(...),
    api_key: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Process uploaded PDF file and extract educational concepts

    Args:
        file: Uploaded PDF file
        assignment_title: Title for the assignment
        api_key: Optional Gemini API key
        db: Database session

    Returns:
        Extracted concepts and metadata for adaptive learning
    """
    try:
        # Validate file type
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Read PDF content
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))

        # Extract text from all pages
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"

        # Extract concepts using AI
        raw_concepts = await extract_concept_from_pdf(text_content, api_key)

        # Process and store concepts in database
        processed_concepts = []
        if isinstance(raw_concepts, list):
            concepts_list = raw_concepts
        elif isinstance(raw_concepts, dict):
            concepts_list = [raw_concepts]
        else:
            concepts_list = []

        for concept_data in concepts_list:
            # Extract concept name and description
            concept_name = concept_data.get('concept') or concept_data.get('name') or 'Unknown Concept'
            concept_description = concept_data.get('definition') or concept_data.get('description') or 'No description available'

            # Check if concept already exists
            existing_concept = db.query(models.Concepts).filter(
                models.Concepts.name.ilike(concept_name)
            ).first()

            if existing_concept:
                # Use existing concept
                concept_id = existing_concept.id
            else:
                # Create new concept
                new_concept = models.Concepts(
                    name=concept_name,
                    description=concept_description
                )
                db.add(new_concept)
                db.commit()
                db.refresh(new_concept)
                concept_id = new_concept.id

            # Add ID and other metadata to concept data
            processed_concept = {
                "id": concept_id,
                "name": concept_name,
                "description": concept_description,
                "difficulty": concept_data.get('difficulty', 'medium'),
                "key_points": concept_data.get('key_points', []),
                "prerequisites": concept_data.get('prerequisites', [])
            }
            processed_concepts.append(processed_concept)

        return {
            "assignment_title": assignment_title,
            "page_count": len(pdf_reader.pages),
            "word_count": len(text_content.split()),
            "concepts": processed_concepts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@router.post("/create-adaptive-assignment")
async def create_adaptive_assignment(
    assignment_data: Dict[str, Any],
    class_id: int = Form(...),
    due_date: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Create an adaptive assignment from processed PDF concepts and assign to class
    
    Args:
        assignment_data: Data including assignment title and extracted concepts
        class_id: ID of the class to assign to
        due_date: Optional due date for the assignment
        db: Database session
        
    Returns:
        Confirmation of assignment creation and class association
    """
    try:
        # Create assignment in database with adaptive learning features enabled
        # This would integrate with the existing assignment system
        
        # For each concept, create adaptive content variations
        adaptive_content = []
        for concept in assignment_data.get("concepts", []):
            # Generate different explanation variants
            # Generate examples
            # Create micro-questions
            # All tailored to different learning speeds and styles
            
            adaptive_content.append({
                "concept_id": concept.get("id"),
                "concept_name": concept.get("name"),
                "adaptive_elements": {
                    "explanations": ["simple", "standard", "technical"],
                    "examples": ["basic", "applied", "advanced"],
                    "questions": ["recall", "application", "critical_thinking"]
                }
            })
        
        # Associate assignment with class
        # This would use the existing class assignment system
        
        return {
            "message": "Adaptive assignment created successfully",
            "assignment_id": 123,  # Placeholder
            "class_id": class_id,
            "adaptive_content": adaptive_content,
            "assigned_students": 25  # Placeholder count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating adaptive assignment: {str(e)}")