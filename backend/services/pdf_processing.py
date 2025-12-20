#!/usr/bin/env python3
"""
PDF Processing Service
Handles PDF file parsing and text extraction for the adaptive learning platform
"""

import PyPDF2
import io
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