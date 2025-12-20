import os
import json
import asyncio
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import schemas
import models

# Load environment variables
load_dotenv()

# Template-based content generation (fallback when API unavailable)
CONTENT_TEMPLATES = {
    "assignment": {
        1: {
            "title": "{concept} Fundamentals Quiz",
            "description": "Test your understanding of basic {concept} concepts including {topics}",
            "objectives": [
                "Identify key {concept} principles",
                "Apply basic {concept} techniques",
                "Solve simple {concept} problems"
            ]
        },
        2: {
            "title": "{concept} Practice Exercises",
            "description": "Practice applying {concept} through hands-on exercises covering {topics}",
            "objectives": [
                "Implement {concept} solutions",
                "Debug common {concept} issues",
                "Optimize {concept} performance"
            ]
        },
        3: {
            "title": "{concept} Advanced Challenges",
            "description": "Tackle complex {concept} problems requiring deep understanding of {topics}",
            "objectives": [
                "Design sophisticated {concept} systems",
                "Analyze {concept} trade-offs",
                "Evaluate {concept} best practices"
            ]
        }
    },
    "project": {
        "app_development": {
            "title": "{skill_area} Application Project",
            "description": "Build a complete {skill_area} application that demonstrates core concepts",
            "outcomes": [
                "Apply {skill_area} design patterns",
                "Implement user authentication",
                "Deploy a production-ready application"
            ]
        },
        "data_analysis": {
            "title": "{skill_area} Analytics Dashboard",
            "description": "Create a dashboard to visualize and analyze {skill_area} data trends",
            "outcomes": [
                "Process large datasets",
                "Create interactive visualizations",
                "Generate actionable insights"
            ]
        }
    }
}

# AI Prompts for Core Educational Functions
AI_PROMPTS = {
    "pdf_concept_extraction": """
You are an education content analyzer.

From the text below, extract:
- Main concept name
- Definition
- Key points (3–6 bullets)
- Prerequisite concepts (if any)
- Difficulty level (easy, medium, hard)

Return ONLY valid JSON in this format:
{{
  "concept": "",
  "definition": "",
  "key_points": [],
  "prerequisites": [],
  "difficulty": ""
}}

Text:
{pdf_text}""",

    "explanation_variant_generator": """
You are a teacher.

Generate three explanations for the concept below:
1. Simple – very easy language, beginner-friendly
2. Standard – normal classroom explanation
3. Compact – short, exam-focused

Return ONLY JSON:
{{
  "simple": "",
  "standard": "",
  "compact": ""
}}

Concept data:
{concept_data}""",

    "example_generator": """
You are an educational assistant.

Using ONLY the information provided below, generate:
- One simple example
- One exam-oriented example

Do not introduce new concepts.

Context:
{pdf_context}""",

    "micro_question_generator": """
Create 2 very basic questions for the concept below.

Rules:
- One MCQ
- One fill-in-the-blank
- Beginner level

Return JSON:
{{
  "mcq": {{
    "question": "",
    "options": [],
    "answer": ""
  }},
  "fill_blank": {{
    "question": "",
    "answer": ""
  }}
}}

Concept:
{concept_data}""",

    "answer_evaluation": """
Evaluate the student's answer.

Concept:
{concept_name}

Correct answer:
{correct_answer}

Student answer:
{student_answer}

Return ONLY JSON:
{{
  "is_correct": true,
  "confidence": "low | medium | high",
  "feedback": ""
}}""",

    "concept_teaching": """
You are teaching a student.

Student level: {student_level}
Explanation type: {explanation_type}

Explain the concept clearly using:
- Short paragraphs
- Bullet points
- Simple language

Concept:
{concept_data}""",

    "reteach_concept": """
The student did not understand the concept.

Re-explain it:
- Using simpler words
- With a new example
- Without technical jargon

Concept:
{concept_data}""",

    "ask_ai_tutor": """
You are a tutor helping a student with their studies.

Answer the student's question using ONLY the context below.
If the answer is not present in the context, say:
"This topic is not covered in your notes."

Context:
{pdf_chunks}

Question:
{student_question}""",

    "reflection_prompt": """
Ask the student to explain the concept in their own words.
Then give short constructive feedback.

Concept:
{concept_data}

Student response:
{student_response}""",

    "learning_state_analyzer": """
Analyze the student's learning behavior.

Inputs:
- Accuracy: {accuracy}%
- Average response time (seconds): {response_time}
- Attempts: {attempts}

Return JSON:
{{
  "learning_speed": "slow | normal | fast",
  "recommended_explanation": "simple | standard | compact",
  "needs_revision": true
}}""",

    "confusing_concept_detector": """
Analyze the class performance data.

Identify:
- Concepts with high error rate
- Concepts taking the most time

Return a short, teacher-friendly summary.

Data:
{class_analytics}""",

    "weekly_teacher_summary": """
Generate a weekly summary for the teacher.

Include:
- Overall class progress
- Students who need attention
- Most confusing topics

Data:
{aggregated_class_data}""",

    "ui_friendly_explanation_formatter": """
Rewrite the explanation below for display on a learning card.

Rules:
- Max 6 bullet points
- Clear and concise
- Highlight important keywords

Text:
{raw_explanation}""",
    
    "contextual_question_answering": """
You are an AI tutor helping a student understand a specific concept.

Use the provided context to answer the student's question accurately and concisely.
If the information needed to answer the question is not in the context, respond with:
"I don't have enough information about that in your notes. Please check with your teacher for more details."

Context:
{context}

Student Question:
{question}

Your response should be educational and encouraging, helping the student understand the concept better."""
}

def generate_assignment_prompt(concept_name: str, difficulty: int, topics: List[str]) -> str:
    """Generate prompt for assignment creation"""
    template = CONTENT_TEMPLATES["assignment"].get(difficulty, CONTENT_TEMPLATES["assignment"][2])
    topics_str = ", ".join(topics)
    
    return f"""
    Create a {concept_name} assignment for students.
    
    Title: {template['title'].format(concept_name=concept_name)}
    Description: {template['description'].format(concept_name=concept_name, topics=topics_str)}
    Difficulty Level: {difficulty}/5
    Estimated Time: {difficulty * 15 + 10} minutes
    
    Learning Objectives:
    {chr(10).join([f"- {obj.format(concept_name=concept_name)}" for obj in template['objectives']])}
    
    Please format the response as JSON with the following structure:
    {{
        "title": "Assignment Title",
        "description": "Detailed description",
        "difficulty_level": 1-5,
        "estimated_time": 15,
        "learning_objectives": ["objective1", "objective2", "objective3"]
    }}
    """

def generate_project_prompt(skill_area: str, project_type: str) -> str:
    """Generate prompt for project creation"""
    template = CONTENT_TEMPLATES["project"].get(project_type, CONTENT_TEMPLATES["project"]["app_development"])
    
    return f"""
    Create a {skill_area} project idea for students.
    
    Title: {template['title'].format(skill_area=skill_area)}
    Description: {template['description'].format(skill_area=skill_area)}
    Duration: {20 + len(skill_area) * 2} hours
    Team Size: {3 if 'app' in project_type else 4} members
    
    Learning Outcomes:
    {chr(10).join([f"- {outcome.format(skill_area=skill_area)}" for outcome in template['outcomes']])}
    
    Please format the response as JSON with the following structure:
    {{
        "title": "Project Title",
        "description": "Detailed description",
        "duration_hours": 20,
        "team_size": 3,
        "learning_outcomes": ["outcome1", "outcome2", "outcome3"]
    }}
    """

async def call_gemini_api(prompt: str, api_key: str = None) -> dict:
    """Call Gemini API to generate content"""
    # Use the provided API key or get from environment
    if not api_key:
        from dotenv import load_dotenv
        import os
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    # Make actual API call to Gemini
    try:
        import google.generativeai as genai
        
        # Configure the API
        genai.configure(api_key=api_key)
        
        # List available models and use the first one that supports generateContent
        available_models = [m for m in genai.list_models() 
                          if 'generateContent' in m.supported_generation_methods]
        
        if not available_models:
            raise ValueError("No models available with generateContent support")
            
        # Use the first available model that supports generateContent
        model_name = available_models[0].name
        print(f"Using model: {model_name}")
        
        # Create the model
        model = genai.GenerativeModel(model_name)
        
        # Generate content
        response = await model.generate_content_async(prompt)
        
        # Try to parse the JSON response
        import json
        try:
            response_data = json.loads(response.text)
        except json.JSONDecodeError:
            # If JSON parsing fails, create a structured response from the text
            response_data = {
                "topic": "Generated Content",
                "difficulty": 3,
                "questions": [
                    {
                        "id": 1,
                        "type": "Short Answer",
                        "question": response.text[:200] + "..." if len(response.text) > 200 else response.text,
                        "options": None,
                        "correct_answer": "See explanation above"
                    }
                ]
            }
        return response_data
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        print(f"API Key used: {api_key[:10]}... (truncated for security)")
        # Re-raise the exception instead of falling back
        raise

def simulate_gemini_response(prompt: str) -> dict:
    """Simulate Gemini API response with topic-appropriate questions"""
    import re
    
    # Extract topic and question count from prompt
    topic_match = re.search(r'Generate \d+ quiz questions about (.+?) at difficulty', prompt)
    topic = topic_match.group(1).strip() if topic_match else "General Knowledge"
    
    count_match = re.search(r'(\d+) quiz questions', prompt)
    question_count = int(count_match.group(1)) if count_match else 5
    
    # Generic question templates that work for any topic
    mcq_templates = [
        f"What is the primary purpose or function of {topic}?",
        f"Which of the following best describes a key concept in {topic}?",
        f"What is the most important principle to understand about {topic}?",
        f"Which of these is a common application of {topic}?",
        f"What differentiates {topic} from similar concepts in the field?"
    ]
    
    tf_templates = [
        f"{topic} is considered a fundamental concept in its field.",
        f"The principles of {topic} can be applied across multiple domains.",
        f"Understanding {topic} requires advanced mathematical knowledge.",
        f"{topic} was first introduced in the 21st century.",
        f"Practical applications of {topic} are still theoretical and not yet implemented."
    ]
    
    sa_templates = [
        f"Explain the basic concept of {topic} in your own words.",
        f"Describe how {topic} is used in practical applications.",
        f"What are the main components or elements of {topic}?",
        f"Compare and contrast {topic} with a related concept.",
        f"What are the potential benefits of understanding {topic}?"
    ]
    
    fib_templates = [
        f"The main idea behind {topic} is _____ .",
        f"One real-world application of {topic} is _____ .",
        f"The study of {topic} became important in the field of _____ .",
        f"A key principle in {topic} is _____ .",
        f"When working with {topic}, it's essential to consider _____ ."
    ]
    
    # Generate generic but relevant options
    mcq_options = [
        [f"A specific aspect of {topic}", f"A related but different concept", "A common misconception", "An outdated approach"],
        ["Theoretical foundation", "Practical implementation", "Historical context", "Future predictions"],
        ["Core principle", "Minor detail", "Common myth", "Outdated practice"],
        ["Real-world problem solving", "Theoretical discussion", "Historical analysis", "Future speculation"],
        ["Fundamental approach", "Implementation method", "Theoretical basis", "Practical limitation"]
    ]
    
    mcq_answers = [f"A specific aspect of {topic}", "Theoretical foundation", "Core principle", "Real-world problem solving", "Fundamental approach"]
    tf_answers = ["True", "True", "False", "False", "False"]
    sa_answers = [
        f"{topic} is a concept that involves... (student should explain in their own words)",
        f"{topic} can be applied in various ways including... (student should provide examples)",
        f"The main components of {topic} include... (student should list key elements)",
        f"While {topic} focuses on..., a related concept differs by... (student should compare and contrast)",
        f"Understanding {topic} can help with... (student should list benefits)"
    ]
    fib_answers = [
        f"to understand and work with {topic} effectively",
        f"in various industries such as technology, healthcare, or education",
        f"computer science, engineering, or data analysis",
        f"understanding its core principles and applications",
        f"both theoretical foundations and practical implications"
    ]
    
    questions = []
    question_types = ["Multiple Choice", "True or False", "Short Answer", "Fill in the Blank"]
    
    for i in range(min(question_count, 5)):  # Limit to 5 questions
        q_type = question_types[i % 4]
        
        if q_type == "Multiple Choice":
            questions.append({
                "id": i+1,
                "type": q_type,
                "question": mcq_templates[i % len(mcq_templates)].format(topic=topic),
                "options": mcq_options[i % len(mcq_options)],
                "correct_answer": mcq_answers[i % len(mcq_answers)]
            })
        elif q_type == "True or False":
            questions.append({
                "id": i+1,
                "type": q_type,
                "question": tf_templates[i % len(tf_templates)].format(topic=topic),
                "options": None,
                "correct_answer": tf_answers[i % len(tf_answers)]
            })
        elif q_type == "Short Answer":
            questions.append({
                "id": i+1,
                "type": q_type,
                "question": sa_templates[i % len(sa_templates)].format(topic=topic),
                "options": None,
                "correct_answer": sa_answers[i % len(sa_answers)]
            })
        else:  # Fill in the Blank
            questions.append({
                "id": i+1,
                "type": q_type,
                "question": fib_templates[i % len(fib_templates)].format(topic=topic),
                "options": None,
                "correct_answer": fib_answers[i % len(fib_answers)]
            })
    
    # For any remaining questions beyond 5, use generic templates
    for i in range(5, question_count):
        q_type = question_types[i % 4]
        if q_type == "Multiple Choice":
            questions.append({
                "id": i+1,
                "type": q_type,
                "question": f"What is a key aspect of {topic}?",
                "options": [f"Aspect {i+1}A", f"Aspect {i+1}B", f"Aspect {i+1}C", f"Aspect {i+1}D"],
                "correct_answer": f"Aspect {i+1}B"
            })
        elif q_type == "True or False":
            questions.append({
                "id": i+1,
                "type": q_type,
                "question": f"{topic} is an important subject.",
                "options": None,
                "correct_answer": "True"
            })
        else:
            questions.append({
                "id": i+1,
                "type": q_type,
                "question": f"Explain a key concept of {topic}.",
                "options": None,
                "correct_answer": f"Key concept explanation for {topic}"
            })
    
    return {
        "topic": topic,
        "difficulty": 3,  # Default difficulty
        "questions": questions
    }

def generate_assignments(concept_id: int, db: Session, api_key: str = None) -> List[schemas.AIGeneratedAssignment]:
    """
    Generate AI-suggested assignments for a concept using Gemini API or templates.
    
    Args:
        concept_id: ID of the concept to generate assignments for
        db: Database session
        api_key: Optional Gemini API key
        
    Returns:
        List of generated assignments
    """
    concept = db.query(models.Concepts).filter(models.Concepts.id == concept_id).first()
    if not concept:
        # Fallback to template-based generation
        template = CONTENT_TEMPLATES["assignment"][2]  # Medium difficulty
        assignments = [
            schemas.AIGeneratedAssignment(
                concept_id=concept_id,
                title=template["title"].format(concept="Programming"),
                description=template["description"].format(concept="Programming", topics="fundamentals"),
                difficulty_level=2,
                estimated_time=40,
                learning_objectives=template["objectives"]
            )
        ]
        return assignments

    # Generate assignments for different difficulty levels
    assignments = []
    topics = ["basics", "intermediate", "advanced"]

    for difficulty in [1, 2, 3]:
        # Try to call Gemini API
        prompt = generate_assignment_prompt(concept.name, difficulty, topics[:difficulty])

        try:
            # Call Gemini API with fallback
            response = asyncio.run(call_gemini_api(prompt, api_key))

            assignment = schemas.AIGeneratedAssignment(
                concept_id=concept_id,
                title=response["title"],
                description=response["description"],
                difficulty_level=response["difficulty_level"],
                estimated_time=response["estimated_time"],
                learning_objectives=response["learning_objectives"]
            )
            assignments.append(assignment)
        except Exception as e:
            # Fallback to template-based generation
            template = CONTENT_TEMPLATES["assignment"].get(difficulty, CONTENT_TEMPLATES["assignment"][2])
            fallback_assignment = schemas.AIGeneratedAssignment(
                concept_id=concept_id,
                title=template["title"].format(concept=concept.name),
                description=template["description"].format(concept=concept.name, topics=", ".join(topics[:difficulty])),
                difficulty_level=difficulty,
                estimated_time=difficulty * 15 + 10,
                learning_objectives=[obj.format(concept=concept.name) for obj in template["objectives"]]
            )
            assignments.append(fallback_assignment)

    return assignments

async def generate_quiz_questions(topic: str, num_questions: int = 5, difficulty: str = "medium", api_key: str = None) -> List[Dict[str, Any]]:
    """
    Generate quiz questions using the Gemini API.
    
    Args:
        topic (str): The topic for the quiz
        num_questions (int): Number of questions to generate (default: 5)
        difficulty (str): Difficulty level (easy, medium, hard)
        api_key (str, optional): Gemini API key. If not provided, will use from environment.
        
    Returns:
        List[Dict[str, Any]]: List of quiz questions with answers and explanations
    """
    try:
        # Get API key from environment if not provided
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                # Try loading .env file directly if not found in environment
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("No Gemini API key provided. Please set GEMINI_API_KEY in your .env file or pass it as a parameter.")
        
        # Configure Gemini
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # List available models and use the first one that supports generateContent
        available_models = [m for m in genai.list_models() 
                          if 'generateContent' in m.supported_generation_methods]
        
        if not available_models:
            raise ValueError("No models available with generateContent support")
            
        # Use the first available model that supports generateContent
        model_name = available_models[0].name
        print(f"Using model: {model_name}")
        
        model = genai.GenerativeModel(model_name)
        
        # Create prompt
        prompt = f"""Generate {num_questions} {difficulty} difficulty multiple-choice questions about {topic}.
        For each question, provide:
        1. The question
        2. 4 possible answers (a, b, c, d)
        3. The correct answer
        4. A brief explanation
        
        Format the response as a JSON array of objects with these fields:
        [
            {{
                "question": "question text",
                "options": ["option a", "option b", "option c", "option d"],
                "correct_answer": "a",
                "explanation": "brief explanation"
            }}
        ]"""
        
        # Generate content
        response = await model.generate_content_async(prompt)
        
        # Parse response
        try:
            # Extract JSON from response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[response_text.find('['):response_text.rfind(']')+1]
            
            questions = json.loads(response_text)
            return questions
            
        except json.JSONDecodeError as e:
            print(f"Error parsing Gemini response: {e}")
            print(f"Response was: {response.text}")
            return []
            
    except Exception as e:
        print(f"Error generating quiz questions: {str(e)}")
        return []

def generate_projects(skill_area: str, db: Session, api_key: str = None):
    """
    Generate AI-suggested projects for a skill area using Gemini API or templates.
    """
    projects = []
    project_types = ["app_development", "data_analysis"]
    
    for project_type in project_types:
        # Try to call Gemini API
        prompt = generate_project_prompt(skill_area, project_type)
        
        try:
            # Call Gemini API with fallback
            response = asyncio.run(call_gemini_api(prompt, api_key))
            
            project = schemas.AIGeneratedProject(
                title=response["title"],
                description=response["description"],
                skill_area=skill_area,
                duration_hours=response["duration_hours"],
                team_size=response["team_size"],
                learning_outcomes=response["learning_outcomes"]
            )
            projects.append(project)
        except Exception as e:
            # Fallback to template-based generation
            template = CONTENT_TEMPLATES["project"].get(project_type, CONTENT_TEMPLATES["project"]["app_development"])
            fallback_project = schemas.AIGeneratedProject(
                title=template["title"].format(skill_area=skill_area),
                description=template["description"].format(skill_area=skill_area),
                skill_area=skill_area,
                duration_hours=20 + len(skill_area) * 2,
                team_size=3 if 'app' in project_type else 4,
                learning_outcomes=[outcome.format(skill_area=skill_area) for outcome in template["outcomes"]]
            )
            projects.append(fallback_project)
    
    return projects


def extract_concept_from_pdf(pdf_text: str, api_key: str = None) -> dict:
    """
    Extract concept information from PDF text using AI.
    
    Args:
        pdf_text (str): The extracted text from a PDF
        api_key (str, optional): Gemini API key
        
    Returns:
        dict: Extracted concept information
    """
    prompt = AI_PROMPTS["pdf_concept_extraction"].format(pdf_text=pdf_text)
    try:
        response = asyncio.run(call_gemini_api(prompt, api_key))
        return response
    except Exception as e:
        print(f"Error extracting concept from PDF: {e}")
        # Return a default structure if extraction fails
        return {
            "concept": "Unknown Concept",
            "definition": "Definition not available",
            "key_points": [],
            "prerequisites": [],
            "difficulty": "medium"
        }


def generate_explanation_variants(concept_data: dict, api_key: str = None) -> dict:
    """
    Generate different explanation variants for a concept.
    
    Args:
        concept_data (dict): Concept information
        api_key (str, optional): Gemini API key
        
    Returns:
        dict: Different explanation variants (simple, standard, compact)
    """
    # Convert concept data to JSON string for the prompt
    concept_json = json.dumps(concept_data, indent=2)
    prompt = AI_PROMPTS["explanation_variant_generator"].format(concept_data=concept_json)
    
    try:
        response = asyncio.run(call_gemini_api(prompt, api_key))
        return response
    except Exception as e:
        print(f"Error generating explanation variants: {e}")
        # Return default explanations if generation fails
        return {
            "simple": f"A simple explanation of {concept_data.get('concept', 'the concept')}.",
            "standard": f"A standard explanation of {concept_data.get('concept', 'the concept')}.",
            "compact": f"A compact explanation of {concept_data.get('concept', 'the concept')}.",
        }


def generate_examples_from_context(pdf_context: str, api_key: str = None) -> dict:
    """
    Generate examples based on PDF context.
    
    Args:
        pdf_context (str): Context from PDF
        api_key (str, optional): Gemini API key
        
    Returns:
        dict: Generated examples (simple, exam-oriented)
    """
    prompt = AI_PROMPTS["example_generator"].format(pdf_context=pdf_context)
    
    try:
        response = asyncio.run(call_gemini_api(prompt, api_key))
        return response
    except Exception as e:
        print(f"Error generating examples: {e}")
        # Return default examples if generation fails
        return {
            "simple_example": "A simple example based on the context.",
            "exam_example": "An exam-oriented example based on the context."
        }


def generate_micro_questions(concept_data: dict, api_key: str = None) -> dict:
    """
    Generate micro-questions for concept understanding.
    
    Args:
        concept_data (dict): Concept information
        api_key (str, optional): Gemini API key
        
    Returns:
        dict: Generated micro-questions (MCQ and fill-in-the-blank)
    """
    # Convert concept data to JSON string for the prompt
    concept_json = json.dumps(concept_data, indent=2)
    prompt = AI_PROMPTS["micro_question_generator"].format(concept_data=concept_json)
    
    try:
        response = asyncio.run(call_gemini_api(prompt, api_key))
        return response
    except Exception as e:
        print(f"Error generating micro-questions: {e}")
        # Return default questions if generation fails
        return {
            "mcq": {
                "question": f"What is {concept_data.get('concept', 'the concept')}?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "answer": "Option A"
            },
            "fill_blank": {
                "question": f"_____ is a key aspect of {concept_data.get('concept', 'the concept')}.",
                "answer": "Concept"
            }
        }


def evaluate_student_answer(concept_name: str, correct_answer: str, student_answer: str, api_key: str = None) -> dict:
    """
    Evaluate a student's answer.
    
    Args:
        concept_name (str): Name of the concept
        correct_answer (str): Correct answer
        student_answer (str): Student's answer
        api_key (str, optional): Gemini API key
        
    Returns:
        dict: Evaluation result with correctness, confidence, and feedback
    """
    prompt = AI_PROMPTS["answer_evaluation"].format(
        concept_name=concept_name,
        correct_answer=correct_answer,
        student_answer=student_answer
    )
    
    try:
        response = asyncio.run(call_gemini_api(prompt, api_key))
        return response
    except Exception as e:
        print(f"Error evaluating student answer: {e}")
        # Return a default evaluation if assessment fails
        return {
            "is_correct": student_answer.lower() == correct_answer.lower(),
            "confidence": "low",
            "feedback": "Unable to assess answer automatically. Please review manually."
        }


def teach_concept(concept_data: dict, student_level: str = "average", explanation_type: str = "standard", api_key: str = None) -> dict:
    """
    Teach a concept to a student based on their level and preferred explanation type.
    
    Args:
        concept_data (dict): Concept information
        student_level (str): Student level (beginner, average, advanced)
        explanation_type (str): Explanation type (simple, standard, compact)
        api_key (str, optional): Gemini API key
        
    Returns:
        dict: Teaching material for the concept
    """
    # Convert concept data to JSON string for the prompt
    concept_json = json.dumps(concept_data, indent=2)
    prompt = AI_PROMPTS["concept_teaching"].format(
        student_level=student_level,
        explanation_type=explanation_type,
        concept_data=concept_json
    )
    
    try:
        response = asyncio.run(call_gemini_api(prompt, api_key))
        return response
    except Exception as e:
        print(f"Error teaching concept: {e}")
        # Return a default explanation if generation fails
        return {
            "explanation": f"Here's an explanation of {concept_data.get('concept', 'the concept')}...",
            "key_points": ["Key point 1", "Key point 2", "Key point 3"],
            "examples": ["Example 1", "Example 2"]
        }


def reteach_concept(concept_data: dict, api_key: str = None) -> dict:
    """
    Re-teach a concept in simpler terms when student struggles.
    
    Args:
        concept_data (dict): Concept information
        api_key (str, optional): Gemini API key
        
    Returns:
        dict: Simplified explanation of the concept
    """
    # Convert concept data to JSON string for the prompt
    concept_json = json.dumps(concept_data, indent=2)
    prompt = AI_PROMPTS["reteach_concept"].format(concept_data=concept_json)
    
    try:
        response = asyncio.run(call_gemini_api(prompt, api_key))
        return response
    except Exception as e:
        print(f"Error re-teaching concept: {e}")
        # Return a simplified default explanation if generation fails
        return {
            "simplified_explanation": f"Let me explain {concept_data.get('concept', 'this concept')} in a simpler way...",
            "simple_example": "Here's a simple example...",
            "key_terms": ["Term 1", "Term 2"]
        }


def ask_ai_tutor(pdf_chunks: str, student_question: str, api_key: str = None) -> dict:
    """
    Answer student questions using AI tutor with RAG from PDF content.
    
    Args:
        pdf_chunks (str): Retrieved PDF chunks as context
        student_question (str): Student's question
        api_key (str, optional): Gemini API key
        
    Returns:
        dict: Answer to student's question
    """
    prompt = AI_PROMPTS["ask_ai_tutor"].format(
        pdf_chunks=pdf_chunks,
        student_question=student_question
    )
    
    try:
        response = asyncio.run(call_gemini_api(prompt, api_key))
        return response
    except Exception as e:
        print(f"Error answering student question: {e}")
        # Return a default response if generation fails
        return {
            "answer": "This topic is not covered in your notes.",
            "related_topics": []
        }


def answer_student_question_with_context(context: str, question: str, api_key: str = None) -> dict:
    """
    Answer a student's question using contextual information.
    
    Args:
        context (str): Context information to base the answer on
        question (str): Student's question
        api_key (str, optional): Gemini API key
        
    Returns:
        dict: Answer to student's question with educational value
    """
    prompt = AI_PROMPTS["contextual_question_answering"].format(
        context=context,
        question=question
    )
    
    try:
        response = asyncio.run(call_gemini_api(prompt, api_key))
        return response
    except Exception as e:
        print(f"Error answering student question with context: {e}")
        # Return a default response if generation fails
        return {
            "answer": "I'm sorry, I couldn't generate a response at the moment. Please try rephrasing your question or consult your teacher.",
            "explanation": "This response was generated due to a system error.",
            "related_concepts": []
        }


def reflection_prompt(concept_data: dict, student_response: str, api_key: str = None) -> dict:
    """
    Provide feedback on student's explanation of a concept.
    
    Args:
        concept_data (dict): Concept information
        student_response (str): Student's explanation of the concept
        api_key (str, optional): Gemini API key
        
    Returns:
        dict: Feedback on student's explanation
    """
    # Convert concept data to JSON string for the prompt
    concept_json = json.dumps(concept_data, indent=2)
    prompt = AI_PROMPTS["reflection_prompt"].format(
        concept_data=concept_json,
        student_response=student_response
    )
    
    try:
        response = asyncio.run(call_gemini_api(prompt, api_key))
        return response
    except Exception as e:
        print(f"Error providing reflection feedback: {e}")
        # Return default feedback if generation fails
        return {
            "feedback": "Thanks for your response. Here's some general feedback on concept explanation...",
            "strengths": ["Strength 1"],
            "areas_for_improvement": ["Area 1"]
        }


def analyze_learning_state(accuracy: float, response_time: float, attempts: int, api_key: str = None) -> dict:
    """
    Analyze student's learning behavior and recommend adaptive strategies.
    
    Args:
        accuracy (float): Student's accuracy percentage
        response_time (float): Average response time in seconds
        attempts (int): Number of attempts
        api_key (str, optional): Gemini API key
        
    Returns:
        dict: Analysis of learning state with recommendations
    """
    prompt = AI_PROMPTS["learning_state_analyzer"].format(
        accuracy=accuracy,
        response_time=response_time,
        attempts=attempts
    )
    
    try:
        response = asyncio.run(call_gemini_api(prompt, api_key))
        return response
    except Exception as e:
        print(f"Error analyzing learning state: {e}")
        # Return default analysis if generation fails
        return {
            "learning_speed": "normal",
            "recommended_explanation": "standard",
            "needs_revision": False
        }


def detect_confusing_concepts(class_analytics: str, api_key: str = None) -> dict:
    """
    Detect confusing concepts based on class performance data.
    
    Args:
        class_analytics (str): Class performance data
        api_key (str, optional): Gemini API key
        
    Returns:
        dict: Analysis of confusing concepts
    """
    prompt = AI_PROMPTS["confusing_concept_detector"].format(class_analytics=class_analytics)
    
    try:
        response = asyncio.run(call_gemini_api(prompt, api_key))
        return response
    except Exception as e:
        print(f"Error detecting confusing concepts: {e}")
        # Return default analysis if generation fails
        return {
            "high_error_concepts": [],
            "time_consuming_concepts": [],
            "summary": "Unable to analyze class performance data."
        }


def generate_weekly_teacher_summary(aggregated_class_data: str, api_key: str = None) -> dict:
    """
    Generate a weekly summary for the teacher.
    
    Args:
        aggregated_class_data (str): Aggregated class data
        api_key (str, optional): Gemini API key
        
    Returns:
        dict: Weekly summary for the teacher
    """
    prompt = AI_PROMPTS["weekly_teacher_summary"].format(aggregated_class_data=aggregated_class_data)
    
    try:
        response = asyncio.run(call_gemini_api(prompt, api_key))
        return response
    except Exception as e:
        print(f"Error generating weekly teacher summary: {e}")
        # Return default summary if generation fails
        return {
            "overall_progress": "Unable to determine class progress.",
            "students_needing_attention": [],
            "confusing_topics": []
        }


def format_ui_friendly_explanation(raw_explanation: str, api_key: str = None) -> dict:
    """
    Format an explanation for UI display on a learning card.
    
    Args:
        raw_explanation (str): Raw explanation text
        api_key (str, optional): Gemini API key
        
    Returns:
        dict: Formatted explanation for UI display
    """
    prompt = AI_PROMPTS["ui_friendly_explanation_formatter"].format(raw_explanation=raw_explanation)
    
    try:
        response = asyncio.run(call_gemini_api(prompt, api_key))
        return response
    except Exception as e:
        print(f"Error formatting UI-friendly explanation: {e}")
        # Return default formatted explanation if generation fails
        return {
            "formatted_explanation": raw_explanation,
            "bullet_points": ["Key point 1", "Key point 2", "Key point 3"],
            "keywords": ["keyword1", "keyword2"]
        }