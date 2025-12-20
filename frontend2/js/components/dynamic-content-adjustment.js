class DynamicContentAdjustment {
    constructor() {
        this.studentId = null;
        this.learningSpeed = null;
        this.pacingRecommendation = null;
        this.pacingFactor = 1.0;
        this.adjustedAssignments = [];
    }

    async init() {
        await this.loadStudentProfile();
        await this.analyzeLearningSpeed();
        await this.adjustContentPacing();
        this.applyAdjustments();
    }

    async loadStudentProfile() {
        try {
            const profile = await studentAPI.getLearningProfile();
            this.studentId = profile.student_id;
            console.log('Student profile loaded:', profile);
        } catch (error) {
            console.error('Error loading student profile:', error);
        }
    }

    async analyzeLearningSpeed() {
        try {
            const analysis = await studentAPI.apiRequest('/student/learning-speed-analysis');
            this.learningSpeed = analysis.learning_speed;
            this.pacingRecommendation = analysis.pacing_recommendation;
            console.log('Learning speed analysis:', analysis);
        } catch (error) {
            console.error('Error analyzing learning speed:', error);
        }
    }

    async adjustContentPacing() {
        try {
            const adjustment = await studentAPI.apiRequest('/student/content-pacing-adjustment');
            this.pacingFactor = adjustment.pacing_factor;
            this.adjustedAssignments = adjustment.adjusted_assignments || [];
            console.log('Content pacing adjustment:', adjustment);
        } catch (error) {
            console.error('Error adjusting content pacing:', error);
        }
    }

    applyAdjustments() {
        // Apply pacing adjustments to the UI
        this.updateAssignmentTimings();
        this.showPacingNotification();
        this.updateProgressBar();
    }

    updateAssignmentTimings() {
        // Update assignment estimated times based on pacing factor
        this.adjustedAssignments.forEach(assignment => {
            const assignmentElement = document.querySelector(`[data-assignment-id="${assignment.assignment_id}"]`);
            if (assignmentElement) {
                const timeElement = assignmentElement.querySelector('.estimated-time');
                if (timeElement) {
                    timeElement.textContent = `${assignment.adjusted_estimated_time} min`;
                    timeElement.classList.add('adjusted-time');
                }
            }
        });
    }

    showPacingNotification() {
        // Show notification about pacing adjustment
        const notification = document.createElement('div');
        notification.className = 'pacing-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-tachometer-alt"></i>
                <div>
                    <strong>Content Pacing Updated</strong>
                    <p>Based on your learning speed, we've ${this.getPacingDescription()} your content pacing.</p>
                </div>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    getPacingDescription() {
        switch (this.pacingRecommendation) {
            case 'accelerate':
                return 'accelerated';
            case 'decelerate':
                return 'slowed down';
            default:
                return 'maintained';
        }
    }

    updateProgressBar() {
        // Update progress bar to reflect adjusted pacing
        const progressBar = document.querySelector('.learning-progress');
        if (progressBar) {
            const speedIndicator = document.createElement('div');
            speedIndicator.className = `speed-indicator speed-${this.learningSpeed}`;
            speedIndicator.innerHTML = `
                <i class="fas fa-${this.getSpeedIcon()}"></i>
                <span>${this.learningSpeed} learner</span>
            `;
            progressBar.appendChild(speedIndicator);
        }
    }

    getSpeedIcon() {
        switch (this.learningSpeed) {
            case 'rapid':
                return 'bolt';
            case 'fast':
                return 'running';
            case 'moderate':
                return 'walking';
            case 'slow':
                return 'turtle';
            default:
                return 'user';
        }
    }

    // Method to manually trigger re-analysis
    async reanalyze() {
        await this.analyzeLearningSpeed();
        await this.adjustContentPacing();
        this.applyAdjustments();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dynamicContentAdjustment = new DynamicContentAdjustment();
    
    // Add a button to manually trigger re-analysis
    const reanalyzeButton = document.createElement('button');
    reanalyzeButton.id = 'reanalyze-button';
    reanalyzeButton.innerHTML = '<i class="fas fa-sync"></i> Re-analyze Learning Speed';
    reanalyzeButton.onclick = () => window.dynamicContentAdjustment.reanalyze();
    
    // Add to a suitable place in the UI (you may need to adjust this selector)
    const controlsContainer = document.querySelector('.controls-container');
    if (controlsContainer) {
        controlsContainer.appendChild(reanalyzeButton);
    }
});

// Add CSS for the component
const style = document.createElement('style');
style.textContent = `
    .pacing-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    }

    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    .notification-content {
        display: flex;
        align-items: center;
        gap: 15px;
    }

    .notification-content i {
        font-size: 1.5rem;
    }

    .adjusted-time {
        font-weight: bold;
        color: #667eea;
        animation: pulse 1s infinite;
    }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }

    .speed-indicator {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 0.9rem;
        margin-left: 10px;
    }

    .speed-rapid {
        background: #28a745;
        color: white;
    }

    .speed-fast {
        background: #17a2b8;
        color: white;
    }

    .speed-moderate {
        background: #ffc107;
        color: #212529;
    }

    .speed-slow {
        background: #dc3545;
        color: white;
    }

    #reanalyze-button {
        background: #6c757d;
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 5px;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9rem;
        transition: background 0.2s ease;
    }

    #reanalyze-button:hover {
        background: #5a6268;
    }
`;
document.head.appendChild(style);