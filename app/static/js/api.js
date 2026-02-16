/**
 * PRISMID API Client
 * Handles all HTTP requests to the backend with JWT token management.
 */

const API_BASE = '/api/v1';

function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Token management
function getToken() {
    return localStorage.getItem('prismid_token');
}

function getRefreshToken() {
    return localStorage.getItem('prismid_refresh_token');
}

function setTokens(access, refresh) {
    if (!access) console.warn('setTokens called with empty access token');
    localStorage.setItem('prismid_token', access);
    localStorage.setItem('prismid_refresh_token', refresh);
    console.log('Tokens updated in localStorage');
}

function clearTokens() {
    localStorage.removeItem('prismid_token');
    localStorage.removeItem('prismid_refresh_token');
    localStorage.removeItem('prismid_admin');
}

function getAdmin() {
    const data = localStorage.getItem('prismid_admin');
    return data ? JSON.parse(data) : null;
}

function setAdmin(admin) {
    localStorage.setItem('prismid_admin', JSON.stringify(admin));
}

// Core request function
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };

    const token = getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Idempotency for state-changing methods
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method)) {
        headers['Idempotency-Key'] = uuidv4();
    }

    const config = {
        method: options.method || 'GET',
        headers,
        ...(options.body ? { body: JSON.stringify(options.body) } : {}),
    };

    try {
        console.log(`[API] Request: ${options.method || 'GET'} ${url}`);
        let response = await fetch(url, config);

        // If 401, try refreshing the token
        if (response.status === 401 && getRefreshToken()) {
            console.warn(`[API] 401 Unauthorized at ${endpoint}. Attempting refresh...`);
            const refreshed = await refreshAccessToken();
            if (refreshed) {
                console.log('[API] Token refreshed. Retrying request...');
                headers['Authorization'] = `Bearer ${getToken()}`;
                config.headers = headers;
                response = await fetch(url, config);
            } else {
                console.error('[API] Refresh failed. Clearing tokens and redirecting to login.');
                clearTokens();
                showLoginScreen();
                throw new Error('Session expired');
            }
        }

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            console.error(`[API] Error ${response.status} at ${endpoint}:`, error);
            throw new Error(error.detail || 'Request failed');
        }

        const data = await response.json();
        console.log(`[API] Success ${endpoint}`, data);
        return data;
    } catch (err) {
        if (err.message !== 'Session expired') {
            console.error(`API Error [${endpoint}]:`, err);
        }
        throw err;
    }
}

// Upload request (for file imports)
async function apiUpload(endpoint, formData) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {};
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || 'Upload failed');
    }

    return await response.json();
}

// Refresh token
async function refreshAccessToken() {
    try {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: getRefreshToken() }),
        });

        if (!response.ok) return false;

        const data = await response.json();
        setTokens(data.access_token, data.refresh_token);
        return true;
    } catch {
        return false;
    }
}

// --- API Methods ---

const api = {
    // Auth
    login: (username, password) =>
        apiRequest('/auth/login', { method: 'POST', body: { username, password } }),

    logout: () =>
        apiRequest('/auth/logout', { method: 'POST' }),

    // Users
    getUsers: (params = {}) => {
        const query = new URLSearchParams();
        Object.entries(params).forEach(([k, v]) => { if (v) query.set(k, v); });
        return apiRequest(`/users?${query.toString()}`);
    },

    getUser: (uid) => apiRequest(`/users/${uid}`),

    createUser: (data) =>
        apiRequest('/users', { method: 'POST', body: data }),

    updateUser: (uid, data) =>
        apiRequest(`/users/${uid}`, { method: 'PUT', body: data }),

    deleteUser: (uid) =>
        apiRequest(`/users/${uid}`, { method: 'DELETE' }),

    assignRole: (uid, roleId) =>
        apiRequest(`/users/${uid}/roles?role_id=${roleId}`, { method: 'POST' }),

    removeRole: (uid, roleId) =>
        apiRequest(`/users/${uid}/roles/${roleId}`, { method: 'DELETE' }),

    convertIntern: (uid, migrateRoles = true) =>
        apiRequest(`/users/${uid}/convert`, { method: 'POST', body: { migrate_roles: migrateRoles } }),

    extendInternship: (uid, newEndDate, reason) =>
        apiRequest(`/users/${uid}/extend`, { method: 'POST', body: { new_end_date: newEndDate, reason } }),

    // Roles
    getRoles: (includeInactive = false) =>
        apiRequest(`/roles?include_inactive=${includeInactive}`),

    createRole: (data) =>
        apiRequest('/roles', { method: 'POST', body: data }),

    updateRole: (id, data) =>
        apiRequest(`/roles/${id}`, { method: 'PUT', body: data }),

    deleteRole: (id) =>
        apiRequest(`/roles/${id}`, { method: 'DELETE' }),

    // Audit
    getAuditLogs: (params = {}) => {
        const query = new URLSearchParams();
        Object.entries(params).forEach(([k, v]) => { if (v) query.set(k, v); });
        return apiRequest(`/audit?${query.toString()}`);
    },

    // Domains & Divisions
    getDomains: () => apiRequest('/domains'),
    getDivisions: () => apiRequest('/divisions'),

    createDomain: (data) => apiRequest('/domains', { method: 'POST', body: data }),
    createDivision: (data) => apiRequest('/divisions', { method: 'POST', body: data }),

    // Stats & Warnings & Trends
    getStats: () => apiRequest('/stats'),
    getWarnings: () => apiRequest('/warnings'),
    getTrend: (days = 30) => apiRequest(`/stats/trend?days=${days}`),

    // Sheets
    exportExcel: () => apiRequest('/sheets/export', { method: 'POST' }),
    syncGoogle: (fullSync = false) =>
        apiRequest(`/sheets/sync-google?full_sync=${fullSync}`, { method: 'POST' }),
    getSyncLogs: () => apiRequest('/sheets/logs'),
    importExcel: (formData) => apiUpload('/sheets/import', formData),
};
