#!/usr/bin/env python3
"""
Concept Explanation Storage and Retrieval Service
Handles storing and retrieving detailed concept explanations
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import models

class ConceptExplanationStorage:
    def __init__(self, db: Session):
        self.db = db
    
    def store_concept_explanation(self, concept_id: int, explanation_data: Dict[str, Any], 
                                 pdf_document_id: Optional[int] = None) -> models.ConceptExplanations:
        """
        Store a detailed concept explanation in the database
        
        Args:
            concept_id: ID of the concept
            explanation_data: Complete explanation data
            pdf_document_id: ID of the source PDF document (optional)
            
        Returns:
            Created ConceptExplanations model instance
        """
        # Check if explanation already exists for this concept
        existing = self.db.query(models.ConceptExplanations).filter(
            models.ConceptExplanations.concept_id == concept_id
        ).first()
        
        if existing:
            # Update existing explanation
            existing.title = explanation_data.get('title', existing.title)
            existing.definition = explanation_data.get('definition', existing.definition)
            existing.detailed_explanation = explanation_data.get('detailed_explanation', existing.detailed_explanation)
            existing.examples = explanation_data.get('examples', existing.examples)
            existing.key_points = explanation_data.get('key_points', existing.key_points)
            existing.prerequisites = explanation_data.get('prerequisites', existing.prerequisites)
            existing.step_by_step_breakdown = explanation_data.get('step_by_step_breakdown', existing.step_by_step_breakdown)
            existing.related_terms = explanation_data.get('related_terms', existing.related_terms)
            existing.applications = explanation_data.get('applications', existing.applications)
            existing.common_misconceptions = explanation_data.get('common_misconceptions', existing.common_misconceptions)
            existing.complexity_level = explanation_data.get('complexity_level', existing.complexity_level)
            existing.word_count = explanation_data.get('word_count', existing.word_count)
            existing.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new explanation
            explanation = models.ConceptExplanations(
                concept_id=concept_id,
                title=explanation_data.get('title', ''),
                definition=explanation_data.get('definition', ''),
                detailed_explanation=explanation_data.get('detailed_explanation', ''),
                examples=explanation_data.get('examples', []),
                key_points=explanation_data.get('key_points', []),
                prerequisites=explanation_data.get('prerequisites', []),
                step_by_step_breakdown=explanation_data.get('step_by_step_breakdown', []),
                related_terms=explanation_data.get('related_terms', []),
                applications=explanation_data.get('applications', []),
                common_misconceptions=explanation_data.get('common_misconceptions', []),
                complexity_level=explanation_data.get('complexity_level', 'medium'),
                word_count=explanation_data.get('word_count', 0)
            )
            
            self.db.add(explanation)
            self.db.commit()
            self.db.refresh(explanation)
            return explanation
    
    def get_concept_explanation(self, concept_id: int, detail_level: str = 'medium') -> Optional[Dict[str, Any]]:
        """
        Retrieve a concept explanation with specified detail level
        
        Args:
            concept_id: ID of the concept
            detail_level: 'basic', 'medium', or 'comprehensive'
            
        Returns:
            Explanation data adjusted for the detail level
        """
        explanation = self.db.query(models.ConceptExplanations).filter(
            models.ConceptExplanations.concept_id == concept_id
        ).first()
        
        if not explanation:
            return None
        
        # Convert to dictionary
        explanation_dict = {
            'id': explanation.id,
            'concept_id': explanation.concept_id,
            'title': explanation.title,
            'definition': explanation.definition,
            'detailed_explanation': explanation.detailed_explanation,
            'examples': explanation.examples or [],
            'key_points': explanation.key_points or [],
            'prerequisites': explanation.prerequisites or [],
            'step_by_step_breakdown': explanation.step_by_step_breakdown or [],
            'related_terms': explanation.related_terms or [],
            'applications': explanation.applications or [],
            'common_misconceptions': explanation.common_misconceptions or [],
            'complexity_level': explanation.complexity_level,
            'word_count': explanation.word_count,
            'created_at': explanation.created_at.isoformat() if explanation.created_at else None,
            'updated_at': explanation.updated_at.isoformat() if explanation.updated_at else None
        }
        
        # Adjust based on detail level
        if detail_level == 'basic':
            return self._filter_for_basic_level(explanation_dict)
        elif detail_level == 'comprehensive':
            return explanation_dict
        else:  # medium
            return self._filter_for_medium_level(explanation_dict)
    
    def _filter_for_basic_level(self, explanation: Dict[str, Any]) -> Dict[str, Any]:
        """Filter explanation for basic level"""
        return {
            'id': explanation['id'],
            'concept_id': explanation['concept_id'],
            'title': explanation['title'],
            'definition': explanation['definition'],
            'examples': explanation['examples'][:2],  # Limit examples
            'key_points': explanation['key_points'][:3],  # Limit key points
            'complexity_level': 'basic',
            'word_count': explanation['word_count']
        }
    
    def _filter_for_medium_level(self, explanation: Dict[str, Any]) -> Dict[str, Any]:
        """Filter explanation for medium level"""
        return {
            'id': explanation['id'],
            'concept_id': explanation['concept_id'],
            'title': explanation['title'],
            'definition': explanation['definition'],
            'detailed_explanation': explanation['detailed_explanation'],
            'examples': explanation['examples'][:3],  # Limit examples
            'key_points': explanation['key_points'][:5],  # Limit key points
            'prerequisites': explanation['prerequisites'],
            'applications': explanation['applications'][:2],  # Limit applications
            'complexity_level': explanation['complexity_level'],
            'word_count': explanation['word_count']
        }
    
    def get_all_explanations_for_concept(self, concept_id: int) -> List[Dict[str, Any]]:
        """Get all explanations for a specific concept"""
        explanations = self.db.query(models.ConceptExplanations).filter(
            models.ConceptExplanations.concept_id == concept_id
        ).all()
        
        return [self._explanation_to_dict(exp) for exp in explanations]
    
    def search_explanations(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search explanations by content
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching explanations
        """
        # Search in title, definition, and detailed explanation
        explanations = self.db.query(models.ConceptExplanations).filter(
            (models.ConceptExplanations.title.ilike(f'%{query}%')) |
            (models.ConceptExplanations.definition.ilike(f'%{query}%')) |
            (models.ConceptExplanations.detailed_explanation.ilike(f'%{query}%'))
        ).limit(limit).all()
        
        return [self._explanation_to_dict(exp) for exp in explanations]
    
    def get_explanations_by_complexity(self, complexity: str) -> List[Dict[str, Any]]:
        """Get explanations filtered by complexity level"""
        explanations = self.db.query(models.ConceptExplanations).filter(
            models.ConceptExplanations.complexity_level == complexity
        ).all()
        
        return [self._explanation_to_dict(exp) for exp in explanations]
    
    def update_explanation(self, explanation_id: int, updates: Dict[str, Any]) -> Optional[models.ConceptExplanations]:
        """Update an existing explanation"""
        explanation = self.db.query(models.ConceptExplanations).filter(
            models.ConceptExplanations.id == explanation_id
        ).first()
        
        if not explanation:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'title', 'definition', 'detailed_explanation', 'examples',
            'key_points', 'prerequisites', 'step_by_step_breakdown',
            'related_terms', 'applications', 'common_misconceptions',
            'complexity_level', 'word_count'
        ]
        
        for field, value in updates.items():
            if field in allowed_fields and hasattr(explanation, field):
                setattr(explanation, field, value)
        
        explanation.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(explanation)
        
        return explanation
    
    def delete_explanation(self, explanation_id: int) -> bool:
        """Delete an explanation"""
        explanation = self.db.query(models.ConceptExplanations).filter(
            models.ConceptExplanations.id == explanation_id
        ).first()
        
        if not explanation:
            return False
        
        self.db.delete(explanation)
        self.db.commit()
        return True
    
    def get_explanation_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored explanations"""
        total_explanations = self.db.query(models.ConceptExplanations).count()
        
        complexity_stats = self.db.query(
            models.ConceptExplanations.complexity_level,
            self.db.func.count(models.ConceptExplanations.id)
        ).group_by(models.ConceptExplanations.complexity_level).all()
        
        avg_word_count = self.db.query(
            self.db.func.avg(models.ConceptExplanations.word_count)
        ).scalar() or 0
        
        return {
            'total_explanations': total_explanations,
            'complexity_distribution': dict(complexity_stats),
            'average_word_count': round(avg_word_count, 2)
        }
    
    def _explanation_to_dict(self, explanation: models.ConceptExplanations) -> Dict[str, Any]:
        """Convert explanation model to dictionary"""
        return {
            'id': explanation.id,
            'concept_id': explanation.concept_id,
            'title': explanation.title,
            'definition': explanation.definition,
            'detailed_explanation': explanation.detailed_explanation,
            'examples': explanation.examples or [],
            'key_points': explanation.key_points or [],
            'prerequisites': explanation.prerequisites or [],
            'step_by_step_breakdown': explanation.step_by_step_breakdown or [],
            'related_terms': explanation.related_terms or [],
            'applications': explanation.applications or [],
            'common_misconceptions': explanation.common_misconceptions or [],
            'complexity_level': explanation.complexity_level,
            'word_count': explanation.word_count,
            'created_at': explanation.created_at.isoformat() if explanation.created_at else None,
            'updated_at': explanation.updated_at.isoformat() if explanation.updated_at else None
        }

class PDFDocumentStorage:
    def __init__(self, db: Session):
        self.db = db
    
    def store_pdf_document(self, filename: str, original_filename: str, 
                          file_size: int, page_count: int, 
                          extracted_text: str) -> models.PDFDocuments:
        """Store PDF document information"""
        document = models.PDFDocuments(
            filename=filename,
            original_filename=original_filename,
            file_size=file_size,
            page_count=page_count,
            extracted_text=extracted_text
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def get_pdf_document(self, document_id: int) -> Optional[models.PDFDocuments]:
        """Get PDF document by ID"""
        return self.db.query(models.PDFDocuments).filter(
            models.PDFDocuments.id == document_id
        ).first()
    
    def update_document_concepts(self, document_id: int, concept_ids: List[int]) -> bool:
        """Update the list of concept IDs for a document"""
        document = self.get_pdf_document(document_id)
        if not document:
            return False
        
        document.concept_ids = concept_ids
        self.db.commit()
        return True
    
    def get_all_documents(self) -> List[models.PDFDocuments]:
        """Get all stored PDF documents"""
        return self.db.query(models.PDFDocuments).all()
