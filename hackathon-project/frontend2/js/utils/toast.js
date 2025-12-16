// Toast notification system
export function showToast(message, type = 'info', duration = 3000) {
    // Create toast container if it doesn't exist
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.gap = '10px';
        document.body.appendChild(container);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Set toast styles
    toast.style.padding = '12px 20px';
    toast.style.borderRadius = '4px';
    toast.style.color = 'white';
    toast.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease-in-out';
    toast.style.position = 'relative';
    toast.style.overflow = 'hidden';
    toast.style.maxWidth = '350px';
    toast.style.wordBreak = 'break-word';

    // Set background color based on type
    const colors = {
        success: '#4CAF50',
        error: '#F44336',
        warning: '#FF9800',
        info: '#2196F3'
    };
    
    toast.style.backgroundColor = colors[type] || colors.info;
    
    // Add message
    toast.textContent = message;
    
    // Add progress bar
    const progressBar = document.createElement('div');
    progressBar.className = 'toast-progress';
    progressBar.style.position = 'absolute';
    progressBar.style.bottom = '0';
    progressBar.style.left = '0';
    progressBar.style.height = '4px';
    progressBar.style.width = '100%';
    progressBar.style.backgroundColor = 'rgba(255, 255, 255, 0.4)';
    progressBar.style.transition = 'width 0.1s linear';
    
    const progressBarInner = document.createElement('div');
    progressBarInner.style.height = '100%';
    progressBarInner.style.width = '100%';
    progressBarInner.style.backgroundColor = 'white';
    progressBarInner.style.transition = 'width 0.1s linear';
    
    progressBar.appendChild(progressBarInner);
    toast.appendChild(progressBar);
    
    // Add to container
    container.appendChild(toast);
    
    // Trigger reflow to enable animation
    void toast.offsetHeight;
    
    // Animate in
    toast.style.opacity = '1';
    toast.style.transform = 'translateX(0)';
    
    // Start progress bar animation
    setTimeout(() => {
        progressBarInner.style.width = '0%';
    }, 10);
    
    // Auto-dismiss after duration
    const dismissTimeout = setTimeout(() => {
        dismissToast(toast);
    }, duration);
    
    // Dismiss on click
    toast.addEventListener('click', () => {
        clearTimeout(dismissTimeout);
        dismissToast(toast);
    });
    
    // Return a function to manually dismiss the toast
    return () => {
        clearTimeout(dismissTimeout);
        dismissToast(toast);
    };
}

function dismissToast(toastElement) {
    if (!toastElement) return;
    
    toastElement.style.opacity = '0';
    toastElement.style.transform = 'translateX(100%)';
    
    // Remove from DOM after animation completes
    setTimeout(() => {
        if (toastElement && toastElement.parentNode) {
            toastElement.parentNode.removeChild(toastElement);
        }
    }, 300);
}

// Add some basic styles if not already present
if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
        .toast {
            position: relative;
            padding: 12px 20px;
            margin-bottom: 10px;
            border-radius: 4px;
            color: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease-in-out;
            max-width: 350px;
            word-break: break-word;
        }
        
        .toast-success {
            background-color: #4CAF50;
        }
        
        .toast-error {
            background-color: #F44336;
        }
        
        .toast-warning {
            background-color: #FF9800;
        }
        
        .toast-info {
            background-color: #2196F3;
        }
        
        .toast-progress {
            position: absolute;
            bottom: 0;
            left: 0;
            height: 4px;
            width: 100%;
            background-color: rgba(255, 255, 255, 0.4);
        }
        
        .toast-progress > div {
            height: 100%;
            width: 100%;
            background-color: white;
            transition: width 0.1s linear;
        }
    `;
    document.head.appendChild(style);
}
