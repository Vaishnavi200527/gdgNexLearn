#!/usr/bin/env python3
"""
PDF Upload Router
Provides endpoints for uploading and processing PDF files for text-based learning
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import PyPDF2
import io
import json
from database import get_db
from services.pdf_processing import process_pdf_for_text_learning
import models

router = APIRouter(tags=["PDF Upload"])

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
        result = process_pdf_for_text_learning(content)
        
        # Extract concepts from the result
        concepts_data = result.get("concepts", [])
        
        # Process each concept and store in database
        processed_concepts = []
<<<<<<< HEAD
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
                models.Concepts.concept_name.ilike(concept_name)
            ).first()

            if existing_concept:
                # Use existing concept
                concept_id = existing_concept.id
            else:
                # Create new concept
                new_concept = models.Concepts(
                    concept_name=concept_name,
                    description=concept_description
=======
        for concept_data in concepts_data:
            # Create or update concept in database
            concept = db.query(models.Concepts).filter(
                models.Concepts.name.ilike(f"%{concept_data['name']}%") | 
                models.Concepts.name.ilike(concept_data['name'])
            ).first()

            if not concept:
                # Create new concept with detailed information
                concept = models.Concepts(
                    name=concept_data['name'],
                    description=concept_data['definition'],
                    id_slug=concept_data['name'].lower().replace(' ', '-').replace('_', '-')
>>>>>>> d1b0e9665ef58abcf16ab9b737febfe080e00a82
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
                "name": concept.name,
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
                "word_count": result["statistics"]["word_count"],
                "character_count": result["statistics"]["character_count"]
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
        result = process_pdf_for_text_learning(content)
        
        # Process concepts and store detailed explanations
        detailed_concepts = []
        for concept_data in result.get("concepts", []):
            # Create or update concept in database
            concept = db.query(models.Concepts).filter(
                models.Concepts.name.ilike(f"%{concept_data['name']}%") | 
                models.Concepts.name.ilike(concept_data['name'])
            ).first()

            if not concept:
                # Create new concept
                concept = models.Concepts(
                    name=concept_data['name'],
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
                "word_count": result["statistics"]["word_count"],
                "character_count": result["statistics"]["character_count"]
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