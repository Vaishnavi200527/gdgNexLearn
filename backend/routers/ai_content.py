#!/usr/bin/env python3
"""
AI Content Generation Router
Provides endpoints for AI-powered educational content generation
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any
import os
from dotenv import load_dotenv

from database import get_db
from services.ai_content_generation import (
    extract_concept_from_pdf,
    generate_explanation_variants,
    generate_examples_from_context,
    generate_micro_questions,
    evaluate_student_answer,
    teach_concept,
    reteach_concept,
    ask_ai_tutor,
    reflection_prompt,
    analyze_learning_state,
    detect_confusing_concepts,
    generate_weekly_teacher_summary,
    format_ui_friendly_explanation
)

# Load environment variables
load_dotenv()

router = APIRouter(tags=["AI Content Generation"])

@router.post("/extract-concept")
async def extract_concept_from_pdf_endpoint(
    pdf_text: str = Body(..., embed=True),
    api_key: str = Body(None, embed=True)
):
    """
    Extract concept information from PDF text

    Args:
        pdf_text: The extracted text from a PDF
        api_key: Optional Gemini API key

    Returns:
        Extracted concept information
    """
    try:
        result = await extract_concept_from_pdf(pdf_text, api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting concept: {str(e)}")

@router.post("/generate-explanations")
async def generate_explanations_endpoint(
    concept_data: Dict[str, Any] = Body(..., embed=True),
    api_key: str = Body(None, embed=True)
):
    """
    Generate different explanation variants for a concept

    Args:
        concept_data: Concept information
        api_key: Optional Gemini API key

    Returns:
        Different explanation variants (simple, standard, compact)
    """
    try:
        result = await generate_explanation_variants(concept_data, api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating explanations: {str(e)}")

@router.post("/generate-examples")
async def generate_examples_endpoint(
    pdf_context: str = Body(..., embed=True),
    api_key: str = Body(None, embed=True)
):
    """
    Generate examples based on PDF context

    Args:
        pdf_context: Context from PDF
        api_key: Optional Gemini API key

    Returns:
        Generated examples (simple, exam-oriented)
    """
    try:
        result = await generate_examples_from_context(pdf_context, api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating examples: {str(e)}")

@router.post("/generate-micro-questions")
async def generate_micro_questions_endpoint(
    concept_data: Dict[str, Any] = Body(..., embed=True),
    api_key: str = Body(None, embed=True)
):
    """
    Generate micro-questions for concept understanding

    Args:
        concept_data: Concept information
        api_key: Optional Gemini API key

    Returns:
        Generated micro-questions (MCQ and fill-in-the-blank)
    """
    try:
        result = await generate_micro_questions(concept_data, api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating micro-questions: {str(e)}")

@router.post("/evaluate-answer")
async def evaluate_answer_endpoint(
    concept_name: str = Body(..., embed=True),
    correct_answer: str = Body(..., embed=True),
    student_answer: str = Body(..., embed=True),
    api_key: str = Body(None, embed=True)
):
    """
    Evaluate a student's answer

    Args:
        concept_name: Name of the concept
        correct_answer: Correct answer
        student_answer: Student's answer
        api_key: Optional Gemini API key

    Returns:
        Evaluation result with correctness, confidence, and feedback
    """
    try:
        result = await evaluate_student_answer(concept_name, correct_answer, student_answer, api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating answer: {str(e)}")


@router.post("/teach-concept")
async def teach_concept_endpoint(
    concept_data: Dict[str, Any] = Body(..., embed=True),
    student_level: str = Body("average", embed=True),
    explanation_type: str = Body("standard", embed=True),
    api_key: str = Body(None, embed=True)
):
    """
    Teach a concept to a student based on their level and preferred explanation type

    Args:
        concept_data: Concept information
        student_level: Student level (beginner, average, advanced)
        explanation_type: Explanation type (simple, standard, compact)
        api_key: Optional Gemini API key

    Returns:
        Teaching material for the concept
    """
    try:
        result = await teach_concept(concept_data, student_level, explanation_type, api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error teaching concept: {str(e)}")


@router.post("/reteach-concept")
async def reteach_concept_endpoint(
    concept_data: Dict[str, Any] = Body(..., embed=True),
    api_key: str = Body(None, embed=True)
):
    """
    Re-teach a concept in simpler terms when student struggles

    Args:
        concept_data: Concept information
        api_key: Optional Gemini API key

    Returns:
        Simplified explanation of the concept
    """
    try:
        result = await reteach_concept(concept_data, api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error re-teaching concept: {str(e)}")


@router.post("/ask-ai-tutor")
async def ask_ai_tutor_endpoint(
    pdf_chunks: str = Body(..., embed=True),
    student_question: str = Body(..., embed=True),
    api_key: str = Body(None, embed=True)
):
    """
    Answer student questions using AI tutor with RAG from PDF content

    Args:
        pdf_chunks: Retrieved PDF chunks as context
        student_question: Student's question
        api_key: Optional Gemini API key

    Returns:
        Answer to student's question
    """
    try:
        result = await ask_ai_tutor(pdf_chunks, student_question, api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering student question: {str(e)}")


@router.post("/reflection-prompt")
async def reflection_prompt_endpoint(
    concept_data: Dict[str, Any] = Body(..., embed=True),
    student_response: str = Body(..., embed=True),
    api_key: str = Body(None, embed=True)
):
    """
    Provide feedback on student's explanation of a concept

    Args:
        concept_data: Concept information
        student_response: Student's explanation of the concept
        api_key: Optional Gemini API key

    Returns:
        Feedback on student's explanation
    """
    try:
        result = await reflection_prompt(concept_data, student_response, api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error providing reflection feedback: {str(e)}")


@router.post("/analyze-learning-state")
async def analyze_learning_state_endpoint(
    accuracy: float = Body(..., embed=True),
    response_time: float = Body(..., embed=True),
    attempts: int = Body(..., embed=True),
    api_key: str = Body(None, embed=True)
):
    """
    Analyze student's learning behavior and recommend adaptive strategies

    Args:
        accuracy: Student's accuracy percentage
        response_time: Average response time in seconds
        attempts: Number of attempts
        api_key: Optional Gemini API key

    Returns:
        Analysis of learning state with recommendations
    """
    try:
        result = await analyze_learning_state(accuracy, response_time, attempts, api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing learning state: {str(e)}")


@router.post("/detect-confusing-concepts")
async def detect_confusing_concepts_endpoint(
    class_analytics: str = Body(..., embed=True),
    api_key: str = Body(None, embed=True)
):
    """
    Detect confusing concepts based on class performance data

    Args:
        class_analytics: Class performance data
        api_key: Optional Gemini API key

    Returns:
        Analysis of confusing concepts
    """
    try:
        result = await detect_confusing_concepts(class_analytics, api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting confusing concepts: {str(e)}")


@router.post("/weekly-teacher-summary")
async def weekly_teacher_summary_endpoint(
    aggregated_class_data: str = Body(..., embed=True),
    api_key: str = Body(None, embed=True)
):
    """
    Generate a weekly summary for the teacher

    Args:
        aggregated_class_data: Aggregated class data
        api_key: Optional Gemini API key

    Returns:
        Weekly summary for the teacher
    """
    try:
        result = await generate_weekly_teacher_summary(aggregated_class_data, api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating weekly teacher summary: {str(e)}")


@router.post("/format-ui-explanation")
async def format_ui_explanation_endpoint(
    raw_explanation: str = Body(..., embed=True),
    api_key: str = Body(None, embed=True)
):
    """
    Format an explanation for UI display on a learning card

    Args:
        raw_explanation: Raw explanation text
        api_key: Optional Gemini API key

    Returns:
        Formatted explanation for UI display
    """
    try:
        result = await format_ui_friendly_explanation(raw_explanation, api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error formatting UI-friendly explanation: {str(e)}")
