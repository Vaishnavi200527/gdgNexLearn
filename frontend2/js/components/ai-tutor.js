class AITutor {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.context = "";
        this.conversationHistory = [];
        this.init();
    }

    init() {
        if (!this.container) return;
        this.render();
    }

    render() {
        this.container.innerHTML = `
            <div class="ai-tutor-container">
                <div class="chat-header">
                    <h3><i class="fas fa-robot"></i> AI Tutor</h3>
                    <p>Ask me anything about the concepts you're learning!</p>
                </div>
                
                <div class="chat-messages" id="chat-messages">
                    <div class="message bot-message">
                        <div class="avatar">🤖</div>
                        <div class="message-content">
                            <p>Hello! I'm your AI tutor. I can help you understand concepts from your course materials. What would you like to know?</p>
                        </div>
                    </div>
                </div>
                
                <div class="chat-input-container">
                    <textarea 
                        id="question-input" 
                        placeholder="Type your question here..." 
                        rows="3"
                        onkeydown="aiTutor.handleKeyDown(event)"
                    ></textarea>
                    <div class="input-actions">
                        <button class="btn btn-secondary" onclick="aiTutor.clearChat()">
                            <i class="fas fa-trash"></i> Clear
                        </button>
                        <button class="btn btn-primary" onclick="aiTutor.askQuestion()">
                            <i class="fas fa-paper-plane"></i> Ask
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    async askQuestion() {
        const inputElement = document.getElementById('question-input');
        const question = inputElement.value.trim();
        
        if (!question) {
            this.showMessage('Please enter a question.', 'warning');
            return;
        }
        
        // Add user question to chat
        this.addMessageToChat(question, 'user');
        inputElement.value = '';
        
        // Show loading indicator
        const loadingId = this.showLoadingIndicator();
        
        try {
            // In a real implementation, this would call the backend API
            // For demo purposes, we'll simulate a response
            const response = await this.simulateAIResponse(question);
            
            // Remove loading indicator
            this.removeLoadingIndicator(loadingId);
            
            // Add AI response to chat
            this.addMessageToChat(response.answer, 'bot');
            
            // Add to conversation history
            this.conversationHistory.push({
                question: question,
                answer: response.answer
            });
        } catch (error) {
            console.error('Error asking question:', error);
            this.removeLoadingIndicator(loadingId);
            this.addMessageToChat("Sorry, I encountered an error processing your question. Please try again.", 'bot');
        }
    }

    handleKeyDown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.askQuestion();
        }
    }

    addMessageToChat(message, sender) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}-message`;
        
        if (sender === 'user') {
            messageElement.innerHTML = `
                <div class="avatar">👤</div>
                <div class="message-content">
                    <p>${message}</p>
                </div>
            `;
        } else {
            messageElement.innerHTML = `
                <div class="avatar">🤖</div>
                <div class="message-content">
                    <p>${message}</p>
                    <div class="message-actions">
                        <button class="btn-icon" onclick="aiTutor.likeResponse(this)" title="Helpful">
                            <i class="fas fa-thumbs-up"></i>
                        </button>
                        <button class="btn-icon" onclick="aiTutor.dislikeResponse(this)" title="Not Helpful">
                            <i class="fas fa-thumbs-down"></i>
                        </button>
                    </div>
                </div>
            `;
        }
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    showLoadingIndicator() {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;
        
        const loadingElement = document.createElement('div');
        loadingElement.className = 'message bot-message loading';
        loadingElement.id = 'loading-' + Date.now();
        loadingElement.innerHTML = `
            <div class="avatar">🤖</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(loadingElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return loadingElement.id;
    }

    removeLoadingIndicator(loadingId) {
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) {
            loadingElement.remove();
        }
    }

    async simulateAIResponse(question) {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Simple response simulation based on question keywords
        const lowerQuestion = question.toLowerCase();
        
        if (lowerQuestion.includes('hello') || lowerQuestion.includes('hi')) {
            return { answer: "Hello there! How can I help you with your studies today?" };
        } else if (lowerQuestion.includes('machine learning')) {
            return { 
                answer: "Machine Learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed. It uses statistical techniques to give computers the ability to 'learn' from data and improve their performance on a specific task over time. Key types include supervised learning, unsupervised learning, and reinforcement learning." 
            };
        } else if (lowerQuestion.includes('algorithm')) {
            return { 
                answer: "An algorithm is a step-by-step procedure or formula for solving a problem. In computer science, algorithms are essential for processing data and performing calculations. They form the backbone of all software applications and are crucial for efficient problem-solving." 
            };
        } else if (lowerQuestion.includes('data structure')) {
            return { 
                answer: "Data structures are ways of organizing and storing data in a computer so that it can be accessed and modified efficiently. Common data structures include arrays, linked lists, stacks, queues, trees, and graphs. Choosing the right data structure is crucial for optimizing program performance." 
            };
        } else {
            return { 
                answer: "That's a great question! Based on your course materials, I can tell you that understanding fundamentals is key. Try breaking down complex concepts into smaller parts, and don't hesitate to ask for clarification when something isn't clear. Practice regularly and review previous concepts to reinforce your learning." 
            };
        }
    }

    likeResponse(button) {
        button.classList.add('liked');
        button.nextElementSibling.classList.remove('disliked');
        this.showMessage('Thank you for your feedback!', 'success');
    }

    dislikeResponse(button) {
        button.classList.add('disliked');
        button.previousElementSibling.classList.remove('liked');
        this.showMessage('Thank you for your feedback. I\'ll try to improve!', 'info');
    }

    clearChat() {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;
        
        // Keep only the initial welcome message
        chatMessages.innerHTML = `
            <div class="message bot-message">
                <div class="avatar">🤖</div>
                <div class="message-content">
                    <p>Hello! I'm your AI tutor. I can help you understand concepts from your course materials. What would you like to know?</p>
                </div>
            </div>
        `;
        
        this.conversationHistory = [];
        this.showMessage('Chat cleared successfully.', 'success');
    }

    showMessage(message, type = 'info') {
        // Create a temporary notification
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    setContext(context) {
        this.context = context;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.aiTutor = new AITutor('ai-tutor-container');
});

// Add CSS for the component
const style = document.createElement('style');
style.textContent = `
    .ai-tutor-container {
        display: flex;
        flex-direction: column;
        height: 100%;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }
    
    .chat-header {
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .chat-header h3 {
        margin: 0 0 5px 0;
        font-size: 1.3rem;
    }
    
    .chat-header p {
        margin: 0;
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    .chat-messages {
        flex: 1;
        padding: 20px;
        overflow-y: auto;
        background: #f8f9fa;
    }
    
    .message {
        display: flex;
        margin-bottom: 20px;
        animation: fadeIn 0.3s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 15px;
        font-size: 1.2rem;
        flex-shrink: 0;
    }
    
    .user-message .avatar {
        background: #007bff;
        color: white;
    }
    
    .bot-message .avatar {
        background: #28a745;
        color: white;
    }
    
    .message-content {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        position: relative;
    }
    
    .user-message .message-content {
        background: #007bff;
        color: white;
        border-bottom-right-radius: 0;
    }
    
    .bot-message .message-content {
        background: white;
        border-bottom-left-radius: 0;
    }
    
    .message-content p {
        margin: 0;
        line-height: 1.5;
    }
    
    .message-actions {
        display: flex;
        gap: 10px;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #eee;
    }
    
    .btn-icon {
        background: none;
        border: none;
        cursor: pointer;
        font-size: 0.9rem;
        color: #6c757d;
        padding: 5px;
        border-radius: 5px;
        transition: all 0.2s ease;
    }
    
    .btn-icon:hover {
        background: #e9ecef;
    }
    
    .btn-icon.liked {
        color: #28a745;
        background: rgba(40, 167, 69, 0.1);
    }
    
    .btn-icon.disliked {
        color: #dc3545;
        background: rgba(220, 53, 69, 0.1);
    }
    
    .loading .message-content {
        background: white;
        border-bottom-left-radius: 10px;
    }
    
    .typing-indicator {
        display: flex;
        align-items: center;
    }
    
    .typing-indicator span {
        height: 8px;
        width: 8px;
        background: #6c757d;
        border-radius: 50%;
        display: inline-block;
        margin: 0 2px;
        animation: typing 1s infinite;
    }
    
    .typing-indicator span:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-indicator span:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes typing {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    
    .chat-input-container {
        padding: 20px;
        background: white;
        border-top: 1px solid #eee;
    }
    
    #question-input {
        width: 100%;
        padding: 12px;
        border: 1px solid #ced4da;
        border-radius: 8px;
        font-size: 1rem;
        resize: none;
        margin-bottom: 15px;
        transition: border-color 0.2s ease;
    }
    
    #question-input:focus {
        outline: none;
        border-color: #007bff;
        box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25);
    }
    
    .input-actions {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
    }
    
    .btn {
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 1rem;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    
    .btn-primary {
        background: #007bff;
        color: white;
    }
    
    .btn-primary:hover {
        background: #0056b3;
    }
    
    .btn-secondary {
        background: #6c757d;
        color: white;
    }
    
    .btn-secondary:hover {
        background: #545b62;
    }
    
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); }
        to { transform: translateX(0); }
    }
    
    .notification-success {
        background: #28a745;
    }
    
    .notification-info {
        background: #17a2b8;
    }
    
    .notification-warning {
        background: #ffc107;
        color: #212529;
    }
`;
document.head.appendChild(style);