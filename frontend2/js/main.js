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

            // Load adaptive homework
            loadAdaptiveHomework();

            // Load dynamic assignments and quizzes
            loadDynamicAssignments();
            loadDynamicQuizzes();
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

// Load adaptive homework for students
async function loadAdaptiveHomework() {
    try {
        const homeworkData = await studentAPI.getAdaptiveHomework();
        console.log('Adaptive homework data:', homeworkData);

        const homeworkContainer = document.getElementById('adaptiveHomeworkContainer');
        const homeworkList = document.getElementById('homeworkList');

        if (homeworkData && homeworkData.length > 0) {
            homeworkContainer.classList.remove('hidden');

            let homeworkHTML = '';
            homeworkData.forEach(homework => {
                const difficultyColor = homework.difficulty === 'easy' ? 'text-green-400' :
                                      homework.difficulty === 'medium' ? 'text-yellow-400' : 'text-red-400';

                homeworkHTML += `
                    <div class="bg-[#1b2427]/50 border border-[#283539] rounded-xl p-6 hover:border-indigo-500/50 transition-all">
                        <div class="flex justify-between items-start mb-4">
                            <h3 class="text-white font-bold text-lg">${homework.concept_name}</h3>
                            <span class="px-2 py-1 bg-primary/10 text-primary text-xs font-medium rounded-full">${homework.difficulty}</span>
                        </div>
                        <p class="text-[#9cb2ba] mb-4">${homework.question_text}</p>
                        <div class="flex justify-between items-center text-sm">
                            <span class="text-[#9cb2ba]">Mastery: ${Math.round(homework.mastery_level)}%</span>
                            <span class="${difficultyColor}">Adaptive Practice</span>
                        </div>
                    </div>
                `;
            });

            homeworkList.innerHTML = homeworkHTML;
        } else {
            // Hide homework section if no homework available
            homeworkContainer.classList.add('hidden');
        }
    } catch (error) {
        console.error('Error loading adaptive homework:', error);
        // Show user-friendly error message
        const homeworkContainer = document.getElementById('adaptiveHomeworkContainer');
        const homeworkList = document.getElementById('homeworkList');
        homeworkContainer.classList.remove('hidden');
        homeworkList.innerHTML = `
            <div class="text-center text-gray-400 py-8">
                <p>Unable to load adaptive homework at this time.</p>
                <p class="text-sm mt-2">Please try refreshing the page.</p>
            </div>
        `;
    }
}

// Load dynamic assignments and quizzes
async function loadDynamicAssignments() {
    try {
        const assignmentsData = await studentAPI.getAssignments();
        console.log('Dynamic assignments data:', assignmentsData);

        // Update assignments table with dynamic data
        const tbody = document.getElementById('assignments-tbody');
        if (assignmentsData && assignmentsData.length > 0) {
            let assignmentsHTML = '';
            assignmentsData.forEach(assignment => {
                const statusColor = assignment.status === 'completed' ? 'text-green-400' :
                                  assignment.status === 'in_progress' ? 'text-yellow-400' : 'text-gray-400';
                const difficultyColor = assignment.difficulty === 'easy' ? 'bg-green-500/20 text-green-400' :
                                      assignment.difficulty === 'medium' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400';

                assignmentsHTML += `
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                            <a href="assignment-details.html?id=${assignment.id}" class="hover:text-primary transition-colors">${assignment.title}</a>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-[#8B949E]">${assignment.subject || 'General'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-[#8B949E]">${assignment.due_date || 'No due date'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm ${statusColor}">${assignment.status.replace('_', ' ')}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm">
                            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${difficultyColor}">${assignment.difficulty}</span>
                        </td>
                    </tr>
                `;
            });
            tbody.innerHTML = assignmentsHTML;
        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="px-6 py-4 text-center text-gray-400">
                        No assignments available at this time.
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error loading dynamic assignments:', error);
        const tbody = document.getElementById('assignments-tbody');
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-gray-400">
                    Unable to load assignments. Please try refreshing the page.
                </td>
            </tr>
        `;
    }
}

// Load dynamic quizzes
async function loadDynamicQuizzes() {
    try {
        const quizzesData = await studentAPI.getQuizzes();
        console.log('Dynamic quizzes data:', quizzesData);

        // You can add quiz display logic here if needed
        // For now, quizzes are handled separately in the quiz interface
    } catch (error) {
        console.error('Error loading dynamic quizzes:', error);
        // Quizzes are optional, so don't show error to user
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
