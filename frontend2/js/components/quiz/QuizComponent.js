import { studentAPI } from '../../api/studentApi.js';

class QuizComponent {
    constructor(containerId, quizId) {
        this.container = document.getElementById(containerId);
        this.quizId = quizId;
        this.quiz = null;
        this.userAnswers = {};
    }

    async init() {
        try {
            // Load the quiz data
            this.quiz = await this.loadQuiz();
            this.renderQuiz();
            this.setupEventListeners();
        } catch (error) {
            console.error('Error loading quiz:', error);
            this.showError('Failed to load quiz. Please try again.');
        }
    }

    async loadQuiz() {
        const response = await fetch(`/api/quizzes/${this.quizId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load quiz');
        }
        
        return await response.json();
    }

    renderQuiz() {
        if (!this.quiz) {
            this.container.innerHTML = '<p>Loading quiz...</p>';
            return;
        }

        this.container.innerHTML = `
            <div class="quiz-container">
                <div class="quiz-header">
                    <h2>${this.quiz.title}</h2>
                    ${this.quiz.description ? `<p class="quiz-description">${this.quiz.description}</p>` : ''}
                </div>
                
                <form id="quiz-form">
                    <div class="questions-container">
                        ${this.quiz.questions && this.quiz.questions.length > 0 
                            ? this.quiz.questions.map((q, index) => this.renderQuestion(q, index + 1)).join('')
                            : '<p>No questions in this quiz yet.</p>'
                        }
                    </div>
                    
                    <div class="quiz-actions">
                        <button type="submit" class="btn btn-primary">Submit Quiz</button>
                    </div>
                </form>
            </div>
        `;
    }

    renderQuestion(question, questionNumber) {
        return `
            <div class="question-card" data-question-id="${question.id}">
                <div class="question-header">
                    <h4>Question ${questionNumber}</h4>
                </div>
                <div class="question-text">
                    ${question.question_text}
                </div>
                <div class="question-options">
                    ${this.renderOptions(question)}
                </div>
            </div>
        `;
    }

    renderOptions(question) {
        if (!question.options || !Array.isArray(question.options)) {
            return '<p>No options provided for this question.</p>';
        }

        return question.options.map((option, index) => `
            <div class="form-check mb-2">
                <input class="form-check-input" type="radio" 
                       name="question_${question.id}" 
                       id="q${question.id}_opt${index}"
                       value="${option}"
                       ${this.userAnswers[question.id] === option ? 'checked' : ''}>
                <label class="form-check-label" for="q${question.id}_opt${index}">
                    ${option}
                </label>
            </div>
        `).join('');
    }

    setupEventListeners() {
        const form = this.container.querySelector('#quiz-form');
        if (form) {
            form.addEventListener('submit', this.handleSubmit.bind(this));
        }

        // Track radio button changes
        const radioInputs = this.container.querySelectorAll('input[type="radio"]');
        radioInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const questionId = e.target.name.replace('question_', '');
                this.userAnswers[questionId] = e.target.value;
            });
        });
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        // Check if all questions are answered
        const unansweredQuestions = this.quiz.questions.filter(q => !this.userAnswers[q.id]);
        if (unansweredQuestions.length > 0) {
            if (!confirm('You have unanswered questions. Are you sure you want to submit?')) {
                return;
            }
        }

        try {
            const response = await fetch(`/api/quizzes/${this.quizId}/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    answers: this.userAnswers
                })
            });

            if (!response.ok) {
                throw new Error('Failed to submit quiz');
            }

            const result = await response.json();
            this.showQuizResult(result);
        } catch (error) {
            console.error('Error submitting quiz:', error);
            this.showError('Failed to submit quiz. Please try again.');
        }
    }

    showQuizResult(result) {
        this.container.innerHTML = `
            <div class="quiz-result text-center">
                <div class="result-icon">
                    <i class="fas fa-check-circle text-success" style="font-size: 4rem; margin-bottom: 1rem;"></i>
                </div>
                <h3>Quiz Submitted Successfully!</h3>
                <div class="score-display">
                    <h1>${result.score.toFixed(1)}%</h1>
                    <p>You scored ${result.score.toFixed(1)}% on this quiz.</p>
                </div>
                <div class="result-actions mt-4">
                    <a href="/student/dashboard.html" class="btn btn-primary">Back to Dashboard</a>
                </div>
            </div>
        `;
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                ${message}
            </div>
        `;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QuizComponent;
}
