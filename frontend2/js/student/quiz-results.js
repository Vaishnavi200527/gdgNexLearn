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

    async loadLatestSubmission(quizId) {
        try {
            // Fetch the latest submission for this quiz
            const response = await studentAPI.getLatestQuizSubmission(quizId);
            this.submission = response.data;

            // Process submission data
            this.processSubmissionData();

        } catch (error) {
            console.error('Error loading latest quiz submission:', error);
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

        // Render concept review if available (for scores < 70%)
        if (this.submission.concept_review) {
            this.renderConceptReview(this.submission.concept_review);
        }

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
        const loadingIndicator = document.getElementById('loadingIndicator');
        const mainContent = document.querySelector('main > div > div:not(#loadingIndicator)');

        if (show) {
            if (loadingIndicator) loadingIndicator.classList.remove('hidden');
            // Hide all main content sections during loading
            const sections = document.querySelectorAll('main > div > div:not(#loadingIndicator)');
            sections.forEach(section => section.classList.add('hidden'));
        } else {
            if (loadingIndicator) loadingIndicator.classList.add('hidden');
            // Show all main content sections after loading
            const sections = document.querySelectorAll('main > div > div:not(#loadingIndicator)');
            sections.forEach(section => section.classList.remove('hidden'));
        }
    }

    renderConceptReview(conceptReview) {
        const conceptReviewSection = document.getElementById('conceptReviewSection');
        const conceptReviewContent = document.getElementById('conceptReviewContent');

        if (!conceptReview || !conceptReview.concept_reviews || conceptReview.concept_reviews.length === 0) {
            conceptReviewSection.classList.add('hidden');
            return;
        }

        // Show the concept review section
        conceptReviewSection.classList.remove('hidden');

        // Add recommendation at the top
        const recommendationHTML = conceptReview.recommendation ? `
            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                <div class="flex items-center">
                    <span class="material-icons text-yellow-600 mr-2">lightbulb</span>
                    <p class="text-sm font-medium text-yellow-800">${conceptReview.recommendation}</p>
                </div>
            </div>
        ` : '';

        // Step 1: Clear identification of weak concepts
        const weakConceptsOverview = `
            <div class="mb-8">
                <h3 class="text-xl font-bold text-gray-900 mb-4 flex items-center">
                    <span class="material-icons text-red-600 mr-3">warning</span>
                    Step 1: Concepts You Need to Focus On
                </h3>
                <p class="text-sm text-gray-600 mb-4">Based on your quiz performance, you struggled with these specific concepts. Let's review them one by one:</p>
                <div class="grid gap-3">
                    ${conceptReview.concept_reviews.map((review, index) => `
                        <div class="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center justify-between hover:bg-red-100 transition-colors">
                            <div class="flex items-center">
                                <span class="bg-red-500 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold mr-3">${index + 1}</span>
                                <div>
                                    <span class="font-semibold text-red-800">${review.concept_name}</span>
                                    <p class="text-xs text-red-600 mt-1">You got ${Math.round(review.accuracy * 100)}% correct on related questions</p>
                                </div>
                            </div>
                            <span class="material-icons text-red-500">arrow_forward</span>
                        </div>
                    `).join('')}
                </div>
                <div class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <p class="text-sm text-blue-800 font-medium mb-2">📚 How This Review Works:</p>
                    <p class="text-sm text-blue-700">Each concept below includes explanations based on the materials your teacher provided. Read through each one carefully - understanding these will help you improve your performance on future quizzes.</p>
                </div>
            </div>
        `;

        // Step 2: Detailed explanations for each weak concept
        const detailedExplanations = `
            <div class="mb-8">
                <h3 class="text-xl font-bold text-gray-900 mb-6 flex items-center">
                    <span class="material-icons text-blue-600 mr-3">school</span>
                    Step 2: Detailed Concept Explanations
                </h3>
                <div class="space-y-6">
                    ${conceptReview.concept_reviews.map((review, index) => `
                        <div class="bg-white border-2 border-gray-200 rounded-xl overflow-hidden shadow-sm">
                            <!-- Concept Header -->
                            <div class="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center">
                                        <span class="bg-white text-blue-600 rounded-full w-10 h-10 flex items-center justify-center text-lg font-bold mr-4">${index + 1}</span>
                                        <div>
                                            <h4 class="text-xl font-bold text-white">${review.title || `Understanding ${review.concept_name}`}</h4>
                                            <p class="text-blue-100 text-sm">Based on your quiz performance (${Math.round(review.accuracy * 100)}% accuracy)</p>
                                        </div>
                                    </div>
                                    <div class="text-right">
                                        <div class="text-white text-sm">Your Score</div>
                                        <div class="text-2xl font-bold text-white">${Math.round(review.accuracy * 100)}%</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Concept Content -->
                            <div class="p-6 space-y-6">
                                <!-- Key Points -->
                                <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                                    <h5 class="font-semibold text-green-800 mb-3 flex items-center">
                                        <span class="material-icons text-green-600 mr-2">check_circle</span>
                                        Key Points to Remember
                                    </h5>
                                    <ul class="space-y-2">
                                        ${review.key_points.map(point => `
                                            <li class="flex items-start">
                                                <span class="text-green-600 mr-2 mt-1">•</span>
                                                <span class="text-sm text-green-800">${point}</span>
                                            </li>
                                        `).join('')}
                                    </ul>
                                </div>

                                <!-- Detailed Explanation -->
                                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                    <h5 class="font-semibold text-blue-800 mb-3 flex items-center">
                                        <span class="material-icons text-blue-600 mr-2">lightbulb</span>
                                        Detailed Explanation
                                    </h5>
                                    <div class="text-sm text-blue-900 leading-relaxed">
                                        ${review.explanation}
                                    </div>
                                </div>

                                <!-- Practice Tip -->
                                <div class="bg-purple-50 border border-purple-200 rounded-lg p-4">
                                    <h5 class="font-semibold text-purple-800 mb-3 flex items-center">
                                        <span class="material-icons text-purple-600 mr-2">tips_and_updates</span>
                                        Practice Tip
                                    </h5>
                                    <div class="bg-white p-3 rounded border border-purple-200">
                                        <p class="text-sm text-purple-900">${review.practice_tip}</p>
                                    </div>
                                </div>

                                <!-- Common Mistakes -->
                                <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                                    <h5 class="font-semibold text-red-800 mb-3 flex items-center">
                                        <span class="material-icons text-red-600 mr-2">warning</span>
                                        Common Mistakes to Avoid
                                    </h5>
                                    <ul class="space-y-2">
                                        ${review.common_mistakes.map(mistake => `
                                            <li class="flex items-start">
                                                <span class="text-red-600 mr-2 mt-1">⚠</span>
                                                <span class="text-sm text-red-800">${mistake}</span>
                                            </li>
                                        `).join('')}
                                    </ul>
                                </div>

                                <!-- Understanding Check -->
                                <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
                                    <h5 class="font-semibold text-gray-800 mb-3 flex items-center">
                                        <span class="material-icons text-gray-600 mr-2">quiz</span>
                                        Quick Check: Do You Understand?
                                    </h5>
                                    <p class="text-sm text-gray-700 mb-3">Before moving on, make sure you can explain this concept in your own words.</p>
                                    <button class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
                                        <span class="material-icons mr-1 text-sm">check</span>
                                        I Understand This Concept
                                    </button>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // Step 3: Action items and next steps
        const nextSteps = `
            <div class="bg-green-50 border border-green-200 rounded-lg p-6">
                <h3 class="text-lg font-bold text-green-800 mb-4 flex items-center">
                    <span class="material-icons text-green-600 mr-2">flag</span>
                    Next Steps to Improve
                </h3>
                <div class="grid md:grid-cols-2 gap-4">
                    <div class="bg-white p-4 rounded border border-green-200">
                        <h4 class="font-semibold text-green-800 mb-2">📖 Review Materials</h4>
                        <p class="text-sm text-green-700">Go back to the assignment materials and re-read the sections covering these concepts.</p>
                    </div>
                    <div class="bg-white p-4 rounded border border-green-200">
                        <h4 class="font-semibold text-green-800 mb-2">✏️ Practice More</h4>
                        <p class="text-sm text-green-700">Try additional practice questions on these topics before your next quiz.</p>
                    </div>
                    <div class="bg-white p-4 rounded border border-green-200">
                        <h4 class="font-semibold text-green-800 mb-2">💬 Ask for Help</h4>
                        <p class="text-sm text-green-700">If you're still confused, reach out to your teacher or classmates for clarification.</p>
                    </div>
                    <div class="bg-white p-4 rounded border border-green-200">
                        <h4 class="font-semibold text-green-800 mb-2">🔄 Retake Quiz</h4>
                        <p class="text-sm text-green-700">Once you feel confident, retake this quiz to test your improvement.</p>
                    </div>
                </div>
            </div>
        `;

        conceptReviewContent.innerHTML = recommendationHTML + weakConceptsOverview + detailedExplanations + nextSteps;
    }

    setupConceptReviewToggles() {
        const conceptHeaders = document.querySelectorAll('.concept-header');
        conceptHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const conceptIndex = header.dataset.conceptIndex;
                const details = document.querySelector(`.concept-details[data-concept-index="${conceptIndex}"]`);
                const expandIcon = header.querySelector('.expand-icon');

                if (details.classList.contains('hidden')) {
                    details.classList.remove('hidden');
                    expandIcon.textContent = 'expand_less';
                } else {
                    details.classList.add('hidden');
                    expandIcon.textContent = 'expand_more';
                }
            });
        });
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
