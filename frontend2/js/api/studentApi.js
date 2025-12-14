import { apiService } from './apiService.js';

// Cache for API responses using localStorage for cross-tab sharing
const CACHE_KEY_PREFIX = 'student_api_cache_';
const CACHE_DURATION = 300000; // 5 minutes

class StudentAPI {
    constructor(apiService) {
        this.api = apiService;
        this.pendingRequests = new Map();
        this.ensureAuthenticated();
    }

    ensureAuthenticated() {
        // Try multiple possible token keys
        const token = localStorage.getItem('access_token') ||
                     localStorage.getItem('auth_token') ||
                     sessionStorage.getItem('access_token') ||
                     sessionStorage.getItem('auth_token');

        if (!token) {
            console.warn('No authentication token found. User not logged in.');
            window.location.href = '/login.html';
            return false;
        }

        this.api.setToken(token);
        return true;
    }

    // Helper method to get cached data from localStorage
    getCachedData(cacheKey) {
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

    // Helper method to set cached data in localStorage
    setCachedData(cacheKey, data) {
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

    async getAssignments(studentId = 1, forceRefresh = false) {
        if (!this.ensureAuthenticated()) {
            return { error: 'Authentication required' };
        }

        const cacheKey = `assignments_${studentId}`;

        // Return cached response if available and not forcing refresh
        if (!forceRefresh) {
            const cached = this.getCachedData(cacheKey);
            if (cached) {
                return Promise.resolve(cached);
            }
        }

        // Check if there's already a pending request for this data
        if (this.pendingRequests.has(cacheKey)) {
            return this.pendingRequests.get(cacheKey);
        }

        try {
            const request = this.api.request(`/student/assignments?student_id=${studentId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.api.token || localStorage.getItem('token')}`
                }
            });

            // Store the promise in pending requests
            this.pendingRequests.set(cacheKey, request);

            const response = await request;

            // Cache the successful response
            this.setCachedData(cacheKey, response);

            return response;
        } catch (error) {
            console.error('Error fetching assignments:', error);
            if (error.status === 401) {
                // Clear auth data and redirect to login
                localStorage.removeItem('auth_token');
                localStorage.removeItem('token');
                sessionStorage.removeItem('access_token');
                sessionStorage.removeItem('auth_token');
                window.location.href = '/login.html';
            }
            // If we have a cached response, return it even if there's an error
            const cached = this.getCachedData(cacheKey);
            if (cached) {
                console.warn('Using cached data due to error:', error.message);
                return cached;
            }
            throw error;
        } finally {
            // Remove from pending requests
            this.pendingRequests.delete(cacheKey);
        }
    }

    async submitAssignment(assignmentId, submissionData) {
        if (!this.ensureAuthenticated()) {
            throw new Error('Authentication required');
        }

        try {
            // Determine if submissionData is FormData or JSON
            const isFormData = submissionData instanceof FormData;
            const headers = {
                'Authorization': `Bearer ${this.api.token || localStorage.getItem('token')}`
            };

            // Don't set Content-Type for FormData, let browser handle it
            if (!isFormData) {
                headers['Content-Type'] = 'application/json';
            }

            const body = isFormData ? submissionData : JSON.stringify(submissionData);

            const response = await this.api.request(`/student/assignments/${assignmentId}/submit`, {
                method: 'POST',
                headers: headers,
                body: body
            });

            // Invalidate cache for assignments since we've made a submission
            this.invalidateCache('assignments');

            return response;
        } catch (error) {
            console.error('Error submitting assignment:', error);
            throw error;
        }
    }

    // Invalidate cache for a specific key or all caches if no key provided
    invalidateCache(key = null) {
        try {
            if (key) {
                // Invalidate all caches that start with the key
                const keysToRemove = [];
                for (let i = 0; i < localStorage.length; i++) {
                    const storageKey = localStorage.key(i);
                    if (storageKey && storageKey.startsWith(CACHE_KEY_PREFIX + key)) {
                        keysToRemove.push(storageKey);
                    }
                }
                keysToRemove.forEach(storageKey => localStorage.removeItem(storageKey));
            } else {
                // Clear all API caches
                const keysToRemove = [];
                for (let i = 0; i < localStorage.length; i++) {
                    const storageKey = localStorage.key(i);
                    if (storageKey && storageKey.startsWith(CACHE_KEY_PREFIX)) {
                        keysToRemove.push(storageKey);
                    }
                }
                keysToRemove.forEach(storageKey => localStorage.removeItem(storageKey));
            }
        } catch (error) {
            console.warn('Error clearing cache:', error);
        }
    }
}

// Create and export a singleton instance
export const studentAPI = new StudentAPI(apiService);
