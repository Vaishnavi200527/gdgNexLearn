#!/usr/bin/env python3
"""
PDF Processing Service
Handles PDF file parsing and text extraction for the adaptive learning platform
"""

import PyPDF2
import io
import re
from typing import Dict, List, Any

def extract_text_from_pdf(content: bytes) -> str:
    """
    Extract text content from PDF bytes
    
    Args:
        content: PDF file content as bytes
        
    Returns:
        Extracted text content from all pages
    """
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        
        # Extract text from all pages
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"
            
        return text_content
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def get_pdf_metadata(content: bytes) -> Dict[str, Any]:
    """
    Get metadata information from PDF
    
    Args:
        content: PDF file content as bytes
        
    Returns:
        Dictionary containing PDF metadata
    """
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        
        metadata = {
            "page_count": len(pdf_reader.pages),
            "author": pdf_reader.metadata.author if pdf_reader.metadata else None,
            "creator": pdf_reader.metadata.creator if pdf_reader.metadata else None,
            "producer": pdf_reader.metadata.producer if pdf_reader.metadata else None,
            "subject": pdf_reader.metadata.subject if pdf_reader.metadata else None,
            "title": pdf_reader.metadata.title if pdf_reader.metadata else None
        }
        
        return metadata
    except Exception as e:
        raise Exception(f"Error getting PDF metadata: {str(e)}")

def process_pdf_for_adaptive_learning(content: bytes) -> Dict[str, Any]:
    """
    Process PDF for adaptive learning by extracting text and metadata
    
    Args:
        content: PDF file content as bytes
        
    Returns:
        Dictionary containing processed PDF information for adaptive learning
    """
    try:
        # Extract text content
        text_content = extract_text_from_pdf(content)
        
        # Get metadata
        metadata = get_pdf_metadata(content)
        
        # Calculate basic statistics
        word_count = len(text_content.split())
        char_count = len(text_content)
        
        return {
            "text_content": text_content,
            "metadata": metadata,
            "statistics": {
                "word_count": word_count,
                "character_count": char_count
            }
        }
    except Exception as e:
        raise Exception(f"Error processing PDF for adaptive learning: {str(e)}")

def identify_key_concepts(text: str) -> List[Dict[str, Any]]:
    """
    Identify key concepts within the text using text analysis techniques.
    
    Args:
        text: The text content to analyze
        
    Returns:
        List of identified concepts with details
    """
    # Common patterns for identifying concepts in academic text
    concept_patterns = [
        # Look for "concept is/are definition" patterns
        r'([A-Z][a-zA-Z\s]{3,20}?)\s+(?:is|are|was|were|represents|means|stands for)\s+([^\.]+?\.)',
        # Look for section headers (often bold or capitalized)
        r'^\s*([A-Z][A-Z\s]{5,50}|[A-Z][a-zA-Z\s]{5,30})\s*$',
        # Look for bold-like formatting (words in all caps or with specific formatting)
        r'\*\*([A-Z][a-zA-Z\s]{3,30}?)\*\*',
        # Look for "The [concept] concept" patterns
        r'The\s+([A-Z][a-zA-Z\s]{3,20}?)\s+concept',
        # Look for "A [concept] is" patterns
        r'A\s+([A-Z][a-zA-Z\s]{3,20}?)\s+(?:is|was|represents)',
    ]
    
    concepts = set()
    
    # Find concepts using patterns
    for pattern in concept_patterns:
        matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            if match and match.groups():  # Check if match exists and has groups
                concept = match.group(1).strip()
                # Filter out common words that are not concepts
                if len(concept) > 2 and not concept.lower() in ['the', 'and', 'for', 'are', 'but', 'not', 'with', 'has', 'have', 'had', 'can', 'will', 'would', 'should', 'could', 'this', 'that', 'these', 'those', 'what', 'when', 'where', 'who', 'why', 'how', 'all', 'any', 'each', 'every', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'than', 'too', 'very', 'just', 'now']:
                    concepts.add(concept)
    
    # Also extract potential concepts from capitalized words/phrases
    # Look for capitalized phrases that might be concepts
    capitalized_phrases = re.findall(r'\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]*){0,4}\b', text)
    for phrase in capitalized_phrases:
        if len(phrase) > 2 and phrase not in concepts and phrase.lower() not in ['the', 'and', 'for', 'are', 'but', 'not', 'with', 'has', 'have', 'had', 'can', 'will', 'would', 'should', 'could', 'this', 'that', 'these', 'those', 'what', 'when', 'where', 'who', 'why', 'how', 'all', 'any', 'each', 'every', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'than', 'too', 'very', 'just', 'now']:
            concepts.add(phrase)
    
    # Create detailed concept explanations
    detailed_concepts = []
    for concept in concepts:
        detailed_concept = generate_detailed_concept_explanation(concept, text)
        detailed_concepts.append(detailed_concept)
    
    return detailed_concepts

def generate_detailed_concept_explanation(concept: str, text: str) -> Dict[str, Any]:
    """
    Generate a detailed explanation for a concept based on the provided text.
    
    Args:
        concept: The concept to explain
        text: The source text to extract information from
        
    Returns:
        Dictionary with detailed concept explanation
    """
    # Find definition in text
    definition = find_definition_for_concept(concept, text)
    if not definition:
        definition = f"Definition of {concept} based on context"
    
    # Find examples in text
    examples = find_examples_for_concept(concept, text)
    
    # Find key points and sub-topics
    key_points = find_key_points_for_concept(concept, text)
    
    # Find prerequisites
    prerequisites = find_prerequisites_for_concept(concept, text)
    
    # Find related terms
    related_terms = find_related_terms(concept, text)
    
    # Find applications
    applications = find_applications_for_concept(concept, text)
    
    # Find common misconceptions
    misconceptions = find_common_misconceptions(concept, text)
    
    # Find sub-topics
    sub_topics = find_sub_topics(concept, text)
    
    # Generate step-by-step breakdown if possible
    step_by_step = generate_step_by_step_breakdown(concept, text)
    
    # Create detailed explanation
    explanation = {
        "name": concept,
        "definition": definition,
        "examples": examples,
        "key_points": key_points,
        "prerequisites": prerequisites,
        "related_terms": related_terms,
        "applications": applications,
        "misconceptions": misconceptions,
        "detailed_explanation": generate_detailed_explanation(concept, text),
        "sub_topics": sub_topics,
        "step_by_step_breakdown": step_by_step
    }
    
    return explanation

def find_definition_for_concept(concept: str, text: str) -> str:
    """Find the definition of a concept in the text."""
    # Look for definition patterns
    patterns = [
        rf'([A-Z][a-zA-Z\s]*?{re.escape(concept)}[a-zA-Z\s]*?)\s+(?:is|are|was|were|represents|means|stands for|defines)\s+([^\.]+?\.)',
        rf'{re.escape(concept)}\s+(?:is|are|was|were|represents|means|stands for|defines)\s+([^\.]+?\.)',
        rf'The\s+{re.escape(concept)}\s+(?:is|are|was|were|represents|means|stands for)\s+([^\.]+?\.)',
        rf'A\s+{re.escape(concept)}\s+(?:is|represents|means)\s+([^\.]+?\.)',
        rf'{re.escape(concept)}.*?(?:refers to|can be defined as|is defined as)\s+([^\.]+?\.)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Get the last matching group
            groups = match.groups()
            if groups:
                # Find the last non-empty group
                for i in range(len(groups)-1, -1, -1):
                    if groups[i]:
                        return groups[i].strip()
                # If all groups are empty, return the full match
                return match.group(0).strip()
            else:
                # If no groups, return the full match
                return match.group(0).strip()
    
    # If no definition found, return a basic definition
    return f"{concept} is a concept discussed in the provided text."

def find_examples_for_concept(concept: str, text: str) -> List[str]:
    """Find examples related to the concept in the text."""
    examples = []
    
    # Look for example patterns
    patterns = [
        rf'(?:For example|For instance|Example|Examples):\s*([^\.]+?\.)',
        rf'(?:For example|For instance|Example|Examples)\s+(.*?)(?:\.|\n)',
        rf'{re.escape(concept)}.*?(?:For example|For instance|Example):\s*([^\.]+?\.)',
        rf'(?:such as)\s+([^\.]+?\.)',
        rf'{re.escape(concept)}.*?(?:like|as in)\s+([^\.]+?\.)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            example = match.strip()
            if example and concept.lower() in example.lower():
                examples.append(example)
    
    # If no specific examples found, extract sentences that mention the concept
    if not examples:
        sentences = text.split('.')
        for sentence in sentences:
            if concept.lower() in sentence.lower() and len(sentence.strip()) > 10:
                examples.append(sentence.strip() + '.')
                if len(examples) >= 3:  # Limit to 3 examples
                    break
    
    return examples[:5]  # Return at most 5 examples

def find_key_points_for_concept(concept: str, text: str) -> List[str]:
    """Find key points related to the concept in the text."""
    key_points = []
    
    # Look for key point patterns
    patterns = [
        r'(?:Key point|Key points|Important|Significant|Critical):\s*([^\.]+?\.)',
        r'(?:First|Second|Third|Next|Finally).*?([^\.]+?\.)',
        rf'(?:One|Another|Additionally).*?{re.escape(concept)}.*?([^\.]+?\.)',
    ]
    
    # Find sentences that contain the concept and seem important
    sentences = text.split('.')
    for sentence in sentences:
        if concept.lower() in sentence.lower():
            sentence = sentence.strip()
            if sentence and ('important' in sentence.lower() or 
                           'key' in sentence.lower() or 
                           'significant' in sentence.lower() or
                           'main' in sentence.lower() or
                           'primary' in sentence.lower() or
                           'crucial' in sentence.lower() or
                           'essential' in sentence.lower() or
                           'critical' in sentence.lower()):
                key_points.append(sentence + '.')

    # If no specific key points found, get sentences that mention the concept
    if not key_points:
        for sentence in sentences:
            if concept.lower() in sentence.lower() and len(sentence.strip()) > 15:
                key_points.append(sentence.strip() + '.')
                if len(key_points) >= 5:  # Limit to 5 key points
                    break
    
    return key_points[:5]

def find_prerequisites_for_concept(concept: str, text: str) -> List[str]:
    """Find prerequisites for understanding the concept."""
    prerequisites = []
    
    # Look for prerequisite patterns
    patterns = [
        r'(?:requires|requires understanding of|prerequisite|pre-requisite|before learning|before understanding).*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        rf'(?:To understand|To learn|Before studying)\s+{re.escape(concept)}.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:depends on|builds on|based on)\s+([^\.]+?\.)',
        r'(?:assumes knowledge of|assumes familiarity with)\s+([^\.]+?\.)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if match.lower() != concept.lower():
                prerequisites.append(match.strip())
    
    return list(set(prerequisites))[:5]  # Return unique prerequisites, max 5

def find_related_terms(concept: str, text: str) -> List[str]:
    """Find related terms to the concept."""
    related_terms = []
    
    # Look for related term patterns
    patterns = [
        rf'{re.escape(concept)}.*?(?:and|with|related to|connected to|associated with)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:similar to|related to|connected to|associated with)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:also known as|AKA|alias)\s+([^\.]+?\.)',
        r'(?:synonymous with|similar to|comparable to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if match.lower() != concept.lower():
                related_terms.append(match.strip())
    
    # Extract capitalized terms that appear near the concept
    sentences = text.split('.')
    for sentence in sentences:
        if concept.lower() in sentence.lower():
            # Find other capitalized terms in the same sentence
            other_terms = re.findall(r'\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]*){0,2}\b', sentence)
            for term in other_terms:
                if term.lower() != concept.lower() and term not in related_terms:
                    related_terms.append(term)
    
    return list(set(related_terms))[:10]  # Return unique terms, max 10

def find_applications_for_concept(concept: str, text: str) -> List[str]:
    """Find applications of the concept."""
    applications = []
    
    # Look for application patterns
    patterns = [
        rf'{re.escape(concept)}.*?(?:used in|applied in|application|applied for|used for)\s+([^\.]+?\.)',
        rf'(?:used in|applied in|application|applied for|used for)\s+{re.escape(concept)}.*?([^\.]+?\.)',
        rf'(?:used|applied|implement|utilize).*?{re.escape(concept)}.*?([^\.]+?\.)',
        r'(?:practical application|real-world use|in practice)\s+([^\.]+?\.)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            applications.append(match.strip())
    
    # If no specific applications found, get sentences that mention usage
    if not applications:
        sentences = text.split('.')
        for sentence in sentences:
            if concept.lower() in sentence.lower() and ('used' in sentence.lower() or 
                                                      'applied' in sentence.lower() or
                                                      'application' in sentence.lower() or
                                                      'implement' in sentence.lower() or
                                                      'practice' in sentence.lower() or
                                                      'real-world' in sentence.lower()):
                applications.append(sentence.strip() + '.')
    
    return applications[:5]

def find_common_misconceptions(concept: str, text: str) -> List[str]:
    """Find common misconceptions about the concept if mentioned in text."""
    misconceptions = []
    
    # Look for misconception patterns
    patterns = [
        r'(?:common misconception|common mistake|often confused|often mistaken)\s+([^\.]+?\.)',
        r'(?:beware of|be careful|note that|important to remember)\s+([^\.]+?\.)',
        rf'{re.escape(concept)}.*?(?:is not|does not mean|not to be confused with)\s+([^\.]+?\.)',
        r'(?:misunderstanding|misconception|wrongly assumed)\s+([^\.]+?\.)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            misconceptions.append(match.strip())
    
    return misconceptions[:3]

def generate_detailed_explanation(concept: str, text: str) -> str:
    """Generate a detailed explanation of the concept based on the text."""
    # Find sentences that contain the concept
    sentences = text.split('.')
    concept_sentences = []
    
    for sentence in sentences:
        if concept.lower() in sentence.lower():
            concept_sentences.append(sentence.strip())
    
    if concept_sentences:
        # Combine relevant sentences into a detailed explanation
        explanation = " ".join(concept_sentences[:10])  # Use up to 10 sentences
        return explanation.strip() + "."
    else:
        return f"Detailed explanation of {concept} based on the provided text content."

def find_sub_topics(concept: str, text: str) -> List[str]:
    """Find sub-topics related to the concept."""
    sub_topics = []
    
    # Look for sub-topic patterns
    patterns = [
        rf'{re.escape(concept)}.*?(?:includes|consists of|has|contains)\s+([^\.]+?\.)',
        r'(?:includes|consists of|has|contains|comprises)\s+([^\.]+?\.)',
        rf'(?:types|kinds|categories|variations)\s+of\s+{re.escape(concept)}.*?([^\.]+?\.)',
        r'(?:subdivided into|broken down into)\s+([^\.]+?\.)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            sub_topics.append(match.strip())
    
    # Extract capitalized terms that appear after the concept
    sentences = text.split('.')
    for sentence in sentences:
        if concept.lower() in sentence.lower():
            # Look for terms after the concept
            parts = sentence.split(concept)
            if len(parts) > 1:
                after_concept = parts[-1]
                if isinstance(after_concept, str):
                    terms = re.findall(r'\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]*){0,2}\b', after_concept)
                    for term in terms:
                        if term not in sub_topics:
                            sub_topics.append(term)
    
    return list(set(sub_topics))[:10]

def generate_step_by_step_breakdown(concept: str, text: str) -> List[str]:
    """Generate a step-by-step breakdown for the concept if applicable."""
    steps = []
    
    # Look for step patterns in the text
    patterns = [
        rf'(?:Step\s*\d+|First|Second|Third|Next|Then|Finally).*?{re.escape(concept)}.*?([^\.]+?\.)',
        r'(?:Step\s*\d+|First|Second|Third|Next|Then|Finally).*?([^\.]+?\.)',
        rf'(?:process|procedure|method|algorithm).*?{re.escape(concept)}.*?([^\.]+?\.)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            steps.append(match.strip())
    
    # If no specific steps found, try to identify procedural content
    sentences = text.split('.')
    for sentence in sentences:
        if concept.lower() in sentence.lower() and ('step' in sentence.lower() or 
                                                  'process' in sentence.lower() or
                                                  'procedure' in sentence.lower() or
                                                  'first' in sentence.lower() or
                                                  'then' in sentence.lower() or
                                                  'next' in sentence.lower() or
                                                  'finally' in sentence.lower()):
            steps.append(sentence.strip() + '.')
    
    return steps[:10]  # Return up to 10 steps

def process_pdf_for_text_learning(content: bytes) -> Dict[str, Any]:
    """
    Process PDF specifically for text-based learning with detailed concept explanations.
    
    Args:
        content: PDF file content as bytes
        
    Returns:
        Dictionary containing detailed concept explanations
    """
    try:
        # Extract text content
        text_content = extract_text_from_pdf(content)
        
        # Verify text_content is a string
        if not isinstance(text_content, str):
            raise ValueError(f"Expected string from extract_text_from_pdf, got {type(text_content)}")
        
        # Get metadata
        metadata = get_pdf_metadata(content)
        
        # Identify key concepts
        concepts = identify_key_concepts(text_content)
        
        # Calculate statistics
        word_count = len(text_content.split()) if text_content else 0
        char_count = len(text_content) if isinstance(text_content, str) else 0
        
        # Return structured learning content
        return {
            "concepts": concepts,
            "text_content": text_content,
            "metadata": metadata,
            "statistics": {
                "word_count": word_count,
                "character_count": char_count,
                "concept_count": len(concepts)
            }
        }
    except Exception as e:
        raise Exception(f"Error processing PDF for text-based learning: {str(e)}")