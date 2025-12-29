#!/usr/bin/env python3
"""
Detailed Explanation Generation Service
Creates comprehensive, structured explanations for identified concepts
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import nltk
from .text_based_concept_extractor import TextBasedConceptExtractor

class DetailedExplanationGenerator:
    def __init__(self):
        self.concept_extractor = TextBasedConceptExtractor()
        
    def generate_comprehensive_explanation(self, concept_data: Dict[str, Any], full_text: str) -> Dict[str, Any]:
        """
        Generate a comprehensive explanation for a concept with all required components
        
        Args:
            concept_data: Basic concept information from extractor
            full_text: Full text from the PDF
            
        Returns:
            Complete explanation with all components
        """
        concept_name = concept_data['name']
        
        # Generate all explanation components
        explanation = {
            'title': concept_name,
            'definition': self._enhance_definition(concept_data.get('definition', ''), full_text),
            'detailed_explanation': self._generate_detailed_explanation(concept_name, full_text),
            'examples': self._enhance_examples(concept_data.get('examples', []), full_text),
            'key_points': self._enhance_key_points(concept_data.get('key_points', []), full_text),
            'prerequisites': self._identify_prerequisites(concept_name, full_text),
            'step_by_step_breakdown': self._generate_step_by_step(concept_name, full_text),
            'related_terms': self._enhance_related_terms(concept_data.get('related_terms', []), full_text),
            'applications': self._enhance_applications(concept_data.get('applications', []), full_text),
            'common_misconceptions': self._enhance_misconceptions(concept_data.get('common_misconceptions', []), full_text),
            'complexity_level': concept_data.get('complexity', 'medium'),
            'word_count': 0,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Calculate total word count
        explanation['word_count'] = self._calculate_word_count(explanation)
        
        return explanation
    
    def _enhance_definition(self, basic_definition: str, full_text: str) -> str:
        """Enhance the basic definition with more context and clarity"""
        if not basic_definition or basic_definition.endswith("found in the provided text."):
            # Try to extract a better definition
            enhanced = self._extract_comprehensive_definition(full_text)
            return enhanced if enhanced else basic_definition
        
        # Enhance existing definition
        enhanced_parts = [basic_definition]
        
        # Add context if available
        context_sentences = self._find_context_sentences(basic_definition, full_text)
        if context_sentences:
            enhanced_parts.append("Context: " + " ".join(context_sentences[:2]))
        
        return " ".join(enhanced_parts)
    
    def _extract_comprehensive_definition(self, text: str) -> str:
        """Extract a comprehensive definition from text"""
        sentences = nltk.sent_tokenize(text)
        
        # Look for definition-rich sentences
        definition_sentences = []
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in 
                   ['is defined as', 'refers to', 'means', 'can be described as', 'represents']):
                definition_sentences.append(sentence)
        
        if definition_sentences:
            return " ".join(definition_sentences[:2])
        
        return ""
    
    def _find_context_sentences(self, definition: str, text: str) -> List[str]:
        """Find sentences that provide context for the definition"""
        sentences = nltk.sent_tokenize(text)
        context_sentences = []
        
        # Look for sentences that contain key terms from the definition
        definition_words = set(definition.lower().split())
        
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            overlap = len(definition_words.intersection(sentence_words))
            
            if overlap > 2 and sentence not in definition:  # Significant overlap but not the definition itself
                context_sentences.append(sentence)
        
        return context_sentences
    
    def _generate_detailed_explanation(self, concept_name: str, full_text: str) -> str:
        """Generate a detailed explanation combining multiple sources"""
        concept_lower = concept_name.lower()
        
        # Collect all sentences mentioning the concept
        sentences = nltk.sent_tokenize(full_text)
        relevant_sentences = []
        
        for sentence in sentences:
            if concept_lower in sentence.lower():
                relevant_sentences.append(sentence)
        
        # Organize by themes
        explanation_parts = []
        
        # Introduction
        if relevant_sentences:
            explanation_parts.append(f"{concept_name} is a fundamental concept discussed in this material.")
        
        # Core explanation
        core_sentences = [s for s in relevant_sentences if 
                        any(indicator in s.lower() for indicator in 
                           ['is', 'are', 'represents', 'involves', 'consists of', 'comprises'])]
        if core_sentences:
            explanation_parts.extend(core_sentences[:3])
        
        # Additional details
        detail_sentences = [s for s in relevant_sentences if s not in core_sentences]
        if detail_sentences:
            explanation_parts.extend(detail_sentences[:2])
        
        return " ".join(explanation_parts) if explanation_parts else f"{concept_name} is an important concept covered in the provided material."
    
    def _enhance_examples(self, basic_examples: List[str], full_text: str) -> List[str]:
        """Enhance and expand examples"""
        enhanced_examples = basic_examples.copy()
        
        # Look for more examples in the text
        example_patterns = [
            r'for example[^.]*', r'for instance[^.]*', r'such as[^.]*', 
            r'like[^.]*', r'including[^.]*'
        ]
        
        for pattern in example_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 10 and match not in enhanced_examples:
                    enhanced_examples.append(match.strip())
        
        return enhanced_examples[:5]  # Limit to 5 examples
    
    def _enhance_key_points(self, basic_points: List[str], full_text: str) -> List[str]:
        """Enhance and expand key points"""
        enhanced_points = basic_points.copy()
        
        # Look for sentences with importance indicators
        importance_indicators = [
            'important', 'significant', 'key', 'crucial', 'essential', 
            'notable', 'critical', 'vital', 'fundamental'
        ]
        
        sentences = nltk.sent_tokenize(full_text)
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in importance_indicators):
                if sentence not in enhanced_points and len(sentence) > 15:
                    enhanced_points.append(sentence)
        
        return enhanced_points[:8]  # Limit to 8 key points
    
    def _identify_prerequisites(self, concept_name: str, full_text: str) -> List[str]:
        """Identify prerequisites for understanding the concept"""
        prerequisites = []
        concept_lower = concept_name.lower()
        
        # Look for prerequisite indicators
        prerequisite_patterns = [
            rf'before understanding {concept_lower}[^.]*?([^.!?]*)',
            rf'to understand {concept_lower}[^.]*?([^.!?]*)',
            rf'{concept_lower}[^.]*?(?:requires|builds on|assumes|presupposes)\s+([^.!?]*)',
        ]
        
        for pattern in prerequisite_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 5:
                    prerequisites.append(match.strip())
        
        # Look for mentions of other concepts that seem foundational
        sentences = [s for s in nltk.sent_tokenize(full_text) if concept_lower in s.lower()]
        for sentence in sentences:
            # Look for patterns suggesting prerequisites
            if any(indicator in sentence.lower() for indicator in 
                   ['first', 'before', 'prior', 'foundation', 'basic', 'fundamental']):
                # Extract other concepts mentioned
                words = nltk.word_tokenize(sentence)
                pos_tags = nltk.pos_tag(words)
                
                for word, pos in pos_tags:
                    if (pos.startswith('NN') and 
                        word.lower() != concept_lower and 
                        len(word) > 3 and
                        word.lower() not in ['concept', 'idea', 'approach', 'method']):
                        prerequisites.append(f"Understanding of {word}")
        
        return list(set(prerequisites))[:4]  # Limit to 4 unique prerequisites
    
    def _generate_step_by_step(self, concept_name: str, full_text: str) -> List[str]:
        """Generate step-by-step breakdown for the concept"""
        steps = []
        concept_lower = concept_name.lower()
        
        # Look for sequential indicators
        sequential_patterns = [
            rf'first[^.]*{concept_lower}[^.]*([.!?])',
            rf'second[^.]*{concept_lower}[^.]*([.!?])',
            rf'third[^.]*{concept_lower}[^.]*([.!?])',
            rf'next[^.]*{concept_lower}[^.]*([.!?])',
            rf'then[^.]*{concept_lower}[^.]*([.!?])',
            rf'finally[^.]*{concept_lower}[^.]*([.!?])',
        ]
        
        for pattern in sequential_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            steps.extend([match.strip() for match in matches])
        
        # Look for numbered steps
        numbered_pattern = rf'\d+\.[^.]*{concept_lower}[^.]*([.!?])'
        numbered_matches = re.findall(numbered_pattern, full_text, re.IGNORECASE)
        steps.extend([match.strip() for match in numbered_matches])
        
        # If no explicit steps found, create logical steps from content
        if not steps:
            steps = self._create_logical_steps(concept_name, full_text)
        
        return steps[:6]  # Limit to 6 steps
    
    def _create_logical_steps(self, concept_name: str, full_text: str) -> List[str]:
        """Create logical steps when explicit steps aren't found"""
        steps = []
        concept_lower = concept_name.lower()
        
        # Extract sentences about the concept
        sentences = [s for s in nltk.sent_tokenize(full_text) if concept_lower in s.lower()]
        
        if sentences:
            # Step 1: Introduction/Definition
            definition_sentences = [s for s in sentences if 
                                  any(indicator in s.lower() for indicator in ['is', 'are', 'defines'])]
            if definition_sentences:
                steps.append(f"Step 1: Understand the definition - {definition_sentences[0]}")
            
            # Step 2: Key components
            component_sentences = [s for s in sentences if 
                                  any(indicator in s.lower() for indicator in ['consists', 'comprises', 'includes'])]
            if component_sentences:
                steps.append(f"Step 2: Identify components - {component_sentences[0]}")
            
            # Step 3: Process/Method
            process_sentences = [s for s in sentences if 
                                any(indicator in s.lower() for indicator in ['process', 'method', 'approach'])]
            if process_sentences:
                steps.append(f"Step 3: Learn the process - {process_sentences[0]}")
            
            # Step 4: Application
            application_sentences = [s for s in sentences if 
                                   any(indicator in s.lower() for indicator in ['application', 'use', 'apply'])]
            if application_sentences:
                steps.append(f"Step 4: Understand applications - {application_sentences[0]}")
        
        return steps
    
    def _enhance_related_terms(self, basic_terms: List[str], full_text: str) -> List[str]:
        """Enhance related terms with descriptions"""
        enhanced_terms = []
        
        for term in basic_terms[:5]:  # Limit to 5 terms
            # Find sentences that define or explain the related term
            term_sentences = []
            sentences = nltk.sent_tokenize(full_text)
            
            for sentence in sentences:
                if term.lower() in sentence.lower():
                    if any(indicator in sentence.lower() for indicator in 
                           ['is', 'are', 'refers to', 'means', 'defines']):
                        term_sentences.append(sentence)
            
            if term_sentences:
                enhanced_terms.append(f"{term.title()}: {term_sentences[0]}")
            else:
                enhanced_terms.append(term.title())
        
        return enhanced_terms
    
    def _enhance_applications(self, basic_applications: List[str], full_text: str) -> List[str]:
        """Enhance applications with more detail"""
        enhanced_applications = []
        
        for app in basic_applications:
            # Make sure it's a complete application description
            if len(app.strip()) > 10:
                enhanced_applications.append(app.strip())
        
        # Look for more applications in the text
        application_patterns = [
            r'used in[^.]*', r'applied in[^.]*', r'application[^.]*', 
            r'practical use[^.]*', r'real-world[^.]*'
        ]
        
        for pattern in application_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 15 and match not in enhanced_applications:
                    enhanced_applications.append(match.strip())
        
        return enhanced_applications[:4]  # Limit to 4 applications
    
    def _enhance_misconceptions(self, basic_misconceptions: List[str], full_text: str) -> List[str]:
        """Enhance misconceptions with clearer explanations"""
        enhanced_misconceptions = []
        
        for misconception in basic_misconceptions:
            # Format as a clear misconception statement
            if not misconception.startswith('Common misconception'):
                enhanced_misconceptions.append(f"Common misconception: {misconception.strip()}")
            else:
                enhanced_misconceptions.append(misconception.strip())
        
        # Look for more misconception indicators
        misconception_patterns = [
            r'is not[^.]*', r'should not be[^.]*', r'avoid[^.]*', 
            r'incorrect[^.]*', r'mistake[^.]*', r'confusion[^.]*'
        ]
        
        for pattern in misconception_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 10 and match not in enhanced_misconceptions:
                    enhanced_misconceptions.append(f"Common misconception: {match.strip()}")
        
        return enhanced_misconceptions[:3]  # Limit to 3 misconceptions
    
    def _calculate_word_count(self, explanation: Dict[str, Any]) -> int:
        """Calculate total word count for the explanation"""
        total_words = 0
        
        # Count words in all text fields
        text_fields = [
            explanation.get('definition', ''),
            explanation.get('detailed_explanation', ''),
            " ".join(explanation.get('examples', [])),
            " ".join(explanation.get('key_points', [])),
            " ".join(explanation.get('prerequisites', [])),
            " ".join(explanation.get('step_by_step_breakdown', [])),
            " ".join(explanation.get('related_terms', [])),
            " ".join(explanation.get('applications', [])),
            " ".join(explanation.get('common_misconceptions', []))
        ]
        
        for text in text_fields:
            total_words += len(text.split())
        
        return total_words
    
    def generate_explanation_by_complexity(self, concept_data: Dict[str, Any], full_text: str, 
                                         detail_level: str = 'medium') -> Dict[str, Any]:
        """
        Generate explanation with varying detail levels based on complexity
        
        Args:
            concept_data: Basic concept information
            full_text: Full text from PDF
            detail_level: 'basic', 'medium', or 'comprehensive'
            
        Returns:
            Explanation adjusted for the specified detail level
        """
        base_explanation = self.generate_comprehensive_explanation(concept_data, full_text)
        
        if detail_level == 'basic':
            return self._create_basic_explanation(base_explanation)
        elif detail_level == 'comprehensive':
            return self._create_comprehensive_explanation(base_explanation)
        else:  # medium
            return base_explanation
    
    def _create_basic_explanation(self, full_explanation: Dict[str, Any]) -> Dict[str, Any]:
        """Create a basic level explanation"""
        return {
            'title': full_explanation['title'],
            'definition': full_explanation['definition'],
            'examples': full_explanation['examples'][:2],
            'key_points': full_explanation['key_points'][:3],
            'complexity_level': 'basic',
            'word_count': len(full_explanation['definition'].split()) + 
                         sum(len(ex.split()) for ex in full_explanation['examples'][:2]) +
                         sum(len(kp.split()) for kp in full_explanation['key_points'][:3])
        }
    
    def _create_comprehensive_explanation(self, full_explanation: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive level explanation"""
        return full_explanation  # Return the full explanation
