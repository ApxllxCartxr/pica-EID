/**
 * PRISMID Dashboard Application Logic
 * Handles UI interactions, panel switching, data loading, and modals.
 */

let currentPanel = 'overview';
let usersPage = 1;
let auditPage = 1;
let allDomains = [];
let allDivisions = [];
let allRoles = [];

// =============================================
// INITIALIZATION
// =============================================

document.addEventListener('DOMContentLoaded', () => {
    const token = getToken();
    if (token) {
        showDashboard();
    } else {
        showLoginScreen();
    }
});

function showLoginScreen() {
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('dashboard').style.display = 'none';
}

function showDashboard() {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('dashboard').style.display = 'flex';

    const admin = getAdmin();
    if (admin) {
        document.getElementById('admin-name').textContent = admin.username;
        document.getElementById('admin-level').textContent = admin.access_level;
        document.getElementById('admin-avatar').textContent = admin.username.charAt(0).toUpperCase();

        // Show superadmin actions
        if (admin.access_level === 'SUPERADMIN') {
            const sa = document.getElementById('superadmin-actions');
            if (sa) sa.style.display = 'flex';
            const rcb = document.getElementById('role-create-btn');
            if (rcb) rcb.style.display = 'flex';
            const dcb = document.getElementById('domain-create-btn');
            if (dcb) dcb.style.display = 'flex';
            const divcb = document.getElementById('division-create-btn');
            if (divcb) divcb.style.display = 'flex';
        }
    }

    loadDashboardData();
}

async function loadDashboardData() {
    try {
        allDomains = await api.getDomains();
        allDivisions = await api.getDivisions();
        allRoles = (await api.getRoles(true)).roles || [];
    } catch (e) { /* ignore initial load errors */ }

    loadOverview();
    loadWarnings();
}

function refreshData() {
    const btn = document.querySelector('button[onclick="refreshData()"] svg');
    btn.style.animation = 'spin 1s linear infinite';

    // Reload current panel data
    const loaders = {
        'overview': loadOverview,
        'users': () => loadUsers(usersPage),
        'roles': loadRoles,
        'audit': () => loadAuditLogs(auditPage),
        'sheets': loadSyncLogs
    };

    if (loaders[currentPanel]) {
        loaders[currentPanel]().then(() => {
            setTimeout(() => btn.style.animation = 'none', 500);
            showToast('Data refreshed', 'success');
        });
    } else {
        setTimeout(() => btn.style.animation = 'none', 500);
    }
}

// =============================================
// AUTH
// =============================================

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');
    const btn = document.getElementById('login-btn');

    console.log(`[Auth] Attempting login for user: ${username}`);

    btn.disabled = true;
    btn.innerHTML = '<span>Signing in...</span>';
    errorEl.style.display = 'none';

    try {
        const data = await api.login(username, password);
        console.log('[Auth] Login successful, setting tokens...');
        setTokens(data.access_token, data.refresh_token);
        setAdmin({ username: data.username, access_level: data.access_level });
        console.log('[Auth] Redirecting to dashboard...');
        showDashboard();
    } catch (err) {
        console.error('[Auth] Login failed:', err);
        errorEl.textContent = err.message || 'Login failed';
        errorEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>Sign In</span><svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8H13M13 8L9 4M13 8L9 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    }
}

async function handleLogout() {
    try { await api.logout(); } catch (e) { /* ignore */ }
    clearTokens();
    showLoginScreen();
}

// =============================================
// PANEL SWITCHING
// =============================================

function switchPanel(panel, el) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    if (el) el.classList.add('active');

    // Switch panel
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    const target = document.getElementById(`panel-${panel}`);
    if (target) target.classList.add('active');

    currentPanel = panel;
    document.getElementById('panel-title').textContent =
        {
            overview: 'Overview',
            users: 'User Management',
            roles: 'Role Management',
            domains: 'Domain Management',
            divisions: 'Division Management',
            audit: 'Audit Logs',
            sheets: 'Spreadsheet Integration'
        }[panel] || panel;

    // Load data
    if (panel === 'overview') loadOverview();
    else if (panel === 'users') loadUsers();
    else if (panel === 'roles') loadRoles();
    else if (panel === 'domains') loadDomains();
    else if (panel === 'divisions') loadDivisions();
    else if (panel === 'audit') loadAuditLogs();
    else if (panel === 'sheets') loadSyncLogs();
}

// =============================================
// OVERVIEW
// =============================================

async function loadOverview() {
    try {
        const stats = await api.getStats();
        animateNumber('stat-total', stats.total_users);
        animateNumber('stat-active', stats.active_users);
        animateNumber('stat-interns', stats.total_interns);
        animateNumber('stat-roles', stats.total_roles);

        // Category chart (bar)
        const total = stats.total_employees + stats.total_interns || 1;
        document.getElementById('bar-employees').style.width = `${(stats.total_employees / total) * 100}%`;
        document.getElementById('bar-interns').style.width = `${(stats.total_interns / total) * 100}%`;
        document.getElementById('val-employees').textContent = stats.total_employees;
        document.getElementById('val-interns').textContent = stats.total_interns;

        // Pie chart
        renderPieChart(stats.total_employees, stats.total_interns, stats.active_users, stats.total_users - stats.active_users);

        // Recent activity
        const activityEl = document.getElementById('recent-activity');
        if (stats.recent_actions && stats.recent_actions.length > 0) {
            activityEl.innerHTML = stats.recent_actions.map((a, i) => {
                const dotClass = getActionDotClass(a.action);
                return `<div class="activity-item stagger-item" style="animation-delay: ${i * 0.05}s">
                    <div class="activity-dot ${dotClass}"></div>
                    <div class="activity-text"><strong>${formatAction(a.action)}</strong> — ${a.entity_type} ${a.entity_id || ''}</div>
                    <div class="activity-time">${formatTime(a.timestamp)}</div>
                </div>`;
            }).join('');
        } else {
            activityEl.innerHTML = '<div class="empty-state">No recent activity</div>';
        }

        // Trend sparkline
        loadTrendChart();
    } catch (err) {
        console.error('Failed to load overview:', err);
    }
}

function renderPieChart(employees, interns, active, inactive) {
    const container = document.getElementById('pie-chart');
    if (!container) return;
    const total = employees + interns || 1;
    const empPct = employees / total;
    const empAngle = empPct * 360;
    container.innerHTML = `
        <svg viewBox="0 0 100 100" width="140" height="140">
            <circle cx="50" cy="50" r="40" fill="transparent" stroke="var(--accent-secondary)" stroke-width="18"
                stroke-dasharray="${empPct * 251.2} ${251.2}" stroke-dashoffset="0" transform="rotate(-90 50 50)" />
            <circle cx="50" cy="50" r="40" fill="transparent" stroke="var(--accent)" stroke-width="18"
                stroke-dasharray="${(1 - empPct) * 251.2} ${251.2}" stroke-dashoffset="${-empPct * 251.2}" transform="rotate(-90 50 50)" />
            <text x="50" y="48" text-anchor="middle" fill="var(--text-primary)" font-size="12" font-weight="700">${total}</text>
            <text x="50" y="60" text-anchor="middle" fill="var(--text-muted)" font-size="6">Total</text>
        </svg>
        <div class="pie-legend">
            <div><span class="dot" style="background:var(--accent-secondary);"></span> Employees: ${employees}</div>
            <div><span class="dot" style="background:var(--accent);"></span> Interns: ${interns}</div>
            <div><span class="dot" style="background:var(--success);"></span> Active: ${active}</div>
            <div><span class="dot" style="background:var(--text-muted);"></span> Inactive: ${inactive}</div>
        </div>
    `;
}

async function loadTrendChart() {
    const container = document.getElementById('trend-chart');
    if (!container) return;
    try {
        const data = await api.getTrend(30);
        if (!data.trend || data.trend.length === 0) { container.innerHTML = '<div class="empty-state">No trend data</div>'; return; }
        const max = Math.max(...data.trend.map(d => d.count), 1);
        const w = 400, h = 80, pad = 4;
        const stepX = (w - pad * 2) / (data.trend.length - 1 || 1);
        const points = data.trend.map((d, i) => `${pad + i * stepX},${h - pad - (d.count / max) * (h - pad * 2)}`).join(' ');
        const areaPoints = `${pad},${h - pad} ${points} ${pad + (data.trend.length - 1) * stepX},${h - pad}`;
        container.innerHTML = `
            <svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}" preserveAspectRatio="none">
                <defs><linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="var(--accent)" stop-opacity="0.3"/>
                    <stop offset="100%" stop-color="var(--accent)" stop-opacity="0.02"/>
                </linearGradient></defs>
                <polygon points="${areaPoints}" fill="url(#trendGrad)" />
                <polyline points="${points}" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <div class="trend-label">User registrations — last 30 days</div>
        `;
    } catch (e) { container.innerHTML = ''; }
}

// =============================================
// WARNINGS
// =============================================

async function loadWarnings() {
    try {
        const data = await api.getWarnings();
        const warnings = data.warnings || [];
        if (warnings.length > 0) {
            document.getElementById('warning-badge').style.display = 'flex';
            document.getElementById('warning-count').textContent = warnings.length;
            document.getElementById('warning-banner').style.display = 'flex';
            document.getElementById('warning-text').textContent =
                `${warnings.length} internship(s) expiring within 7 days`;
        }
    } catch (e) { /* Redis not available */ }
}

// =============================================
// USERS
// =============================================

async function loadUsers(page = 1) {
    usersPage = page;
    const params = {
        page: page,
        per_page: 20,
        category: document.getElementById('filter-category').value,
        status: document.getElementById('filter-status').value,
    };

    try {
        const data = await api.getUsers(params);
        const tbody = document.getElementById('users-tbody');
        const admin = getAdmin();
        const isSuperadmin = admin && admin.access_level === 'SUPERADMIN';
        const isAdmin = admin && (admin.access_level === 'ADMIN' || admin.access_level === 'SUPERADMIN');

        if (data.users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="empty-state">No users found</td></tr>';
        } else {
            tbody.innerHTML = data.users.map((u, i) => `
                <tr class="stagger-item" style="animation-delay: ${i * 0.03}s">
                    <td class="user-id-cell" title="ULID: ${u.ulid}">${escapeHtml(u.display_id)}</td>
                    <td><strong style="color: var(--text-primary)">${escapeHtml(u.name)}</strong><br><span style="font-size:11px;color:var(--text-muted)">${escapeHtml(u.email)}</span></td>
                    <td><span class="badge badge-${u.category.toLowerCase()}">${u.category}</span></td>
                    <td><span class="badge badge-${u.status.toLowerCase()}">${u.status}</span></td>
                    <td><div class="roles-list">${u.roles.map(r => `<span class="role-tag">${escapeHtml(r)}</span>`).join('') || '—'}</div></td>
                    <td><span style="font-size:12px;color:var(--text-primary);">${escapeHtml(u.domain_name || '—')}</span><br><span style="font-size:11px;color:var(--text-muted);">${escapeHtml(u.division_name || '—')}</span></td>
                    <td>${u.end_date || '—'}</td>
                    <td>
                        <div class="action-group">
                            <button class="action-btn" onclick="showUserDetailsModal('${u.ulid}')" title="View Details">👁</button>
                            ${isAdmin ? `<button class="action-btn" onclick="showEditUserModal('${u.ulid}')" title="Edit User">✏</button>` : ''}
                            ${isAdmin ? `<button class="action-btn roles" onclick="showRoleAssignModal('${u.ulid}', '${escapeHtml(u.name)}')" title="Manage Roles">⚙</button>` : ''}
                            ${isSuperadmin && u.category === 'INTERN' && u.status === 'ACTIVE' ? `
                                <button class="action-btn convert" onclick="confirmConvert('${u.ulid}', '${escapeHtml(u.name)}')" title="Convert to Employee">↑</button>
                                <button class="action-btn extend" onclick="showExtendModal('${u.ulid}', '${escapeHtml(u.name)}')" title="Extend Internship">⏰</button>
                            ` : ''}
                            ${isSuperadmin ? `<button class="action-btn delete" onclick="confirmDeleteUser('${u.ulid}', '${escapeHtml(u.name)}')" title="Delete User">🗑</button>` : ''}
                        </div>
                    </td>
                </tr>
            `).join('');
        }

        // Pagination
        renderPagination('users-pagination', data.page, data.pages, (p) => loadUsers(p));
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// =============================================
// ROLES
// =============================================

async function loadRoles() {
    const includeInactive = document.getElementById('show-inactive-roles')?.checked || false;
    try {
        const data = await api.getRoles(includeInactive);
        const grid = document.getElementById('roles-grid');
        const admin = getAdmin();
        const isSuperadmin = admin && admin.access_level === 'SUPERADMIN';

        if (!data.roles || data.roles.length === 0) {
            grid.innerHTML = '<div class="empty-state">No roles found</div>';
            return;
        }

        grid.innerHTML = data.roles.map(r => `
            <div class="role-card ${r.is_active ? '' : 'inactive'}">
                <div class="role-card-header">
                    <span class="role-name">${escapeHtml(r.name)}</span>
                    <span class="clearance-badge">L${r.clearance_level}</span>
                </div>
                <p class="role-description">${escapeHtml(r.description || 'No description')}</p>
                <div class="role-meta">
                    <span class="role-users-count">${r.assigned_users_count} user(s) assigned</span>
                    ${isSuperadmin ? `
                        <div class="role-actions">
                            <button class="action-btn" onclick="showEditRoleModal(${r.id}, '${escapeHtml(r.name)}', '${escapeHtml(r.description || '')}', ${r.clearance_level})" title="Edit">✏</button>
                            ${r.is_active ? `<button class="action-btn" onclick="confirmArchiveRole(${r.id}, '${escapeHtml(r.name)}')" title="Archive">📦</button>` : ''}
                            <button class="action-btn" onclick="confirmDeleteRole(${r.id}, '${escapeHtml(r.name)}')" title="Delete">🗑</button>
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// =============================================
// AUDIT LOGS
// =============================================

async function loadAuditLogs(page = 1) {
    auditPage = page;
    const params = {
        page: page,
        per_page: 50,
        action: document.getElementById('audit-action-filter').value,
        date_from: document.getElementById('audit-date-from').value,
        date_to: document.getElementById('audit-date-to').value,
    };

    try {
        const data = await api.getAuditLogs(params);
        const timeline = document.getElementById('audit-timeline');

        if (!data.logs || data.logs.length === 0) {
            timeline.innerHTML = '<div class="empty-state">No audit logs found</div>';
            return;
        }

        timeline.innerHTML = data.logs.map((log, i) => {
            const iconClass = getAuditIconClass(log.action);
            const icon = getAuditIcon(log.action);
            return `
                <div class="audit-entry stagger-item" style="animation-delay: ${i * 0.03}s">
                    <div class="audit-icon ${iconClass}">${icon}</div>
                    <div class="audit-info">
                        <div class="audit-action-text">${formatAction(log.action)}</div>
                        <div class="audit-details">
                            ${log.entity_type} ${log.entity_id || ''} ${log.changed_by_name ? `by ${log.changed_by_name}` : ''}
                            ${log.description ? `— ${log.description}` : ''}
                        </div>
                    </div>
                    <div class="audit-time">${formatTime(log.timestamp)}</div>
                </div>
            `;
        }).join('');

        renderPagination('audit-pagination', data.page, data.pages, (p) => loadAuditLogs(p));
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// =============================================
// SHEETS
// =============================================

async function loadSyncLogs() {
    try {
        const data = await api.getSyncLogs();
        const tbody = document.getElementById('sync-logs-tbody');

        if (!data.logs || data.logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No sync history</td></tr>';
            return;
        }

        tbody.innerHTML = data.logs.map(log => `
            <tr>
                <td><span class="badge badge-${log.sync_type === 'PUSH' || log.sync_type === 'EXPORT' ? 'employee' : 'intern'}">${log.sync_type}</span></td>
                <td>${log.sync_target}</td>
                <td>${log.records_affected}</td>
                <td><span class="badge badge-${log.status === 'SUCCESS' ? 'active' : log.status === 'PARTIAL' ? 'intern' : 'expired'}">${log.status}</span></td>
                <td>${log.initiated_by_name || 'System'}</td>
                <td>${formatTime(log.timestamp)}</td>
                <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;">${log.error_message || '—'}</td>
            </tr>
        `).join('');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function exportExcel() {
    try {
        showToast('Exporting...', 'info');
        const data = await api.exportExcel();
        showToast(`Exported ${data.records_count} records`, 'success');
        // Trigger download
        window.open(data.download_url, '_blank');
        loadSyncLogs();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function importExcel(input) {
    if (!input.files.length) return;
    const formData = new FormData();
    formData.append('file', input.files[0]);

    try {
        showToast('Importing...', 'info');
        const result = await api.importExcel(formData);
        showToast(`Imported: ${result.updated} updated, ${result.skipped} skipped`, 'success');
        loadSyncLogs();
    } catch (err) {
        showToast(err.message, 'error');
    }
    input.value = '';
}

async function syncGoogleSheets() {
    try {
        showToast('Syncing with Google Sheets...', 'info');
        const result = await api.syncGoogle(false);
        showToast(result.message, 'success');
        loadSyncLogs();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// =============================================
// SEARCH
// =============================================

let searchTimeout;
function handleGlobalSearch(e) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
        const query = e.target.value.trim();
        if (!query) {
            switchPanel('overview', document.querySelector('[data-panel=overview]'));
            return;
        }
        // Switch to users panel and search
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.querySelector('[data-panel=users]').classList.add('active');
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        document.getElementById('panel-users').classList.add('active');
        document.getElementById('panel-title').textContent = 'Search Results';

        try {
            const data = await api.getUsers({ q: query });
            renderUserResults(data);
        } catch (err) {
            showToast(err.message, 'error');
        }
    }, 300);
}

function renderUserResults(data) {
    const tbody = document.getElementById('users-tbody');
    const admin = getAdmin();
    const isSuperadmin = admin && admin.access_level === 'SUPERADMIN';
    const isAdmin = admin && (admin.access_level === 'ADMIN' || admin.access_level === 'SUPERADMIN');

    if (data.users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">No users found</td></tr>';
        return;
    }
    tbody.innerHTML = data.users.map(u => `
        <tr>
            <td class="user-id-cell" title="ULID: ${u.ulid}">${escapeHtml(u.display_id)}</td>
            <td><strong style="color: var(--text-primary)">${escapeHtml(u.name)}</strong></td>
            <td><span class="badge badge-${u.category.toLowerCase()}">${u.category}</span></td>
            <td><span class="badge badge-${u.status.toLowerCase()}">${u.status}</span></td>
            <td><div class="roles-list">${u.roles.map(r => `<span class="role-tag">${escapeHtml(r)}</span>`).join('') || '—'}</div></td>
            <td><span style="font-size:12px;color:var(--text-primary);">${escapeHtml(u.domain_name || '—')}</span><br><span style="font-size:11px;color:var(--text-muted);">${escapeHtml(u.division_name || '—')}</span></td>
            <td>${u.end_date || '—'}</td>
            <td>
                <div class="action-group">
                    <button class="action-btn" onclick="showUserDetailsModal('${u.ulid}')" title="View Details">👁</button>
                    ${isAdmin ? `<button class="action-btn roles" onclick="showRoleAssignModal('${u.ulid}', '${escapeHtml(u.name)}')" title="Manage Roles">⚙</button>` : ''}
                    ${isSuperadmin && u.category === 'INTERN' && u.status === 'ACTIVE' ? `
                        <button class="action-btn convert" onclick="confirmConvert('${u.ulid}', '${escapeHtml(u.name)}')" title="Convert">↑</button>
                        <button class="action-btn extend" onclick="showExtendModal('${u.ulid}', '${escapeHtml(u.name)}')" title="Extend">⏰</button>
                    ` : ''}
                </div>
            </td>
        </tr>
    `).join('');
}

// =============================================
// MODALS
// =============================================

function showModal(title, bodyHtml) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHtml;
    document.getElementById('modal-overlay').style.display = 'flex';
}

function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
}

// --- User Details Modal ---
async function showUserDetailsModal(uid) {
    try {
        const user = await api.getUser(uid);
        const rolesHtml = user.roles && user.roles.length > 0
            ? user.roles.map(r => `<span class="role-tag">${escapeHtml(typeof r === 'string' ? r : r.name)}</span>`).join(' ')
            : '<span style="color:var(--text-muted)">No roles assigned</span>';

        showModal(`User Details — ${escapeHtml(user.name)}`, `
            <div style="display:flex;flex-direction:column;gap:12px;">
                <div class="form-row">
                    <div class="form-group"><label>Display ID</label><div style="font-size:15px;font-weight:700;color:var(--accent);letter-spacing:1px;">${escapeHtml(user.display_id)}</div></div>
                    <div class="form-group"><label>Category</label><div><span class="badge badge-${(user.category || '').toLowerCase()}">${escapeHtml(user.category || '—')}</span></div></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Full ULID</label><div style="font-size:12px;color:var(--text-muted);word-break:break-all;font-family:monospace;">${escapeHtml(user.ulid)}</div></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Name</label><div style="color:var(--text-primary);font-weight:600;">${escapeHtml(user.name)}</div></div>
                    <div class="form-group"><label>Email</label><div style="color:var(--text-secondary);">${escapeHtml(user.email)}</div></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Phone</label><div style="color:var(--text-secondary);">${escapeHtml(user.phone_number || '—')}</div></div>
                    <div class="form-group"><label>Status</label><div><span class="badge badge-${(user.status || '').toLowerCase()}">${escapeHtml(user.status || '—')}</span></div></div>
                </div>
                <div class="form-row">
                    <div class="form-group"><label>Domain</label><div style="color:var(--text-secondary);">${escapeHtml(user.domain_name || '—')}</div></div>
                    <div class="form-group"><label>Division</label><div style="color:var(--text-secondary);">${escapeHtml(user.division_name || '—')}</div></div>
                    <div class="form-group"><label>Date of Joining</label><div style="color:var(--text-secondary);">${escapeHtml(user.date_of_joining || '—')}</div></div>
                </div>
                ${user.category === 'INTERN' ? `
                <div class="form-row">
                    <div class="form-group"><label>Start Date</label><div style="color:var(--text-secondary);">${escapeHtml(user.start_date || '—')}</div></div>
                    <div class="form-group"><label>End Date</label><div style="color:var(--text-secondary);">${escapeHtml(user.end_date || '—')}</div></div>
                </div>
                ` : ''}
                <div class="form-group"><label>Roles</label><div class="roles-list" style="margin-top:4px;">${rolesHtml}</div></div>
                <div class="form-row">
                    <div class="form-group"><label>Created</label><div style="color:var(--text-muted);font-size:12px;">${user.created_at ? formatTime(user.created_at) : '—'}</div></div>
                    <div class="form-group"><label>Last Updated</label><div style="color:var(--text-muted);font-size:12px;">${user.updated_at ? formatTime(user.updated_at) : '—'}</div></div>
                </div>
            </div>
            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="closeModal()">Close</button>
            </div>
        `);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- Add User Modal ---
function showAddUserModal() {
    const domainOptions = allDomains.map(d => `<option value="${d.id}">${escapeHtml(d.name)}</option>`).join('');
    const divisionOptions = allDivisions.map(d => `<option value="${d.id}">${escapeHtml(d.name)}</option>`).join('');
    const roleOptions = allRoles.filter(r => r.is_active).map(r => `<label style="display:flex;align-items:center;gap:6px;font-size:13px;color:var(--text-secondary);"><input type="checkbox" value="${r.id}" class="role-checkbox"> ${escapeHtml(r.name)}</label>`).join('');
    const today = new Date().toISOString().split('T')[0];

    showModal('Add New User', `
        <form onsubmit="submitAddUser(event)">
            <div class="form-row">
                <div class="form-group"><label>Full Name</label><input type="text" id="add-name" required></div>
                <div class="form-group"><label>Email</label><input type="email" id="add-email" required></div>
            </div>
            <div class="form-row">
                 <div class="form-group"><label>Phone Number (Optional)</label><input type="tel" id="add-phone" placeholder="+1234567890"></div>
                 <div class="form-group"><label>Date of Joining</label><input type="date" id="add-doj" value="${today}" required></div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Category</label>
                    <select id="add-category" required onchange="toggleInternFields()">
                        <option value="EMPLOYEE">Employee</option>
                        <option value="INTERN">Intern</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Domain</label>
                    <select id="add-domain"><option value="">— Select —</option>${domainOptions}</select>
                </div>
                <div class="form-group">
                    <label>Division</label>
                    <select id="add-division"><option value="">— Select —</option>${divisionOptions}</select>
                </div>
            </div>
            <div id="intern-fields" style="display:none;">
                <div class="form-row">
                    <div class="form-group"><label>Start Date</label><input type="date" id="add-start-date" min="${today}"></div>
                    <div class="form-group"><label>End Date</label><input type="date" id="add-end-date" min="${today}"></div>
                </div>
            </div>
            <div class="form-group"><label>Roles</label><div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:4px;">${roleOptions || '<span style="color:var(--text-muted)">No roles available</span>'}</div></div>
            <div class="modal-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Create User</button>
            </div>
        </form>
    `);
}

function toggleInternFields() {
    const cat = document.getElementById('add-category').value;
    document.getElementById('intern-fields').style.display = cat === 'INTERN' ? 'block' : 'none';
}

async function submitAddUser(e) {
    e.preventDefault();
    const category = document.getElementById('add-category').value;
    const roleCheckboxes = document.querySelectorAll('.role-checkbox:checked');
    const roleIds = Array.from(roleCheckboxes).map(cb => parseInt(cb.value));

    const body = {
        name: document.getElementById('add-name').value,
        email: document.getElementById('add-email').value,
        phone_number: document.getElementById('add-phone').value || null,
        date_of_joining: document.getElementById('add-doj').value || null,
        category: category,
        domain_id: parseInt(document.getElementById('add-domain').value) || null,
        division_id: parseInt(document.getElementById('add-division').value) || null,
        role_ids: roleIds,
    };

    if (category === 'INTERN') {
        body.start_date = document.getElementById('add-start-date').value;
        body.end_date = document.getElementById('add-end-date').value;
    }

    try {
        const user = await api.createUser(body);
        showToast(`User created: ${user.display_id}`, 'success');
        closeModal();
        loadUsers();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- Role Assign Modal ---
function showRoleAssignModal(uid, name) {
    const roleOptions = allRoles.filter(r => r.is_active).map(r =>
        `<option value="${r.id}">${escapeHtml(r.name)} (L${r.clearance_level})</option>`
    ).join('');

    showModal(`Manage Roles — ${name}`, `
        <div class="form-group">
            <label>Assign Role</label>
            <div style="display:flex;gap:8px;">
                <select id="assign-role-select" style="flex:1;">${roleOptions}</select>
                <button class="btn btn-primary btn-sm" onclick="submitAssignRole('${uid}')">Assign</button>
            </div>
        </div>
        <div class="modal-actions">
            <button class="btn btn-secondary" onclick="closeModal()">Close</button>
        </div>
    `);
}

async function submitAssignRole(uid) {
    const roleId = document.getElementById('assign-role-select').value;
    try {
        await api.assignRole(uid, roleId);
        showToast('Role assigned', 'success');
        closeModal();
        loadUsers();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- Convert Confirm ---
async function confirmConvert(uid, name) {
    if (confirm(`Convert intern "${name}" to permanent employee?\n\nThis will:\n• Keep the same ULID\n• Change category from INTERN to EMPLOYEE\n• Update display prefix from INT- to EMP-\n• Migrate all current roles`)) {
        try {
            const user = await api.convertIntern(uid);
            showToast(`Converted! Display ID: ${user.display_id}`, 'success');
            loadUsers();
        } catch (err) {
            showToast(err.message, 'error');
        }
    }
}

// --- Extend Internship Modal ---
function showExtendModal(uid, name) {
    const today = new Date().toISOString().split('T')[0];
    showModal(`Extend Internship — ${name}`, `
        <form onsubmit="submitExtend(event, '${uid}')">
            <div class="form-group"><label>New End Date</label><input type="date" id="extend-date" required min="${today}"></div>
            <div class="form-group"><label>Reason for Extension</label><input type="text" id="extend-reason" required placeholder="e.g., Performance review pending" minlength="5"></div>
            <div class="modal-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Extend</button>
            </div>
        </form>
    `);
}

async function submitExtend(e, uid) {
    e.preventDefault();
    try {
        await api.extendInternship(uid, document.getElementById('extend-date').value, document.getElementById('extend-reason').value);
        showToast('Internship extended', 'success');
        closeModal();
        loadUsers();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- Edit User Modal ---
async function showEditUserModal(uid) {
    try {
        const user = await api.getUser(uid);
        const divisionOptions = allDivisions.map(d => `<option value="${d.id}" ${d.id === user.division_id ? 'selected' : ''}>${escapeHtml(d.name)}</option>`).join('');
        const doj = user.date_of_joining ? user.date_of_joining : '';

        showModal(`Edit User — ${user.name}`, `
            <form onsubmit="submitEditUser(event, '${uid}')">
                <div class="form-row">
                    <div class="form-group"><label>Full Name</label><input type="text" id="edit-user-name" value="${escapeHtml(user.name)}" required></div>
                    <div class="form-group"><label>Email</label><input type="email" id="edit-user-email" value="${escapeHtml(user.email)}" required></div>
                </div>
                 <div class="form-row">
                     <div class="form-group"><label>Phone Number</label><input type="tel" id="edit-user-phone" value="${escapeHtml(user.phone_number || '')}" placeholder="+1234567890"></div>
                     <div class="form-group"><label>Date of Joining</label><input type="date" id="edit-user-doj" value="${doj}"></div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Division</label>
                        <select id="edit-user-division"><option value="">— Select —</option>${divisionOptions}</select>
                    </div>
                    <div class="form-group">
                        <label>Status</label>
                        <select id="edit-user-status">
                            <option value="ACTIVE" ${user.status === 'ACTIVE' ? 'selected' : ''}>Active</option>
                            <option value="INACTIVE" ${user.status === 'INACTIVE' ? 'selected' : ''}>Inactive</option>
                        </select>
                    </div>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Save Changes</button>
                </div>
            </form>
        `);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function submitEditUser(e, uid) {
    e.preventDefault();
    try {
        await api.updateUser(uid, {
            name: document.getElementById('edit-user-name').value,
            email: document.getElementById('edit-user-email').value,
            phone_number: document.getElementById('edit-user-phone').value || null,
            date_of_joining: document.getElementById('edit-user-doj').value || null,
            division_id: parseInt(document.getElementById('edit-user-division').value) || null,
            status: document.getElementById('edit-user-status').value,
        });
        showToast('User updated', 'success');
        closeModal();
        loadUsers();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- Delete User Confirm ---
async function confirmDeleteUser(uid, name) {
    if (confirm(`Delete user "${name}"?\n\nThis is a soft-delete — the user will be marked inactive and hidden from listings.`)) {
        try {
            await api.deleteUser(uid);
            showToast(`User ${name} deleted`, 'success');
            loadUsers();
        } catch (err) {
            showToast(err.message, 'error');
        }
    }
}

// --- Create Role Modal ---
function showCreateRoleModal() {
    showModal('Create New Role', `
        <form onsubmit="submitCreateRole(event)">
            <div class="form-group"><label>Role Name</label><input type="text" id="role-name" required></div>
            <div class="form-group"><label>Description</label><input type="text" id="role-desc"></div>
            <div class="form-group"><label>Clearance Level (1-10)</label><input type="number" id="role-level" min="1" max="10" value="5" required></div>
            <div class="modal-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Create Role</button>
            </div>
        </form>
    `);
}

async function submitCreateRole(e) {
    e.preventDefault();
    try {
        await api.createRole({
            name: document.getElementById('role-name').value,
            description: document.getElementById('role-desc').value,
            clearance_level: parseInt(document.getElementById('role-level').value),
        });
        showToast('Role created', 'success');
        closeModal();
        loadRoles();
        allRoles = (await api.getRoles(true)).roles || [];
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- Edit Role Modal ---
function showEditRoleModal(id, name, desc, level) {
    showModal('Edit Role', `
        <form onsubmit="submitEditRole(event, ${id})">
            <div class="form-group"><label>Role Name</label><input type="text" id="edit-role-name" value="${escapeHtml(name)}" required></div>
            <div class="form-group"><label>Description</label><input type="text" id="edit-role-desc" value="${escapeHtml(desc || '')}"></div>
            <div class="form-group"><label>Clearance Level (1-10)</label><input type="number" id="edit-role-level" min="1" max="10" value="${level}" required></div>
            <div class="modal-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Save Changes</button>
            </div>
        </form>
    `);
}

async function submitEditRole(e, id) {
    e.preventDefault();
    try {
        await api.updateRole(id, {
            name: document.getElementById('edit-role-name').value,
            description: document.getElementById('edit-role-desc').value,
            clearance_level: parseInt(document.getElementById('edit-role-level').value),
        });
        showToast('Role updated', 'success');
        closeModal();
        loadRoles();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function confirmArchiveRole(id, name) {
    if (confirm(`Archive role "${name}"? It will be deactivated.`)) {
        try {
            await api.updateRole(id, { is_active: false });
            showToast('Role archived', 'success');
            loadRoles();
        } catch (err) {
            showToast(err.message, 'error');
        }
    }
}

async function confirmDeleteRole(id, name) {
    if (confirm(`Delete role "${name}"? This is a soft-delete.`)) {
        try {
            await api.deleteRole(id);
            showToast('Role deleted', 'success');
            loadRoles();
        } catch (err) {
            showToast(err.message, 'error');
        }
    }
}

// =============================================
// UTILITIES
// =============================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'} ${escapeHtml(message)}`;
    container.appendChild(toast);
    setTimeout(() => { toast.classList.add('toast-out'); setTimeout(() => toast.remove(), 300); }, 4000);
}

function renderPagination(containerId, currentPage, totalPages, callback) {
    const el = document.getElementById(containerId);
    if (totalPages <= 1) { el.innerHTML = ''; return; }

    let html = `<button ${currentPage <= 1 ? 'disabled' : ''} onclick="(${callback.toString()})(${currentPage - 1})">← Prev</button>`;
    for (let i = 1; i <= Math.min(totalPages, 7); i++) {
        html += `<button class="${i === currentPage ? 'active' : ''}" onclick="(${callback.toString()})(${i})">${i}</button>`;
    }
    if (totalPages > 7) html += `<button disabled>…</button><button onclick="(${callback.toString()})(${totalPages})">${totalPages}</button>`;
    html += `<button ${currentPage >= totalPages ? 'disabled' : ''} onclick="(${callback.toString()})(${currentPage + 1})">Next →</button>`;
    el.innerHTML = html;
}

function animateNumber(elementId, target) {
    const el = document.getElementById(elementId);
    let current = 0;
    const step = Math.ceil(target / 30) || 1;
    const interval = setInterval(() => {
        current = Math.min(current + step, target);
        el.textContent = current;
        if (current >= target) clearInterval(interval);
    }, 20);
}

function escapeHtml(s) {
    if (!s) return '';
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function formatAction(action) {
    return action.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
}

function formatTime(ts) {
    const d = new Date(ts);
    const now = new Date();
    const diff = Math.floor((now - d) / 60000);
    if (diff < 1) return 'Just now';
    if (diff < 60) return `${diff}m ago`;
    if (diff < 1440) return `${Math.floor(diff / 60)}h ago`;
    return d.toLocaleDateString();
}

function getActionDotClass(action) {
    if (action.includes('CREATED')) return 'create';
    if (action.includes('UPDATED') || action.includes('ASSIGNED') || action.includes('EXTENDED')) return 'update';
    if (action.includes('DELETED') || action.includes('REMOVED')) return 'delete';
    if (action.includes('CONVERTED')) return 'convert';
    if (action.includes('EXPIRED')) return 'expire';
    return 'update';
}

function getAuditIconClass(action) {
    if (action.includes('CREATED')) return 'create';
    if (action.includes('DELETED')) return 'delete';
    if (action.includes('ROLE')) return 'role';
    if (action.includes('CONVERTED')) return 'convert';
    if (action.includes('EXPIRED')) return 'expire';
    return 'update';
}

function getAuditIcon(action) {
    if (action.includes('CREATED')) return '➕';
    if (action.includes('DELETED')) return '🗑';
    if (action.includes('ROLE')) return '⭐';
    if (action.includes('CONVERTED')) return '↑';
    if (action.includes('EXPIRED')) return '⏰';
    if (action.includes('EXTENDED')) return '📅';
    return '✏';
}

function showExpiringInterns() {
    switchPanel('users', document.querySelector('[data-panel=users]'));
    document.getElementById('filter-category').value = 'INTERN';
    document.getElementById('filter-status').value = 'ACTIVE';
    loadUsers();
}

// =============================================
// AUDIT CSV EXPORT
// =============================================

function exportAuditCSV() {
    const params = new URLSearchParams();
    const action = document.getElementById('audit-action-filter').value;
    const dateFrom = document.getElementById('audit-date-from').value;
    const dateTo = document.getElementById('audit-date-to').value;
    if (action) params.set('action', action);
    if (dateFrom) params.set('date_from', dateFrom);
    if (dateTo) params.set('date_to', dateTo);

    const token = getToken();
    // Open in new tab with auth (use fetch + blob)
    fetch(`/api/audit/export?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    }).then(res => {
        if (!res.ok) throw new Error('Export failed');
        return res.blob();
    }).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('Audit logs exported', 'success');
    }).catch(err => showToast(err.message, 'error'));
}

// =============================================
// NOTIFICATION CENTER
// =============================================

function toggleNotifications() {
    const panel = document.getElementById('notification-panel');
    if (!panel) return;
    if (panel.style.display === 'flex') {
        panel.style.display = 'none';
        return;
    }
    panel.style.display = 'flex';
    loadNotifications();
}

async function loadNotifications() {
    const list = document.getElementById('notification-list');
    if (!list) return;
    try {
        const data = await api.getWarnings();
        const warnings = data.warnings || [];
        if (warnings.length === 0) {
            list.innerHTML = '<div class="empty-state" style="padding:20px;">No active notifications</div>';
            return;
        }
        list.innerHTML = warnings.map(w => `
            <div class="notification-item">
                <div class="notification-icon">⚠</div>
                <div class="notification-text">
                    <strong>${escapeHtml(w.user_name || w.name || 'Intern')}</strong>
                    <span>${escapeHtml(w.message || 'Internship expiring soon')}</span>
                </div>
            </div>
        `).join('');
    } catch (e) {
        list.innerHTML = '<div class="empty-state" style="padding:20px;">Could not load notifications</div>';
    }
}

// =============================================
// DOMAINS
// =============================================

async function loadDomains() {
    try {
        const domains = await api.getDomains();
        const grid = document.getElementById('domains-grid');

        if (!domains || domains.length === 0) {
            grid.innerHTML = '<div class="empty-state">No domains found</div>';
            return;
        }

        grid.innerHTML = domains.map(d => `
            <div class="role-card ${d.is_active ? '' : 'inactive'}">
                <div class="role-card-header">
                    <span class="role-name">${escapeHtml(d.name)}</span>
                </div>
                <p class="role-description">${escapeHtml(d.description || 'No description')}</p>
                <div class="role-meta">
                   <span class="role-users-count">${d.is_active ? 'Active' : 'Inactive'}</span>
                </div>
            </div>
        `).join('');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function showCreateDomainModal() {
    showModal('Create Domain', `
        <form onsubmit="submitCreateDomain(event)">
            <div class="form-group"><label>Name</label><input type="text" id="domain-name" required placeholder="e.g., PIKA, TECH"></div>
            <div class="form-group"><label>Description</label><textarea id="domain-desc" rows="3" placeholder="Optional description"></textarea></div>
            <div class="modal-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Create</button>
            </div>
        </form>
    `);
}

async function submitCreateDomain(e) {
    e.preventDefault();
    try {
        await api.createDomain({
            name: document.getElementById('domain-name').value,
            description: document.getElementById('domain-desc').value
        });
        showToast('Domain created', 'success');
        closeModal();
        loadDomains();
        // Refresh global list for dropdowns
        allDomains = await api.getDomains();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// =============================================
// DIVISIONS
// =============================================

async function loadDivisions() {
    try {
        const divisions = await api.getDivisions();
        const grid = document.getElementById('divisions-grid');

        if (!divisions || divisions.length === 0) {
            grid.innerHTML = '<div class="empty-state">No divisions found</div>';
            return;
        }

        grid.innerHTML = divisions.map(d => `
            <div class="role-card ${d.is_active ? '' : 'inactive'}">
                <div class="role-card-header">
                    <span class="role-name">${escapeHtml(d.name)}</span>
                </div>
                <p class="role-description">${escapeHtml(d.description || 'No description')}</p>
                <div class="role-meta">
                   <span class="role-users-count">${d.is_active ? 'Active' : 'Inactive'}</span>
                </div>
            </div>
        `).join('');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function showCreateDivisionModal() {
    showModal('Create Division', `
        <form onsubmit="submitCreateDivision(event)">
            <div class="form-group"><label>Name</label><input type="text" id="division-name" required placeholder="e.g., Backend, Frontend"></div>
            <div class="form-group"><label>Description</label><textarea id="division-desc" rows="3" placeholder="Optional description"></textarea></div>
            <div class="modal-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Create</button>
            </div>
        </form>
    `);
}

async function submitCreateDivision(e) {
    e.preventDefault();
    try {
        await api.createDivision({
            name: document.getElementById('division-name').value,
            description: document.getElementById('division-desc').value
        });
        showToast('Division created', 'success');
        closeModal();
        loadDivisions();
        // Refresh global list for dropdowns
        allDivisions = await api.getDivisions();
    } catch (err) {
        showToast(err.message, 'error');
    }
}
