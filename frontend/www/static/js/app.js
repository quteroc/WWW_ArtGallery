/**
 * Application-wide JavaScript helpers
 */

/**
 * Make an authenticated API request
 * @param {string} url - API endpoint URL
 * @param {object} options - Fetch options
 * @returns {Promise<Response>}
 */
async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem('access_token');
    
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    return fetch(url, {
        ...options,
        headers
    });
}

/**
 * Check if user is authenticated
 * @returns {boolean}
 */
function isAuthenticated() {
    return !!localStorage.getItem('access_token');
}

/**
 * Get stored auth token
 * @returns {string|null}
 */
function getAuthToken() {
    return localStorage.getItem('access_token');
}

/**
 * Clear authentication data
 */
function clearAuth() {
    localStorage.removeItem('access_token');
}

/**
 * Format date to readable string
 * @param {string} dateString - ISO date string
 * @returns {string}
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

/**
 * Display a toast notification (simple implementation)
 * @param {string} message - Message to display
 * @param {string} type - Type of message (success, error, info)
 */
function showToast(message, type = 'info') {
    // Simple alert implementation - can be enhanced with a proper toast library
    const colors = {
        success: '#10B981',
        error: '#EF4444',
        info: '#3B82F6'
    };
    
    console.log(`[${type.toUpperCase()}]`, message);
    // In a real app, you'd create a toast UI element here
}

// Export functions for use in templates
window.fetchWithAuth = fetchWithAuth;
window.isAuthenticated = isAuthenticated;
window.getAuthToken = getAuthToken;
window.clearAuth = clearAuth;
window.formatDate = formatDate;
window.showToast = showToast;
