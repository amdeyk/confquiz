// Common JavaScript utilities

// Debug mode - set to true to enable console logging
const DEBUG = true;

function debug(...args) {
    if (DEBUG) {
        console.log('[DEBUG]', new Date().toISOString(), ...args);
    }
}

function debugError(...args) {
    if (DEBUG) {
        console.error('[ERROR]', new Date().toISOString(), ...args);
    }
}

function debugWarn(...args) {
    if (DEBUG) {
        console.warn('[WARN]', new Date().toISOString(), ...args);
    }
}

// API Base URL
const API_BASE = '/api';

// Get auth token from localStorage
function getAuthToken() {
    const token = localStorage.getItem('auth_token');
    debug('getAuthToken:', token ? `Token exists (${token.substring(0, 20)}...)` : 'No token');
    return token;
}

// Set auth token
function setAuthToken(token) {
    debug('setAuthToken:', token ? `Setting token (${token.substring(0, 20)}...)` : 'Setting null token');
    localStorage.setItem('auth_token', token);
}

// Clear auth token
function clearAuthToken() {
    debug('clearAuthToken: Clearing token');
    localStorage.removeItem('auth_token');
}

// Make authenticated API request
async function apiRequest(endpoint, options = {}) {
    debug('apiRequest START:', endpoint, options);

    const token = getAuthToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
        debug('apiRequest: Added auth token to headers');
    } else {
        debugWarn('apiRequest: No auth token available');
    }

    const url = `${API_BASE}${endpoint}`;
    debug('apiRequest: Fetching', url);

    try {
        const response = await fetch(url, {
            ...options,
            headers
        });

        debug('apiRequest RESPONSE:', endpoint, 'Status:', response.status, response.statusText);

        if (!response.ok) {
            if (response.status === 401) {
                debugError('apiRequest: Unauthorized (401) - Redirecting to login');
                clearAuthToken();
                window.location.href = '/';
                return;
            }
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            debugError('apiRequest ERROR:', endpoint, error);
            throw new Error(error.detail || 'Request failed');
        }

        const data = await response.json();
        debug('apiRequest SUCCESS:', endpoint, data);
        return data;
    } catch (error) {
        debugError('apiRequest EXCEPTION:', endpoint, error);
        throw error;
    }
}

// Show alert message
function showAlert(message, type = 'info') {
    debug('showAlert:', type, message);

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    const container = document.querySelector('.container');
    if (!container) {
        debugError('showAlert: Container not found');
        console.error('Alert:', type, message);
        return;
    }

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
        debug('WSConnection: Creating connection for', endpoint);
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

        debug('WSConnection: Connecting to', wsUrl);
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            debug('WSConnection: Connected successfully');
            this.reconnectAttempts = 0;
            if (this.listeners['open']) {
                this.listeners['open']();
            }
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                const eventType = data.event;
                debug('WSConnection: Received message:', eventType, data);

                if (this.listeners[eventType]) {
                    this.listeners[eventType](data);
                }

                if (this.listeners['message']) {
                    this.listeners['message'](data);
                }
            } catch (error) {
                debugError('WSConnection: Error parsing message:', error, event.data);
            }
        };

        this.ws.onerror = (error) => {
            debugError('WSConnection: Error:', error);
            if (this.listeners['error']) {
                this.listeners['error'](error);
            }
        };

        this.ws.onclose = () => {
            debug('WSConnection: Closed');
            if (this.listeners['close']) {
                this.listeners['close']();
            }

            // Attempt reconnection
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
                debugWarn(`WSConnection: Reconnecting in ${delay}ms... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                setTimeout(() => this.connect(), delay);
            } else {
                debugError('WSConnection: Max reconnection attempts reached');
            }
        };
    }

    on(event, callback) {
        debug('WSConnection: Registering listener for event:', event);
        this.listeners[event] = callback;
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            debug('WSConnection: Sending data:', data);
            this.ws.send(JSON.stringify(data));
        } else {
            debugError('WSConnection: Cannot send, not connected. ReadyState:', this.ws?.readyState);
        }
    }

    close() {
        debug('WSConnection: Closing connection');
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
window.debug = debug;
window.debugError = debugError;
window.debugWarn = debugWarn;

// Global error handler
window.addEventListener('error', (event) => {
    debugError('Global error caught:', event.error || event.message);
    debugError('  File:', event.filename);
    debugError('  Line:', event.lineno, 'Col:', event.colno);
    if (event.error && event.error.stack) {
        debugError('  Stack:', event.error.stack);
    }
});

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', (event) => {
    debugError('Unhandled promise rejection:', event.reason);
    if (event.reason && event.reason.stack) {
        debugError('  Stack:', event.reason.stack);
    }
});

// Log when common.js is loaded
debug('common.js loaded successfully');
