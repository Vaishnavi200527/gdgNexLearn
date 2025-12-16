import { teacherAPI } from '../api/teacherApi.js';
import { showToast } from '../utils/toast.js';

// Add fadeOut animation for removing elements
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(10px); }
    }
    .fade-out {
        animation: fadeOut 0.3s ease-out forwards;
    }
`;
document.head.appendChild(style);

class QuizCreator {
    constructor() {
        // DOM Elements
        this.quizForm = document.getElementById('quizForm');
        this.questionsContainer = document.getElementById('questionsContainer');
        this.addQuestionBtn = document.getElementById('addQuestionBtn');
        this.classSelect = document.getElementById('classSelect');
        this.saveDraftBtn = document.getElementById('saveDraftBtn');
        this.publishBtn = document.getElementById('publishBtn');
        
        // Templates
        this.questionTemplate = document.getElementById('questionTemplate');
        this.optionTemplate = document.getElementById('optionTemplate');
        
        // State
        this.questionCount = 0;
        
        // Initialize
        this.initializeEventListeners();
        this.loadClasses();
        this.addNewQuestion(); // Add first question by default
    }
    
    initializeEventListeners() {
        // Add question button
        this.addQuestionBtn.addEventListener('click', () => this.addNewQuestion());
        
        // Form submission
        this.quizForm.addEventListener('submit', (e) => this.handleSubmit(e, false));
        
        // Save as draft
        this.saveDraftBtn.addEventListener('click', (e) => this.handleSubmit(e, true));
        
        // Delegated event listeners for dynamic elements
        this.questionsContainer.addEventListener('click', (e) => {
            // Remove question
            if (e.target.closest('.remove-question')) {
                this.removeQuestion(e.target.closest('.question-card'));
            }
            // Add option
            else if (e.target.closest('.add-option')) {
                this.addOptionToQuestion(e.target.closest('.question-card'));
            }
            // Remove option
            else if (e.target.closest('.remove-option')) {
                this.removeOption(e.target.closest('.option-item'));
            }
        });
    }
    
    async loadClasses() {
        try {
            const classes = await teacherAPI.getClasses();
            
            // Clear existing options except the first one
            while (this.classSelect.options.length > 1) {
                this.classSelect.remove(1);
            }
            
            if (classes && classes.length > 0) {
                classes.forEach(cls => {
                    const option = document.createElement('option');
                    option.value = cls.id;
                    option.textContent = cls.name;
                    this.classSelect.appendChild(option);
                });
            } else {
                this.showError('No classes found. Please create a class first.');
            }
        } catch (error) {
            console.error('Error loading classes:', error);
            this.showError('Failed to load classes. Please try again later.');
        }
    }
    
    addNewQuestion() {
        this.questionCount++;
        const questionElement = this.questionTemplate.content.cloneNode(true);
        const questionCard = questionElement.querySelector('.question-card');
        
        // Update question number
        questionCard.querySelector('.question-index').textContent = this.questionCount;
        
        // Add to container
        this.questionsContainer.appendChild(questionElement);
        
        // Add first two options by default
        this.addOptionToQuestion(questionCard);
        this.addOptionToQuestion(questionCard);
        
        return questionCard;
    }
    
    addOptionToQuestion(questionCard) {
        const optionsContainer = questionCard.querySelector('.options-container');
        const optionElement = this.optionTemplate.content.cloneNode(true);
        
        // Set radio button name to be unique per question
        const questionId = questionCard.querySelector('.question-number').textContent;
        const radio = optionElement.querySelector('.correct-option');
        radio.name = `correctOption_${questionId}`;
        
        // Add to container
        optionsContainer.appendChild(optionElement);
    }
    
    removeQuestion(questionCard) {
        // Don't allow removing the last question
        if (this.questionsContainer.children.length <= 1) {
            this.showError('A quiz must have at least one question.');
            return;
        }
        
        questionCard.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => {
            questionCard.remove();
            this.updateQuestionNumbers();
            this.questionCount--;
        }, 300);
    }
    
    removeOption(optionElement) {
        const optionsContainer = optionElement.parentElement;
        // Don't allow removing if only two options remain
        if (optionsContainer.children.length <= 2) {
            this.showError('A question must have at least two options.');
            return;
        }
        optionElement.remove();
    }
    
    updateQuestionNumbers() {
        const questions = this.questionsContainer.querySelectorAll('.question-card');
        questions.forEach((question, index) => {
            question.querySelector('.question-index').textContent = index + 1;
        });
    }
    
    async handleSubmit(event, isDraft) {
        event.preventDefault();
        
        // Validate form
        if (!this.validateForm()) {
            return;
        }
        
        try {
            // Show loading state
            this.setLoading(true);
            
            // Prepare quiz data
            const quizData = this.prepareQuizData(isDraft);
            
            // Step 1: Create the quiz
            const quizResponse = await teacherAPI.createQuiz({
                title: quizData.title,
                description: quizData.description,
                questions: quizData.questions.map(q => ({
                    question_text: q.question_text,
                    options: q.options,
                    correct_answer: q.correct_answer,
                    order: q.order
                })),
                status: isDraft ? 'draft' : 'published'
            });
            
            // Step 2: Assign quiz to class
            await teacherAPI.assignQuizToClass(
                quizResponse.id,
                quizData.class_id,
                quizData.due_date
            );
            
            // Show success message
            showToast(
                isDraft ? 'Quiz saved as draft successfully!' : 'Quiz published successfully!',
                'success'
            );
            
            // Redirect to quizzes list after a short delay
            setTimeout(() => {
                window.location.href = '/pages/teacher/quizzes.html';
            }, 1500);
            
        } catch (error) {
            console.error('Error saving quiz:', error);
            const errorMessage = error.message || 'Failed to save quiz. Please try again.';
            showToast(errorMessage, 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    validateForm() {
        // Basic validation
        const title = document.getElementById('quizTitle').value.trim();
        if (!title) {
            this.showError('Please enter a quiz title');
            return false;
        }
        
        // Validate at least one question
        const questions = this.questionsContainer.querySelectorAll('.question-card');
        if (questions.length === 0) {
            this.showError('Please add at least one question');
            return false;
        }
        
        // Validate each question
        for (const question of questions) {
            const questionText = question.querySelector('.question-text').value.trim();
            if (!questionText) {
                this.showError('Please enter text for all questions');
                return false;
            }
            
            // Validate options
            const options = question.querySelectorAll('.option-text');
            if (options.length < 2) {
                this.showError('Each question must have at least two options');
                return false;
            }
            
            let hasOptionText = true;
            options.forEach(opt => {
                if (!opt.value.trim()) hasOptionText = false;
            });
            
            if (!hasOptionText) {
                this.showError('Please enter text for all options');
                return false;
            }
            
            // Validate correct answer selected
            const correctOption = question.querySelector('.correct-option:checked');
            if (!correctOption) {
                this.showError('Please select the correct answer for each question');
                return false;
            }
        }
        
        // Validate class selection
        if (!this.classSelect.value) {
            this.showError('Please select a class');
            return false;
        }
        
        // Validate due date
        const dueDate = document.getElementById('dueDate').value;
        if (!dueDate) {
            this.showError('Please select a due date');
            return false;
        }
        
        return true;
    }
    
    prepareQuizData(isDraft) {
        const quizData = {
            title: document.getElementById('quizTitle').value.trim(),
            description: document.getElementById('quizDescription').value.trim(),
            status: isDraft ? 'draft' : 'published',
            class_id: parseInt(this.classSelect.value),
            due_date: document.getElementById('dueDate').value,
            questions: []
        };
        
        // Add questions
        const questionCards = this.questionsContainer.querySelectorAll('.question-card');
        questionCards.forEach((card, index) => {
            const questionText = card.querySelector('.question-text').value.trim();
            const options = [];
            let correctAnswer = '';
            
            // Process options
            const optionInputs = card.querySelectorAll('.option-item');
            optionInputs.forEach(item => {
                const optionText = item.querySelector('.option-text').value.trim();
                const isCorrect = item.querySelector('.correct-option').checked;
                
                options.push(optionText);
                
                if (isCorrect) {
                    correctAnswer = optionText;
                }
            });
            
            quizData.questions.push({
                question_text: questionText,
                options: options,
                correct_answer: correctAnswer,
                order: index + 1
            });
        });
        
        return quizData;
    }
    
    setLoading(isLoading) {
        const buttons = [this.saveDraftBtn, this.publishBtn, this.addQuestionBtn];
        
        buttons.forEach(btn => {
            if (btn) {
                btn.disabled = isLoading;
                const icon = btn.querySelector('i');
                if (icon) {
                    icon.className = isLoading ? 'fas fa-spinner fa-spin' : icon.className.replace('fa-spinner fa-spin', '');
                }
            }
        });
    }
    
    showError(message) {
        showToast(message, 'error');
    }
    
    showSuccess(message, callback) {
        showToast(message, 'success');
        if (callback && typeof callback === 'function') {
            setTimeout(callback, 1500);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const quizCreator = new QuizCreator();
});
