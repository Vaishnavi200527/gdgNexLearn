#!/usr/bin/env python3
"""
Text-based Learning System Router
Provides endpoints for PDF processing and detailed concept explanations
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import PyPDF2
import io
import json
from datetime import datetime
import uuid
import os

from database import get_db
from services.text_based_concept_extractor import TextBasedConceptExtractor
from services.detailed_explanation_generator import DetailedExplanationGenerator
from services.concept_explanation_storage import ConceptExplanationStorage, PDFDocumentStorage
import models

router = APIRouter(tags=["Text-based Learning"])

# Initialize services
concept_extractor = TextBasedConceptExtractor()
explanation_generator = DetailedExplanationGenerator()

@router.post("/process-pdf-text-based")
async def process_pdf_text_based(
    file: UploadFile = File(...),
    detail_level: str = Form('medium'),
    db: Session = Depends(get_db)
):
    """
    Process PDF file and generate detailed text-based concept explanations
    """
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files are allowed")
    
    if detail_level not in ['basic', 'medium', 'comprehensive']:
        raise HTTPException(400, "detail_level must be 'basic', 'medium', or 'comprehensive'")
    
    try:
        # Read PDF content
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        
        # Extract text from all pages
        text_content = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n"
        
        if not text_content.strip():
            raise HTTPException(400, "PDF has no extractable text")
        
        # Store PDF document
        filename = f"pdf_{uuid.uuid4().hex}.pdf"
        pdf_storage = PDFDocumentStorage(db)
        pdf_document = pdf_storage.store_pdf_document(
            filename=filename,
            original_filename=file.filename,
            file_size=len(content),
            page_count=len(pdf_reader.pages),
            extracted_text=text_content
        )
        
        # Extract concepts using text-based methods
        concepts_data = concept_extractor.extract_concepts_from_text(text_content)
        
        # Generate detailed explanations for each concept
        storage = ConceptExplanationStorage(db)
        processed_concepts = []
        concept_ids = []
        
        for concept_data in concepts_data:
            # Generate comprehensive explanation
            explanation_data = explanation_generator.generate_explanation_by_complexity(
                concept_data, text_content, detail_level
            )
            
            # Create or update concept in database
            concept = db.query(models.Concepts).filter(
                models.Concepts.name.ilike(concept_data['name'])
            ).first()
            
            if not concept:
                concept = models.Concepts(
                    name=concept_data['name'],
                    description=explanation_data['definition'],
                    irt_difficulty=0.5 if concept_data.get('complexity') == 'easy' else 
                                  0.7 if concept_data.get('complexity') == 'medium' else 0.9,
                    discrimination_index=1.0,
                    id_slug=concept_data['name'].lower().replace(' ', '-').replace('_', '-')
                )
                db.add(concept)
                db.flush()
            
            concept_ids.append(concept.id)
            
            # Store explanation
            stored_explanation = storage.store_concept_explanation(
                concept_id=concept.id,
                explanation_data=explanation_data
            )
            
            processed_concepts.append({
                "concept_id": concept.id,
                "name": concept.name,
                "explanation_id": stored_explanation.id,
                "complexity": explanation_data.get('complexity_level', 'medium'),
                "word_count": explanation_data.get('word_count', 0)
            })
        
        # Update PDF document with concept IDs
        pdf_storage.update_document_concepts(pdf_document.id, concept_ids)
        
        return {
            "success": True,
            "document_id": pdf_document.id,
            "filename": file.filename,
            "pages_processed": len(pdf_reader.pages),
            "total_concepts": len(processed_concepts),
            "detail_level": detail_level,
            "concepts": processed_concepts,
            "statistics": {
                "total_words": len(text_content.split()),
                "processing_time": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"PDF processing failed: {str(e)}")

@router.get("/concept-explanation/{concept_id}")
async def get_concept_explanation(
    concept_id: int,
    detail_level: str = Query('medium', description="Detail level: basic, medium, comprehensive"),
    db: Session = Depends(get_db)
):
    """
    Retrieve detailed explanation for a specific concept
    """
    if detail_level not in ['basic', 'medium', 'comprehensive']:
        raise HTTPException(400, "detail_level must be 'basic', 'medium', or 'comprehensive'")
    
    storage = ConceptExplanationStorage(db)
    explanation = storage.get_concept_explanation(concept_id, detail_level)
    
    if not explanation:
        raise HTTPException(404, f"No explanation found for concept {concept_id}")
    
    return {
        "success": True,
        "concept_id": concept_id,
        "detail_level": detail_level,
        "explanation": explanation
    }

@router.get("/search-concepts")
async def search_concepts(
    query: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Search for concepts and their explanations
    """
    storage = ConceptExplanationStorage(db)
    results = storage.search_explanations(query, limit)
    
    return {
        "success": True,
        "query": query,
        "results_count": len(results),
        "results": results
    }

@router.get("/concepts-by-complexity")
async def get_concepts_by_complexity(
    complexity: str = Query(..., description="Complexity level: easy, medium, hard"),
    db: Session = Depends(get_db)
):
    """
    Get concepts filtered by complexity level
    """
    if complexity not in ['easy', 'medium', 'hard']:
        raise HTTPException(400, "complexity must be 'easy', 'medium', or 'hard'")
    
    storage = ConceptExplanationStorage(db)
    explanations = storage.get_explanations_by_complexity(complexity)
    
    return {
        "success": True,
        "complexity": complexity,
        "count": len(explanations),
        "concepts": explanations
    }

@router.get("/all-concepts")
async def get_all_concepts(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of concepts"),
    offset: int = Query(0, ge=0, description="Number of concepts to skip"),
    db: Session = Depends(get_db)
):
    """
    Get all concepts with pagination
    """
    concepts = db.query(models.Concepts).offset(offset).limit(limit).all()
    
    concept_list = []
    storage = ConceptExplanationStorage(db)
    
    for concept in concepts:
        # Get basic explanation info
        explanation = storage.get_concept_explanation(concept.id, 'basic')
        
        concept_list.append({
            "id": concept.id,
            "name": concept.name,
            "description": concept.description,
            "id_slug": concept.id_slug,
            "irt_difficulty": concept.irt_difficulty,
            "discrimination_index": concept.discrimination_index,
            "has_explanation": explanation is not None,
            "complexity": explanation.get('complexity_level') if explanation else None
        })
    
    return {
        "success": True,
        "count": len(concept_list),
        "offset": offset,
        "limit": limit,
        "concepts": concept_list
    }

@router.get("/concept-statistics")
async def get_concept_statistics(db: Session = Depends(get_db)):
    """
    Get statistics about stored concepts and explanations
    """
    storage = ConceptExplanationStorage(db)
    stats = storage.get_explanation_statistics()
    
    # Additional statistics
    total_concepts = db.query(models.Concepts).count()
    total_documents = db.query(models.PDFDocuments).count()
    
    return {
        "success": True,
        "statistics": {
            "total_concepts": total_concepts,
            "total_explanations": stats['total_explanations'],
            "total_pdf_documents": total_documents,
            "complexity_distribution": stats['complexity_distribution'],
            "average_word_count": stats['average_word_count']
        }
    }

@router.put("/update-explanation/{explanation_id}")
async def update_explanation(
    explanation_id: int,
    updates: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Update an existing explanation
    """
    storage = ConceptExplanationStorage(db)
    updated_explanation = storage.update_explanation(explanation_id, updates)
    
    if not updated_explanation:
        raise HTTPException(404, f"Explanation {explanation_id} not found")
    
    return {
        "success": True,
        "explanation_id": explanation_id,
        "updated_at": updated_explanation.updated_at.isoformat()
    }

@router.delete("/delete-explanation/{explanation_id}")
async def delete_explanation(
    explanation_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an explanation
    """
    storage = ConceptExplanationStorage(db)
    success = storage.delete_explanation(explanation_id)
    
    if not success:
        raise HTTPException(404, f"Explanation {explanation_id} not found")
    
    return {
        "success": True,
        "message": f"Explanation {explanation_id} deleted successfully"
    }

@router.get("/document-info/{document_id}")
async def get_document_info(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Get information about a processed PDF document
    """
    pdf_storage = PDFDocumentStorage(db)
    document = pdf_storage.get_pdf_document(document_id)
    
    if not document:
        raise HTTPException(404, f"Document {document_id} not found")
    
    # Get associated concepts
    concept_ids = document.concept_ids or []
    concepts = db.query(models.Concepts).filter(models.Concepts.id.in_(concept_ids)).all()
    
    return {
        "success": True,
        "document": {
            "id": document.id,
            "original_filename": document.original_filename,
            "file_size": document.file_size,
            "page_count": document.page_count,
            "processed_at": document.processed_at.isoformat(),
            "concept_count": len(concepts),
            "concepts": [
                {
                    "id": concept.id,
                    "name": concept.name,
                    "description": concept.description
                }
                for concept in concepts
            ]
        }
    }

@router.get("/learning-path/{concept_id}")
async def get_learning_path(
    concept_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate a learning path for a concept including prerequisites and related concepts
    """
    # Get the main concept
    concept = db.query(models.Concepts).filter(models.Concepts.id == concept_id).first()
    if not concept:
        raise HTTPException(404, f"Concept {concept_id} not found")
    
    storage = ConceptExplanationStorage(db)
    explanation = storage.get_concept_explanation(concept_id, 'medium')
    
    if not explanation:
        raise HTTPException(404, f"No explanation found for concept {concept_id}")
    
    # Get prerequisites
    prerequisites = explanation.get('prerequisites', [])
    prerequisite_concepts = []
    
    for prereq in prerequisites:
        # Try to find matching concepts
        prereq_concept = db.query(models.Concepts).filter(
            models.Concepts.name.ilike(f'%{prereq}%')
        ).first()
        
        if prereq_concept:
            prereq_explanation = storage.get_concept_explanation(prereq_concept.id, 'basic')
            prerequisite_concepts.append({
                "id": prereq_concept.id,
                "name": prereq_concept.name,
                "description": prereq_explanation.get('definition', '') if prereq_explanation else '',
                "complexity": prereq_explanation.get('complexity_level', 'medium') if prereq_explanation else 'medium'
            })
    
    # Get related concepts
    related_terms = explanation.get('related_terms', [])
    related_concepts = []
    
    for term in related_terms[:5]:  # Limit to 5 related concepts
        if isinstance(term, str):
            term_name = term
        else:
            # Extract name from "Name: description" format
            term_name = term.split(':')[0] if ':' in term else term
        
        related_concept = db.query(models.Concepts).filter(
            models.Concepts.name.ilike(f'%{term_name}%')
        ).first()
        
        if related_concept and related_concept.id != concept_id:
            related_explanation = storage.get_concept_explanation(related_concept.id, 'basic')
            related_concepts.append({
                "id": related_concept.id,
                "name": related_concept.name,
                "description": related_explanation.get('definition', '') if related_explanation else '',
                "complexity": related_explanation.get('complexity_level', 'medium') if related_explanation else 'medium'
            })
    
    return {
        "success": True,
        "main_concept": {
            "id": concept.id,
            "name": concept.name,
            "description": explanation.get('definition', ''),
            "complexity": explanation.get('complexity_level', 'medium'),
            "word_count": explanation.get('word_count', 0)
        },
        "prerequisites": prerequisite_concepts,
        "related_concepts": related_concepts[:5],  # Limit to 5 related concepts
        "learning_order": [p["id"] for p in prerequisite_concepts] + [concept_id] + [r["id"] for r in related_concepts[:3]]
    }
