// KidGuard WebSocket Client
document.addEventListener('DOMContentLoaded', function() {
    // Check if the user is logged in (this would typically be determined by the server)
    const isLoggedIn = document.body.classList.contains('logged-in') || 
                       document.querySelector('[data-user-id]') !== null;
                       
    if (!isLoggedIn) {
        console.log('WebSocket not initialized: User not logged in');
        return;
    }
    
    // Request notification permission for alert notifications
    requestNotificationPermission();
    
    // Initialize Socket.IO connection
    const socket = io();
    
    socket.on('connect', function() {
        console.log('WebSocket connected');
        
        // Get user ID from page data attribute if available
        const userElement = document.querySelector('[data-user-id]');
        const userId = userElement ? userElement.getAttribute('data-user-id') : null;
        
        if (userId) {
            // Join a room for this specific user to receive targeted notifications
            socket.emit('join', { room: userId });
            console.log('Joined room:', userId);
        }
    });
    
    socket.on('disconnect', function() {
        console.log('WebSocket disconnected');
    });
    
    // Listen for new alerts
    socket.on('new_alert', function(data) {
        console.log('New alert received:', data);
        
        // Show browser notification
        showNotification(data);
        
        // Update UI with new alert (if appropriate elements exist)
        updateAlertUI(data);
        
        // Play alert sound
        playAlertSound(data.alert_type);
    });
    
    // Error handling
    socket.on('error', function(error) {
        console.error('WebSocket error:', error);
    });
});

function requestNotificationPermission() {
    if ('Notification' in window) {
        if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
            Notification.requestPermission().then(function(permission) {
                console.log('Notification permission:', permission);
            });
        }
    }
}

function showNotification(alertData) {
    if (!('Notification' in window) || Notification.permission !== 'granted') {
        return;
    }
    
    let title, options;
    
    switch (alertData.alert_type) {
        case 'emergency':
            title = '🚨 EMERGENCY ALERT';
            options = {
                body: `${alertData.child_name}: ${alertData.message || 'Emergency assistance needed!'}`,
                icon: '/static/img/emergency-icon.png', // This would need to be created
                requireInteraction: true,
                vibrate: [200, 100, 200]
            };
            break;
            
        case 'inappropriate_content':
            title = '⚠️ Content Alert';
            options = {
                body: `${alertData.child_name}: ${alertData.message}`,
                icon: '/static/img/warning-icon.png' // This would need to be created
            };
            break;
            
        default:
            title = 'KidGuard Alert';
            options = {
                body: alertData.message,
                icon: '/static/img/notification-icon.png' // This would need to be created
            };
    }
    
    const notification = new Notification(title, options);
    
    notification.onclick = function() {
        window.focus();
        
        // Navigate to the alert details page if an ID is provided
        if (alertData.alert_id) {
            window.location.href = `/alert/${alertData.alert_id}`;
        }
    };
}

function markAlertAsRead(alertId) {
    // In a real implementation, this would make an AJAX call to mark the alert as read
    fetch(`/alert/${alertId}/read`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Visual feedback
            const btn = document.querySelector('button');
            btn.innerHTML = '<i class="fas fa-check-double me-1"></i> Marked as Read';
            btn.classList.remove('btn-outline-secondary');
            btn.classList.add('btn-success');
            btn.disabled = true;
        }
    })
    .catch(error => {
        console.error('Error marking alert as read:', error);
    });
}

function updateAlertUI(alertData) {
    // Check if alerts container exists
    const alertsContainer = document.querySelector('.alerts-container');
    if (!alertsContainer) return;
    
    // Create alert element
    const alertElement = document.createElement('div');
    alertElement.classList.add('alert-item', 'unread');
    alertElement.setAttribute('data-alert-id', alertData.alert_id);
    
    let iconClass;
    switch (alertData.alert_type) {
        case 'emergency':
            iconClass = 'fa-exclamation-triangle text-danger';
            break;
        case 'inappropriate_content':
            iconClass = 'fa-exclamation-circle text-warning';
            break;
        default:
            iconClass = 'fa-info-circle text-info';
    }
    
    // Format the alert HTML
    alertElement.innerHTML = `
        <div class="d-flex">
            <div class="me-3">
                <i class="fas ${iconClass} fa-lg"></i>
            </div>
            <div>
                <div class="alert-message">${alertData.message}</div>
                <div class="alert-meta">
                    <span class="alert-from">${alertData.child_name}</span>
                    <span class="alert-time">${alertData.timestamp}</span>
                </div>
            </div>
        </div>
    `;
    
    // Add click event to navigate to alert details
    alertElement.addEventListener('click', function() {
        window.location.href = `/alert/${alertData.alert_id}`;
    });
    
    // Add to the beginning of the alerts container
    alertsContainer.prepend(alertElement);
    
    // Update alert badge count if it exists
    const alertBadge = document.querySelector('.alert-badge');
    if (alertBadge) {
        const currentCount = parseInt(alertBadge.textContent) || 0;
        alertBadge.textContent = currentCount + 1;
        alertBadge.style.display = 'block';
    }
}

function playAlertSound(alertType) {
    let soundUrl;
    
    switch (alertType) {
        case 'emergency':
            soundUrl = 'https://assets.mixkit.co/sfx/preview/mixkit-alarm-digital-clock-beep-989.mp3';
            break;
        case 'inappropriate_content':
            soundUrl = 'https://assets.mixkit.co/sfx/preview/mixkit-alert-quick-chime-766.mp3';
            break;
        default:
            soundUrl = 'https://assets.mixkit.co/sfx/preview/mixkit-positive-notification-951.mp3';
    }
    
    const audio = new Audio(soundUrl);
    audio.play().catch(error => {
        console.warn('Audio playback failed:', error);
    });
}
