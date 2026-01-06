from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn  # Add this import
import models  # Import models to register them with SQLAlchemy Base
from routers.student import router as student_router
from routers.teacher import router as teacher_router
from routers.auth import router as auth_router
from routers.continuous_assessment import router as continuous_assessment_router
from routers.teacher_dashboard import router as teacher_dashboard_router
from routers.ai_content import router as ai_content_router
from routers.pdf_upload import router as pdf_upload_router  # Add this import
from routers.classes import router as classes_router  # Add this import


# Import models to register them with SQLAlchemy Base
import models
from database import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    from database import Base
    Base.metadata.create_all(bind=engine)
    print("Database tables created on startup")
    yield

app = FastAPI(title="AI-Powered Adaptive Learning Platform", lifespan=lifespan)

# Origins for CORS
origins = [
    "http://localhost",
    "http://localhost:5173",  # Origin from the error message
    "http://localhost:5174",  # Vite dev server port
    "http://localhost:8080",  # Common dev server port
    "http://127.0.0.1:5500",  # VS Code Live Server
    "http://127.0.0.1:5173",  # Vite local IP
    "http://127.0.0.1:5174",  # Vite dev server IP
    "http://localhost:5173",  # Added for Vite frontend
    "http://localhost:5174",  # Added for Vite frontend
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
import os
frontend2_path = os.path.join(os.path.dirname(__file__), "..", "frontend2")
app.mount("/frontend2", StaticFiles(directory=frontend2_path, html=True), name="frontend2")

storage_path = "storage"
if not os.path.exists(storage_path):
    os.makedirs(os.path.join(storage_path, "assignments"))
app.mount("/storage", StaticFiles(directory=storage_path), name="storage")

# Include routers
app.include_router(auth_router, prefix="/auth")
app.include_router(student_router, prefix="/student")
app.include_router(teacher_router, prefix="/teacher")
app.include_router(continuous_assessment_router, prefix="/continuous-assessment")
app.include_router(teacher_dashboard_router, prefix="/teacher/dashboard")
app.include_router(ai_content_router, prefix="/ai")
app.include_router(pdf_upload_router, prefix="/pdf-upload")
app.include_router(classes_router, prefix="/classes")


@app.get("/student-api.js")
async def get_student_api_js():
    js_content = """
console.log('Student API JS loaded - Version: Loop Protection v3');

// API Request utility function
async function apiRequest(endpoint, method = 'GET', data = null) {
    const url = `http://localhost:8000${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    };

    const config = {
        method,
        headers,
        credentials: 'include'
    };

    if (data) {
        config.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, config);
        
        // Global Error Handling for Authentication/Authorization
        if (response.status === 401) {
            console.warn('Session expired or unauthorized. Redirecting to login.');
            localStorage.clear(); // Clear EVERYTHING
            sessionStorage.clear();
            window.location.replace('index.html?reason=401'); // Redirect to login
            return new Promise(() => {}); // Halt execution
        }
        
        if (response.status === 403) {
            console.warn('Access forbidden (403). Checking role for redirection...');
            const role = localStorage.getItem('user_role');
            const r = role ? role.toLowerCase() : '';
            if (r === 'student') {
                // LOOP PROTECTION: If already on student dashboard but getting 403, force logout
                if (window.location.pathname.includes('student-dashboard')) {
                    console.error('403 Loop Detected. Session corrupted. Forcing logout.');
                    localStorage.clear();
                    window.location.replace('index.html?reason=403_loop');
                    return new Promise(() => {});
                }
                console.log('Redirecting student to student dashboard...');
                window.location.replace('student-dashboard.html');
                return new Promise(() => {}); // Halt execution to prevent further errors
            } else if (r === 'teacher') {
                // LOOP PROTECTION for teachers
                if (window.location.pathname.includes('teacher-dashboard')) {
                    console.error('403 Loop Detected. Session corrupted. Forcing logout.');
                    localStorage.clear();
                    window.location.replace('index.html?reason=403_loop');
                    return new Promise(() => {});
                }
                console.log('Redirecting teacher to teacher dashboard...');
                window.location.replace('teacher-dashboard.html');
                return new Promise(() => {}); // Halt execution to prevent further errors
            } else {
                // Fallback if role is missing or unknown
                console.warn('Role missing on 403. Redirecting to login.');
                localStorage.clear();
                window.location.replace('index.html?reason=403_unknown');
                return new Promise(() => {}); // Halt execution
            }
        }

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Request failed');
        }

        // Handle empty responses
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }

        // For non-JSON responses (like empty responses with 200 OK)
        return {};
    } catch (error) {
        console.error('API Request failed:', error);
        throw error;
    }
}

// Student API endpoints
const studentAPI = {
    // --- Authentication ---
    signup: async (userData) => {
        return await apiRequest('/student/signup', 'POST', userData);
    },

    login: async (credentials) => {
        const response = await apiRequest('/student/login', 'POST', credentials);
        if (response.access_token) {
            localStorage.setItem('access_token', response.access_token);
            if (response.role) {
                localStorage.setItem('user_role', response.role);
                // Always redirect on successful login
                studentAPI.redirectUser(response.role);
            }
        }
        return response;
    },

    // New method to match the /auth/token endpoint (OAuth2 standard)
    loginOAuth: async (username, password) => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch('http://localhost:8000/auth/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Login failed');
        }
        
        const data = await response.json();
        if (data.access_token) {
            localStorage.setItem('access_token', data.access_token);
            if (data.role) {
                localStorage.setItem('user_role', data.role);
                studentAPI.redirectUser(data.role);
            }
        }
        return data;
    },

    // Helper to handle redirection based on role
    redirectUser: (role) => {
        console.log('Redirecting user with role:', role);
        const r = role ? role.toLowerCase() : '';
        
        if (r === 'student') {
            window.location.replace('student-dashboard.html');
        } else if (r === 'teacher') {
            window.location.replace('teacher-dashboard.html');
        } else {
            console.warn('Unknown role:', role);
            // Fallback
            window.location.replace('student-dashboard.html');
        }
    },

    // --- Mastery & Progress ---
    getMastery: async () => {
        return await apiRequest('/student/mastery');
    },

    getLearningProfile: async () => {
        return await apiRequest('/student/learning-profile');
    },

    getContentAdjustment: async () => {
        return await apiRequest('/student/content-adjustment');
    },

    // --- Assignments ---
    getAssignments: async () => {
        return await apiRequest('/student/assignments');
    },

    getAssignment: async (id) => {
        return await apiRequest(`/student/assignments/${id}`);
    },

    submitAssignment: async (id, data) => {
        return await apiRequest(`/student/assignments/${id}/submit`, 'POST', data);
    },

    getAssignmentConcepts: async (id, detailLevel = 'medium') => {
        return await apiRequest(`/student/assignments/${id}/concepts?detail_level=${detailLevel}`);
    },

    // --- Quiz Endpoints ---
    getAssignmentQuiz: async (assignmentId, count = 10) => {
        // Pass question count to backend to generate appropriate number of questions
        return await apiRequest(`/student/assignments/${assignmentId}/quiz?question_count=${count}`);
    },

    getQuiz: async (id) => {
        return await apiRequest(`/api/quizzes/${id}`);
    },

    submitQuiz: async (id, data) => {
        return await apiRequest(`/api/quizzes/${id}/submit`, 'POST', data);
    },

    submitAssignmentQuiz: async (assignmentId, data) => {
        return await apiRequest(`/student/assignments/${assignmentId}/quiz/submit`, 'POST', data);
    },

    // --- Dashboard/Stats Endpoints ---

    getProjects: async () => {
        return await apiRequest('/student/projects');
    },

    getLeaderboard: async () => {
        return await apiRequest('/student/leaderboard');
    },

    getBadges: async () => {
        return await apiRequest('/student/badges');
    },
    
    // --- Continuous Assessment ---
    generateUnderstandingChecks: async (conceptId) => {
        return await apiRequest('/continuous-assessment/generate-checks', 'POST', { concept_id: conceptId });
    },
    
    evaluateUnderstandingResponse: async (questionId, studentAnswer) => {
        return await apiRequest('/continuous-assessment/evaluate-response', 'POST', {
            question_id: questionId,
            student_answer: studentAnswer
        });
    },
    
    adaptContent: async (conceptId, responses) => {
        return await apiRequest('/continuous-assessment/adapt-content', 'POST', {
            concept_id: conceptId,
            responses: responses
        });
    }
};

// Teacher API endpoints
const teacherAPI = {
    // --- Dashboard ---
    getClassOverview: async () => {
        return await apiRequest('/teacher/dashboard/class-overview');
    },
    
    getStrugglingStudents: async () => {
        return await apiRequest('/teacher/dashboard/struggling-students');
    },
    
    getStudentInsights: async (studentId) => {
        return await apiRequest(`/teacher/dashboard/student-insights/${studentId}`);
    },
    
    getConceptAnalytics: async () => {
        return await apiRequest('/teacher/dashboard/concept-analytics');
    },
    
    getEngagementTrends: async (days = 30) => {
        return await apiRequest(`/teacher/dashboard/engagement-trends?days=${days}`);
    },
    
    getInterventionSummary: async () => {
        return await apiRequest('/teacher/dashboard/intervention-summary');
    },
    
    // --- AI Content Generation ---
    getAIAssignments: async (conceptId, apiKey = null) => {
        const params = new URLSearchParams({ concept_id: conceptId });
        if (apiKey) params.append('api_key', apiKey);
        return await apiRequest(`/teacher/ai/assignments?${params.toString()}`);
    },
    
    createAssignments: async (assignments) => {
        return await apiRequest('/teacher/assignments/create', 'POST', assignments);
    },
    
    getAIProjects: async (skillArea, apiKey = null) => {
        const params = new URLSearchParams({ skill_area: skillArea });
        if (apiKey) params.append('api_key', apiKey);
        return await apiRequest(`/teacher/ai/projects?${params.toString()}`);
    },
    
    createProject: async (project) => {
        return await apiRequest('/teacher/projects/create', 'POST', project);
    },
    
    // --- Interventions ---
    recordIntervention: async (intervention) => {
        return await apiRequest('/teacher/intervene', 'POST', intervention);
    },
    
    getInterventions: async () => {
        return await apiRequest('/teacher/interventions');
    },
    
    // --- Soft Skills ---
    recordSoftSkillScore: async (score) => {
        return await apiRequest('/teacher/softskills/score', 'POST', score);
    },
    
    // --- Quiz Generation ---
    generateQuiz: async (topic, difficulty = 3, questionCount = 5, apiKey = null) => {
        const params = new URLSearchParams({
            topic: topic,
            difficulty: difficulty,
            question_count: questionCount
        });
        if (apiKey) params.append('api_key', apiKey);
        return await apiRequest(`/teacher/ai/generate-quiz?${params.toString()}`, 'POST');
    }
};

// Make APIs globally available
window.studentAPI = studentAPI;
window.teacherAPI = teacherAPI;

// --- AUTO-REDIRECT PROTECTION ---
// This runs immediately when the script loads to ensure users are on the correct page
(function() {
    try {
        const role = localStorage.getItem('user_role');
        const path = window.location.pathname.toLowerCase();
        const token = localStorage.getItem('access_token');
        
        // Only run checks if we have a token (logged in)
        if (token && role) {
            const r = role.toLowerCase();
            
            // If student is on teacher dashboard
            if (r === 'student' && path.includes('teacher-dashboard')) {
                console.warn('Student detected on teacher dashboard. Redirecting...');
                window.location.replace('student-dashboard.html');
            }
            // If teacher is on student dashboard
            else if (r === 'teacher' && path.includes('student-dashboard')) {
                console.warn('Teacher detected on student dashboard. Redirecting...');
                window.location.replace('teacher-dashboard.html');
            }
            // Strict check for student on teacher pages
            else if (r === 'student' && (path.includes('teacher') || path.includes('class-overview'))) {
                 console.warn('Student detected on restricted teacher page. Redirecting...');
                 window.location.replace('student-dashboard.html');
            }
        }
    } catch (e) {
        console.error('Auto-redirect error:', e);
    }
})();
"""
    return Response(content=js_content, media_type="application/javascript", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/")
async def root():
    return {"message": "Welcome to the EduAI Platform API! Visit /docs for API documentation."}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Change port to 8000 to match frontend
