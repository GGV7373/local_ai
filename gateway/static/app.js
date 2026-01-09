// =============================================================================
// State
// =============================================================================
let token = localStorage.getItem('nora_token');
let currentUser = localStorage.getItem('nora_user');
let config = { assistant_name: 'Nora', company_name: 'My Company' };
let currentFileDir = 'uploads';

// =============================================================================
// Initialization
// =============================================================================
document.addEventListener('DOMContentLoaded', async () => {
    // Load config
    try {
        const res = await fetch('/config');
        config = await res.json();
    } catch (e) {}

    document.getElementById('appTitle').textContent = config.assistant_name + ' AI';
    document.getElementById('mobileTitle').textContent = config.assistant_name + ' AI';
    document.getElementById('companyName').textContent = config.company_name;
    document.title = config.assistant_name + ' AI';

    // Check auth
    if (token) {
        const valid = await verifyToken();
        if (valid) {
            showApp();
        } else {
            showLogin();
        }
    } else {
        showLogin();
    }

    // Setup event listeners
    setupEventListeners();
});

// =============================================================================
// Event Listeners Setup
// =============================================================================
function setupEventListeners() {
    // Login form
    document.getElementById('loginForm').addEventListener('submit', handleLogin);

    // Chat input
    document.getElementById('chatInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // File upload
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    // Modal close on outside click
    document.getElementById('fileModal').addEventListener('click', (e) => {
        if (e.target.id === 'fileModal') closeModal();
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
}

// =============================================================================
// Authentication
// =============================================================================
async function verifyToken() {
    try {
        const res = await fetch('/auth/verify', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const data = await res.json();
            currentUser = data.username;
            return true;
        }
        return false;
    } catch (e) {
        return false;
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('loginError');

    try {
        const res = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (res.ok) {
            const data = await res.json();
            token = data.token;
            currentUser = data.username;
            localStorage.setItem('nora_token', token);
            localStorage.setItem('nora_user', currentUser);
            showApp();
        } else {
            errorEl.textContent = 'Invalid username or password';
            errorEl.style.display = 'block';
        }
    } catch (e) {
        errorEl.textContent = 'Connection error. Please try again.';
        errorEl.style.display = 'block';
    }
}

function logout() {
    token = null;
    currentUser = null;
    localStorage.removeItem('nora_token');
    localStorage.removeItem('nora_user');
    showLogin();
}

function showLogin() {
    document.getElementById('loginPage').style.display = 'flex';
    document.getElementById('appContainer').classList.remove('active');
}

function showApp() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('appContainer').classList.add('active');
    
    // Update user info
    document.getElementById('userName').textContent = currentUser || 'User';
    document.getElementById('userAvatar').textContent = (currentUser || 'U')[0].toUpperCase();

    // Add welcome message
    addMessage(`Hi! I'm ${config.assistant_name}, your AI assistant for ${config.company_name}. How can I help you today?`, 'assistant');
}

// =============================================================================
// Chat
// =============================================================================
function addMessage(text, type) {
    const messages = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'message ' + type;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

function showTyping() {
    const messages = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'typing-indicator';
    div.id = 'typingIndicator';
    div.innerHTML = '<span></span><span></span><span></span>';
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

function hideTyping() {
    const el = document.getElementById('typingIndicator');
    if (el) el.remove();
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, 'user');
    input.value = '';
    document.getElementById('sendBtn').disabled = true;

    showTyping();

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ message: text })
        });

        hideTyping();

        if (res.status === 401) {
            logout();
            return;
        }

        const data = await res.json();
        addMessage(data.response, 'assistant');
    } catch (e) {
        hideTyping();
        addMessage('Sorry, something went wrong. Please try again.', 'assistant');
    }

    document.getElementById('sendBtn').disabled = false;
    input.focus();
}

// =============================================================================
// Files
// =============================================================================
async function loadFiles() {
    const grid = document.getElementById('filesGrid');
    grid.innerHTML = '<div class="loading-spinner"></div>';

    try {
        const res = await fetch(`/files/list?directory=${currentFileDir}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.status === 401) {
            logout();
            return;
        }

        const files = await res.json();
        
        if (files.length === 0) {
            grid.innerHTML = '<p style="color: var(--text-secondary); text-align: center; grid-column: 1/-1;">No files found. Upload some files to get started!</p>';
            return;
        }

        grid.innerHTML = files.map(file => `
            <div class="file-card">
                <div class="file-icon">${getFileIcon(file.type)}</div>
                <div class="file-name">
                    ${escapeHtml(file.name)}
                    ${file.readable ? '<span class="readable-badge">AI Readable</span>' : ''}
                </div>
                <div class="file-meta">
                    ${formatSize(file.size)} • ${formatDate(file.modified)}
                </div>
                <div class="file-actions">
                    <button onclick="viewFile('${escapeHtml(file.path)}')">👁️ View</button>
                    <button onclick="downloadFile('${escapeHtml(file.path)}')">⬇️ Download</button>
                    <button class="delete" onclick="deleteFile('${escapeHtml(file.path)}')">🗑️</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        grid.innerHTML = '<p style="color: var(--danger);">Error loading files</p>';
    }
}

function getFileIcon(type) {
    const icons = {
        'txt': '📄', 'md': '📝', 'json': '📋', 'csv': '📊',
        'pdf': '📕', 'doc': '📘', 'docx': '📘',
        'xls': '📗', 'xlsx': '📗',
        'py': '🐍', 'js': '💛', 'html': '🌐', 'css': '🎨'
    };
    return icons[type] || '📄';
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}

function formatDate(isoDate) {
    return new Date(isoDate).toLocaleDateString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function viewFile(path) {
    try {
        const res = await fetch(`/files/view/${currentFileDir}/${path}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        
        document.getElementById('modalTitle').textContent = data.filename;
        document.getElementById('modalContent').textContent = data.content;
        document.getElementById('fileModal').classList.add('active');
    } catch (e) {
        alert('Error loading file');
    }
}

function downloadFile(path) {
    window.open(`/files/download/${currentFileDir}/${path}`, '_blank');
}

async function deleteFile(path) {
    if (!confirm('Are you sure you want to delete this file?')) return;

    try {
        const res = await fetch(`/files/delete/${currentFileDir}/${path}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            loadFiles();
        } else {
            const data = await res.json();
            alert(data.detail || 'Error deleting file');
        }
    } catch (e) {
        alert('Error deleting file');
    }
}

function closeModal() {
    document.getElementById('fileModal').classList.remove('active');
}

async function handleFiles(files) {
    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('directory', currentFileDir);

        try {
            const res = await fetch('/files/upload', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            if (!res.ok) {
                const data = await res.json();
                alert(`Error uploading ${file.name}: ${data.detail}`);
            }
        } catch (e) {
            alert(`Error uploading ${file.name}`);
        }
    }
    loadFiles();
    document.getElementById('fileInput').value = '';
}

function switchFileTab(dir) {
    currentFileDir = dir;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.dir === dir);
    });
    loadFiles();
}

// =============================================================================
// Stats
// =============================================================================
async function loadStats() {
    const grid = document.getElementById('statsGrid');
    grid.innerHTML = '<div class="loading-spinner"></div>';

    try {
        const res = await fetch('/files/stats', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.status === 401) {
            logout();
            return;
        }

        const stats = await res.json();

        grid.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${stats.company_info.count}</div>
                <div class="stat-label">Company Info Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.uploads.count}</div>
                <div class="stat-label">Uploaded Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.ai_readable_files}</div>
                <div class="stat-label">AI Readable Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${formatSize(stats.total_context_chars)}</div>
                <div class="stat-label">Total Context Size</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${formatSize(stats.company_info.total_size + stats.uploads.total_size)}</div>
                <div class="stat-label">Total Storage Used</div>
            </div>
        `;
    } catch (e) {
        grid.innerHTML = '<p style="color: var(--danger);">Error loading stats</p>';
    }
}

// =============================================================================
// Navigation
// =============================================================================
function switchView(view) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === view);
    });

    // Show/hide views
    document.getElementById('chatView').style.display = view === 'chat' ? 'block' : 'none';
    document.getElementById('filesView').style.display = view === 'files' ? 'block' : 'none';
    document.getElementById('statsView').style.display = view === 'stats' ? 'block' : 'none';

    // Load data
    if (view === 'files') loadFiles();
    if (view === 'stats') loadStats();

    // Close mobile sidebar
    document.getElementById('sidebar').classList.remove('open');
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}
