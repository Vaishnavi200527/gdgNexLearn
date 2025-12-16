import { studentAPI } from '../api/studentApi.js';
import { showToast } from '../utils/toast.js';

class QuizResults {
    constructor() {
        // Quiz results data
        this.quiz = null;
        this.questions = [];
        this.submission = null;
        
        // DOM elements
        this.elements = {
            quizTitle: document.getElementById('quizTitle'),
            quizDescription: document.getElementById('quizDescription'),
            scoreBar: document.getElementById('scoreBar'),
            scoreText: document.getElementById('scoreText'),
            correctAnswers: document.getElementById('correctAnswers'),
            totalQuestions: document.getElementById('totalQuestions'),
            timeTaken: document.getElementById('timeTaken'),
            submittedOn: document.getElementById('submittedOn'),
            questionsContainer: document.getElementById('questionsContainer'),
            quizFeedback: document.getElementById('quizFeedback'),
            retakeQuizBtn: document.getElementById('retakeQuizBtn'),
            downloadResultsBtn: document.getElementById('downloadResultsBtn'),
            feedbackModal: document.getElementById('feedbackModal'),
            closeFeedbackModal: document.getElementById('closeFeedbackModal'),
            detailedFeedbackContent: document.getElementById('detailedFeedbackContent')
        };
        
        // Initialize the component
        this.init();
    }

    async init() {
        // Get quiz and submission IDs from URL
        const urlParams = new URLSearchParams(window.location.search);
        const quizId = urlParams.get('id');
        const submissionId = urlParams.get('submission');

        if (!quizId) {
            showToast('No quiz ID provided', 'error');
            window.location.href = '/pages/student/quizzes.html';
            return;
        }

        try {
            // Load quiz data
            await this.loadQuizData(quizId);
            
            // Load submission data if available
            if (submissionId) {
                await this.loadSubmissionData(quizId, submissionId);
            } else {
                // If no submission ID, try to get the latest submission
                await this.loadLatestSubmission(quizId);
            }
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Render the results
            this.renderResults();
            
        } catch (error) {
            console.error('Error initializing quiz results:', error);
            showToast('Failed to load quiz results. Please try again.', 'error');
            this.showErrorState();
        }
    }

    async loadQuizData(quizId) {
        try {
            // Show loading state
            this.showLoading(true);
            
            // Fetch quiz data from API
            const response = await studentAPI.getQuiz(quizId);
            this.quiz = response.data;
            this.questions = this.quiz.questions || [];
            
            // Update quiz info
            this.elements.quizTitle.textContent = this.quiz.title;
            this.elements.quizDescription.textContent = this.quiz.description || '';
            this.elements.totalQuestions.textContent = this.questions.length;
            
        } catch (error) {
            console.error('Error loading quiz data:', error);
            throw error;
        }
    }

    async loadSubmissionData(quizId, submissionId) {
        try {
            // Fetch submission data from API
            const response = await studentAPI.getQuizSubmission(quizId, submissionId);
            this.submission = response.data;
            
            // Process submission data
            this.processSubmissionData();
            
        } catch (error) {
            console.error('Error loading quiz results:', error);
            showToast('Failed to load quiz results', 'error');
            throw error;
        }
    }

    processSubmissionData() {
        // No need to process submission data as it's now handled by the server
        if (!this.submission) return;
        
        // Calculate score percentage
        const scorePercentage = Math.round((this.submission.score / this.questions.length) * 100);
        
        // Update score display
        this.elements.scoreText.textContent = `${scorePercentage}%`;
        this.elements.scoreBar.style.width = `${scorePercentage}%`;
        this.elements.scoreBar.className = `progress-bar ${
            scorePercentage >= 70 ? 'bg-green-500' : 
            scorePercentage >= 50 ? 'bg-yellow-500' : 'bg-red-500'
        }`;
        
        // Update other submission info
        this.elements.correctAnswers.textContent = `${this.submission.correct_answers} of ${this.questions.length}`;
        this.elements.timeTaken.textContent = this.formatTime(this.submission.time_taken);
        this.elements.submittedOn.textContent = new Date(this.submission.submitted_at).toLocaleString();
        
        // Update feedback
        this.updateFeedback(scorePercentage);
    }

    updateFeedback(scorePercentage) {
        let feedback = '';
        
        if (scorePercentage >= 90) {
            feedback = 'Excellent work! You have a strong understanding of this material.';
        } else if (scorePercentage >= 70) {
            feedback = 'Good job! You have a good grasp of the material, but there is room for improvement.';
        } else if (scorePercentage >= 50) {
            feedback = 'You passed, but consider reviewing the material and trying again to improve your score.';
        } else {
            feedback = 'You may want to review the material and try again. Consider reaching out to your instructor for additional help.';
        }
        
        this.elements.quizFeedback.textContent = feedback;
    }

    renderResults() {
        if (!this.questions.length || !this.submission) {
            this.showErrorState('No results to display.');
            return;
        }
        
        // Clear loading state
        this.showLoading(false);
        
        // Render each question with feedback
        const questionsHTML = this.questions.map((question, index) => {
            const userAnswer = this.submission.answers[index];
            const isCorrect = this.submission.correct_answers_by_question[index] || false;
            const correctAnswer = question.correct_option_index;
            
            return this.renderQuestion(question, index, userAnswer, isCorrect, correctAnswer);
        }).join('');
        
        this.elements.questionsContainer.innerHTML = questionsHTML;
        
        // Set up event listeners for question toggles
        this.setupQuestionToggles();
    }

    renderQuestion(question, index, userAnswer, isCorrect, correctAnswer) {
        const questionNumber = index + 1;
        const questionClass = isCorrect ? 'correct' : 'incorrect';
        const icon = isCorrect ? 'check_circle' : 'cancel';
        const iconColor = isCorrect ? 'text-green-500' : 'text-red-500';
        
        return `
            <div class="question-card ${questionClass} mb-6" data-question-index="${index}">
                <div class="question-header">
                    <h3 class="question-text">
                        <span class="material-icons ${iconColor} mr-2 align-middle">${icon}</span>
                        Question ${questionNumber}: ${question.question_text}
                    </h3>
                    <button class="text-indigo-600 hover:text-indigo-800 focus:outline-none view-feedback-btn" data-question-index="${index}">
                        <span class="material-icons">info</span>
                    </button>
                </div>
                <div class="answer-section">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Your Answer:</h4>
                    <div class="answer-option ${isCorrect ? 'correct-answer' : 'incorrect-answer'}">
                        <span class="material-icons answer-icon">${isCorrect ? 'check_circle' : 'cancel'}</span>
                        <div class="answer-text">
                            <p>${this.getOptionText(question.options, userAnswer)}</p>
                            ${!isCorrect ? `
                                <p class="text-sm text-gray-600 mt-1">
                                    <span class="font-medium">Correct Answer:</span> 
                                    ${this.getOptionText(question.options, correctAnswer)}
                                </p>
                            ` : ''}
                        </div>
                    </div>
                    ${question.explanation ? `
                        <div class="feedback-section ${isCorrect ? 'correct' : 'incorrect'} mt-3">
                            <p class="text-sm">${question.explanation}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    getOptionText(options, optionIndex) {
        if (!options || optionIndex === undefined || optionIndex === null) {
            return 'No answer provided';
        }
        const option = options[optionIndex];
        return option ? option.text : 'Invalid option';
    }

    setupEventListeners() {
        // Retake quiz button
        this.elements.retakeQuizBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to retake this quiz? Your previous attempts will be saved.')) {
                window.location.href = `/pages/student/quiz-take.html?id=${this.quiz.id}`;
            }
        });
        
        // Download results button
        this.elements.downloadResultsBtn.addEventListener('click', () => this.downloadResults());
        
        // Close modal button
        this.elements.closeFeedbackModal.addEventListener('click', () => {
            this.elements.feedbackModal.classList.add('hidden');
        });
        
        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target === this.elements.feedbackModal) {
                this.elements.feedbackModal.classList.add('hidden');
            }
        });
    }

    setupQuestionToggles() {
        // Set up click handlers for view feedback buttons
        const viewFeedbackBtns = document.querySelectorAll('.view-feedback-btn');
        viewFeedbackBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const questionIndex = parseInt(btn.dataset.questionIndex);
                this.showDetailedFeedback(questionIndex);
            });
        });
        
        // Set up click handlers for question cards to toggle answer visibility
        const questionCards = document.querySelectorAll('.question-card');
        questionCards.forEach(card => {
            const header = card.querySelector('.question-header');
            const content = card.querySelector('.answer-section');
            
            header.addEventListener('click', () => {
                content.style.display = content.style.display === 'none' ? 'block' : 'none';
            });
        });
    }

    showDetailedFeedback(questionIndex) {
        if (questionIndex < 0 || questionIndex >= this.questions.length) return;
        
        const question = this.questions[questionIndex];
        const userAnswer = this.submission.answers[questionIndex];
        const isCorrect = this.submission.correct_answers_by_question[questionIndex] || false;
        const correctAnswer = question.correct_option_index;
        
        // Create detailed feedback content
        let feedbackHTML = `
            <h4 class="text-lg font-medium mb-4">Question ${questionIndex + 1}: ${question.question_text}</h4>
            
            <div class="mb-6">
                <h5 class="font-medium text-gray-700 mb-2">Your Answer:</h5>
                <div class="p-3 rounded-md ${isCorrect ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}">
                    ${this.getOptionText(question.options, userAnswer)}
                </div>
                ${!isCorrect ? `
                    <div class="mt-2">
                        <h5 class="font-medium text-gray-700 mb-1">Correct Answer:</h5>
                        <div class="p-3 rounded-md bg-green-50 border border-green-200">
                            ${this.getOptionText(question.options, correctAnswer)}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        // Add explanation if available
        if (question.explanation) {
            feedbackHTML += `
                <div class="mb-6">
                    <h5 class="font-medium text-gray-700 mb-2">Explanation:</h5>
                    <div class="p-3 rounded-md bg-blue-50 border border-blue-200">
                        ${question.explanation}
                    </div>
                </div>
            `;
        }
        
        // Add references if available
        if (question.references && question.references.length > 0) {
            feedbackHTML += `
                <div class="mb-4">
                    <h5 class="font-medium text-gray-700 mb-2">References:</h5>
                    <ul class="list-disc pl-5 space-y-1">
                        ${question.references.map(ref => 
                            `<li class="text-sm">${ref}</li>`
                        ).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Update modal content and show it
        this.elements.detailedFeedbackContent.innerHTML = feedbackHTML;
        this.elements.feedbackModal.classList.remove('hidden');
    }

    async downloadResults() {
        try {
            // Show loading state
            const originalText = this.elements.downloadResultsBtn.innerHTML;
            this.elements.downloadResultsBtn.disabled = true;
            this.elements.downloadResultsBtn.innerHTML = '<span class="loading-spinner"></span> Preparing...';
            
            // Generate a PDF or text file with the results
            const content = this.generateResultsContent();
            
            // Create a blob and download link
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `quiz-results-${this.quiz.title.replace(/\s+/g, '-').toLowerCase()}-${new Date().toISOString().split('T')[0]}.txt`;
            document.body.appendChild(a);
            a.click();
            
            // Clean up
            setTimeout(() => {
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                this.elements.downloadResultsBtn.disabled = false;
                this.elements.downloadResultsBtn.innerHTML = originalText;
            }, 100);
            
        } catch (error) {
            console.error('Error downloading results:', error);
            showToast('Failed to download results. Please try again.', 'error');
            this.elements.downloadResultsBtn.disabled = false;
            this.elements.downloadResultsBtn.textContent = 'Download Results';
        }
    }

    generateResultsContent() {
        let content = `Quiz Results\n`;
        content += `====================\n\n`;
        content += `Title: ${this.quiz.title}\n`;
        content += `Description: ${this.quiz.description || 'N/A'}\n`;
        content += `Score: ${this.submission.score} out of ${this.questions.length} (${Math.round((this.submission.score / this.questions.length) * 100)}%)\n`;
        content += `Time Taken: ${this.formatTime(this.submission.time_time)}\n`;
        content += `Submitted On: ${new Date(this.submission.submitted_at).toLocaleString()}\n\n`;
        
        // Add questions and answers
        content += `Questions and Answers\n`;
        content += `====================\n\n`;
        
        this.questions.forEach((question, index) => {
            const userAnswer = this.submission.answers[index];
            const isCorrect = this.submission.correct_answers_by_question[index] || false;
            const correctAnswer = question.correct_option_index;
            
            content += `${index + 1}. ${question.question_text}\n`;
            content += `   Your Answer: ${this.getOptionText(question.options, userAnswer)} ${isCorrect ? '✓' : '✗'}\n`;
            
            if (!isCorrect) {
                content += `   Correct Answer: ${this.getOptionText(question.options, correctAnswer)}\n`;
            }
            
            if (question.explanation) {
                content += `   Explanation: ${question.explanation}\n`;
            }
            
            content += `\n`;
        });
        
        // Add summary
        content += `\nSummary\n`;
        content += `====================\n\n`;
        content += `Total Questions: ${this.questions.length}\n`;
        content += `Correct Answers: ${this.submission.correct_answers}\n`;
        content += `Incorrect Answers: ${this.questions.length - this.submission.correct_answers}\n`;
        content += `Percentage: ${Math.round((this.submission.correct_answers / this.questions.length) * 100)}%\n\n`;
        
        // Add feedback
        content += `Feedback\n`;
        content += `====================\n\n`;
        content += this.elements.quizFeedback.textContent + '\n';
        
        return content;
    }

    formatTime(seconds) {
        if (!seconds && seconds !== 0) return 'N/A';
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    showLoading(show = true) {
        if (show) {
            this.elements.questionsContainer.innerHTML = `
                <div class="text-center py-12">
                    <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mx-auto"></div>
                    <p class="mt-2 text-gray-600">Loading your results...</p>
                </div>
            `;
        }
    }

    showErrorState(message = 'An error occurred while loading the quiz results.') {
        this.elements.questionsContainer.innerHTML = `
            <div class="text-center py-12">
                <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                    <span class="material-icons text-red-600">error</span>
                </div>
                <h3 class="mt-2 text-lg font-medium text-gray-900">Error</h3>
                <p class="mt-1 text-sm text-gray-500">${message}</p>
                <div class="mt-6">
                    <a href="/pages/student/quizzes.html" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        Back to Quizzes
                    </a>
                </div>
            </div>
        `;
    }
}

// Initialize the quiz results when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on the quiz results page
    if (document.getElementById('quizTitle')) {
        const quizResults = new QuizResults();
    }
});
