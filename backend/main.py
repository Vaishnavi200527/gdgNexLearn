from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn  # Add this import
from routers.student import router as student_router
from routers.teacher import router as teacher_router
from routers.auth import router as auth_router
from routers.continuous_assessment import router as continuous_assessment_router
from routers.teacher_dashboard import router as teacher_dashboard_router
from routers.ai_content import router as ai_content_router
from routers.pdf_upload import router as pdf_upload_router  # Add this import
from routers.classes import router as classes_router  # Add this import

app = FastAPI(title="AI-Powered Adaptive Learning Platform")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(student_router)
app.include_router(teacher_router)
app.include_router(continuous_assessment_router)
app.include_router(teacher_dashboard_router)
app.include_router(ai_content_router)
app.include_router(pdf_upload_router)  # Add this line
app.include_router(classes_router)  # Add this line


@app.get("/student-api.js")
async def get_student_api_js():
    js_content = """
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
        return await apiRequest('/student/login', 'POST', credentials);
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

    // --- Quiz Endpoints ---
    getQuizzes: async () => {
        return await apiRequest('/api/quizzes/student');
    },

    getQuiz: async (id) => {
        return await apiRequest(`/api/quizzes/${id}`);
    },

    submitQuiz: async (id, data) => {
        return await apiRequest(`/api/quizzes/${id}/submit`, 'POST', data);
    },

    // --- Dashboard/Stats Endpoints ---
    getMastery: async () => {
        return await apiRequest('/student/mastery');
    },

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
"""
    return Response(content=js_content, media_type="application/javascript")

@app.get("/")
async def root():
    return {"message": "Welcome to the EduAI Platform API! Visit /docs for API documentation."}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Change port to 8000 to match frontend
