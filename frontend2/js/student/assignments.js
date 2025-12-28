
import { studentAPI } from '../js/api/studentApi.js';
import { logout } from '../src/services/auth.js';

// Store assignments data globally
let globalAssignmentsData = [];

// Mobile navigation functionality
function setupMobileNavigation() {
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const closeMobileNav = document.getElementById('close-mobile-nav');
    const mobileNavOverlay = document.getElementById('mobile-nav-overlay');

    if (mobileMenuToggle && mobileNavOverlay) {
        mobileMenuToggle.addEventListener('click', () => {
            mobileNavOverlay.classList.remove('hidden');
        });
    }

    if (closeMobileNav && mobileNavOverlay) {
        closeMobileNav.addEventListener('click', () => {
            mobileNavOverlay.classList.add('hidden');
        });
    }

    // Close mobile menu when clicking on a link
    if (mobileNavOverlay) {
        const mobileLinks = mobileNavOverlay.querySelectorAll('a');
        mobileLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileNavOverlay.classList.add('hidden');
            });
        });
    }
}

// Function to highlight the active navigation link
function highlightActiveNavLink() {
    const currentPage = window.location.pathname.split('/').pop();
    const navLinks = document.querySelectorAll('.nav-link');
   
    navLinks.forEach(link => {
        link.classList.remove('text-white', 'font-medium');
        link.classList.add('text-gray-300');
       
        // Map pages to their respective nav items
        const pageMap = {
            'student-dashboard.html': 'dashboard',
            'mastery-tracker.html': 'mastery',
            'assignments.html': 'assignments',
            'assignment-details.html': 'assignments',
            'projects.html': 'projects',
            'project-details.html': 'projects',
            'leaderboard.html': 'leaderboard',
            'badges.html': 'badges'
        };
       
        const pageKey = pageMap[currentPage];
        if (link.getAttribute('data-page') === pageKey) {
            link.classList.remove('text-gray-300');
            link.classList.add('text-white', 'font-medium');
        }
    });
}

// Show loading state
function showLoadingState() {
    const tbody = document.querySelector('tbody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-gray-400">
                    Loading assignments...
                </td>
            </tr>
        `;
    }
}

// Navigate to assignment details page
function navigateToAssignmentDetails(assignmentId, assignmentTitle) {
    console.log('Navigating to assignment details:', assignmentId, assignmentTitle);
    
    // Store in sessionStorage for the details page
    if (assignmentTitle) {
        sessionStorage.setItem('lastClickedAssignment', JSON.stringify({
            id: assignmentId,
            title: assignmentTitle
        }));
    }
    
    // Navigate to assignment details page
    window.location.href = `assignment-details.html?id=${assignmentId}`;
}

// Setup click listeners for assignment rows
function setupAssignmentRowListeners() {
    console.log('Setting up assignment row listeners...');
    
    // Use event delegation on the table body
    const tbody = document.querySelector('tbody');
    if (!tbody) return;
    
    // Add click listener to table body
    tbody.addEventListener('click', (e) => {
        // Find the closest table row
        const row = e.target.closest('tr');
        if (!row) return;
        
        // Check if it's an assignment row
        const assignmentId = row.dataset.assignmentId;
        if (!assignmentId) return;
        
        // Don't trigger if clicking on buttons or links
        if (e.target.tagName === 'BUTTON' || 
            e.target.tagName === 'A' || 
            e.target.closest('button') || 
            e.target.closest('a')) {
            return;
        }
        
        // Get assignment title
        const titleElement = row.querySelector('.text-white');
        const assignmentTitle = titleElement ? titleElement.textContent : '';
        
        console.log('Assignment row clicked:', assignmentId, assignmentTitle);
        navigateToAssignmentDetails(assignmentId, assignmentTitle);
    });
    
    // Add hover effect to rows
    tbody.addEventListener('mouseover', (e) => {
        const row = e.target.closest('tr');
        if (row && row.dataset.assignmentId) {
            row.style.cursor = 'pointer';
            row.style.backgroundColor = 'rgba(31, 41, 55, 0.3)';
        }
    });
    
    tbody.addEventListener('mouseout', (e) => {
        const row = e.target.closest('tr');
        if (row && row.dataset.assignmentId) {
            row.style.backgroundColor = '';
        }
    });
}

// Update assignments display
function updateAssignmentsDisplay(assignmentsData) {
    const tbody = document.querySelector('tbody');
    if (!tbody) return;
    
    console.log('Rendering assignments:', assignmentsData);
    globalAssignmentsData = assignmentsData;
   
    tbody.innerHTML = '';
   
    // If no data, show appropriate message
    if (!assignmentsData || assignmentsData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-gray-400">
                    No assignments available yet. Check back later for new assignments.
                </td>
            </tr>
        `;
        return;
    }
   
    // Add each assignment to the table
    assignmentsData.forEach((assignment, index) => {
        // Determine status and difficulty classes
        let statusClass, statusText;
        if (assignment.status === 'completed') {
            statusClass = 'text-[#3fb950]';
            statusText = 'Completed';
        } else if (assignment.due_date && new Date(assignment.due_date) < new Date()) {
            statusClass = 'text-[#ff7b72]';
            statusText = 'Overdue';
        } else {
            statusClass = 'text-[#8B949E]';
            statusText = 'Not Started';
        }
       
        let difficultyClass, difficultyText;
        if (assignment.difficulty === 'hard') {
            difficultyClass = 'bg-[#A371F7]/20 text-[#A371F7]';
            difficultyText = 'Hard';
        } else if (assignment.difficulty === 'medium') {
            difficultyClass = 'bg-[#79c0ff]/20 text-[#79c0ff]';
            difficultyText = 'Medium';
        } else {
            difficultyClass = 'bg-primary/20 text-primary';
            difficultyText = 'Easy';
        }
       
        // Format due date
        const dueDate = assignment.due_date ? new Date(assignment.due_date).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        }) : 'N/A';
       
        // Use assignment.id or create a fallback ID
        const assignmentId = assignment.id || assignment.assignment_id || `assignment-${index + 1}`;
        const assignmentTitle = assignment.title || `Assignment ${index + 1}`;
       
        // Create the HTML for this assignment
        const assignmentHTML = `
            <tr class="hover:bg-gray-800/50 transition-colors" 
                data-assignment-id="${assignmentId}">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="ml-4">
                            <div class="text-sm font-medium text-white">${assignmentTitle}</div>
                            <div class="text-sm text-gray-400">${assignment.description || 'No description'}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">${assignment.course || assignment.subject || 'General'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">${dueDate}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm ${statusClass}">${statusText}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${difficultyClass}">
                        ${difficultyText}
                    </span>
                </td>
            </tr>
        `;
       
        // Add to table
        tbody.insertAdjacentHTML('beforeend', assignmentHTML);
    });
    
    // Setup click listeners after rendering
    setTimeout(() => {
        setupAssignmentRowListeners();
    }, 100);
}

// Fetch and display assignments data
async function fetchAssignmentsData() {
    try {
        showLoadingState();
       
        // Call the API
        const response = await studentAPI.getAssignments();
        console.log('API Response:', response);
       
        if (response.error) {
            console.error('Error fetching assignments:', response.error);
            if (response.error === 'Authentication required') {
                window.location.href = 'login.html';
            }
            return;
        }

        // Process response data
        let assignmentsData = [];
       
        if (Array.isArray(response)) {
            assignmentsData = response;
        } else if (response && typeof response === 'object') {
            if (Array.isArray(response.data)) {
                assignmentsData = response.data;
            } else if (Array.isArray(response.assignments)) {
                assignmentsData = response.assignments;
            } else if (response.items && Array.isArray(response.items)) {
                assignmentsData = response.items;
            } else {
                console.warn('Unexpected response format');
                assignmentsData = [response];
            }
        }
       
        console.log('Assignments data:', assignmentsData);
       
        if (!Array.isArray(assignmentsData)) {
            throw new Error('Invalid response format from server');
        }
       
        updateAssignmentsDisplay(assignmentsData);
    } catch (error) {
        console.error('Error fetching assignments data:', error);
       
        if (error.message.includes('401') || error.message.includes('Unauthorized')) {
            window.location.href = '/login.html';
            return;
        }
       
        updateAssignmentsDisplay([]);
    }
}

// Update user name and initials in the navigation bar
function updateUserNameDisplay() {
    try {
        const userName = localStorage.getItem('userName') || 'John Doe';
        const userInitials = localStorage.getItem('userInitials') || 'JD';
       
        const nameElement = document.getElementById('user-name');
        const initialsElement = document.getElementById('user-initials');
       
        if (nameElement) nameElement.textContent = userName;
        if (initialsElement) initialsElement.textContent = userInitials;
    } catch (error) {
        console.error('Error updating user display:', error);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing assignments page...');
    
    // Setup mobile navigation
    setupMobileNavigation();
   
    // Highlight active nav link
    highlightActiveNavLink();
   
    // Update user info
    updateUserNameDisplay();
   
    // Load assignments
    fetchAssignmentsData();
   
    // Add logout functionality
    const logoutButtons = [
        document.getElementById('logout-btn'),
        document.getElementById('desktop-logout-btn')
    ];
   
    logoutButtons.forEach(button => {
        if (button) {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                if (confirm('Are you sure you want to logout?')) {
                    logout();
                }
            });
        }
    });
});