#!/usr/bin/env python3
"""
Test script for the new AI prompt functions
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

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
import json

def test_pdf_concept_extraction():
    """Test PDF concept extraction"""
    sample_text = """
    Machine Learning is a subset of artificial intelligence that enables computers to learn and make decisions 
    from data without being explicitly programmed. It uses statistical techniques to give computers the 
    ability to "learn" from data and improve their performance on a specific task over time.
    
    Key aspects include:
    - Supervised learning
    - Unsupervised learning
    - Reinforcement learning
    
    Applications range from recommendation systems to autonomous vehicles.
    """
    
    print("Testing PDF Concept Extraction...")
    result = extract_concept_from_pdf(sample_text)
    print(json.dumps(result, indent=2))
    print()

def test_explanation_generation():
    """Test explanation variant generation"""
    concept_data = {
        "concept": "Machine Learning",
        "definition": "A subset of artificial intelligence that enables computers to learn from data",
        "key_points": [
            "Supervised learning",
            "Unsupervised learning", 
            "Reinforcement learning"
        ],
        "prerequisites": ["Statistics", "Programming"],
        "difficulty": "medium"
    }
    
    print("Testing Explanation Variant Generation...")
    result = generate_explanation_variants(concept_data)
    print(json.dumps(result, indent=2))
    print()

def test_example_generation():
    """Test example generation"""
    context = """
    Machine Learning algorithms can be categorized into three main types:
    1. Supervised learning - Uses labeled training data
    2. Unsupervised learning - Finds patterns in unlabeled data
    3. Reinforcement learning - Learns through interaction with an environment
    """
    
    print("Testing Example Generation...")
    result = generate_examples_from_context(context)
    print(json.dumps(result, indent=2))
    print()

def test_micro_question_generation():
    """Test micro-question generation"""
    concept_data = {
        "concept": "Neural Networks",
        "definition": "Computational models inspired by the human brain",
        "key_points": [
            "Consist of layers of interconnected nodes",
            "Can learn complex patterns in data",
            "Used in deep learning applications"
        ],
        "prerequisites": ["Linear Algebra", "Calculus"],
        "difficulty": "hard"
    }
    
    print("Testing Micro Question Generation...")
    result = generate_micro_questions(concept_data)
    print(json.dumps(result, indent=2))
    print()

def test_answer_evaluation():
    """Test student answer evaluation"""
    print("Testing Answer Evaluation...")
    result = evaluate_student_answer(
        concept_name="Database Indexing",
        correct_answer="An index is a data structure that improves the speed of data retrieval operations",
        student_answer="Indexing helps find data faster in databases"
    )
    print(json.dumps(result, indent=2))
    print()


def test_concept_teaching():
    """Test concept teaching"""
    concept_data = {
        "concept": "Neural Networks",
        "definition": "Computational models inspired by the human brain",
        "key_points": [
            "Consist of layers of interconnected nodes",
            "Can learn complex patterns in data",
            "Used in deep learning applications"
        ],
        "prerequisites": ["Linear Algebra", "Calculus"],
        "difficulty": "hard"
    }
    
    print("Testing Concept Teaching...")
    result = teach_concept(concept_data, "beginner", "simple")
    print(json.dumps(result, indent=2))
    print()


def test_reteach_concept():
    """Test re-teaching concept"""
    concept_data = {
        "concept": "Blockchain",
        "definition": "A distributed ledger technology",
        "key_points": [
            "Decentralized",
            "Immutable records",
            "Cryptographic security"
        ],
        "prerequisites": ["Basic Computer Science"],
        "difficulty": "medium"
    }
    
    print("Testing Re-teach Concept...")
    result = reteach_concept(concept_data)
    print(json.dumps(result, indent=2))
    print()


def test_ask_ai_tutor():
    """Test AI tutor question answering"""
    pdf_chunks = """
    Machine Learning is a subset of artificial intelligence that enables computers to learn from data.
    It uses statistical techniques to give computers the ability to "learn" from data.
    Key types include supervised learning, unsupervised learning, and reinforcement learning.
    """
    
    print("Testing AI Tutor...")
    result = ask_ai_tutor(pdf_chunks, "What is supervised learning?")
    print(json.dumps(result, indent=2))
    print()


def test_reflection_prompt():
    """Test reflection prompt with feedback"""
    concept_data = {
        "concept": "Object Oriented Programming",
        "definition": "A programming paradigm based on objects containing data and methods",
        "key_points": [
            "Encapsulation",
            "Inheritance",
            "Polymorphism"
        ],
        "prerequisites": ["Basic Programming"],
        "difficulty": "medium"
    }
    student_response = "OOP is about organizing code with classes and objects. Classes are blueprints and objects are instances."
    
    print("Testing Reflection Prompt...")
    result = reflection_prompt(concept_data, student_response)
    print(json.dumps(result, indent=2))
    print()


def test_learning_state_analysis():
    """Test learning state analysis"""
    print("Testing Learning State Analysis...")
    result = analyze_learning_state(
        accuracy=75.5,
        response_time=12.3,
        attempts=3
    )
    print(json.dumps(result, indent=2))
    print()


def test_confusing_concept_detection():
    """Test confusing concept detection"""
    class_analytics = """
    Class Performance Data:
    - Concept A: 85% accuracy, avg time 45s
    - Concept B: 45% accuracy, avg time 120s
    - Concept C: 90% accuracy, avg time 30s
    - Concept D: 30% accuracy, avg time 90s
    """
    
    print("Testing Confusing Concept Detection...")
    result = detect_confusing_concepts(class_analytics)
    print(json.dumps(result, indent=2))
    print()


def test_weekly_teacher_summary():
    """Test weekly teacher summary generation"""
    aggregated_class_data = """
    Week of April 1-7:
    - Overall class progress: 75%
    - Students needing attention: ["John Doe", "Jane Smith"]
    - Most confusing topics: ["Database Normalization", "Recursion"]
    """
    
    print("Testing Weekly Teacher Summary...")
    result = generate_weekly_teacher_summary(aggregated_class_data)
    print(json.dumps(result, indent=2))
    print()


def test_ui_friendly_explanation_formatting():
    """Test UI-friendly explanation formatting"""
    raw_explanation = """
    Machine Learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed. 
    It uses statistical techniques to give computers the ability to "learn" from data and improve their performance on a specific task over time.
    Key aspects include supervised learning, unsupervised learning, and reinforcement learning.
    Applications range from recommendation systems to autonomous vehicles.
    """
    
    print("Testing UI-Friendly Explanation Formatting...")
    result = format_ui_friendly_explanation(raw_explanation)
    print(json.dumps(result, indent=2))
    print()

if __name__ == "__main__":
    print("Running AI Prompt Tests...\n")
    
    test_pdf_concept_extraction()
    test_explanation_generation()
    test_example_generation()
    test_micro_question_generation()
    test_answer_evaluation()
    test_concept_teaching()
    test_reteach_concept()
    test_ask_ai_tutor()
    test_reflection_prompt()
    test_learning_state_analysis()
    test_confusing_concept_detection()
    test_weekly_teacher_summary()
    test_ui_friendly_explanation_formatting()
    
    print("All tests completed!")