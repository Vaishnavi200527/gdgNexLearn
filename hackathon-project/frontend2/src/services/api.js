const API_BASE_URL = 'http://localhost:8000'; // Backend server URL - FIXED to 8000

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
  // Make sure endpoint starts with /
  if (!endpoint.startsWith('/')) {
    endpoint = '/' + endpoint;
  }
  
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

  // Start with empty headers
  const headers = {};

  // Add authorization token if available
  const token = localStorage.getItem('authToken');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Prepare the body - handle different types
  let body = options.body;
  
  // If body is FormData, let the browser set Content-Type automatically
  if (body && body instanceof FormData) {
    // No Content-Type header needed - browser will set it with boundary
  } 
  // If body is a string (like for login), use as-is
  else if (body && typeof body === 'string') {
    // Assume it's already formatted (like for login)
    headers['Content-Type'] = 'application/x-www-form-urlencoded';
  }
  // If body exists and is not FormData or string, stringify it
  else if (body) {
    body = JSON.stringify(body);
    headers['Content-Type'] = 'application/json';
  }

  // Merge any additional headers from options
  if (options.headers) {
    Object.assign(headers, options.headers);
  }

  const fetchOptions = {
    method: options.method || 'GET',
    headers: headers,
    body: body
  };

  // Don't cache POST/PUT/DELETE requests
  const shouldCache = cacheKey && !forceRefresh && fetchOptions.method === 'GET';

  try {
    console.log(`Making ${fetchOptions.method} request to:`, url);
    console.log('Request options:', { 
      method: fetchOptions.method,
      headers: fetchOptions.headers,
      hasBody: !!fetchOptions.body,
      bodyType: fetchOptions.body ? fetchOptions.body.constructor.name : 'none'
    });

    const request = fetch(url, fetchOptions);
    pendingRequests.set(url, request);

    const response = await request;

    // Handle unauthorized access
    if (response.status === 401) {
      // Clear auth token and redirect to login
      localStorage.removeItem('authToken');
      localStorage.removeItem('userRole');
      // Save current page to return after successful login
      try {
        localStorage.setItem('postLoginRedirect', window.location.pathname + window.location.search);
      } catch (e) {
        console.warn('Could not set postLoginRedirect:', e);
      }
      window.location.href = 'login.html';
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

      // Cache the successful response if cacheKey provided and it's a GET request
      if (shouldCache) {
        setCachedData(cacheKey, data);
      }

      return data;
    }

    // Handle error responses
    let errorMessage = `HTTP Error: ${response.status} ${response.statusText}`;
    let errorDetail = null;
    try {
      const errorData = await response.json();
      errorDetail = errorData;
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch (parseError) {
      // If we can't parse the error response, use the status text
      console.warn('Could not parse error response:', parseError);
    }
    
    // Log full error for debugging
    console.error('Full error response from server:', errorDetail || errorMessage);
    throw new Error(errorMessage);
  } catch (error) {
    console.error(`API request failed: ${error.message}`);
    throw error;
  } finally {
    pendingRequests.delete(url);
  }
}

// Auth endpoints
export const authAPI = {
  signup: (userData) => apiRequest('/auth/register', {
    method: 'POST',
    body: userData,
  }),
  
  login: (credentials) => apiRequest('/auth/token', {
    method: 'POST',
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
    body: `student_id=${studentId}&assignment_id=${assignmentId}`,
  }),

  logEngagement: (engagementData) => apiRequest('/student/engagement', {
    method: 'POST',
    body: engagementData,
  }),

  getProjects: (studentId) => apiRequest(`/student/projects?student_id=${studentId}`, {}, `projects_${studentId}`),

  getLeaderboard: () => apiRequest('/student/leaderboard', {}, 'leaderboard'),

  getBadges: (studentId) => apiRequest(`/student/badges?student_id=${studentId}`, {}, `badges_${studentId}`),

  getQuizzes: () => apiRequest('/api/quizzes/student', {}, 'quizzes'),

  getQuizById: (quizId) => apiRequest(`/api/quizzes/${quizId}`, {}, `quiz_${quizId}`),

  submitQuiz: (quizId, answers) => apiRequest(`/api/quizzes/${quizId}/submit`, {
    method: 'POST',
    body: { answers },
  }),

  // ✅ submitProject function - CORRECT
  submitProject: (projectId, formData) => apiRequest(`/student/projects/${projectId}/submit`, {
    method: 'POST',
    body: formData,
  }),
};

// Quiz endpoints (for teachers)
export const quizAPI = {
  createQuiz: (quizData) => apiRequest('/api/quizzes/', {
    method: 'POST',
    body: quizData,
  }),

  assignQuiz: (assignmentData) => apiRequest('/api/quizzes/assign', {
    method: 'POST',
    body: assignmentData,
  }),
};

// Teacher endpoints
export const teacherAPI = {
  getAIAssignments: (conceptId, apiKey = null) => {
    const params = new URLSearchParams({ concept_id: conceptId });
    if (apiKey) params.append('api_key', apiKey);
    return apiRequest(`/teacher/ai/assignments?${params.toString()}`);
  },
  
  createAssignments: (assignments) => apiRequest('/teacher/assignments/create', {
    method: 'POST',
    body: assignments,
  }),
  
  getAIProjects: (skillArea, apiKey = null) => {
    const params = new URLSearchParams({ skill_area: skillArea });
    if (apiKey) params.append('api_key', apiKey);
    return apiRequest(`/teacher/ai/projects?${params.toString()}`);
  },
  
  createProjects: (projects) => apiRequest('/teacher/projects/create', {
    method: 'POST',
    body: projects,
  }),
  
  getDashboard: (teacherId) => apiRequest(`/teacher/dashboard?teacher_id=${teacherId}`),
  
  getInterventions: (teacherId) => apiRequest(`/teacher/interventions?teacher_id=${teacherId}`),
  
  createIntervention: (interventionData) => apiRequest('/teacher/intervene', {
    method: 'POST',
    body: interventionData,
  }),
  
  // Class management endpoints
  createClass: (classData) => apiRequest('/classes/', {
    method: 'POST',
    body: classData,
  }),
  
  getClasses: () => {
    return apiRequest(`/classes/`);
  },
  
  getClassById: (classId) => apiRequest(`/classes/${classId}`),
  
  enrollStudent: (classId, enrollmentData) => apiRequest(`/classes/${classId}/enroll`, {
    method: 'POST',
    body: enrollmentData,
  }),
  
  getClassStudents: (classId) => apiRequest(`/classes/${classId}/students`),
  
  assignProjectToClass: (classId, projectData) => apiRequest(`/classes/${classId}/assign-project`, {
    method: 'POST',
    body: projectData,
  }),
  
  assignAssignmentToClass: (classId, assignmentData) => apiRequest(`/classes/${classId}/assign-assignment`, {
    method: 'POST',
    body: assignmentData,
  }),
  
  getClassProjects: (classId) => apiRequest(`/classes/${classId}/projects`),
  
  getClassAssignments: (classId) => apiRequest(`/classes/${classId}/assignments`),
};