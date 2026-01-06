from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"

class EngagementType(str, Enum):
    PROJECT_WORK = "project_work"
    ASSIGNMENT = "assignment"
    DISCUSSION = "discussion"

class AssignmentStatus(str, Enum):
    ASSIGNED = "assigned"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    GRADED = "graded"

# Base Models
class UserBase(BaseModel):
    name: str
    email: str
    role: UserRole

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(UserBase):
    id: int
    
    class Config:
        from_attributes = True

class ConceptBase(BaseModel):
    name: str
    description: str
    irt_difficulty: float = 0.0
    discrimination_index: float = 1.0
    id_slug: Optional[str] = None
    prerequisite_ids: Optional[str] = None

class ConceptCreate(ConceptBase):
    pass

class ConceptResponse(ConceptBase):
    id: int
    
    class Config:
        from_attributes = True

class StudentMasteryBase(BaseModel):
    student_id: int
    concept_id: int
    mastery_score: float = Field(ge=0, le=100)

class StudentMasteryCreate(StudentMasteryBase):
    pass

class StudentMasteryResponse(StudentMasteryBase):
    class Config:
        from_attributes = True

class AssignmentBase(BaseModel):
    concept_id: int
    difficulty_level: int = Field(ge=1, le=5)
    content_url: Optional[str]
    title: str
    description: str

class AssignmentCreate(AssignmentBase):
    pass

class AssignmentResponse(AssignmentBase):
    id: int
    
    class Config:
        from_attributes = True

class StudentAssignmentBase(BaseModel):
    student_id: int
    assignment_id: int
    status: AssignmentStatus = AssignmentStatus.ASSIGNED
    score: Optional[float] = Field(None, ge=0, le=100)

class StudentAssignmentCreate(StudentAssignmentBase):
    pass

class StudentAssignmentResponse(StudentAssignmentBase):
    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    title: str
    description: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]

class ProjectCreate(ProjectBase):
    evaluation_rubric: List[Dict[str, Any]] = []

class ProjectResponse(ProjectBase):
    id: int
    teacher_id: int
    evaluation_rubric: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True

class ProjectTeamBase(BaseModel):
    project_id: int
    student_id: int
    role: str

class ProjectTeamCreate(ProjectTeamBase):
    pass

class ProjectTeamResponse(ProjectTeamBase):
    class Config:
        from_attributes = True

class EngagementLogBase(BaseModel):
    student_id: int
    project_id: Optional[int]
    engagement_type: EngagementType
    value: float
    metadata_json: Optional[str]

class EngagementLogCreate(EngagementLogBase):
    pass

class EngagementLogResponse(EngagementLogBase):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class SoftSkillScoreBase(BaseModel):
    student_id: int
    skill: str
    score: float = Field(ge=0, le=100)
    evaluator_id: int

class SoftSkillScoreCreate(SoftSkillScoreBase):
    pass

class SoftSkillScoreResponse(SoftSkillScoreBase):
    id: int
    
    class Config:
        from_attributes = True

class StudentXPBase(BaseModel):
    student_id: int
    total_xp: int = 0
    weekly_xp: int = 0

class StudentXPCreate(StudentXPBase):
    pass

class StudentXPResponse(StudentXPBase):
    last_updated: datetime
    
    class Config:
        from_attributes = True

class StudentStreakBase(BaseModel):
    student_id: int
    current_streak: int = 0
    longest_streak: int = 0

class StudentStreakCreate(StudentStreakBase):
    pass

class StudentStreakResponse(StudentStreakBase):
    last_active_date: datetime
    
    class Config:
        from_attributes = True

class StudentBadgeBase(BaseModel):
    student_id: int
    badge_name: str

class StudentBadgeCreate(StudentBadgeBase):
    pass

class StudentBadgeResponse(StudentBadgeBase):
    id: int
    date_awarded: datetime
    
    class Config:
        from_attributes = True

class ConceptProgressBase(BaseModel):
    student_id: int
    concept_id: int
    mastery_score: float = Field(ge=0, le=100)
    level: int = 1

class ConceptProgressCreate(ConceptProgressBase):
    pass

class ConceptProgressResponse(ConceptProgressBase):
    id: int
    
    class Config:
        from_attributes = True

class TeacherInterventionBase(BaseModel):
    teacher_id: int
    student_id: int
    concept_id: Optional[int]
    message: str
    action_taken: str

class TeacherInterventionCreate(TeacherInterventionBase):
    pass

class TeacherInterventionResponse(TeacherInterventionBase):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Additional Response Models for APIs
class MasteryResponse(BaseModel):
    concept_id: int
    concept_name: str
    mastery_score: float
    level: int
    
    class Config:
        from_attributes = True

class AdaptiveAssignmentResponse(BaseModel):
    assignment_id: int
    title: str
    description: str
    difficulty_level: int
    estimated_time: int  # in minutes
    
    class Config:
        from_attributes = True

class LeaderboardEntry(BaseModel):
    student_id: int
    student_name: str
    total_xp: int
    rank: int
    
    class Config:
        from_attributes = True

class BadgeDisplay(BaseModel):
    badge_name: str
    date_awarded: datetime
    
    class Config:
        from_attributes = True

class AIGeneratedAssignment(BaseModel):
    concept_id: int
    title: str
    description: str
    difficulty_level: int
    estimated_time: int  # in minutes
    learning_objectives: List[str]
    
    class Config:
        from_attributes = True

class AIGeneratedProject(BaseModel):
    title: str
    description: str
    skill_area: str
    duration_hours: int
    team_size: int
    learning_outcomes: List[str]
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class TokenData(BaseModel):
    email: str
    role: UserRole

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    metadata: Dict[str, Any]
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AssignmentCreateWithClasses(BaseModel):
    title: str
    description: str
    concept_id: int
    difficulty_level: int
    content_url: Optional[str] = None
    class_ids: List[int]
    due_date: Optional[datetime] = None
    max_score: Optional[int] = 100

class ClassSimple(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class AssignmentWithClassesResponse(AssignmentResponse):
    classes: List[ClassSimple] = []
    class Config:
        from_attributes = True

# Class Management Schemas
class ClassBase(BaseModel):
    name: str
    description: Optional[str] = None

class ClassCreate(ClassBase):
    pass

class ClassResponse(ClassBase):
    id: int
    teacher_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ClassEnrollmentBase(BaseModel):
    class_id: int
    student_id: int

class ClassEnrollmentCreate(BaseModel):
    student_id: int

class ClassEnrollmentResponse(ClassEnrollmentBase):
    id: int
    enrolled_at: datetime
    
    class Config:
        from_attributes = True

class ClassProjectAssignment(BaseModel):
    project_id: int

class ClassAssignmentAssignment(BaseModel):
    assignment_id: int
    due_date: Optional[datetime] = None

class AssignmentSubmissionRequest(BaseModel):
    submission_url: str
    submission_notes: Optional[str] = None

class AssignmentSubmissionBase(BaseModel):
    assignment_id: int
    student_id: int
    submission_url: str
    submission_notes: Optional[str] = None

class AssignmentSubmissionCreate(AssignmentSubmissionBase):
    pass

class AssignmentSubmissionResponse(AssignmentSubmissionBase):
    id: int
    submitted_at: datetime
    status: AssignmentStatus = AssignmentStatus.SUBMITTED
    
    class Config:
        from_attributes = True

class ClassAssignmentResponse(AssignmentResponse):
    due_date: Optional[datetime] = None
    assigned_at: datetime
    class_id: int
    
    class Config:
        from_attributes = True

class StudentAssignmentDetail(AssignmentResponse):
    status: AssignmentStatus
    score: Optional[float] = None
    submitted_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# AI Quiz Generation Schemas
class QuizQuestion(BaseModel):
    id: int
    type: str
    question: str
    options: Optional[List[str]]
    correct_answer: str
    
    class Config:
        from_attributes = True

class GeneratedQuiz(BaseModel):
    topic: str
    difficulty: int
    questions: List[QuizQuestion]
    
    class Config:
        from_attributes = True

# Quiz Schemas
class QuizQuestionBase(BaseModel):
    question_text: str
    options: dict
    correct_answer: str
    irt_difficulty: float = 0.0
    discrimination_index: float = 1.0

class QuizQuestionCreate(QuizQuestionBase):
    pass

class QuizQuestionResponse(QuizQuestionBase):
    id: int
    quiz_id: int

    class Config:
        from_attributes = True

class QuizBase(BaseModel):
    title: str
    description: Optional[str] = None

class QuizCreate(QuizBase):
    questions: List[QuizQuestionCreate]

class QuizResponse(QuizBase):
    id: int
    teacher_id: int
    created_at: datetime
    questions: List[QuizQuestionResponse]

    class Config:
        from_attributes = True

class ClassQuizBase(BaseModel):
    class_id: int
    quiz_id: int
    due_date: Optional[datetime] = None

class ClassQuizCreate(ClassQuizBase):
    pass

class ClassQuizResponse(ClassQuizBase):
    id: int
    assigned_at: datetime

    class Config:
        from_attributes = True

class StudentQuizBase(BaseModel):
    student_id: int
    quiz_id: int
    class_id: int
    status: str
    score: Optional[float] = None

class StudentQuizCreate(StudentQuizBase):
    pass

class StudentQuizResponse(StudentQuizBase):
    id: int
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class QuizQuestionForStudentResponse(BaseModel):
    id: int
    quiz_id: int
    question_text: str
    options: dict

    class Config:
        from_attributes = True

class QuizForStudentResponse(QuizBase):
    id: int
    teacher_id: int
    created_at: datetime
    questions: List[QuizQuestionForStudentResponse]

    class Config:
        from_attributes = True

class StudentQuizSubmission(BaseModel):
    answers: Dict[int, str]

# Project Submission Schemas
class ProjectSubmissionBase(BaseModel):
    project_id: int
    student_id: int
    class_id: int
    submission_url: Optional[str] = None
    submission_notes: Optional[str] = None
    status: AssignmentStatus = AssignmentStatus.SUBMITTED
    score: Optional[float] = Field(None, ge=0, le=100)

class ProjectSubmissionCreate(ProjectSubmissionBase):
    pass

class ProjectSubmissionResponse(ProjectSubmissionBase):
    id: int
    submitted_at: datetime
    
    class Config:
        from_attributes = True

# Quiz Submission and Statistics Schemas
class QuizSubmissionResponse(StudentQuizResponse):
    """Response model for quiz submissions list"""
    student_name: str
    submitted_at: Optional[datetime] = None
    score: Optional[float] = None
    status: str

    class Config:
        from_attributes = True

class QuizSubmissionDetailResponse(QuizSubmissionResponse):
    """Detailed response model for a single quiz submission"""
    quiz: QuizResponse
    answers: Dict[int, str]
    question_stats: Optional[Dict[int, Dict[str, Any]]] = None

class ShareQuizSubmissionEmail(BaseModel):
    """Request model for sharing quiz results via email"""
    recipient_emails: List[str]
    message: Optional[str] = None

class QuizStatisticsResponse(BaseModel):
    """Response model for quiz statistics"""
    quiz_id: int
    total_submissions: int
    average_score: float
    passing_rate: float
    score_distribution: Dict[str, int]  # score_range -> count
    question_statistics: Dict[int, Dict[str, Any]]
    average_time_spent_minutes: float
    question_type_statistics: Dict[str, Dict[str, Any]]
    difficulty_analysis: Dict[str, List[tuple]]

    class Config:
        from_attributes = True

# Enhanced schemas for adaptive learning features
class StudentLearningProfile(BaseModel):
    student_id: int
    learning_pace: str
    preferred_difficulty: str
    avg_score: float
    completion_rate: float
    total_engagement_minutes: float
    avg_daily_engagement_minutes: float
    strengths: List[Dict[str, Any]]
    weaknesses: List[Dict[str, Any]]
    total_assignments: int
    completed_assignments: int
    
    class Config:
        from_attributes = True

class ContentDifficultyAdjustment(BaseModel):
    student_id: int
    current_difficulty: str
    recommended_adjustment: str
    reasoning: str
    
    class Config:
        from_attributes = True

class UnderstandingCheckQuestion(BaseModel):
    question_id: str
    question_text: str
    options: Optional[List[str]]
    correct_answer: str
    question_type: str
    
    class Config:
        from_attributes = True

class UnderstandingCheckResponse(BaseModel):
    is_correct: bool
    confidence: str
    feedback: str
    
    class Config:
        from_attributes = True

class ContentAdaptationRecommendation(BaseModel):
    student_id: int
    concept_id: int
    accuracy: float
    next_step: str
    recommended_explanation_type: str
    feedback: str
    
    class Config:
        from_attributes = True

class ClassDashboardResponse(BaseModel):
    class_mastery_summary: Dict[str, Dict[str, Any]]
    engagement_metrics: Dict[str, Any]
    soft_skill_summary: Dict[str, float]
    leaderboard: List[Dict[str, Any]]
    struggling_students: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class StudentInsightsResponse(BaseModel):
    student_id: int
    student_name: str
    email: str
    total_assignments: int
    completed_assignments: int
    completion_rate: float
    avg_score: float
    total_engagement_minutes: float
    avg_daily_engagement_minutes: float
    strengths: List[Dict[str, Any]]
    weaknesses: List[Dict[str, Any]]
    recent_engagement_trend: str
    
    class Config:
        from_attributes = True

class ConceptAnalyticsResponse(BaseModel):
    concept_name: str
    avg_mastery: float
    min_mastery: float
    max_mastery: float
    student_count: int
    mastery_distribution: Dict[str, int]

    class Config:
        from_attributes = True

class AdaptiveHomeworkResponse(BaseModel):
    question_id: int
    concept_id: int
    concept_name: str
    question_text: str
    difficulty: str
    mastery_level: float

    class Config:
        from_attributes = True
