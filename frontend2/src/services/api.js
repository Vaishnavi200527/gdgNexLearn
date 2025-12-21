const API_BASE_URL = 'http://localhost:8000'; // Backend server URL

// Cache configuration
const CACHE_KEY_PREFIX = 'api_cache_';
const CACHE_DURATION = 300000; // 5 minutes
const pendingRequests = new Map();

// Helper function to get cached data from localStorage
function getCachedData(cacheKey) {
  try {
    const cached = localStorage.getItem(CACHE_KEY_PREFIX + cacheKey);
    if (cached) {
      const parsed = JSON.parse(cached);
      if (Date.now() - parsed.timestamp < CACHE_DURATION) {
        return parsed.data;
      } else {
        // Remove expired cache
        localStorage.removeItem(CACHE_KEY_PREFIX + cacheKey);
      }
    }
  } catch (error) {
    console.warn('Error reading cache:', error);
  }
  return null;
}

// Helper function to set cached data in localStorage
function setCachedData(cacheKey, data) {
  try {
    const cacheEntry = {
      data: data,
      timestamp: Date.now()
    };
    localStorage.setItem(CACHE_KEY_PREFIX + cacheKey, JSON.stringify(cacheEntry));
  } catch (error) {
    console.warn('Error writing cache:', error);
  }
}

// Helper function for API requests with caching
async function apiRequest(endpoint, options = {}, cacheKey = null, forceRefresh = false) {
    const url = `${API_BASE_URL}${endpoint}`;

    // Check cache first if cacheKey provided and not forcing refresh
    if (cacheKey && !forceRefresh) {
        const cached = getCachedData(cacheKey);
        if (cached) {
            return cached;
        }
    }

    // Check if there's already a pending request for this endpoint
    if (pendingRequests.has(url)) {
        return pendingRequests.get(url);
    }

    // Set default headers
    const defaultHeaders = {
        'Content-Type': 'application/json',
    };

    // Merge headers
    const headers = {
        ...defaultHeaders,
        ...options.headers,
    };

    // Add authorization token if available
    const token = localStorage.getItem('authToken');
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Create fetch options
    const fetchOptions = {
        ...options,
        headers,
    };

    // Special handling for FormData - let the browser set the Content-Type
    if (options.body instanceof FormData) {
        // Remove Content-Type header so browser can set it with proper boundary
        delete fetchOptions.headers['Content-Type'];
    }

    // Create a promise that resolves to the final data
    const requestPromise = (async () => {
        try {
            const response = await fetch(url, fetchOptions);

            // Handle unauthorized access (but not for login endpoint)
            if (response.status === 401 && !endpoint.includes('/token')) {
                // Clear auth token and redirect to login
                localStorage.removeItem('authToken');
                localStorage.removeItem('userRole');
                window.location.href = '/frontend2/pages/login.html';
                return;
            }

            // Handle successful responses
            if (response.ok) {
                const contentType = response.headers.get('content-type');
                let data;
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json();
                } else {
                    data = await response.text();
                }

                // Cache the successful response if cacheKey provided
                if (cacheKey) {
                    setCachedData(cacheKey, data);
                }

                return data;
            }

            // Handle error responses
            let errorMessage = `HTTP Error: ${response.status}`;
            try {
                const errorData = await response.json();
                console.error("Full error response from server:", errorData);

                // Handle FastAPI validation errors (detail can be an array)
                if (errorData.detail) {
                    if (Array.isArray(errorData.detail)) {
                        // Validation errors from Pydantic
                        const validationErrors = errorData.detail.map(err => {
                            if (err.loc && err.loc.length > 0) {
                                const field = err.loc[err.loc.length - 1];
                                return `${field}: ${err.msg}`;
                            }
                            return err.msg || err.message || 'Validation error';
                        });
                        errorMessage = `Validation Error:\n${validationErrors.join('\n')}`;
                    } else {
                        // Single error message
                        errorMessage = errorData.detail;
                    }
                } else if (errorData.message) {
                    errorMessage = errorData.message;
                } else {
                    errorMessage = errorData.error || errorMessage;
                }
            } catch (parseError) {
                // If we can't parse the error response, use the status text
                errorMessage = response.statusText || errorMessage;
            }
            throw new Error(errorMessage);
        } catch (error) {
            console.error(`API request failed: ${error.message}`);
            throw error;
        } finally {
            pendingRequests.delete(url);
        }
    })();

    // Store the promise that resolves to the data
    pendingRequests.set(url, requestPromise);

    return requestPromise;
}

// Auth endpoints
export const authAPI = {
  signup: (userData) => apiRequest('/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      name: userData.name,
      email: userData.email,
      password: userData.password,
      role: userData.role || 'student'
    }),
  }),
  
  login: (credentials) => apiRequest('/auth/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: `username=${encodeURIComponent(credentials.email)}&password=${encodeURIComponent(credentials.password)}`,
  }),
};

// Student endpoints
export const studentAPI = {
  getMastery: () => apiRequest('/student/mastery', {}, 'mastery'),

  getAssignments: (studentId) => apiRequest(`/student/assignments?student_id=${studentId}`, {}, `assignments_${studentId}`),

  getAssignmentById: (assignmentId) => apiRequest(`/student/assignments/${assignmentId}`, {}, `assignment_${assignmentId}`),

  submitAssignment: (studentId, assignmentId) => apiRequest('/student/assignments/submit', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: `student_id=${studentId}&assignment_id=${assignmentId}`,
  }),

  logEngagement: (engagementData) => apiRequest('/student/engagement', {
    method: 'POST',
    body: JSON.stringify(engagementData),
  }),

  getProjects: (studentId) => apiRequest(`/student/projects?student_id=${studentId}`, {}, `projects_${studentId}`),

  getLeaderboard: () => apiRequest('/student/leaderboard', {}, 'leaderboard'),

  getBadges: (studentId) => apiRequest(`/student/badges?student_id=${studentId}`, {}, `badges_${studentId}`),

  getQuizzes: () => apiRequest('/api/quizzes/student', {}, 'quizzes'),

  getQuizById: (quizId) => apiRequest(`/api/quizzes/${quizId}`, {}, `quiz_${quizId}`),

  submitQuiz: (quizId, answers) => apiRequest(`/api/quizzes/${quizId}/submit`, {
    method: 'POST',
    body: JSON.stringify({ answers }),
  }),
};

// Quiz endpoints (for teachers)
export const quizAPI = {
  createQuiz: (quizData) => apiRequest('/api/quizzes/', {
    method: 'POST',
    body: JSON.stringify(quizData),
  }),

  assignQuiz: (assignmentData) => apiRequest('/api/quizzes/assign', {
    method: 'POST',
    body: JSON.stringify(assignmentData),
  }),
};

// Teacher endpoints
export const teacherAPI = {
  // PDF Upload endpoints
  processPDF: (formData) => apiRequest('/pdf-upload/process-pdf', {
    method: 'POST',
    body: formData,
  }),
  
  createAdaptiveAssignment: (formData) => apiRequest('/pdf-upload/create-adaptive-assignment', {
    method: 'POST',
    body: formData,
  }),
  
  getAIAssignments: (conceptId, apiKey = null) => {
    const params = new URLSearchParams({ concept_id: conceptId });
    if (apiKey) params.append('api_key', apiKey);
    return apiRequest(`/teacher/ai/assignments?${params.toString()}`);
  },
  
  createAssignments: (assignments) => apiRequest('/teacher/assignments/create', {
    method: 'POST',
    body: JSON.stringify(assignments),
  }),
  
  getAIProjects: (skillArea, apiKey = null) => {
    const params = new URLSearchParams({ skill_area: skillArea });
    if (apiKey) params.append('api_key', apiKey);
    return apiRequest(`/teacher/ai/projects?${params.toString()}`);
  },
  
  createProjects: (projects) => apiRequest('/teacher/projects/create', {
    method: 'POST',
    body: JSON.stringify(projects),
  }),
  
  getDashboard: () => apiRequest('/teacher/dashboard'),
  
  getInterventions: () => apiRequest('/teacher/interventions'),
  
  createIntervention: (interventionData) => apiRequest('/teacher/intervene', {
    method: 'POST',
    body: JSON.stringify(interventionData),
  }),
  
  // Class management endpoints
  createClass: (classData) => apiRequest('/classes/', {
    method: 'POST',
    body: JSON.stringify(classData),
  }),
  
  getClasses: () => {
    return apiRequest(`/classes/`);
  },
  
  getClassById: (classId) => apiRequest(`/classes/${classId}`),
  
  enrollStudent: (classId, enrollmentData) => apiRequest(`/classes/${classId}/enroll`, {
    method: 'POST',
    body: JSON.stringify(enrollmentData),
  }),
  
  getClassStudents: (classId) => apiRequest(`/classes/${classId}/students`),
  
  assignProjectToClass: (classId, projectData) => apiRequest(`/classes/${classId}/assign-project`, {
    method: 'POST',
    body: JSON.stringify(projectData),
  }),
  
  assignAssignmentToClass: (classId, assignmentData) => apiRequest(`/classes/${classId}/assign-assignment`, {
    method: 'POST',
    body: JSON.stringify(assignmentData),
  }),
  
  getClassProjects: (classId) => apiRequest(`/classes/${classId}/projects`),
  
  getClassAssignments: (classId) => apiRequest(`/classes/${classId}/assignments`),
};
