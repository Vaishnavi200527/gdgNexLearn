const API_BASE_URL = 'http://localhost:8000';

class ApiService {
    constructor() {
        // Try multiple possible token storage locations
        this.token = localStorage.getItem('authToken') ||
                    localStorage.getItem('access_token') ||
                    localStorage.getItem('auth_token') ||
                    sessionStorage.getItem('authToken') ||
                    sessionStorage.getItem('access_token') ||
                    sessionStorage.getItem('auth_token');
    }

    setToken(token, rememberMe = true) {
        this.token = token;
        // Store token based on rememberMe preference
        if (rememberMe) {
            localStorage.setItem('authToken', token);
            localStorage.setItem('access_token', token);
            // Clean up any old token storage
            localStorage.removeItem('auth_token');
            sessionStorage.removeItem('authToken');
            sessionStorage.removeItem('access_token');
            sessionStorage.removeItem('auth_token');
        } else {
            sessionStorage.setItem('authToken', token);
            sessionStorage.setItem('access_token', token);
            // Clean up any old token storage
            localStorage.removeItem('authToken');
            localStorage.removeItem('access_token');
            localStorage.removeItem('auth_token');
            sessionStorage.removeItem('auth_token');
        }
    }

    clearToken() {
        this.token = null;
        // Clear all possible token storage locations
        localStorage.removeItem('authToken');
        localStorage.removeItem('access_token');
        localStorage.removeItem('auth_token');
        sessionStorage.removeItem('authToken');
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('auth_token');
    }

    getAuthHeader() {
        return this.token ? { 'Authorization': `Bearer ${this.token}` } : {};
    }

    async request(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            ...this.getAuthHeader(),
            ...options.headers,
        };

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                ...options,
                headers,
                mode: 'cors', // Enable CORS mode
            });

            // Handle 401 Unauthorized
            if (response.status === 401) {
                this.clearToken();
                // Only redirect if not already on the login page
                if (!window.location.pathname.endsWith('login.html')) {
                    window.location.href = '/login.html';
                }
                return null;
            }

            // Handle empty responses
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                if (response.ok) return null;
                throw new Error('Invalid response from server');
            }

            const data = await response.json();
            
            if (!response.ok) {
                const error = new Error(data.detail || 'Something went wrong');
                error.status = response.status;
                error.data = data;
                throw error;
            }
            
            return data;
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    // Auth endpoints
    async login(email, password) {
        const data = await this.request('/student/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        if (data && data.access_token) {
            this.setToken(data.access_token);
            return this.getCurrentUser();
        }
        return null;
    }

    async getCurrentUser() {
        return this.request('/student/me');
    }

    // Assignment endpoints
    async getAssignments(status) {
        const query = status ? `?status=${status}` : '';
        return this.request(`/student/assignments${query}`);
    }

    async getAssignmentDetails(assignmentId) {
        return this.request(`/student/assignments/${assignmentId}`);
    }

    async submitAssignment(assignmentId, submissionUrl, notes = '') {
        return this.request(`/student/assignments/${assignmentId}/submit`, {
            method: 'POST',
            body: JSON.stringify({
                student_id: (await this.getCurrentUser()).id,
                submission_url: submissionUrl,
                submission_notes: notes
            })
        });
    }

    // Teacher endpoints
    async assignToClass(classId, assignmentData) {
        return this.request(`/teacher/assignments/class/${classId}`, {
            method: 'POST',
            body: JSON.stringify(assignmentData)
        });
    }

    async getClassAssignments(classId) {
        return this.request(`/teacher/classes/${classId}/assignments`);
    }

    async getAssignmentSubmissions(assignmentId, classId = null) {
        const query = classId ? `?class_id=${classId}` : '';
        return this.request(`/teacher/assignments/${assignmentId}/submissions${query}`);
    }
}

export const apiService = new ApiService();
