class ContinuousAssessment {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentConceptId = null;
        this.questions = [];
        this.responses = [];
    }

    async init(conceptId) {
        this.currentConceptId = conceptId;
        await this.loadUnderstandingChecks();
        this.render();
    }

    async loadUnderstandingChecks() {
        try {
            this.questions = await studentAPI.generateUnderstandingChecks(this.currentConceptId);
            this.responses = [];
        } catch (error) {
            console.error('Error loading understanding checks:', error);
            this.showError('Failed to load understanding checks. Please try again.');
        }
    }

    render() {
        if (!this.container) return;

        if (this.questions.length === 0) {
            this.container.innerHTML = `
                <div class="assessment-container">
                    <h3>Checking Your Understanding</h3>
                    <p>No understanding checks available for this concept.</p>
                    <button class="btn btn-primary" onclick="location.reload()">Refresh</button>
                </div>
            `;
            return;
        }

        let html = `
            <div class="assessment-container">
                <h3>Quick Check: How well do you understand this concept?</h3>
                <div class="questions-container">
        `;

        this.questions.forEach((question, index) => {
            html += `
                <div class="question-card" data-question-id="${question.question_id}">
                    <h4>Question ${index + 1}</h4>
                    <p class="question-text">${question.question_text}</p>
            `;

            if (question.options && question.options.length > 0) {
                html += `<div class="options-container">`;
                question.options.forEach((option, optIndex) => {
                    html += `
                        <div class="option">
                            <input type="radio" 
                                   id="q${index}_opt${optIndex}" 
                                   name="question_${index}" 
                                   value="${option}"
                                   onchange="continuousAssessment.handleOptionSelect('${question.question_id}', this.value)">
                            <label for="q${index}_opt${optIndex}">${option}</label>
                        </div>
                    `;
                });
                html += `</div>`;
            } else {
                html += `
                    <div class="text-input-container">
                        <input type="text" 
                               id="q${index}_text" 
                               placeholder="Type your answer here..."
                               onchange="continuousAssessment.handleTextAnswer('${question.question_id}', this.value)">
                    </div>
                `;
            }

            html += `</div>`;
        });

        html += `
                </div>
                <div class="actions">
                    <button class="btn btn-primary" onclick="continuousAssessment.submitAnswers()">Submit Answers</button>
                </div>
                <div class="feedback-container" id="feedback-container"></div>
            </div>
        `;

        this.container.innerHTML = html;
    }

    handleOptionSelect(questionId, selectedValue) {
        // Update or add response
        const existingIndex = this.responses.findIndex(r => r.question_id === questionId);
        if (existingIndex >= 0) {
            this.responses[existingIndex].answer = selectedValue;
        } else {
            this.responses.push({
                question_id: questionId,
                answer: selectedValue,
                is_correct: false // Will be updated after evaluation
            });
        }
    }

    handleTextAnswer(questionId, answerText) {
        // Update or add response
        const existingIndex = this.responses.findIndex(r => r.question_id === questionId);
        if (existingIndex >= 0) {
            this.responses[existingIndex].answer = answerText;
        } else {
            this.responses.push({
                question_id: questionId,
                answer: answerText,
                is_correct: false // Will be updated after evaluation
            });
        }
    }

    async submitAnswers() {
        if (this.responses.length === 0) {
            this.showFeedback('Please answer at least one question.', 'warning');
            return;
        }

        // Evaluate each response
        const evaluationResults = [];
        for (const response of this.responses) {
            try {
                const result = await studentAPI.evaluateUnderstandingResponse(
                    response.question_id, 
                    response.answer
                );
                evaluationResults.push({
                    ...response,
                    ...result
                });
            } catch (error) {
                console.error('Error evaluating response:', error);
                evaluationResults.push({
                    ...response,
                    is_correct: false,
                    confidence: 'low',
                    feedback: 'Error evaluating response'
                });
            }
        }

        // Show feedback
        this.showEvaluationResults(evaluationResults);

        // Adapt content based on responses
        try {
            const adaptation = await studentAPI.adaptContent(this.currentConceptId, evaluationResults);
            this.showContentAdaptation(adaptation);
        } catch (error) {
            console.error('Error adapting content:', error);
        }
    }

    showEvaluationResults(results) {
        const container = document.getElementById('feedback-container');
        if (!container) return;

        let html = '<div class="evaluation-results">';
        html += '<h4>Evaluation Results</h4>';

        results.forEach((result, index) => {
            const isCorrect = result.is_correct;
            const feedbackClass = isCorrect ? 'correct' : 'incorrect';
            
            html += `
                <div class="result-item ${feedbackClass}">
                    <p><strong>Question ${index + 1}:</strong> ${isCorrect ? '✓ Correct' : '✗ Incorrect'}</p>
                    <p class="feedback-text">${result.feedback}</p>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    showContentAdaptation(adaptation) {
        const container = document.getElementById('feedback-container');
        if (!container) return;

        let html = `
            <div class="content-adaptation">
                <h4>Next Steps</h4>
                <p>${adaptation.feedback}</p>
        `;

        switch (adaptation.next_step) {
            case 'advance':
                html += `
                    <div class="alert alert-success">
                        <p>You're ready to move on to the next concept!</p>
                        <button class="btn btn-success" onclick="continuousAssessment.moveToNextConcept()">Continue to Next Concept</button>
                    </div>
                `;
                break;
            case 'review':
                html += `
                    <div class="alert alert-warning">
                        <p>Let's review some key points to strengthen your understanding.</p>
                        <button class="btn btn-warning" onclick="continuousAssessment.reviewConcept()">Review Concept</button>
                    </div>
                `;
                break;
            case 'reteach':
                html += `
                    <div class="alert alert-danger">
                        <p>Let's go through this concept again with a simpler explanation.</p>
                        <button class="btn btn-danger" onclick="continuousAssessment.reteachConcept()">Simpler Explanation</button>
                    </div>
                `;
                break;
        }

        html += '</div>';
        container.innerHTML += html;
    }

    moveToNextConcept() {
        // In a real implementation, this would navigate to the next concept
        alert('Moving to next concept...');
        // You could redirect to another page or load new content here
    }

    reviewConcept() {
        // In a real implementation, this would show a review of the current concept
        alert('Reviewing concept...');
        // You could reload the current content or show a summary
    }

    reteachConcept() {
        // In a real implementation, this would show a simplified explanation
        alert('Showing simplified explanation...');
        // You could load a different version of the content
    }

    showFeedback(message, type = 'info') {
        const container = document.getElementById('feedback-container');
        if (!container) return;

        container.innerHTML = `
            <div class="alert alert-${type}">
                <p>${message}</p>
            </div>
        `;
    }

    showError(message) {
        this.showFeedback(message, 'danger');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.continuousAssessment = new ContinuousAssessment('continuous-assessment-container');
});