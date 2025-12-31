#!/usr/bin/env python3
"""
PDF Processing Service - FINAL WORKING VERSION
"""

import PyPDF2
import io
import re
import logging
import json
from typing import Dict, List, Any
from concept_extractor import extract_concepts_with_gemini, extract_clean_pdf_text_only

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Process PDFs and extract ONLY meaningful concepts."""
    
    def __init__(self):
        self.meaningless_phrases = {
            "the values", "the sorted values", "mostly data", "these tests",
            "the observed values", "the expected values", "smoothing by bin",
            "skewed data", "best used when data", "handle noisy data",
            "the value", "use multiple linear regression", "square test formula",
            "data data", "there", "here", "each", "which"
        }
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract raw text from PDF."""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            raise
    
    def is_meaningful_concept(self, concept_name: str) -> bool:
        """Determine if a concept name is meaningful."""
        if not concept_name:
            return False
        
        concept_lower = concept_name.lower().strip()
        
        # REJECT meaningless phrases
        if concept_lower in self.meaningless_phrases:
            return False
        
        # REJECT if starts with meaningless words
        if concept_lower.startswith(('the ', 'these ', 'mostly ', 'best ', 'handle ', 'use ')):
            return False
        
        # REJECT single words (usually not meaningful concepts)
        if len(concept_name.split()) < 2:
            return False
        
        # REJECT too short or too long
        if len(concept_name) < 5 or len(concept_name) > 60:
            return False
        
        # MUST start with capital letter
        if not concept_name[0].isupper():
            return False
        
        # Should look like a proper concept (not a sentence fragment)
        if concept_name.endswith('?') or concept_name.endswith('!'):
            return False
        
        return True
    
    def format_concept_output(self, concept: Dict[str, str]) -> Dict[str, Any]:
        """Format a concept for final output."""
        name = concept.get('name', '').strip()
        description = concept.get('description', '').strip()
        
        # Ensure description has proper formatting
        if '\\n\\n' not in description and '\n\n' not in description:
            # Add double newline before bullet points
            if '*' in description:
                bullet_index = description.find('*')
                if bullet_index > 0:
                    description = description[:bullet_index].rstrip() + '\n\n' + description[bullet_index:]
            else:
                # Create bullet points from sentences
                sentences = [s.strip() + '.' for s in description.split('.') if s.strip()]
                if len(sentences) > 1:
                    description = sentences[0] + '\n\n* ' + '\n* '.join(sentences[1:4])
        
        # Extract examples and key points
        examples = []
        key_points = []
        
        # Look for examples in description
        lines = description.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(phrase in line_lower for phrase in ['for example', 'e.g.', 'such as', 'including']):
                examples.append(line.strip())
        
        # Extract key points (bullet points)
        for line in lines:
            if line.strip().startswith('*'):
                key_points.append(line.strip()[2:].strip())
        
        return {
            "name": name,
            "definition": description.split('.')[0] + '.' if '.' in description else description,
            "description": description,
            "examples": examples[:2],
            "key_points": key_points[:4] if key_points else self.extract_key_points(description)
        }
    
    def extract_key_points(self, description: str) -> List[str]:
        """Extract key points from description."""
        key_points = []
        sentences = [s.strip() + '.' for s in description.split('.') if s.strip()]
        
        # Take the most important sounding sentences
        for sentence in sentences[1:5]:  # Skip definition sentence
            if len(sentence) > 30 and any(word in sentence.lower() for word in ['include', 'involve', 'essential', 'important', 'critical']):
                key_points.append(sentence)
        
        return key_points[:3]
    
    def get_fallback_concepts(self, text: str) -> List[Dict[str, Any]]:
        """Get fallback concepts if AI extraction fails."""
        # Common data preprocessing concepts
        common_concepts = [
            "Data Preprocessing",
            "Data Cleaning", 
            "Data Integration",
            "Data Transformation",
            "Data Reduction",
            "Normalization",
            "Dimensionality Reduction",
            "Feature Selection",
            "Outlier Detection",
            "Missing Data Handling",
            "Noise Reduction",
            "Data Quality",
            "Binning Methods",
            "Regression Analysis",
            "Chi-Square Test"
        ]
        
        concepts = []
        for concept_name in common_concepts[:12]:  # Take first 12
            if concept_name.lower() in text.lower():
                concepts.append({
                    "name": concept_name,
                    "definition": f"{concept_name} is a key concept in data preprocessing and data mining.",
                    "description": f"{concept_name} is a key concept in data preprocessing and data mining.\n\n* Essential for preparing data for analysis* Improves data quality and reliability* Used in various data mining applications",
                    "examples": [],
                    "key_points": ["Essential for data preparation", "Improves data quality", "Used in data mining"]
                })
        
        return concepts
    
    def process_pdf(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Main processing function."""
        try:
            # Step 1: Extract raw text
            raw_text = self.extract_text_from_pdf(pdf_bytes)
            
            if not raw_text or len(raw_text.strip()) < 100:
                return {
                    "success": False,
                    "error": "PDF is empty or has no extractable text",
                    "concepts": []
                }
            
            # Step 2: Use AI to extract concepts
            ai_concepts = extract_concepts_with_gemini(raw_text)
            
            # Step 3: Validate and format concepts
            valid_concepts = []
            
            for concept in ai_concepts:
                concept_name = concept.get('name', '').strip()
                
                # STRICT VALIDATION
                if not self.is_meaningful_concept(concept_name):
                    continue
                
                # Format the concept
                formatted_concept = self.format_concept_output(concept)
                valid_concepts.append(formatted_concept)
                
                if len(valid_concepts) >= 15:
                    break
            
            # # Step 4: If AI failed, use fallback
            # if len(valid_concepts) < 8:
            #     logger.warning(f"AI extracted only {len(valid_concepts)} concepts, using fallback")
            #     
            #     # Get clean text for fallback
            #     clean_text, _ = extract_clean_pdf_text_only(raw_text)
            #     fallback_concepts = self.get_fallback_concepts(clean_text)
            #     
            #     # Add unique fallback concepts
            #     existing_names = {c['name'].lower() for c in valid_concepts}
            #     for fb_concept in fallback_concepts:
            #         if fb_concept['name'].lower() not in existing_names:
            #             valid_concepts.append(fb_concept)
            #             existing_names.add(fb_concept['name'].lower())
            #             
            #             if len(valid_concepts) >= 15:
            #                 break
            # 
            # # Step 5: Ensure we have 10-15 concepts
            # if len(valid_concepts) < 10:
            #     # Add more generic concepts
            #     generic_concepts = [
            #         "Data Mining", "Machine Learning", "Statistical Analysis",
            #         "Data Visualization", "Pattern Recognition", "Predictive Modeling"
            #     ]
            #     
            #     for gen_concept in generic_concepts:
            #         if len(valid_concepts) >= 10:
            #             break
            #         
            #         valid_concepts.append({
            #             "name": gen_concept,
            #             "definition": f"{gen_concept} is an important field in data science.",
            #             "description": f"{gen_concept} is an important field in data science.\n\n* Used for extracting insights from data* Involves various algorithms and techniques* Essential for business intelligence",
            #             "examples": [],
            #             "key_points": ["Extracts insights from data", "Uses algorithms and techniques", "Supports decision making"]
            #         })
            
            # Step 6: Get metadata
            metadata = self.get_pdf_metadata(pdf_bytes)
            
            # Calculate word and character count
            total_words = len(raw_text.split())
            total_characters = len(raw_text)

            return {
                "success": True,
                "text_content": raw_text,
                "concepts": valid_concepts[:15],  # Ensure max 15
                "metadata": metadata,
                "statistics": {
                    "total_concepts": len(valid_concepts),
                    "pages": metadata.get("page_count", 0),
                    "valid_concepts": len([c for c in valid_concepts if self.is_meaningful_concept(c['name'])]),
                    "total_words": total_words,
                    "total_characters": total_characters,
                },
                "message": f"Successfully extracted {len(valid_concepts)} meaningful concepts"
            }
        except Exception as e:
            logger.error(f"PDF processing failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "concepts": [],
                "message": "Failed to process PDF"
            }
    
    def get_pdf_metadata(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Extract PDF metadata."""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            return {
                "page_count": len(pdf_reader.pages),
                "title": pdf_reader.metadata.title if pdf_reader.metadata else "Unknown",
                "author": pdf_reader.metadata.author if pdf_reader.metadata else "Unknown",
                "creator": pdf_reader.metadata.creator if pdf_reader.metadata else "Unknown",
                "subject": pdf_reader.metadata.subject if pdf_reader.metadata else "Unknown"
            }
        except:
            return {
                "page_count": 0,
                "title": "Unknown",
                "author": "Unknown",
                "creator": "Unknown",
                "subject": "Unknown"
            }

# Create global instance
pdf_processor = PDFProcessor()

# Public API functions
def process_pdf_for_concepts(pdf_content: bytes) -> Dict[str, Any]:
    """Process PDF and extract meaningful concepts."""
    return pdf_processor.process_pdf(pdf_content)

# For backward compatibility
def process_pdf_for_adaptive_learning(content: bytes) -> Dict[str, Any]:
    """Legacy function name."""
    return process_pdf_for_concepts(content)

def identify_key_concepts(text: str) -> List[Dict[str, Any]]:
    """Identify key concepts from text (for backward compatibility)."""
    try:
        # Use AI extraction
        ai_concepts = extract_concepts_with_gemini(text)
        
        # Format concepts
        formatted_concepts = []
        for concept in ai_concepts:
            concept_name = concept.get('name', '').strip()
            if pdf_processor.is_meaningful_concept(concept_name):
                formatted_concept = pdf_processor.format_concept_output(concept)
                formatted_concepts.append(formatted_concept)
        
        return formatted_concepts[:15]
    except Exception as e:
        logger.error(f"identify_key_concepts failed: {e}")
        return []