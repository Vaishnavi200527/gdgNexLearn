import { studentAPI } from '../../api/studentApi.js';

// Fallback to global studentAPI if import fails
const api = studentAPI || window.studentAPI;
if (!api) {
    console.error('studentAPI not available. Ensure studentApi.js is loaded.');
}

class StudentAssignmentList {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.assignments = [];
        this.isMounted = false;
        this.eventListeners = [];
        this.currentFilter = 'all';
        this.loading = false;
        this.init();
    }

    async init() {
        if (this.isMounted) return;
        
        this.isMounted = true;
        try {
            await this.loadAssignments();
        } catch (error) {
            console.error('Error initializing StudentAssignmentList:', error);
            this.showError('Failed to initialize assignments. Please refresh the page.');
        }
    }

    async loadAssignments() {
        this.loading = true;
        this.render();
        try {
            // Load both regular assignments and quizzes
            const [assignmentsResponse, quizzesResponse] = await Promise.all([
                api.getAssignments(),
                fetch('/student/quizzes', {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                }).then(res => res.ok ? res.json() : []).catch(err => {
                    console.warn('Failed to load quizzes:', err);
                    return [];
                })
            ]);

            // Process regular assignments
            const regularAssignments = assignmentsResponse.map(a => ({
                ...a,
                type: 'assignment',
                due_date: a.due_date || new Date().toISOString()
            }));

            // Process quizzes
            const quizAssignments = quizzesResponse.map(q => ({
                id: q.quiz_id,
                title: q.quiz?.title || 'Quiz',
                description: q.quiz?.description || 'No description',
                type: 'quiz',
                status: q.status,
                score: q.score,
                due_date: q.due_date || new Date().toISOString(),
                submitted_at: q.submitted_at,
                max_score: 100
            }));

            // Combine and sort
            this.assignments = [...regularAssignments, ...quizAssignments]
                .sort((a, b) => new Date(a.due_date) - new Date(b.due_date));

        } catch (error) {
            console.error('Error loading assignments:', error);
            this.showError('Failed to load assignments. Please try again.');
        } finally {
            this.loading = false;
            this.render();
        }
    }

    render() {
        if (this.loading) {
            this.container.innerHTML = `
                <div class="text-center p-5">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-2">Loading assignments...</p>
                </div>
            `;
            return;
        }

        if (this.assignments.length === 0) {
            this.container.innerHTML = `
                <div class="no-assignments">
                    <p>No assignments found.</p>
                </div>
            `;
            return;
        }

        const now = new Date();
        
        this.container.innerHTML = `
            <div class="assignments-container">
                <div class="assignments-header">
                    <h2>My Assignments</h2>
                    <div class="assignment-filters">
                        <button class="filter-btn ${this.currentFilter === 'all' ? 'active' : ''}" data-filter="all">All</button>
                        <button class="filter-btn ${this.currentFilter === 'pending' ? 'active' : ''}" data-filter="pending">Pending</button>
                        <button class="filter-btn ${this.currentFilter === 'submitted' ? 'active' : ''}" data-filter="submitted">Submitted</button>
                        <button class="filter-btn ${this.currentFilter === 'graded' ? 'active' : ''}" data-filter="graded">Graded</button>
                    </div>
                </div>
                
                <div class="assignments-list">
                    ${this.assignments.map(assignment => {
                        const dueDate = new Date(assignment.due_date);
                        const isOverdue = dueDate < now && assignment.status !== 'submitted' && assignment.status !== 'graded';
                        const statusClass = this.getStatusClass(assignment.status, isOverdue);
                        
                        return `
                            <div class="assignment-card" data-status="${assignment.status}" data-id="${assignment.id}">
                                <div class="assignment-header">
                                    <h3 class="assignment-title">${assignment.title}</h3>
                                    <span class="assignment-status ${statusClass}">
                                        ${this.formatStatus(assignment.status, isOverdue)}
                                    </span>
                                </div>
                                
                                <div class="assignment-meta">
                                    <span class="assignment-class">${assignment.class_name}</span>
                                    <span class="assignment-due">
                                        <i class="far fa-calendar-alt"></i> 
                                        Due: ${dueDate.toLocaleString()}
                                    </span>
                                </div>
                                
                                <div class="assignment-description">
                                    ${assignment.description || 'No description provided.'}
                                </div>
                                
                                <div class="assignment-actions">
                                    ${assignment.status === 'assigned' ? `
                                        <button class="btn btn-primary btn-sm start-assignment" 
                                                data-id="${assignment.id}"
                                                data-type="${assignment.type}">
                                            ${assignment.type === 'quiz' ? 'Start Quiz' : 'Start Assignment'}
                                        </button>
                                    ` : assignment.status === 'submitted' ? `
                                        <span class="submitted-text">Submitted on: ${new Date(assignment.submitted_at).toLocaleString()}</span>
                                    ` : assignment.status === 'graded' ? `
                                        <span class="graded-text">
                                            Graded: ${assignment.score}%
                                            ${assignment.type === 'quiz' ? '(Auto-graded)' : ''}
                                        </span>
                                    ` : ''}
                                    
                                    ${assignment.content_url ? `
                                        <a href="${assignment.content_url}" target="_blank" class="btn btn-outline-secondary btn-sm">
                                            <i class="fas fa-external-link-alt"></i> View Content
                                        </a>
                                    ` : ''}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
        this.setupEventListeners();
        this.filterAssignments(this.currentFilter);
    }
    
    getStatusClass(status, isOverdue) {
        if (isOverdue) return 'status-overdue';
        switch(status) {
            case 'assigned': return 'status-pending';
            case 'submitted': return 'status-submitted';
            case 'graded': return 'status-graded';
            default: return '';
        }
    }
    
    formatStatus(status, isOverdue) {
        if (isOverdue) return 'Overdue';
        return status.charAt(0).toUpperCase() + status.slice(1);
    }
    
    setupEventListeners() {
        // Remove any existing event listeners to prevent duplicates
        this.cleanupEventListeners();
        
        // Filter buttons
        const filterButtons = this.container.querySelectorAll('.filter-btn');
        filterButtons.forEach(btn => {
            const handler = (e) => {
                e.preventDefault();
                const filter = e.currentTarget.dataset.filter;
                this.filterAssignments(filter);
                
                // Update active state
                filterButtons.forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
            };
            btn.addEventListener('click', handler);
            this.eventListeners.push({ element: btn, event: 'click', handler });
        });
        
        // Start assignment buttons
        const startButtons = this.container.querySelectorAll('.start-assignment');
        startButtons.forEach(btn => {
            const handler = (e) => {
                e.preventDefault();
                const assignmentId = e.currentTarget.dataset.id;
                this.startAssignment(assignmentId);
            };
            btn.addEventListener('click', handler);
            this.eventListeners.push({ element: btn, event: 'click', handler });
        });
    }
    
    filterAssignments(filter) {
        this.currentFilter = filter;
        const cards = this.container.querySelectorAll('.assignment-card');
        cards.forEach(card => {
            const status = card.dataset.status;
            // Map 'assigned' status to 'pending' filter
            const effectiveStatus = status === 'assigned' ? 'pending' : status;
            if (filter === 'all' || effectiveStatus === filter) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    }
    
    async startAssignment(assignmentId) {
        // In a real app, you would navigate to an assignment submission page
        // For now, we'll just show a simple submission form
        const assignment = this.assignments.find(a => a.id == assignmentId);
        if (!assignment) return;
        
        this.container.innerHTML = `
            <div class="assignment-submission-container">
                <h2>${assignment.title}</h2>
                <p class="assignment-description">${assignment.description || 'No description provided.'}</p>
                
                <div class="assignment-details">
                    <p><strong>Class:</strong> ${assignment.class_name}</p>
                    <p><strong>Due:</strong> ${new Date(assignment.due_date).toLocaleString()}</p>
                    ${assignment.content_url ? `
                        <p>
                            <a href="${assignment.content_url}" target="_blank">
                                <i class="fas fa-external-link-alt"></i> View Assignment Content
                            </a>
                        </p>
                    ` : ''}
                </div>
                
                <form id="assignmentSubmissionForm">
                    <div class="form-group">
                        <label for="submissionText">Your Work</label>
                        <textarea id="submissionText" name="submission_text" rows="8" class="form-control" 
                                  placeholder="Type your response here or paste a link to your work..." required></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="submissionFiles">Attach Files (Optional)</label>
                        <input type="file" id="submissionFiles" name="files" multiple class="form-control">
                    </div>
                    
                    <div class="form-group">
                        <label for="submissionNotes">Notes to Teacher (Optional)</label>
                        <textarea id="submissionNotes" name="notes" rows="3" class="form-control" 
                                  placeholder="Any additional notes for your teacher..."></textarea>
                    </div>
                    
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">Submit Assignment</button>
                        <button type="button" id="cancelSubmission" class="btn btn-secondary">Cancel</button>
                    </div>
                </form>
                
                <div id="submissionError" class="error-message"></div>
            </div>
        `;
        
        // Set up form submission
        document.getElementById('assignmentSubmissionForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.submitAssignment(assignmentId);
        });
        
        // Set up cancel button
        document.getElementById('cancelSubmission').addEventListener('click', () => this.render());
    }
    
    async submitAssignment(assignmentId) {
        const form = document.getElementById('assignmentSubmissionForm');
        const formData = new FormData(form);
        
        const assignment = this.assignments.find(a => a.id == assignmentId);
        const endpoint = assignment && assignment.type === 'quiz'
            ? `/student/quizzes/${assignmentId}/submit`
            : `/student/assignments/${assignmentId}/submit`;

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to submit assignment');
            }
            
            // Refresh the assignments list
            await this.loadAssignments();
            this.render();
            
            // Show success message
            alert('Assignment submitted successfully!');
            
        } catch (error) {
            console.error('Error submitting assignment:', error);
            const errorElement = document.getElementById('submissionError');
            if (errorElement) {
                errorElement.textContent = error.message || 'Failed to submit assignment';
                errorElement.style.display = 'block';
            }
        }
    }
    
    cleanupEventListeners() {
        // Remove all registered event listeners
        this.eventListeners.forEach(({ element, event, handler }) => {
            element.removeEventListener(event, handler);
        });
        this.eventListeners = [];
    }

    showError(message) {
        // Remove any existing error messages
        const existingError = this.container.querySelector('.alert-danger');
        if (existingError) {
            existingError.remove();
        }
        
        const errorElement = document.createElement('div');
        errorElement.className = 'alert alert-danger';
        errorElement.textContent = message;
        this.container.prepend(errorElement);
        
        // Remove error after 5 seconds
        setTimeout(() => {
            if (errorElement.parentNode) {
                errorElement.remove();
            }
        }, 5000);
    }
    
    destroy() {
        this.isMounted = false;
        this.cleanupEventListeners();
        this.container.innerHTML = '';
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StudentAssignmentList;
}
