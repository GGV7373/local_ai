// =============================================================================
// State
// =============================================================================
let token = localStorage.getItem('nora_token');
let currentUser = localStorage.getItem('nora_user');
let config = { assistant_name: 'Nora', company_name: 'My Company' };
let currentFileDir = 'uploads';
let chatHistory = [];
let savedChats = JSON.parse(localStorage.getItem('nora_saved_chats') || '[]');
let providers = [];
let currentProvider = localStorage.getItem('nora_provider') || 'ollama';
let currentModel = localStorage.getItem('nora_model') || '';
let currentLanguage = localStorage.getItem('nora_language') || 'en';
let currentChatId = null;

// =============================================================================
// Toast Notifications
// =============================================================================
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '✕' : type === 'warning' ? '⚠' : 'ℹ'}</span>
        <span class="toast-message">${escapeHtml(message)}</span>
    `;
    container.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    document.body.appendChild(container);
    return container;
}

// =============================================================================
// Markdown Rendering
// =============================================================================
function renderMarkdown(text) {
    // Code blocks with language
    text = text.replace(/```(\w+)?\n([\s\S]*?)```/g, (_, lang, code) => 
        `<pre class="code-block${lang ? ` language-${lang}` : ''}"><code>${escapeHtml(code.trim())}</code></pre>`
    );
    // Inline code
    text = text.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    // Bold
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // Italic
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    // Headers
    text = text.replace(/^### (.+)$/gm, '<h4>$1</h4>');
    text = text.replace(/^## (.+)$/gm, '<h3>$1</h3>');
    text = text.replace(/^# (.+)$/gm, '<h2>$1</h2>');
    // Lists
    text = text.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    // Numbered lists
    text = text.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
    // Links
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    // Line breaks (preserve paragraphs)
    text = text.replace(/\n\n/g, '</p><p>');
    text = text.replace(/\n/g, '<br>');
    
    return `<p>${text}</p>`;
}

// =============================================================================
// Initialization
// =============================================================================
document.addEventListener('DOMContentLoaded', async () => {
    // If no token, show login immediately
    if (!token) {
        showLogin();
    }
    
    // Load config
    try {
        const res = await fetch('/config');
        config = await res.json();
    } catch (e) {}

    document.getElementById('appTitle').textContent = config.assistant_name + ' AI';
    document.getElementById('mobileTitle').textContent = config.assistant_name + ' AI';
    document.getElementById('companyName').textContent = config.company_name;
    document.title = config.assistant_name + ' AI';

    // Load providers
    await loadProviders();
    
    // Load saved language preference
    const langSelect = document.getElementById('languageSelect');
    if (langSelect) {
        langSelect.value = currentLanguage;
    }

    // Check auth - only if we have a token
    if (token) {
        const valid = await verifyToken();
        if (valid) {
            showApp();
        } else {
            showLogin();
        }
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

    // Add welcome message based on language
    const greeting = currentLanguage === 'no' 
        ? `Hei! Jeg er ${config.assistant_name}, din AI-assistent for ${config.company_name}. Hvordan kan jeg hjelpe deg i dag?`
        : `Hi! I'm ${config.assistant_name}, your AI assistant for ${config.company_name}. How can I help you today?`;
    addMessage(greeting, 'assistant');
}

// =============================================================================
// Chat
// =============================================================================
function addMessage(text, type, isMarkdown = false) {
    const messages = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'message ' + type;
    
    if (type === 'assistant' && isMarkdown) {
        div.innerHTML = renderMarkdown(text);
    } else {
        div.textContent = text;
    }
    
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    
    // Store in history
    chatHistory.push({ role: type, content: text });
}

function clearChat() {
    const messages = document.getElementById('messages');
    messages.innerHTML = '';
    chatHistory = [];
    currentChatId = null;
    const greeting = currentLanguage === 'no' 
        ? `Hei! Jeg er ${config.assistant_name}, din AI-assistent for ${config.company_name}. Hvordan kan jeg hjelpe deg i dag?`
        : `Hi! I'm ${config.assistant_name}, your AI assistant for ${config.company_name}. How can I help you today?`;
    addMessage(greeting, 'assistant');
    showToast(currentLanguage === 'no' ? 'Chat tømt' : 'Chat cleared', 'success');
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
            body: JSON.stringify({ 
                message: text,
                provider: currentProvider,
                model: currentModel || null,
                language: currentLanguage
            })
        });

        hideTyping();

        if (res.status === 401) {
            logout();
            return;
        }

        const data = await res.json();
        addMessage(data.response, 'assistant', true);
        
        // Show warning if there was an error but we got a response
        if (data.success === false && data.error_type === 'connection') {
            showToast(currentLanguage === 'no' ? 'Tilkoblingsproblem - sjekk Ollama' : 'Connection issue - check Ollama', 'warning', 5000);
        }
    } catch (e) {
        hideTyping();
        const errorMsg = currentLanguage === 'no' 
            ? 'Beklager, noe gikk galt. Vennligst prøv igjen.'
            : 'Sorry, something went wrong. Please try again.';
        addMessage(errorMsg, 'assistant');
        showToast(currentLanguage === 'no' ? 'Kunne ikke sende melding' : 'Failed to send message', 'error');
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
        const content = document.getElementById('modalContent');
        
        // Apply markdown rendering for certain file types
        if (path.endsWith('.md')) {
            content.innerHTML = renderMarkdown(data.content);
        } else {
            content.textContent = data.content;
        }
        
        document.getElementById('fileModal').classList.add('active');
    } catch (e) {
        showToast('Error loading file', 'error');
    }
}

async function downloadFile(path) {
    try {
        const res = await fetch(`/files/download/${currentFileDir}/${path}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!res.ok) {
            showToast('Error downloading file', 'error');
            return;
        }
        
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = path;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        showToast('Download started', 'success');
    } catch (e) {
        showToast('Error downloading file', 'error');
    }
}

async function deleteFile(path) {
    if (!confirm('Are you sure you want to delete this file?')) return;

    try {
        const res = await fetch(`/files/delete/${currentFileDir}/${path}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            showToast('File deleted successfully', 'success');
            loadFiles();
        } else {
            const data = await res.json();
            showToast(data.detail || 'Error deleting file', 'error');
        }
    } catch (e) {
        showToast('Error deleting file', 'error');
    }
}

function closeModal() {
    document.getElementById('fileModal').classList.remove('active');
}

async function handleFiles(files) {
    const uploadCount = files.length;
    let successCount = 0;
    let errorCount = 0;
    
    showToast(`Uploading ${uploadCount} file(s)...`, 'info');
    
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

            if (res.ok) {
                successCount++;
            } else {
                errorCount++;
                const data = await res.json();
                showToast(`Error uploading ${file.name}: ${data.detail}`, 'error');
            }
        } catch (e) {
            errorCount++;
            showToast(`Error uploading ${file.name}`, 'error');
        }
    }
    
    if (successCount > 0) {
        showToast(`Successfully uploaded ${successCount} file(s)`, 'success');
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
    document.getElementById('historyView').style.display = view === 'history' ? 'block' : 'none';
    document.getElementById('filesView').style.display = view === 'files' ? 'block' : 'none';
    document.getElementById('statsView').style.display = view === 'stats' ? 'block' : 'none';

    // Load data
    if (view === 'files') loadFiles();
    if (view === 'stats') loadStats();
    if (view === 'history') loadChatHistory();

    // Close mobile sidebar
    document.getElementById('sidebar').classList.remove('open');
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// =============================================================================
// AI Provider Selection
// =============================================================================
async function loadProviders() {
    try {
        const res = await fetch('/providers');
        const data = await res.json();
        providers = data.providers;
        
        // Set defaults from server if not stored locally
        if (!localStorage.getItem('nora_provider')) {
            currentProvider = data.default_provider;
        }
        
        updateProviderUI();
    } catch (e) {
        console.error('Failed to load providers:', e);
    }
}

function updateProviderUI() {
    const providerSelect = document.getElementById('providerSelect');
    const modelSelect = document.getElementById('modelSelect');
    
    if (!providerSelect || !modelSelect) return;
    
    // Update provider dropdown
    providerSelect.innerHTML = providers.map(p => {
        const icon = p.id === 'ollama' ? '🖥️' : '✨';
        const status = p.status === 'available' ? '' : p.status === 'not_configured' ? ' (No API Key)' : ' (Offline)';
        return `<option value="${p.id}" ${p.status !== 'available' ? 'disabled' : ''}>${icon} ${p.name}${status}</option>`;
    }).join('');
    
    providerSelect.value = currentProvider;
    
    // Update model dropdown for selected provider
    updateModelDropdown();
}

function updateModelDropdown() {
    const modelSelect = document.getElementById('modelSelect');
    const provider = providers.find(p => p.id === currentProvider);
    
    if (!provider || !modelSelect) return;
    
    modelSelect.innerHTML = '<option value="">Default Model</option>' + 
        provider.models.map(m => `<option value="${m}">${m}</option>`).join('');
    
    if (currentModel && provider.models.includes(currentModel)) {
        modelSelect.value = currentModel;
    }
}

function onProviderChange() {
    const providerSelect = document.getElementById('providerSelect');
    currentProvider = providerSelect.value;
    localStorage.setItem('nora_provider', currentProvider);
    
    updateModelDropdown();
    
    const provider = providers.find(p => p.id === currentProvider);
    showToast(`Switched to ${provider?.name || currentProvider}`, 'success');
}

function onModelChange() {
    const modelSelect = document.getElementById('modelSelect');
    currentModel = modelSelect.value;
    localStorage.setItem('nora_model', currentModel);
    
    if (currentModel) {
        showToast(`Using model: ${currentModel}`, 'info');
    }
}

// =============================================================================
// Language Selection
// =============================================================================
function onLanguageChange() {
    const langSelect = document.getElementById('languageSelect');
    currentLanguage = langSelect.value;
    localStorage.setItem('nora_language', currentLanguage);
    
    const langName = currentLanguage === 'no' ? 'Norsk' : 'English';
    showToast(currentLanguage === 'no' ? `Språk endret til ${langName}` : `Language changed to ${langName}`, 'success');
}

// =============================================================================
// Chat History Management
// =============================================================================
function saveCurrentChat() {
    if (chatHistory.length <= 1) {
        showToast(currentLanguage === 'no' ? 'Ingen samtale å lagre' : 'No conversation to save', 'warning');
        return;
    }
    
    const chatId = currentChatId || Date.now().toString();
    const firstUserMsg = chatHistory.find(m => m.role === 'user');
    const title = firstUserMsg ? firstUserMsg.content.substring(0, 50) + (firstUserMsg.content.length > 50 ? '...' : '') : 'Untitled Chat';
    
    const chatData = {
        id: chatId,
        title: title,
        timestamp: new Date().toISOString(),
        messages: [...chatHistory],
        provider: currentProvider,
        model: currentModel,
        language: currentLanguage
    };
    
    // Update or add chat
    const existingIndex = savedChats.findIndex(c => c.id === chatId);
    if (existingIndex >= 0) {
        savedChats[existingIndex] = chatData;
    } else {
        savedChats.unshift(chatData);
    }
    
    // Keep only last 50 chats
    if (savedChats.length > 50) {
        savedChats = savedChats.slice(0, 50);
    }
    
    localStorage.setItem('nora_saved_chats', JSON.stringify(savedChats));
    currentChatId = chatId;
    
    showToast(currentLanguage === 'no' ? 'Samtale lagret!' : 'Chat saved!', 'success');
}

function loadChatHistory() {
    const historyList = document.getElementById('historyList');
    savedChats = JSON.parse(localStorage.getItem('nora_saved_chats') || '[]');
    
    if (savedChats.length === 0) {
        historyList.innerHTML = `
            <div class="empty-history">
                <span class="empty-icon">💬</span>
                <p>${currentLanguage === 'no' ? 'Ingen lagrede samtaler ennå.' : 'No saved chats yet.'}</p>
                <p style="font-size: 0.9rem; color: var(--text-secondary);">${currentLanguage === 'no' ? 'Start en samtale og klikk "Lagre" for å beholde den!' : 'Start a conversation and click "Save" to keep it!'}</p>
            </div>
        `;
        return;
    }
    
    historyList.innerHTML = savedChats.map(chat => {
        const date = new Date(chat.timestamp).toLocaleDateString();
        const time = new Date(chat.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const msgCount = chat.messages.filter(m => m.role === 'user').length;
        const providerIcon = chat.provider === 'gemini' ? '✨' : '🖥️';
        
        return `
            <div class="history-card" data-id="${chat.id}">
                <div class="history-card-header">
                    <h3 class="history-title">${escapeHtml(chat.title)}</h3>
                    <span class="history-provider">${providerIcon}</span>
                </div>
                <div class="history-meta">
                    <span>📅 ${date} ${time}</span>
                    <span>💬 ${msgCount} ${currentLanguage === 'no' ? 'meldinger' : 'messages'}</span>
                    <span>${chat.language === 'no' ? '🇳🇴' : '🇬🇧'}</span>
                </div>
                <div class="history-actions">
                    <button class="action-btn" onclick="loadSavedChat('${chat.id}')">${currentLanguage === 'no' ? '📂 Åpne' : '📂 Open'}</button>
                    <button class="action-btn delete" onclick="deleteSavedChat('${chat.id}')">${currentLanguage === 'no' ? '🗑️ Slett' : '🗑️ Delete'}</button>
                </div>
            </div>
        `;
    }).join('');
}

function loadSavedChat(chatId) {
    const chat = savedChats.find(c => c.id === chatId);
    if (!chat) {
        showToast(currentLanguage === 'no' ? 'Samtale ikke funnet' : 'Chat not found', 'error');
        return;
    }
    
    // Clear current chat
    const messages = document.getElementById('messages');
    messages.innerHTML = '';
    chatHistory = [];
    currentChatId = chatId;
    
    // Set language and provider from saved chat
    if (chat.language) {
        currentLanguage = chat.language;
        localStorage.setItem('nora_language', currentLanguage);
        document.getElementById('languageSelect').value = currentLanguage;
    }
    if (chat.provider) {
        currentProvider = chat.provider;
        localStorage.setItem('nora_provider', currentProvider);
        document.getElementById('providerSelect').value = currentProvider;
        updateModelDropdown();
    }
    if (chat.model) {
        currentModel = chat.model;
        localStorage.setItem('nora_model', currentModel);
        document.getElementById('modelSelect').value = currentModel;
    }
    
    // Restore messages
    chat.messages.forEach(msg => {
        addMessage(msg.content, msg.role, msg.role === 'assistant');
    });
    
    // Switch to chat view
    switchView('chat');
    showToast(currentLanguage === 'no' ? 'Samtale lastet!' : 'Chat loaded!', 'success');
}

function deleteSavedChat(chatId) {
    const confirmMsg = currentLanguage === 'no' ? 'Er du sikker på at du vil slette denne samtalen?' : 'Are you sure you want to delete this chat?';
    if (!confirm(confirmMsg)) return;
    
    savedChats = savedChats.filter(c => c.id !== chatId);
    localStorage.setItem('nora_saved_chats', JSON.stringify(savedChats));
    
    if (currentChatId === chatId) {
        currentChatId = null;
    }
    
    loadChatHistory();
    showToast(currentLanguage === 'no' ? 'Samtale slettet' : 'Chat deleted', 'success');
}

function exportAllChats() {
    if (savedChats.length === 0) {
        showToast(currentLanguage === 'no' ? 'Ingen samtaler å eksportere' : 'No chats to export', 'warning');
        return;
    }
    
    const dataStr = JSON.stringify(savedChats, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `nora-chat-history-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast(currentLanguage === 'no' ? 'Samtaler eksportert!' : 'Chats exported!', 'success');
}
