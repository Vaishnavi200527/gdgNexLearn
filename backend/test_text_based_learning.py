#!/usr/bin/env python3
"""
Test script for the text-based learning system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.text_based_concept_extractor import TextBasedConceptExtractor
from services.detailed_explanation_generator import DetailedExplanationGenerator

def test_concept_extraction():
    """Test the concept extraction functionality"""
    print("Testing concept extraction...")
    
    # Sample text about machine learning
    sample_text = """
    Machine Learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. 
    It focuses on the development of computer programs that can access data and use it to learn for themselves.
    
    The process of learning begins with observations or data, such as examples, direct experience, or instruction, in order to look for patterns in data and make better decisions in the future based on the examples that we provide.
    
    Deep Learning is a subset of machine learning that uses neural networks with multiple layers to analyze various forms of data. These networks are inspired by the structure and function of the human brain.
    
    Supervised learning is a type of machine learning where the algorithm learns from labeled training data. In supervised learning, the algorithm is provided with input-output pairs.
    
    Unsupervised learning is a type of machine learning where the algorithm works with unlabeled data. The goal is to find hidden patterns and structures in the data.
    """
    
    extractor = TextBasedConceptExtractor()
    concepts = extractor.extract_concepts_from_text(sample_text)
    
    print(f"Found {len(concepts)} concepts:")
    for i, concept in enumerate(concepts[:5], 1):
        print(f"{i}. {concept['name']} (Score: {concept['score']:.2f})")
        print(f"   Definition: {concept.get('definition', 'N/A')[:100]}...")
        print(f"   Complexity: {concept.get('complexity', 'N/A')}")
        print()
    
    return concepts

def test_explanation_generation():
    """Test the detailed explanation generation"""
    print("Testing explanation generation...")
    
    sample_text = """
    Machine Learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. 
    It focuses on the development of computer programs that can access data and use it to learn for themselves.
    
    The process of learning begins with observations or data, such as examples, direct experience, or instruction, in order to look for patterns in data and make better decisions in the future based on the examples that we provide.
    
    Deep Learning is a subset of machine learning that uses neural networks with multiple layers to analyze various forms of data.
    """
    
    extractor = TextBasedConceptExtractor()
    generator = DetailedExplanationGenerator()
    
    concepts = extractor.extract_concepts_from_text(sample_text)
    
    if concepts:
        concept = concepts[0]  # Test with the first concept
        print(f"Generating detailed explanation for: {concept['name']}")
        
        explanation = generator.generate_comprehensive_explanation(concept, sample_text)
        
        print(f"Title: {explanation['title']}")
        print(f"Definition: {explanation['definition']}")
        print(f"Examples: {explanation['examples']}")
        print(f"Key Points: {explanation['key_points']}")
        print(f"Complexity: {explanation['complexity_level']}")
        print(f"Word Count: {explanation['word_count']}")
        print()
        
        return explanation
    else:
        print("No concepts found for explanation generation test")
        return None

def test_different_detail_levels():
    """Test different detail levels"""
    print("Testing different detail levels...")
    
    sample_text = """
    Neural Networks are computing systems inspired by biological neural networks. 
    They consist of interconnected nodes or neurons that process information using connectionist approaches.
    """
    
    extractor = TextBasedConceptExtractor()
    generator = DetailedExplanationGenerator()
    
    concepts = extractor.extract_concepts_from_text(sample_text)
    
    if concepts:
        concept = concepts[0]
        
        for level in ['basic', 'medium', 'comprehensive']:
            print(f"\n--- {level.upper()} LEVEL ---")
            explanation = generator.generate_explanation_by_complexity(concept, sample_text, level)
            print(f"Word Count: {explanation['word_count']}")
            print(f"Definition: {explanation.get('definition', 'N/A')[:100]}...")
            if 'examples' in explanation:
                print(f"Examples: {len(explanation['examples'])}")
            if 'key_points' in explanation:
                print(f"Key Points: {len(explanation['key_points'])}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("TEXT-BASED LEARNING SYSTEM TEST")
    print("=" * 60)
    
    try:
        # Test concept extraction
        concepts = test_concept_extraction()
        
        print("\n" + "=" * 60)
        
        # Test explanation generation
        explanation = test_explanation_generation()
        
        print("\n" + "=" * 60)
        
        # Test different detail levels
        test_different_detail_levels()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
