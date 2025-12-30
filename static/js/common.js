// Common JavaScript utilities

// API Base URL
const API_BASE = '/api';

// Get auth token from localStorage
function getAuthToken() {
    return localStorage.getItem('auth_token');
}

// Set auth token
function setAuthToken(token) {
    localStorage.setItem('auth_token', token);
}

// Clear auth token
function clearAuthToken() {
    localStorage.removeItem('auth_token');
}

// Make authenticated API request
async function apiRequest(endpoint, options = {}) {
    const token = getAuthToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });

    if (!response.ok) {
        if (response.status === 401) {
            // Unauthorized - clear token and redirect to login
            clearAuthToken();
            window.location.href = '/';
        }
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || 'Request failed');
    }

    return response.json();
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Format time from milliseconds
function formatTime(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

// WebSocket connection helper
class WSConnection {
    constructor(endpoint) {
        this.endpoint = endpoint;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.listeners = {};
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const token = getAuthToken();
        const wsUrl = `${protocol}//${window.location.host}${this.endpoint}?token=${token}`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            if (this.listeners['open']) {
                this.listeners['open']();
            }
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                const eventType = data.event;

                if (this.listeners[eventType]) {
                    this.listeners[eventType](data);
                }

                if (this.listeners['message']) {
                    this.listeners['message'](data);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            if (this.listeners['error']) {
                this.listeners['error'](error);
            }
        };

        this.ws.onclose = () => {
            console.log('WebSocket closed');
            if (this.listeners['close']) {
                this.listeners['close']();
            }

            // Attempt reconnection
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
                console.log(`Reconnecting in ${delay}ms...`);
                setTimeout(() => this.connect(), delay);
            }
        };
    }

    on(event, callback) {
        this.listeners[event] = callback;
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.error('WebSocket is not connected');
        }
    }

    close() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Export for use in other files
window.apiRequest = apiRequest;
window.showAlert = showAlert;
window.getAuthToken = getAuthToken;
window.setAuthToken = setAuthToken;
window.clearAuthToken = clearAuthToken;
window.formatTime = formatTime;
window.WSConnection = WSConnection;
