import { studentAPI } from '../api/studentApi.js';
import { showToast } from '../utils/toast.js';

class StudentQuizzes {
    constructor() {
        this.quizzes = [];
        this.filteredQuizzes = [];
        this.currentFilter = 'all';
        this.templates = {
            quizCard: document.getElementById('quizCardTemplate'),
            emptyState: document.getElementById('emptyStateTemplate')
        };
        
        // Initialize the component
        this.init();
    }

    async init() {
        // Cache DOM elements
        this.quizzesContainer = document.getElementById('quizzesContainer');
        this.filterButtons = document.querySelectorAll('.filter-btn');
        this.searchInput = document.querySelector('input[type="text"]');
        
        // Add event listeners
        this.addEventListeners();
        
        // Load quizzes
        await this.loadQuizzes();
    }

    addEventListeners() {
        // Filter buttons
        this.filterButtons.forEach(button => {
            button.addEventListener('click', () => this.handleFilterClick(button));
        });

        // Search input
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        }
    }

    async loadQuizzes() {
        try {
            // Show loading state
            this.showLoading();
            
            // Fetch quizzes from the API
            const response = await studentAPI.getQuizzes();
            this.quizzes = this.processQuizzes(response.data || []);
            
            // Apply initial filter
            this.applyFilter(this.currentFilter);
            
        } catch (error) {
            console.error('Error loading quizzes:', error);
            showToast('Failed to load quizzes. Please try again.', 'error');
            this.showEmptyState('Failed to load quizzes. Please refresh the page.');
        }
    }

    processQuizzes(quizzes) {
        const now = new Date();
        
        return quizzes.map(quiz => {
            const dueDate = new Date(quiz.due_date);
            const isOverdue = dueDate < now && !quiz.completed;
            const status = this.determineQuizStatus(quiz, isOverdue);
            const progress = this.calculateProgress(quiz);
            
            return {
                ...quiz,
                dueDate,
                isOverdue,
                status,
                progress,
                formattedDueDate: this.formatDate(dueDate),
                timeRemaining: this.getTimeRemaining(dueDate)
            };
        });
    }

    determineQuizStatus(quiz, isOverdue) {
        if (quiz.completed) return 'completed';
        if (isOverdue) return 'overdue';
        if (quiz.started) return 'in-progress';
        return 'pending';
    }

    calculateProgress(quiz) {
        if (quiz.completed) return 100;
        if (!quiz.questions || !quiz.questions.length) return 0;
        
        const answered = quiz.questions.filter(q => q.answer).length;
        return Math.round((answered / quiz.questions.length) * 100);
    }

    formatDate(date) {
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    getTimeRemaining(dueDate) {
        const now = new Date();
        const diff = dueDate - now;
        
        if (diff <= 0) return 'Overdue';
        
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        
        if (days > 0) return `Due in ${days} day${days > 1 ? 's' : ''}`;
        if (hours > 0) return `Due in ${hours} hour${hours > 1 ? 's' : ''}`;
        return 'Due soon';
    }

    handleFilterClick(button) {
        // Update active filter button
        this.filterButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        
        // Apply the filter
        const filter = button.dataset.filter;
        this.currentFilter = filter;
        this.applyFilter(filter);
    }

    applyFilter(filter) {
        this.filteredQuizzes = this.quizzes.filter(quiz => {
            if (filter === 'all') return true;
            if (filter === 'pending') return quiz.status === 'pending';
            if (filter === 'in-progress') return quiz.status === 'in-progress';
            if (filter === 'completed') return quiz.status === 'completed';
            return true;
        });
        
        this.renderQuizzes();
    }

    handleSearch(query) {
        const searchTerm = query.toLowerCase().trim();
        
        if (!searchTerm) {
            this.applyFilter(this.currentFilter);
            return;
        }
        
        this.filteredQuizzes = this.quizzes.filter(quiz => 
            quiz.title.toLowerCase().includes(searchTerm) ||
            quiz.description.toLowerCase().includes(searchTerm) ||
            quiz.class_name.toLowerCase().includes(searchTerm)
        );
        
        this.renderQuizzes();
    }

    renderQuizzes() {
        // Clear the container
        this.quizzesContainer.innerHTML = '';
        
        // Show empty state if no quizzes
        if (this.filteredQuizzes.length === 0) {
            this.showEmptyState('No quizzes match your current filter.');
            return;
        }
        
        // Render each quiz
        this.filteredQuizzes.forEach(quiz => {
            const quizElement = this.createQuizCard(quiz);
            this.quizzesContainer.appendChild(quizElement);
        });
    }

    createQuizCard(quiz) {
        const card = this.templates.quizCard.content.cloneNode(true);
        const quizElement = card.querySelector('.quiz-card');
        
        // Set quiz data attributes
        quizElement.dataset.id = quiz.id;
        quizElement.dataset.status = quiz.status;
        
        // Set quiz content
        quizElement.querySelector('.quiz-title').textContent = quiz.title;
        quizElement.querySelector('.quiz-description').textContent = quiz.description;
        quizElement.querySelector('.quiz-class').textContent = quiz.class_name || 'No Class';
        quizElement.querySelector('.quiz-due-date').textContent = quiz.formattedDueDate;
        
        // Set status badge
        const statusBadge = quizElement.querySelector('.quiz-status-badge');
        statusBadge.textContent = quiz.status.replace('-', ' ');
        statusBadge.dataset.status = quiz.status;
        
        // Set progress
        const progressBar = quizElement.querySelector('.quiz-progress');
        progressBar.style.width = `${quiz.progress}%`;
        
        const progressText = quizElement.querySelector('.quiz-progress-text');
        progressText.textContent = `${quiz.progress}% complete`;
        
        // Set up action button
        const actionButton = quizElement.querySelector('.quiz-action-btn');
        
        if (quiz.status === 'completed') {
            actionButton.textContent = 'View Results';
            actionButton.dataset.action = 'view';
            actionButton.addEventListener('click', () => this.viewQuizResults(quiz.id));
        } else if (quiz.status === 'in-progress') {
            actionButton.textContent = 'Continue';
            actionButton.dataset.action = 'continue';
            actionButton.addEventListener('click', () => this.startQuiz(quiz.id));
        } else {
            actionButton.textContent = 'Start Quiz';
            actionButton.dataset.action = 'start';
            actionButton.addEventListener('click', () => this.startQuiz(quiz.id));
        }
        
        return quizElement;
    }

    showLoading() {
        this.quizzesContainer.innerHTML = `
            <div class="text-center py-10">
                <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mx-auto"></div>
                <p class="mt-2 text-gray-600">Loading your quizzes...</p>
            </div>
        `;
    }

    showEmptyState(message = 'No quizzes found.') {
        const emptyState = this.templates.emptyState.content.cloneNode(true);
        const title = emptyState.querySelector('h3');
        const description = emptyState.querySelector('p');
        
        if (message) {
            title.textContent = message;
            description.textContent = 'Try changing your filters or check back later.';
        }
        
        this.quizzesContainer.innerHTML = '';
        this.quizzesContainer.appendChild(emptyState);
    }

    startQuiz(quizId) {
        // Navigate to quiz taking page
        window.location.href = `/pages/student/quiz-take.html?id=${quizId}`;
    }

    viewQuizResults(quizId) {
        // Navigate to quiz results page
        window.location.href = `/pages/student/quiz-results.html?id=${quizId}`;
    }
}

// Initialize the student quizzes interface when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on the quizzes page
    if (document.getElementById('quizzesContainer')) {
        new StudentQuizzes();
    }
});
