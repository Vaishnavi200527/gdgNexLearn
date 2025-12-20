# AMEP - Adaptive Mastery & Engagement Platform

Backend API for the Adaptive Mastery & Engagement Platform hackathon prototype.

## Features

- Student and teacher authentication
- Adaptive learning with mastery tracking
- AI-powered assignment and project generation
- Project-based learning with team management
- Real-time engagement tracking
- Soft skill assessment
- Gamification (XP, streaks, leaderboards, badges)
- Teacher intervention for struggling students
- Duolingo-style concept progress
- Advanced AI content generation (PDF concept extraction, explanation variants, examples, micro-questions, answer evaluation)

## Tech Stack

- Python 3.10+
- FastAPI
- SQLite (for hackathon demo)
- SQLAlchemy ORM
- Pydantic for request/response validation

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd amep-backend
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install fastapi uvicorn sqlalchemy pydantic
   ```

4. Initialize the database:
   ```
   python seed_data.py
   ```

5. Run the server:
   ```
   python main.py
   ```

6. Access the API documentation:
   Open `http://localhost:8000/docs` in your browser

## API Endpoints

### Student Routes

- `POST /student/signup` - Register a new student
- `POST /student/login` - Login as a student
- `GET /student/mastery` - Fetch mastery scores and concept progress
- `GET /student/assignments` - Fetch adaptive homework
- `POST /student/assignments/submit` - Submit assignment
- `POST /student/engagement` - Log engagement
- `GET /student/projects` - List projects and teams
- `GET /student/leaderboard` - Class/global leaderboard
- `GET /student/badges` - List earned badges

### Teacher Routes

- `GET /teacher/ai/assignments?concept_id=XX` - AI suggests assignments
- `POST /teacher/ai/generate-quiz?topic=XX&difficulty=X&question_count=X` - AI generates quiz questions
- `POST /teacher/assignments/create` - Create assignments from AI suggestions
- `GET /teacher/ai/projects?skill_area=XX` - AI suggests projects
- `POST /teacher/projects/create` - Create projects from AI suggestions
- `POST /teacher/softskills/score` - Record soft skill ratings
- `GET /teacher/dashboard` - Class-wide dashboard
- `POST /teacher/intervene` - Intervene with struggling students
- `GET /teacher/interventions` - View all interventions

### AI Content Generation Routes

- `POST /ai/extract-concept` - Extract concept information from PDF text
- `POST /ai/generate-explanations` - Generate different explanation variants
- `POST /ai/generate-examples` - Generate examples from PDF context
- `POST /ai/generate-micro-questions` - Generate micro-questions for concepts
- `POST /ai/evaluate-answer` - Evaluate student answers
- `POST /ai/teach-concept` - Teach a concept to a student based on their level
- `POST /ai/reteach-concept` - Re-teach a concept in simpler terms
- `POST /ai/ask-ai-tutor` - Answer student questions using AI tutor
- `POST /ai/reflection-prompt` - Provide feedback on student's explanation
- `POST /ai/analyze-learning-state` - Analyze student's learning behavior and recommend adaptive strategies
- `POST /ai/detect-confusing-concepts` - Detect confusing concepts based on class performance data
- `POST /ai/weekly-teacher-summary` - Generate a weekly summary for the teacher
- `POST /ai/format-ui-explanation` - Format an explanation for UI display on a learning card

### PDF Upload Routes

- `POST /pdf-upload/process-pdf` - Process uploaded PDF file and extract educational concepts
- `POST /pdf-upload/create-adaptive-assignment` - Create an adaptive assignment from processed PDF concepts and assign to class

## Demo Data

The seed script creates:
- 5 students and 2 teachers
- 5 learning concepts
- Sample assignments and projects
- Engagement logs, soft skill scores, and gamification data
- Teacher interventions for struggling students

## Architecture

```
amep-backend/
├── main.py              # FastAPI app entry point
├── database.py          # Database configuration
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── seed_data.py         # Demo data seeding
├── routers/             # API route handlers
│   ├── student.py       # Student endpoints
│   ├── teacher.py       # Teacher endpoints
│   └── ai_content.py    # AI content generation endpoints
└── services/            # Business logic
    ├── adaptive_learning.py
    ├── ai_content_generation.py
    ├── engagement_tracking.py
    ├── gamification.py
    ├── soft_skills.py
    └── teacher_interventions.py
```