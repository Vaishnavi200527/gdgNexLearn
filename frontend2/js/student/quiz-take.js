import { studentAPI } from '../api/studentApi.js';
import { showToast } from '../utils/toast.js';

class QuizTaker {
    constructor() {
        // Quiz state
        this.quiz = null;
        this.questions = [];
        this.currentQuestionIndex = 0;
        this.answers = {};
        this.timeLimit = 0;
        this.timeRemaining = 0;
        this.timerInterval = null;
        this.isSubmitting = false;

        // DOM elements
        this.elements = {
            quizTitle: document.getElementById('quizTitle'),
            timeRemaining: document.getElementById('timeRemaining'),
            progressText: document.getElementById('progressText'),
            progressBar: document.getElementById('progressBar'),
            questionContainer: document.getElementById('questionContainer'),
            questionNav: document.getElementById('questionNav'),
            prevBtn: document.getElementById('prevBtn'),
            nextBtn: document.getElementById('nextBtn'),
            submitBtn: document.getElementById('submitQuizBtn'),
            confirmationModal: document.getElementById('confirmationModal'),
            cancelSubmitBtn: document.getElementById('cancelSubmitBtn'),
            confirmSubmitBtn: document.getElementById('confirmSubmitBtn')
        };

        // Initialize the quiz
        this.init();
    }

    async init() {
        // Get quiz ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        const quizId = urlParams.get('id');

        if (!quizId) {
            showToast('No quiz ID provided', 'error');
            window.location.href = '/pages/student/quizzes.html';
            return;
        }

        // Load the quiz
        try {
            await this.loadQuiz(quizId);
            this.setupEventListeners();
            this.renderQuestion();
            this.updateNavigation();
            this.startTimer();
        } catch (error) {
            console.error('Error initializing quiz:', error);
            showToast('Failed to load quiz. Please try again.', 'error');
            window.location.href = '/pages/student/quizzes.html';
        }
    }

    async loadQuiz(quizId) {
        try {
            // Show loading state
            this.showLoading();
            
            // Fetch quiz data from API
            const response = await studentAPI.getQuiz(quizId);
            this.quiz = response.data;
            this.questions = this.quiz.questions || [];
            
            // Initialize answers object
            this.questions.forEach((_, index) => {
                this.answers[index] = null;
            });
            
            // Set time limit (in minutes, convert to milliseconds)
            this.timeLimit = (this.quiz.time_limit || 30) * 60 * 1000;
            this.timeRemaining = this.timeLimit;
            
            // Update UI
            this.elements.quizTitle.textContent = this.quiz.title;
            this.updateProgress();
            
        } catch (error) {
            console.error('Error loading quiz:', error);
            throw error;
        }
    }

    setupEventListeners() {
        // Navigation buttons
        this.elements.prevBtn.addEventListener('click', () => this.navigateToQuestion(this.currentQuestionIndex - 1));
        this.elements.nextBtn.addEventListener('click', () => this.navigateToQuestion(this.currentQuestionIndex + 1));
        
        // Submit button
        this.elements.submitBtn.addEventListener('click', () => this.showConfirmationModal(true));
        this.elements.cancelSubmitBtn.addEventListener('click', () => this.showConfirmationModal(false));
        this.elements.confirmSubmitBtn.addEventListener('click', () => this.submitQuiz());
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' && this.currentQuestionIndex > 0) {
                this.navigateToQuestion(this.currentQuestionIndex - 1);
            } else if (e.key === 'ArrowRight' && this.currentQuestionIndex < this.questions.length - 1) {
                this.navigateToQuestion(this.currentQuestionIndex + 1);
            } else if (e.key === 'Enter' && this.currentQuestionIndex === this.questions.length - 1) {
                this.showConfirmationModal(true);
            }
        });
    }

    renderQuestion() {
        if (!this.questions.length) {
            this.elements.questionContainer.innerHTML = `
                <div class="text-center py-12">
                    <p class="text-gray-600">No questions available for this quiz.</p>
                </div>
            `;
            return;
        }

        const question = this.questions[this.currentQuestionIndex];
        
        // Create question HTML
        const questionHTML = `
            <div class="question-container">
                <div class="question-text">
                    <span class="font-semibold">Question ${this.currentQuestionIndex + 1}:</span> ${question.question_text}
                </div>
                <div class="space-y-3 mt-4" id="optionsContainer">
                    ${this.renderOptions(question.options, question.type)}
                </div>
            </div>
        `;

        // Update question container with fade animation
        this.elements.questionContainer.style.opacity = '0';
        setTimeout(() => {
            this.elements.questionContainer.innerHTML = questionHTML;
            this.elements.questionContainer.style.opacity = '1';
            
            // Set up option selection
            this.setupOptionSelection();
        }, 200);
        
        // Update navigation buttons
        this.updateNavigation();
    }

    renderOptions(options, type = 'multiple_choice') {
        if (!options || !options.length) {
            return '<p class="text-gray-500">No options available for this question.</p>';
        }

        return options.map((option, index) => {
            const isSelected = this.answers[this.currentQuestionIndex] === index;
            return `
                <div class="option-item ${isSelected ? 'selected' : ''}" data-option-index="${index}">
                    <div class="flex items-center">
                        <input 
                            type="${type === 'multiple_choice' ? 'radio' : 'checkbox'}" 
                            name="question_${this.currentQuestionIndex}" 
                            id="option_${this.currentQuestionIndex}_${index}" 
                            value="${index}" 
                            class="option-radio"
                            ${isSelected ? 'checked' : ''}
                        >
                        <label for="option_${this.currentQuestionIndex}_${index}" class="option-label">
                            ${String.fromCharCode(65 + index)}. ${option.text}
                        </label>
                    </div>
                </div>
            `;
        }).join('');
    }

    setupOptionSelection() {
        const optionItems = this.elements.questionContainer.querySelectorAll('.option-item');
        
        optionItems.forEach(item => {
            item.addEventListener('click', (e) => {
                // Don't toggle if clicking on the radio input directly (handled by default browser behavior)
                if (e.target.tagName === 'INPUT') return;
                
                const optionIndex = parseInt(item.dataset.optionIndex);
                this.selectOption(optionIndex);
            });
            
            // Also handle clicks on the radio input
            const radioInput = item.querySelector('input[type="radio"], input[type="checkbox"]');
            if (radioInput) {
                radioInput.addEventListener('change', () => {
                    const optionIndex = parseInt(item.dataset.optionIndex);
                    this.selectOption(optionIndex);
                });
            }
        });
    }

    selectOption(optionIndex) {
        // Save the answer
        this.answers[this.currentQuestionIndex] = optionIndex;
        
        // Update UI
        const optionItems = this.elements.questionContainer.querySelectorAll('.option-item');
        optionItems.forEach((item, idx) => {
            if (idx === optionIndex) {
                item.classList.add('selected');
                item.querySelector('input').checked = true;
            } else {
                item.classList.remove('selected');
            }
        });
        
        // Update navigation
        this.updateQuestionNav(this.currentQuestionIndex, true);
        this.updateProgress();
    }

    updateNavigation() {
        // Previous button
        this.elements.prevBtn.disabled = this.currentQuestionIndex === 0;
        
        // Next/Submit button
        if (this.currentQuestionIndex === this.questions.length - 1) {
            this.elements.nextBtn.textContent = 'Submit Quiz';
            this.elements.nextBtn.classList.remove('bg-indigo-600', 'hover:bg-indigo-700');
            this.elements.nextBtn.classList.add('bg-green-600', 'hover:bg-green-700');
        } else {
            this.elements.nextBtn.textContent = 'Next Question';
            this.elements.nextBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
            this.elements.nextBtn.classList.add('bg-indigo-600', 'hover:bg-indigo-700');
        }
        
        // Update question navigation
        this.renderQuestionNav();
    }

    renderQuestionNav() {
        if (!this.questions.length) return;
        
        this.elements.questionNav.innerHTML = '';
        
        this.questions.forEach((_, index) => {
            const isAnswered = this.answers[index] !== null;
            const isCurrent = index === this.currentQuestionIndex;
            
            const button = document.createElement('button');
            button.type = 'button';
            button.className = `question-nav-btn ${
                isCurrent ? 'current ' : ''
            } ${
                isAnswered ? 'answered' : ''
            }`;
            button.textContent = index + 1;
            button.title = `Question ${index + 1}${isAnswered ? ' (Answered)' : ''}`;
            button.addEventListener('click', () => this.navigateToQuestion(index));
            
            this.elements.questionNav.appendChild(button);
        });
    }

    updateQuestionNav(questionIndex, isAnswered) {
        const buttons = this.elements.questionNav.querySelectorAll('button');
        if (buttons[questionIndex]) {
            const button = buttons[questionIndex];
            if (isAnswered) {
                button.classList.add('answered');
                button.title = `Question ${questionIndex + 1} (Answered)`;
            }
        }
    }

    navigateToQuestion(index) {
        // Validate index
        if (index < 0 || index >= this.questions.length) {
            return;
        }
        
        // Update current question index
        this.currentQuestionIndex = index;
        
        // Render the question
        this.renderQuestion();
        
        // Scroll to top of question
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }

    updateProgress() {
        if (!this.questions.length) return;
        
        // Calculate progress
        const answeredCount = Object.values(this.answers).filter(a => a !== null).length;
        const totalQuestions = this.questions.length;
        const progress = Math.round((answeredCount / totalQuestions) * 100);
        
        // Update progress bar
        this.elements.progressBar.style.width = `${progress}%`;
        this.elements.progressText.textContent = `${answeredCount}/${totalQuestions}`;
    }

    startTimer() {
        // Clear any existing timer
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        
        // Update timer immediately
        this.updateTimerDisplay();
        
        // Update timer every second
        this.timerInterval = setInterval(() => {
            this.timeRemaining -= 1000;
            this.updateTimerDisplay();
            
            // Check if time is up
            if (this.timeRemaining <= 0) {
                clearInterval(this.timerInterval);
                this.timeUp();
            }
        }, 1000);
    }

    updateTimerDisplay() {
        if (this.timeRemaining <= 0) {
            this.elements.timeRemaining.textContent = '00:00';
            this.elements.timeRemaining.className = 'timer-danger';
            return;
        }
        
        const minutes = Math.floor(this.timeRemaining / 60000);
        const seconds = Math.floor((this.timeRemaining % 60000) / 1000);
        
        this.elements.timeRemaining.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Update timer color based on remaining time
        if (this.timeRemaining < 300000) { // Less than 5 minutes
            this.elements.timeRemaining.className = 'timer-danger';
        } else if (this.timeRemaining < 600000) { // Less than 10 minutes
            this.elements.timeRemaining.className = 'timer-warning';
        } else {
            this.elements.timeRemaining.className = '';
        }
    }

    timeUp() {
        // Disable all inputs
        const inputs = document.querySelectorAll('input[type="radio"], input[type="checkbox"]');
        inputs.forEach(input => {
            input.disabled = true;
        });
        
        // Disable navigation
        this.elements.prevBtn.disabled = true;
        this.elements.nextBtn.disabled = true;
        
        // Show time's up message
        showToast('Time\'s up! Submitting your quiz...', 'warning');
        
        // Auto-submit after a short delay
        setTimeout(() => {
            this.submitQuiz();
        }, 2000);
    }

    showConfirmationModal(show) {
        if (show) {
            this.elements.confirmationModal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        } else {
            this.elements.confirmationModal.classList.add('hidden');
            document.body.style.overflow = '';
        }
    }

    async submitQuiz() {
        if (this.isSubmitting) return;
        
        try {
            this.isSubmitting = true;
            this.showConfirmationModal(false);
            
            // Prepare submission data
            const submission = {
                quiz_id: this.quiz.id,
                answers: this.answers,
                time_taken: Math.floor((this.timeLimit - this.timeRemaining) / 1000) // in seconds
            };
            
            // Show loading state
            const submitBtn = this.elements.submitBtn;
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading-spinner"></span> Submitting...';
            
            // Submit to API
            const response = await studentAPI.submitQuiz(submission);
            
            // Redirect to results page
            window.location.href = `/pages/student/quiz-results.html?id=${this.quiz.id}&submission=${response.submission_id}`;
            
        } catch (error) {
            console.error('Error submitting quiz:', error);
            showToast('Failed to submit quiz. Please try again.', 'error');
            this.isSubmitting = false;
            this.elements.submitBtn.disabled = false;
            this.elements.submitBtn.textContent = originalText;
        }
    }

    showLoading() {
        this.elements.questionContainer.innerHTML = `
            <div class="text-center py-12">
                <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mx-auto"></div>
                <p class="mt-2 text-gray-600">Loading quiz...</p>
            </div>
        `;
    }

    cleanup() {
        // Clear timer
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        
        // Remove event listeners
        this.elements.prevBtn.removeEventListener('click', this.navigateToQuestion);
        this.elements.nextBtn.removeEventListener('click', this.navigateToQuestion);
        this.elements.submitBtn.removeEventListener('click', this.showConfirmationModal);
        document.removeEventListener('keydown', this.handleKeyDown);
    }
}

// Initialize the quiz taker when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on the quiz take page
    if (document.getElementById('quizTitle')) {
        const quizTaker = new QuizTaker();
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            quizTaker.cleanup();
        });
    }
});
