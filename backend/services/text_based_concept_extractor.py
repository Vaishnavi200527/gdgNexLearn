#!/usr/bin/env python3
"""
Text-based Concept Extraction Service
Identifies key concepts from text without heavy AI dependencies
"""

import re
import nltk
from typing import List, Dict, Any, Tuple
from collections import Counter
import string

# Download required NLTK data (only once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

class TextBasedConceptExtractor:
    def __init__(self):
        self.stop_words = set(nltk.corpus.stopwords.words('english'))
        self.technical_indicators = [
            'definition', 'concept', 'theory', 'principle', 'method', 'approach',
            'algorithm', 'process', 'system', 'model', 'framework', 'technique',
            'procedure', 'strategy', 'mechanism', 'structure', 'function', 'operation'
        ]
        
    def extract_concepts_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract key concepts from text using linguistic patterns and statistical analysis
        
        Args:
            text: Input text from PDF
            
        Returns:
            List of identified concepts with their properties
        """
        # Clean and preprocess text
        cleaned_text = self._clean_text(text)
        
        # Extract potential concepts using multiple methods
        noun_phrases = self._extract_noun_phrases(cleaned_text)
        technical_terms = self._extract_technical_terms(cleaned_text)
        defined_terms = self._extract_defined_terms(cleaned_text)
        
        # Combine and rank concepts
        all_candidates = noun_phrases + technical_terms + defined_terms
        ranked_concepts = self._rank_concepts(all_candidates, cleaned_text)
        
        # Generate detailed concept information
        detailed_concepts = []
        for concept_data in ranked_concepts[:10]:  # Top 10 concepts
            concept_info = self._generate_concept_details(concept_data, cleaned_text)
            detailed_concepts.append(concept_info)
            
        return detailed_concepts
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for processing"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation for sentence detection
        text = re.sub(r'[^\w\s.,;:!?()-]', ' ', text)
        return text.strip()
    
    def _extract_noun_phrases(self, text: str) -> List[str]:
        """Extract noun phrases as potential concepts"""
        try:
            sentences = nltk.sent_tokenize(text)
            noun_phrases = []
            
            for sentence in sentences:
                tokens = nltk.word_tokenize(sentence)
                pos_tags = nltk.pos_tag(tokens)
                
                # Extract noun phrases (patterns like adjective+noun, noun+noun)
                current_phrase = []
                for i, (word, pos) in enumerate(pos_tags):
                    if pos.startswith('NN') or pos == 'JJ':  # Noun or adjective
                        current_phrase.append(word)
                    elif current_phrase and len(current_phrase) <= 3:  # Limit phrase length
                        phrase = ' '.join(current_phrase).lower()
                        if len(phrase) > 3 and phrase not in self.stop_words:
                            noun_phrases.append(phrase)
                        current_phrase = []
                    else:
                        current_phrase = []
                
                # Handle phrases at end of sentence
                if current_phrase and len(current_phrase) <= 3:
                    phrase = ' '.join(current_phrase).lower()
                    if len(phrase) > 3 and phrase not in self.stop_words:
                        noun_phrases.append(phrase)
            
            return list(set(noun_phrases))
        except Exception as e:
            print(f"Error extracting noun phrases: {e}")
            return []
    
    def _extract_technical_terms(self, text: str) -> List[str]:
        """Extract technical terms using patterns"""
        technical_terms = []
        
        # Pattern for capitalized terms (often technical concepts)
        capitalized_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        capitalized_terms = re.findall(capitalized_pattern, text)
        technical_terms.extend([term.lower() for term in capitalized_terms if len(term) > 3])
        
        # Pattern for acronyms
        acronym_pattern = r'\b[A-Z]{2,}\b'
        acronyms = re.findall(acronym_pattern, text)
        technical_terms.extend(acronyms)
        
        # Pattern for terms followed by definitions
        definition_pattern = r'(\w+(?:\s+\w+)*)\s+(?:is|are|refers to|means|defines?|describes?)\s+'
        definitions = re.findall(definition_pattern, text, re.IGNORECASE)
        technical_terms.extend([term.lower() for term in definitions if len(term) > 3])
        
        return list(set(technical_terms))
    
    def _extract_defined_terms(self, text: str) -> List[str]:
        """Extract terms that are explicitly defined in the text"""
        defined_terms = []
        
        # Pattern for explicit definitions
        definition_patterns = [
            r'(\w+(?:\s+\w+)*)\s*:\s*[^.]*\.?',  # Term: definition
            r'"([^"]+)"\s+(?:is|means|refers to)\s+[^.]*\.?',  # "Term" is/means
            r'(\w+(?:\s+\w+)*)\s+(?:can be defined as|is defined as)\s+[^.]*\.?',  # Term can be defined as
        ]
        
        for pattern in definition_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            defined_terms.extend([match.lower() for match in matches if len(match) > 3])
        
        return list(set(defined_terms))
    
    def _rank_concepts(self, candidates: List[str], text: str) -> List[Dict[str, Any]]:
        """Rank concepts by importance using various metrics"""
        concept_scores = {}
        word_count = len(text.split())
        
        for concept in candidates:
            score = 0
            
            # Frequency score
            frequency = text.lower().count(concept)
            score += frequency * 0.3
            
            # Length score (prefer medium-length concepts)
            length_score = 1.0 - abs(len(concept.split()) - 2) * 0.2
            score += max(0, length_score) * 0.2
            
            # Position score (concepts appearing earlier might be more important)
            first_occurrence = text.lower().find(concept)
            if first_occurrence != -1:
                position_score = 1.0 - (first_occurrence / len(text))
                score += position_score * 0.2
                
            # Technical indicator score
            if any(indicator in concept for indicator in self.technical_indicators):
                score += 0.3
                
            concept_scores[concept] = score
        
        # Sort by score and return top concepts
        ranked = sorted(concept_scores.items(), key=lambda x: x[1], reverse=True)
        return [{'concept': concept, 'score': score} for concept, score in ranked]
    
    def _generate_concept_details(self, concept_data: Dict[str, str], text: str) -> Dict[str, Any]:
        """Generate detailed information for a concept"""
        concept = concept_data['concept']
        score = concept_data['score']
        
        # Extract definition
        definition = self._extract_definition(concept, text)
        
        # Find examples
        examples = self._find_examples(concept, text)
        
        # Extract key points
        key_points = self._extract_key_points(concept, text)
        
        # Determine complexity
        complexity = self._determine_complexity(concept, text, score)
        
        # Find related terms
        related_terms = self._find_related_terms(concept, text)
        
        # Find applications
        applications = self._find_applications(concept, text)
        
        # Identify misconceptions
        misconceptions = self._identify_misconceptions(concept, text)
        
        return {
            'name': concept.title(),
            'definition': definition,
            'examples': examples,
            'key_points': key_points,
            'complexity': complexity,
            'related_terms': related_terms,
            'applications': applications,
            'common_misconceptions': misconceptions,
            'score': score,
            'word_count': len(definition.split()) + sum(len(ex.split()) for ex in examples)
        }
    
    def _extract_definition(self, concept: str, text: str) -> str:
        """Extract definition for a concept from text"""
        concept_lower = concept.lower()
        
        # Look for definition patterns
        definition_patterns = [
            rf'{concept_lower}\s+(?:is|are|refers to|means|defines?|describes?)\s+([^.!?]*[.!?])',
            rf'{concept_lower}\s*:\s*([^.!?]*[.!?])',
            rf'"?{concept_lower}"?\s+(?:can be defined as|is defined as)\s+([^.!?]*[.!?])',
        ]
        
        for pattern in definition_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        # If no explicit definition, create one from context
        sentences = nltk.sent_tokenize(text)
        for sentence in sentences:
            if concept_lower in sentence.lower():
                # Return the sentence as a contextual definition
                return sentence.strip()
        
        return f"{concept.title()} is a concept found in the provided text."
    
    def _find_examples(self, concept: str, text: str) -> List[str]:
        """Find examples related to the concept"""
        examples = []
        concept_lower = concept.lower()
        
        # Look for example indicators
        example_patterns = [
            rf'{concept_lower}[^.]*?(?:for example|for instance|such as|like)\s+([^.!?]*[.!?])',
            rf'for example[^.]*?{concept_lower}[^.!?]*([.!?])',
            rf'for instance[^.]*?{concept_lower}[^.!?]*([.!?])',
        ]
        
        for pattern in example_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            examples.extend(matches)
        
        return examples[:3]  # Limit to 3 examples
    
    def _extract_key_points(self, concept: str, text: str) -> List[str]:
        """Extract key points about the concept"""
        key_points = []
        concept_lower = concept.lower()
        
        # Look for sentences that contain the concept and important indicators
        sentences = nltk.sent_tokenize(text)
        for sentence in sentences:
            if concept_lower in sentence.lower():
                # Check for key point indicators
                if any(indicator in sentence.lower() for indicator in 
                       ['important', 'key', 'crucial', 'essential', 'significant', 'notable']):
                    key_points.append(sentence.strip())
        
        return key_points[:5]  # Limit to 5 key points
    
    def _determine_complexity(self, concept: str, text: str, score: float) -> str:
        """Determine complexity level of the concept"""
        # Factors for complexity
        word_count = len(concept.split())
        definition_length = len(self._extract_definition(concept, text))
        technical_terms_count = sum(1 for term in self.technical_indicators if term in concept.lower())
        
        # Simple heuristic for complexity
        if word_count <= 2 and definition_length < 100 and technical_terms_count == 0:
            return 'easy'
        elif word_count <= 3 and definition_length < 200 and technical_terms_count <= 1:
            return 'medium'
        else:
            return 'hard'
    
    def _find_related_terms(self, concept: str, text: str) -> List[str]:
        """Find terms related to the concept"""
        related_terms = []
        concept_lower = concept.lower()
        
        # Find sentences containing the concept
        sentences = [s for s in nltk.sent_tokenize(text) if concept_lower in s.lower()]
        
        # Extract other nouns from these sentences
        for sentence in sentences:
            tokens = nltk.word_tokenize(sentence)
            pos_tags = nltk.pos_tag(tokens)
            
            for word, pos in pos_tags:
                if (pos.startswith('NN') and 
                    word.lower() != concept_lower and 
                    word.lower() not in self.stop_words and
                    len(word) > 3):
                    related_terms.append(word.lower())
        
        # Return most common related terms
        term_counts = Counter(related_terms)
        return [term for term, count in term_counts.most_common(5)]
    
    def _find_applications(self, concept: str, text: str) -> List[str]:
        """Find real-world applications of the concept"""
        applications = []
        concept_lower = concept.lower()
        
        # Look for application indicators
        application_patterns = [
            rf'{concept_lower}[^.]*?(?:used in|applied in|application of|use of|utilized in)\s+([^.!?]*[.!?])',
            rf'{concept_lower}[^.]*?(?:helps|enables|allows|supports)\s+([^.!?]*[.!?])',
        ]
        
        for pattern in application_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            applications.extend(matches)
        
        return applications[:3]  # Limit to 3 applications
    
    def _identify_misconceptions(self, concept: str, text: str) -> List[str]:
        """Identify common misconceptions about the concept"""
        misconceptions = []
        concept_lower = concept.lower()
        
        # Look for misconception indicators
        misconception_patterns = [
            rf'{concept_lower}[^.]*?(?:is not|are not|not to be confused with|should not be|misconception|common mistake)\s+([^.!?]*[.!?])',
            rf'(?:however|but|although|while)\s+{concept_lower}[^.]*([.!?])',
        ]
        
        for pattern in misconception_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            misconceptions.extend(matches)
        
        return misconceptions[:2]  # Limit to 2 misconceptions
