document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const loginOverlay = document.getElementById('loginOverlay');
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('usernameInput');
    const displayUsername = document.getElementById('displayUsername');
    const logoutBtn = document.getElementById('logoutBtn');

    const sessionList = document.getElementById('sessionList');
    const newChatBtn = document.getElementById('newChatBtn');
    const currentSessionTitle = document.getElementById('currentSessionTitle');
    
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const attachBtn = document.getElementById('attachBtn');
    const imageUpload = document.getElementById('imageUpload');
    const attachmentPreviewArea = document.getElementById('attachmentPreviewArea');
    const attachmentPreviewImg = document.getElementById('attachmentPreviewImg');
    const removeAttachmentBtn = document.getElementById('removeAttachmentBtn');
    const chatMessages = document.getElementById('chatMessages');
    const loadingIndicator = document.getElementById('loadingIndicator');

    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightboxImg');
    const closeLightbox = document.getElementById('closeLightbox');
    const downloadLink = document.getElementById('downloadLink');

    // State
    let currentSessionId = null;

    // --- Auth Flow ---
    checkAuth();

    async function checkAuth() {
        try {
            const res = await fetch('/auth/me');
            const data = await res.json();
            if (data.logged_in) {
                loginOverlay.classList.remove('active');
                displayUsername.textContent = data.username;
                userInput.disabled = false;
                sendBtn.disabled = false;
                attachBtn.disabled = false;
                loadSessions();
            } else {
                loginOverlay.classList.add('active');
            }
        } catch (e) {
            console.error("Auth check failed", e);
        }
    }

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = usernameInput.value.trim();
        const passwordInput = document.getElementById('passwordInput');
        const password = passwordInput ? passwordInput.value.trim() : '';
        if (!username || !password) return;

        const res = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.success) {
            loginOverlay.classList.remove('active');
            displayUsername.textContent = data.username;
            userInput.disabled = false;
            sendBtn.disabled = false;
            attachBtn.disabled = false;
            loadSessions();
        } else {
            alert(data.error || 'Login failed');
        }
    });

    logoutBtn.addEventListener('click', async () => {
        await fetch('/auth/logout', { method: 'POST' });
        loginOverlay.classList.add('active');
        usernameInput.value = '';
        chatMessages.innerHTML = '';
        sessionList.innerHTML = '';
        currentSessionId = null;
        userInput.disabled = true;
        sendBtn.disabled = true;
        attachBtn.disabled = true;
        clearAttachment();
    });

    // --- Session Flow ---
    async function loadSessions() {
        const res = await fetch('/sessions');
        const sessions = await res.json();
        
        sessionList.innerHTML = '';
        if (sessions.length === 0) {
            createNewSession();
            return;
        }

        sessions.forEach(s => {
            const li = document.createElement('li');
            li.className = 'session-item';
            li.textContent = s.title;
            li.addEventListener('click', () => switchSession(s.id, s.title, li));
            sessionList.appendChild(li);
        });

        // Auto select first
        if (!currentSessionId && sessions.length > 0) {
            switchSession(sessions[0].id, sessions[0].title, sessionList.firstChild);
        }
    }

    async function createNewSession() {
        const res = await fetch('/sessions', { method: 'POST' });
        const s = await res.json();
        chatMessages.innerHTML = '';
        currentSessionId = s.id;
        currentSessionTitle.textContent = s.title;
        loadSessions();
    }

    newChatBtn.addEventListener('click', createNewSession);

    async function switchSession(id, title, element) {
        currentSessionId = id;
        currentSessionTitle.textContent = title;
        
        document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
        if (element) element.classList.add('active');

        chatMessages.innerHTML = '';
        
        // Load messages for session
        const res = await fetch(`/sessions/${id}/messages`);
        const msgs = await res.json();

        if (msgs.length === 0) {
            renderEmptyState();
        } else {
            msgs.forEach(m => {
                if (m.role === 'user') {
                    appendMessage(m.content, 'user', m.uploaded_image_path);
                } else {
                    const kws = m.keywords ? m.keywords.split(', ') : [];
                    appendBotMessage(m.content, kws, m.image_path, m.structured_prompt);
                }
            });
        }
    }

    function renderEmptyState() {
        // Welcome message with username
        const username = displayUsername.textContent || 'Creator';
        const emptyStateHtml = `
            <div class="empty-state-container">
                <div class="empty-state-greeting">Hello, ${username}</div>
                <div class="suggestion-grid">
                    <div class="suggestion-card" onclick="fillSuggestion('A futuristic neon cyberpunk cityscape with flying cars')">
                        <div class="suggestion-icon"><i class="fa-solid fa-city"></i></div>
                        <div class="suggestion-text">A futuristic neon cyberpunk cityscape</div>
                        <div class="suggestion-desc">Explore the future</div>
                    </div>
                    <div class="suggestion-card" onclick="fillSuggestion('A beautiful watercolor landscape of mountains at sunset')">
                        <div class="suggestion-icon"><i class="fa-solid fa-mountain-sun"></i></div>
                        <div class="suggestion-text">A beautiful watercolor landscape</div>
                        <div class="suggestion-desc">Serene aesthetic</div>
                    </div>
                    <div class="suggestion-card" onclick="fillSuggestion('A highly detailed, hyper-realistic cat sitting on the moon')">
                        <div class="suggestion-icon"><i class="fa-solid fa-cat"></i></div>
                        <div class="suggestion-text">A hyper-realistic cat on the moon</div>
                        <div class="suggestion-desc">Dreamscape</div>
                    </div>
                    <div class="suggestion-card" onclick="fillSuggestion('Abstract fluid art with gold and deep blue gradients')">
                        <div class="suggestion-icon"><i class="fa-solid fa-palette"></i></div>
                        <div class="suggestion-text">Abstract fluid art with gold</div>
                        <div class="suggestion-desc">Modern expression</div>
                    </div>
                </div>
            </div>
        `;
        chatMessages.innerHTML = emptyStateHtml;
    }

    window.fillSuggestion = function(text) {
        userInput.value = text;
        userInput.focus();
    };

    // --- Attachment UI Flow ---
    attachBtn.addEventListener('click', () => {
        imageUpload.click();
    });

    imageUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (re) => {
                attachmentPreviewImg.src = re.target.result;
                attachmentPreviewArea.style.display = 'inline-block';
            };
            reader.readAsDataURL(file);
        }
    });

    removeAttachmentBtn.addEventListener('click', (e) => {
        e.preventDefault();
        clearAttachment();
    });

    function clearAttachment() {
        imageUpload.value = '';
        attachmentPreviewArea.style.display = 'none';
        attachmentPreviewImg.src = '';
    }

    // --- Chat Flow ---
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        const file = imageUpload.files[0];
        
        if (!text || !currentSessionId) return;

        // Render locally (for user bubble, we pass base64 preview if it exists)
        const currentPreview = attachmentPreviewImg.src;
        appendMessage(text, 'user', attachmentPreviewArea.style.display !== 'none' ? currentPreview : null);
        
        userInput.value = '';
        userInput.disabled = true;
        sendBtn.disabled = true;
        attachBtn.disabled = true;
        
        const attachFormData = new FormData();
        attachFormData.append('prompt', text);
        attachFormData.append('session_id', currentSessionId);
        if (file) {
            attachFormData.append('image', file);
        }
        
        clearAttachment();
        loadingIndicator.style.display = 'flex';
        scrollToBottom();

        try {
            const res = await fetch('/chat', {
                method: 'POST',
                body: attachFormData
            });
            const data = await res.json();
            
            if (data.error) {
                appendBotMessage(`Error: ${data.error}`);
            } else {
                appendBotMessage(data.content, data.keywords, data.image_path, data.structured_prompt);
                loadSessions(); // refresh title if it was first message
            }
        } catch (err) {
            appendBotMessage(`System error: ${err.message}`);
        } finally {
            loadingIndicator.style.display = 'none';
            userInput.disabled = false;
            sendBtn.disabled = false;
            attachBtn.disabled = false;
            userInput.focus();
            scrollToBottom();
        }
    });

    function appendMessage(text, sender, uploadedImage = null) {
        const div = document.createElement('div');
        div.className = `message ${sender}-message`;
        
        let contentHtml = `<p>${escapeHTML(text)}</p>`;
        if (uploadedImage) {
            contentHtml = `<img src="${uploadedImage}" class="uploaded-image" alt="User Upload"><br>` + contentHtml;
        }
        
        div.innerHTML = `<div class="message-content">${contentHtml}</div>`;
        chatMessages.appendChild(div);
        scrollToBottom();
    }

    function appendBotMessage(text, keywords = [], imageUrl = null, structuredPrompt = null) {
        let h = '';
        
        if (structuredPrompt) {
            h += `<div class="prompt-trace"><i class="fa-solid fa-wand-magic-sparkles"></i> <strong>Enhanced Prompt:</strong> ${escapeHTML(structuredPrompt)}</div>`;
        }
        
        h += `<p>${escapeHTML(text)}</p>`;
        
        if (keywords && keywords.length > 0 && keywords[0] !== "") {
            h += `<div class="keywords-tags">`;
            keywords.forEach(kw => {
                h += `<span class="keyword-tag">${escapeHTML(kw)}</span>`;
            });
            h += `</div>`;
        }

        if (imageUrl) {
            h += `<img src="${imageUrl}" alt="Generated Image" loading="lazy" onclick="openLightbox('${imageUrl}')">`;
        }

        const div = document.createElement('div');
        div.className = 'message bot-message';
        div.innerHTML = `<div class="message-content">${h}</div>`;
        chatMessages.appendChild(div);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function escapeHTML(str) {
        if (!str) return '';
        const p = document.createElement('p');
        p.appendChild(document.createTextNode(str));
        return p.innerHTML;
    }

    // --- Lightbox logic ---
    window.openLightbox = function(url) {
        lightboxImg.src = url;
        downloadLink.href = url;
        lightbox.classList.add('active');
    }

    closeLightbox.addEventListener('click', () => {
        lightbox.classList.remove('active');
    });

    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) {
            lightbox.classList.remove('active');
        }
    });
});
