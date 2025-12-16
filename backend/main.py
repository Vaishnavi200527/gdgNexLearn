from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import uvicorn
import os
from typing import Optional
import jwt
from datetime import datetime, timedelta

# Import models and database
import models
import database
from database import get_db

# Import routers
from routers import auth, student, teacher, classes, notifications, quiz

# Import auth utilities
from auth_utils import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, oauth2_scheme, get_current_user, get_current_teacher, get_current_student

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

# Initialize FastAPI app
app = FastAPI(title="EduAI Platform API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(teacher.router, prefix="", tags=["teacher"])
app.include_router(student.router, prefix="", tags=["student"])
app.include_router(notifications.router, prefix="", tags=["notifications"])
app.include_router(classes.router, prefix="", tags=["classes"])
app.include_router(quiz.router)

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
        return await response.text();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Student API methods
const studentAPI = {
    // --- Assignment Endpoints ---
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
    }
};

// Make studentAPI globally available
window.studentAPI = studentAPI;
"""
    return Response(content=js_content, media_type="application/javascript")

@app.get("/")
async def root():
    return {"message": "Welcome to the EduAI Platform API! Visit /docs for API documentation."}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)