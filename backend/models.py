from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from typing import Optional, Dict, Any
import enum
import json

Base = declarative_base()

class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"

class EngagementType(str, enum.Enum):
    PROJECT_WORK = "project_work"
    ASSIGNMENT = "assignment"
    DISCUSSION = "discussion"

class AssignmentStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    SUBMITTED = "submitted"
    GRADED = "graded"

class Users(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    
    # Relationships
    mastery_scores = relationship("MasteryScores", back_populates="student")
    student_assignments = relationship("StudentAssignments", back_populates="student")
    project_teams = relationship("ProjectTeams", back_populates="student")
    engagement_logs = relationship("EngagementLogs", back_populates="student")
    soft_skill_scores_given = relationship("SoftSkillScores", foreign_keys="SoftSkillScores.student_id", back_populates="student")
    soft_skill_scores_received = relationship("SoftSkillScores", foreign_keys="SoftSkillScores.evaluator_id", back_populates="evaluator")
    student_xp = relationship("StudentXP", back_populates="student", uselist=False)
    student_streaks = relationship("StudentStreaks", back_populates="student", uselist=False)
    student_badges = relationship("StudentBadges", back_populates="student")
    interventions_as_student = relationship("TeacherInterventions", foreign_keys="TeacherInterventions.student_id", back_populates="student")
    interventions_as_teacher = relationship("TeacherInterventions", foreign_keys="TeacherInterventions.teacher_id", back_populates="teacher")
    taught_classes = relationship("Classes", foreign_keys="Classes.teacher_id", back_populates="teacher")
    class_enrollments = relationship("ClassEnrollments", back_populates="student")
    notifications = relationship("Notification", back_populates="user")
    attempts = relationship("Attempt", back_populates="student")

class Concept(Base):
    __tablename__ = "concepts"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, nullable=True)
    concept_name = Column(String, nullable=False)
    description = Column(String)
    
    # Relationships
    mastery_scores = relationship("MasteryScores", back_populates="concept")
    questions = relationship("Question", back_populates="concept")

# Alias Concepts to Concept to fix typo in PDF upload module
Concepts = Concept

class MasteryScores(Base):
    __tablename__ = "mastery_scores"
    
    student_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), primary_key=True)
    mastery_score = Column(Float, default=0.0)  # 0-100
    
    # Relationships
    student = relationship("Users", back_populates="mastery_scores")
    concept = relationship("Concept", back_populates="mastery_scores")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"))
    question_text = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)  # "easy", "medium", "hard"

    concept = relationship("Concept", back_populates="questions")
    attempts = relationship("Attempt", back_populates="question")

class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    is_correct = Column(Boolean, nullable=False)

    student = relationship("Users", back_populates="attempts")
    question = relationship("Question", back_populates="attempts")

class Assignments(Base):
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"))
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    difficulty_level = Column(Integer)  # 1-5
    content_url = Column(String)
    title = Column(String, nullable=False)
    description = Column(String)
    
    # Relationships
    student_assignments = relationship("StudentAssignments", back_populates="assignment")

class StudentAssignments(Base):
    __tablename__ = "student_assignments"
    
    student_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), primary_key=True)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.ASSIGNED)
    score = Column(Float, nullable=True)  # 0-100
    submitted_at = Column(DateTime, nullable=True)
    submission_url = Column(String, nullable=True)
    submission_notes = Column(String, nullable=True)
    
    # Relationships
    student = relationship("Users", back_populates="student_assignments")
    assignment = relationship("Assignments", back_populates="student_assignments")

class Projects(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    
    # Relationships
    teacher = relationship("Users", foreign_keys=[teacher_id])
    project_teams = relationship("ProjectTeams", back_populates="project")
    engagement_logs = relationship("EngagementLogs", back_populates="project")

class ProjectTeams(Base):
    __tablename__ = "project_teams"
    
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role = Column(String)  # e.g., "leader", "member"
    
    # Relationships
    project = relationship("Projects", back_populates="project_teams")
    student = relationship("Users", back_populates="project_teams")

class EngagementLogs(Base):
    __tablename__ = "engagement_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    engagement_type = Column(Enum(EngagementType), nullable=False)
    value = Column(Float)  # e.g., time spent, clicks, etc.
    metadata_json = Column(String)  # For additional data like confusion index
    
    # Relationships
    student = relationship("Users", back_populates="engagement_logs")
    project = relationship("Projects", back_populates="engagement_logs")

class SoftSkillScores(Base):
    __tablename__ = "soft_skill_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    skill = Column(String, nullable=False)  # e.g., "communication", "teamwork"
    score = Column(Float)  # 0-100
    evaluator_id = Column(Integer, ForeignKey("users.id"))  # Teacher or peer ID
    
    # Relationships
    student = relationship("Users", foreign_keys=[student_id], back_populates="soft_skill_scores_given")
    evaluator = relationship("Users", foreign_keys=[evaluator_id], back_populates="soft_skill_scores_received")

class StudentXP(Base):
    __tablename__ = "student_xp"
    
    student_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    total_xp = Column(Integer, default=0)
    weekly_xp = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("Users", back_populates="student_xp")

class StudentStreaks(Base):
    __tablename__ = "student_streaks"
    
    student_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_active_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("Users", back_populates="student_streaks")

class StudentBadges(Base):
    __tablename__ = "student_badges"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    badge_name = Column(String, nullable=False)
    date_awarded = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("Users", back_populates="student_badges")

class TeacherInterventions(Base):
    __tablename__ = "teacher_interventions"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=True)
    message = Column(String, nullable=False)
    action_taken = Column(String)  # e.g., "assigned_extra_practice", "scheduled_meeting"
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    teacher = relationship("Users", foreign_keys=[teacher_id], back_populates="interventions_as_teacher")
    student = relationship("Users", foreign_keys=[student_id], back_populates="interventions_as_student")
    concept = relationship("Concept", foreign_keys=[concept_id])

class Classes(Base):
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    teacher = relationship("Users", foreign_keys=[teacher_id])
    enrollments = relationship("ClassEnrollments", back_populates="class_obj")
    assignments = relationship("ClassAssignments", back_populates="class_obj")
    projects = relationship("ClassProjects", back_populates="class_obj")

class ClassEnrollments(Base):
    __tablename__ = "class_enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    class_obj = relationship("Classes", back_populates="enrollments")
    student = relationship("Users")

class ClassAssignments(Base):
    __tablename__ = "class_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    assigned_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    
    # Relationships
    class_obj = relationship("Classes", back_populates="assignments")
    assignment = relationship("Assignments")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    notification_type = Column(String, nullable=False)
    meta_data = Column('metadata', JSON, default=dict)  # Using 'metadata' as the actual column name in DB
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("Users", back_populates="notifications")

class ClassProjects(Base):
    __tablename__ = "class_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    assigned_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    class_obj = relationship("Classes", back_populates="projects")
    project = relationship("Projects")

class Quiz(Base):
    __tablename__ = 'quizzes'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    teacher_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship('QuizQuestion', back_populates='quiz')
    teacher = relationship('Users')

class QuizQuestion(Base):
    __tablename__ = 'quiz_questions'

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'))
    concept_id = Column(Integer, ForeignKey('concepts.id'), nullable=True)  # Link to concept for mastery tracking
    question_text = Column(String, nullable=False)
    options = Column(JSON, nullable=False)  # e.g., {"A": "Option 1", "B": "Option 2"}
    correct_answer = Column(String, nullable=False) # e.g., "A"

    quiz = relationship('Quiz', back_populates='questions')
    concept = relationship('Concept')

class ClassQuizzes(Base):
    __tablename__ = 'class_quizzes'

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey('classes.id'))
    quiz_id = Column(Integer, ForeignKey('quizzes.id'))
    assigned_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)

    class_obj = relationship('Classes')
    quiz = relationship('Quiz')

class StudentQuizzes(Base):
    __tablename__ = 'student_quizzes'

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('users.id'))
    quiz_id = Column(Integer, ForeignKey('quizzes.id'))
    class_id = Column(Integer, ForeignKey('classes.id'))
    status = Column(String, default='assigned') # assigned, in-progress, submitted, graded
    score = Column(Float, nullable=True)
    submitted_at = Column(DateTime, nullable=True)

    student = relationship('Users')
    quiz = relationship('Quiz')
    class_obj = relationship('Classes')
