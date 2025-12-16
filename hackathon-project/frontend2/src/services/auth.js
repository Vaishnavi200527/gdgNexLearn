// Authentication utility functions

// Check if user is authenticated
export function isAuthenticated() {
    return !!localStorage.getItem('authToken');
}

// Get user role
export function getUserRole() {
    const r = localStorage.getItem('userRole');
    return r ? String(r).toLowerCase() : null;
}

// Logout user
export function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userRole');
    window.location.href = 'landing.html';
}

// Check role-based access
export function hasAccess(requiredRole) {
    const userRole = getUserRole();
    if (!userRole) return false;
    
    // Admin can access everything
    if (userRole === 'admin') return true;
    
    // Exact match
    return userRole === requiredRole;
}

// Redirect if not authenticated
export function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Redirect if not authorized for role
export function requireRole(role) {
    if (!requireAuth()) return false;
    
    if (!hasAccess(role)) {
        // Redirect to appropriate dashboard based on user role
        const userRole = getUserRole();
        if (userRole === 'student') {
            window.location.href = 'student-dashboard.html';
        } else if (userRole === 'teacher') {
            window.location.href = 'teacher-dashboard.html';
        } else {
            window.location.href = 'landing.html';
        }
        return false;
    }
    return true;
}