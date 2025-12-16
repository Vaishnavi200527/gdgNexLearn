import { apiService } from './api/apiService.js';
import { studentAPI } from './api/studentApi.js';
import { StudentAssignmentList } from './components/assignments/StudentAssignmentList.js';

// Make APIs globally available for debugging
window.apiService = apiService;
window.studentAPI = studentAPI;

// Get DOM elements
const assignmentListContainer = document.getElementById('assignmentListContainer');
const assignmentFormContainer = document.getElementById('assignmentFormContainer');
const createAssignmentBtn = document.getElementById('createAssignmentBtn');
const userRole = document.getElementById('userRole');
const userName = document.getElementById('userName');
const userAvatar = document.getElementById('userAvatar');

// Check if user is logged in
const token = localStorage.getItem('access_token');
if (!token) {
    // Redirect to login if not authenticated
    window.location.href = 'login.html';
}

// Decode JWT to get user info
function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        return JSON.parse(window.atob(base64));
    } catch (e) {
        console.error('Error parsing JWT:', e);
        return null;
    }
}

// Initialize the application
function initApp() {
    const userData = parseJwt(token);
    if (!userData) {
        console.error('Failed to parse user data from token');
        window.location.href = 'login.html';
        return;
    }

    // Update UI with user data
    userRole.textContent = userData.role || 'user';
    userName.textContent = userData.email ? userData.email.split('@')[0] : 'User';
    userAvatar.textContent = userData.email ? userData.email.charAt(0).toUpperCase() : 'U';

    // Initialize components based on user role
    if (userData.role === 'teacher') {
        // Show create assignment button for teachers
        if (createAssignmentBtn) {
            createAssignmentBtn.style.display = 'inline-flex';
            createAssignmentBtn.addEventListener('click', showAssignmentForm);
        }
        initializeTeacherView();
    } else {
        // Hide create assignment button for students
        if (createAssignmentBtn) {
            createAssignmentBtn.style.display = 'none';
        }
        initializeStudentView();
    }
}

// Initialize teacher's view
function initializeTeacherView() {
    if (assignmentListContainer) {
        assignmentListContainer.innerHTML = `
            <div class="no-assignments">
                <p>No assignments created yet. Click "Create Assignment" to get started.</p>
            </div>
        `;
    }
}

// Initialize student's view
function initializeStudentView() {
    if (assignmentListContainer) {
        try {
            const studentAssignmentList = new StudentAssignmentList('assignmentListContainer');
            console.log('StudentAssignmentList initialized successfully');
        } catch (error) {
            console.error('Error initializing StudentAssignmentList:', error);
            assignmentListContainer.innerHTML = `
                <div class="error-message">
                    <p>Error loading assignments. Please try refreshing the page.</p>
                </div>
            `;
        }
    }
}

// Show assignment creation form
function showAssignmentForm() {
    if (assignmentListContainer && assignmentFormContainer) {
        assignmentListContainer.style.display = 'none';
        assignmentFormContainer.style.display = 'block';
        
        // In a real implementation, you would initialize the teacher assignment form here
        // const teacherAssignmentForm = new TeacherAssignmentForm('assignmentFormContainer', (assignment) => {
        //     assignmentFormContainer.style.display = 'none';
        //     assignmentListContainer.style.display = 'block';
        //     initializeTeacherView();
        // });
    }
}

// Start the application
document.addEventListener('DOMContentLoaded', initApp);
