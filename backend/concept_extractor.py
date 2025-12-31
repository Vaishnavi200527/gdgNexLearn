import json
import logging
import re
import os
import google.generativeai as genai
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

def extract_clean_pdf_text_only(text_content: str) -> Tuple[str, List[str]]:
    """
    ULTRA-AGGRESSIVE cleaning that removes ALL UI noise, fragments, and extracts only clean content.
    Returns: (cleaned_text, valid_headings_found)
    """
    if not text_content:
        return "", []
    
    # REMOVE ALL UI NOISE COMPLETELY
    ui_patterns = [
        # Platform UI - MUST BE REMOVED
        r'Step\s*\d+:\s*Review\s*Extracted\s*Content',
        r'Extracted\s*Concepts',
        r'medium\s*Estimated\s*time:\s*\d+\s*minutes\s*auto_awesome\s*Adaptive\s*Learning',
        r'medium\s*Estimated\s*time:\s*\d+\s*minutes',
        r'auto_awesome\s*Adaptive\s*Learning',
        r'Estimated\s*time:\s*\d+\s*minutes',
        
        # Remove ALL individual UI words
        r'\bmedium\b',
        r'\bestimated\b',
        r'\bauto_awesome\b',
        r'\badaptive\b',
        r'\blearning\b',
        r'\bminutes\b',
        r'\b30\s*minutes\b',
        
        # Remove noise headers
        r'SEE\s*WHAT\s*IS\s*HAPPENING',
        r'SEE\s*HOW\s*IT\s*IS\s*EXTRACTING',
        r'SEEE\s*BELOW\s*HOW\s*IT\s*IS\s*EXTRACTING',
    ]
    
    for pattern in ui_patterns:
        text_content = re.sub(pattern, '', text_content, flags=re.IGNORECASE)
    
    # Remove ALL bullet characters and symbols
    bullet_chars = ['■', '●', '•', '→', '←', '↑', '↓', '►', '◄', '◆', '◇', '❑', '✓', '✗']
    for char in bullet_chars:
        text_content = text_content.replace(char, '')
    
    # REMOVE ALL MEANINGLESS FRAGMENTS (like the ones you're seeing)
    meaningless_patterns = [
        # Sentence fragments
        r'\n\s*The\s+values\s*\n',
        r'\n\s*The\s+sorted\s+values\s*\n',
        r'\n\s*Mostly\s+data\s*\n',
        r'\n\s*These\s+tests\s*\n',
        r'\n\s*The\s+Observed\s+values\s*\n',
        r'\n\s*The\s+expected\s+values\s*\n',
        r'\n\s*Smoothing\s+by\s+bin\s*\n',
        r'\n\s*Skewed\s+data\s*\n',
        
        # Short meaningless phrases
        r'\b[A-Z][a-z]+\s+data\b(?=\s|$)',
        r'\bThe\s+[A-Za-z]+\b(?=\s|$)',
        r'\bBest\s+used\s+when\s+data\b',
        
        # Remove lines that are too short or meaningless
        r'^\s*\w{1,3}\s*$',  # Single short words
        r'^\s*[^.\n]{0,20}\s*$',  # Very short lines
    ]
    
    for pattern in meaningless_patterns:
        text_content = re.sub(pattern, '', text_content, flags=re.MULTILINE)
    
    # Extract VALID headings from the text (not random fragments)
    valid_headings = []
    
    # Pattern 1: Proper section headings (with or without numbers)
    heading_patterns = [
        r'\b([A-Z][a-z]+(?:\s+[A-Za-z][a-z]+){1,4})\b\s*(?::|$)',  # Title with colon or end
        r'\n\s*([A-Z][A-Za-z\s]{10,60})\n',  # Lines that look like headings
        r'\d+\.\s*([A-Z][A-Za-z\s]{10,60})\b',  # Numbered sections
    ]
    
    for pattern in heading_patterns:
        matches = re.findall(pattern, text_content)
        for match in matches:
            heading = match.strip()
            # Validate it's a real heading, not noise
            if (len(heading) > 8 and 
                len(heading.split()) >= 2 and 
                heading[0].isupper() and
                not any(word in heading.lower() for word in ['example', 'figure', 'table', 'step', 'see'])):
                valid_headings.append(heading)
    
    # Remove duplicates
    valid_headings = list(dict.fromkeys(valid_headings))
    
    # Clean the text further
    text_content = re.sub(r'\s+', ' ', text_content)
    text_content = re.sub(r'\n\s*\n+', '\n\n', text_content)
    text_content = text_content.strip()
    
    return text_content, valid_headings[:20]  # Return clean text and found headings

def create_ai_prompt_for_concepts(clean_text: str, found_headings: List[str]) -> str:
    """
    Create a STRICT prompt that forces extraction of ONLY meaningful concepts.
    """
    # Provide examples of what to EXCLUDE
    bad_examples = [
        "The values", "The sorted values", "Mostly data", "These tests",
        "The Observed values", "The expected values", "Smoothing by bin",
        "Skewed data", "Best used when data", "Handle Noisy Data"
    ]
    
    prompt = f"""EXTRACT 10-15 KEY CONCEPTS from this educational text.

CRITICAL RULES:
1. CONCEPT NAMES MUST BE:
   - Meaningful noun phrases (e.g., "Data Preprocessing", "Binning Methods", "Chi-Square Test")
   - EXACT phrases from the text
   - Professional and specific
   
2. ABSOLUTELY REJECT THESE AS CONCEPTS:
   {', '.join(bad_examples)}
   - Any sentence fragments starting with "The", "These", "Mostly"
   - Any generic phrases
   - Any UI elements (medium, estimated time, etc.)

3. FOR EACH CONCEPT, CREATE THIS EXACT FORMAT:
   - First line: Clear definition
   - THEN: \\n\\n (TWO newlines - REQUIRED)
   - THEN: * Bullet point 1
   - THEN: * Bullet point 2
   - THEN: * Bullet point 3

4. EXAMPLE OF CORRECT OUTPUT:
{{
  "name": "Data Preprocessing",
  "description": "Data preprocessing transforms raw data into a useful and efficient format for analysis.\\n\\n* Includes data cleaning, integration, transformation, and reduction* Essential step before data mining* Improves data quality and accuracy"
}}

5. POTENTIAL VALID CONCEPTS FOUND IN TEXT (use these as guidance):
{', '.join(found_headings[:10]) if found_headings else "None found"}

SOURCE TEXT:
{clean_text[:8000]}...

EXTRACT EXACTLY 10-15 VALID CONCEPTS FOLLOWING THESE RULES. OUTPUT ONLY JSON."""
    
    return prompt

def extract_concepts_with_gemini(text_content: str) -> List[Dict[str, str]]:
    """
    Main function to extract concepts using Gemini AI with STRICT filtering.
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found")
            return []
        
        # STEP 1: ULTRA-CLEAN the text
        clean_text, found_headings = extract_clean_pdf_text_only(text_content)
        
        if len(clean_text) < 200:
            logger.warning("Text too short after cleaning")
            return []
        
        logger.info(f"Found {len(found_headings)} potential headings in text")
        
        # STEP 2: Configure Gemini
        genai.configure(api_key=api_key)
        
        # Try to use gemini-1.5-flash, fallback to available models if it fails
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # STEP 3: Create STRICT prompt
            prompt = create_ai_prompt_for_concepts(clean_text, found_headings)
            
            # STEP 4: Get response
            response = model.generate_content(prompt)
        except Exception as e:
            logger.warning(f"Failed to use gemini-1.5-flash: {e}. Attempting fallback to available models.")
            
            # List available models
            available_models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            if not available_models:
                logger.error("No available Gemini models found.")
                return []
            
            # Use the first available model (usually gemini-pro or similar)
            model_name = available_models[0].name
            logger.info(f"Falling back to model: {model_name}")
            
            model = genai.GenerativeModel(model_name)
            prompt = create_ai_prompt_for_concepts(clean_text, found_headings)
            response = model.generate_content(prompt)
            
        response_text = response.text.strip()
        
        # STEP 5: Parse JSON response
        # Clean response text
        response_text = re.sub(r'```json\s*|\s*```', '', response_text)
        response_text = re.sub(r'^\s*\[\s*|\s*\]\s*$', '', response_text)
        
        try:
            # Parse as JSON array
            concepts_data = json.loads(f'[{response_text}]')
        except json.JSONDecodeError:
            # Try to extract JSON array with regex
            json_match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
            if json_match:
                concepts_data = json.loads(json_match.group(0))
            else:
                logger.error("Could not parse JSON from response")
                return []
        
        # STEP 6: VALIDATE and FILTER concepts
        valid_concepts = []
        
        for concept in concepts_data:
            if not isinstance(concept, dict):
                continue
            
            name = concept.get('name', '').strip()
            description = concept.get('description', '').strip()
            
            # STRICT VALIDATION
            if not name or not description:
                continue
            
            # REJECT meaningless names
            meaningless_patterns = [
                r'^The\s+',
                r'^These\s+',
                r'^Mostly\s+',
                r'^Best\s+used',
                r'^Handle\s+',
                r'^\w+\s+data$',
                r'^\w+\s+values$',
            ]
            
            if any(re.search(pattern, name, re.IGNORECASE) for pattern in meaningless_patterns):
                continue
            
            # Must have at least 2 words and reasonable length
            if len(name.split()) < 2 or len(name) < 5:
                continue
            
            # Description must have proper formatting
            if '\\n\\n' not in description and '\n\n' not in description:
                # Try to format it
                sentences = description.split('. ')
                if len(sentences) > 1:
                    description = f"{sentences[0]}.\\n\\n* " + "\n* ".join(sentences[1:3])
            
            valid_concepts.append({
                "name": name,
                "description": description
            })
            
            if len(valid_concepts) >= 15:
                break
        
        logger.info(f"Extracted {len(valid_concepts)} valid concepts")
        return valid_concepts
        
    except Exception as e:
        logger.error(f"Error in extract_concepts_with_gemini: {e}", exc_info=True)
        return []

# For backward compatibility
def extract_concepts_with_ai(text_content: str) -> list:
    return extract_concepts_with_gemini(text_content)