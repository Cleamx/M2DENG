// ===== DOM Elements =====
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const messagesContainer = document.getElementById('messages');
const sendButton = document.getElementById('sendButton');
const videoModal = document.getElementById('videoModal');
const videoContainer = document.getElementById('videoContainer');

// ===== Conversation History =====
let conversationHistory = [];

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    userInput.focus();

    // Add initial system message to history
    conversationHistory.push({
        role: 'system',
        content: CONFIG.SYSTEM_PROMPT
    });
});

// ===== Form Submit Handler =====
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const message = userInput.value.trim();
    if (!message) return;

    // Disable input while processing
    setInputState(false);

    // Add user message to UI
    addMessage(message, 'user');

    // Clear input
    userInput.value = '';

    // Add to conversation history
    conversationHistory.push({
        role: 'user',
        content: message
    });

    // Show video modal while waiting
    showVideoModal();

    try {
        // Call Mistral API
        const response = await callMistralAPI(message);

        // Hide video modal
        hideVideoModal();

        // Add bot response to UI
        addMessage(response, 'bot');

        // Add to conversation history
        conversationHistory.push({
            role: 'assistant',
            content: response
        });

    } catch (error) {
        console.error('Error:', error);
        hideVideoModal();
        addMessage(`Désolé, une erreur s'est produite: ${error.message}`, 'bot');
    }

    // Re-enable input
    setInputState(true);
    userInput.focus();
});

// ===== Add Message to UI =====
function addMessage(content, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    const avatar = sender === 'bot' ? '🤖' : '👤';

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <p>${escapeHtml(content)}</p>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    scrollToBottom();
}

// ===== Scroll to Bottom =====
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ===== Escape HTML =====
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

// ===== Set Input State =====
function setInputState(enabled) {
    userInput.disabled = !enabled;
    sendButton.disabled = !enabled;
}

// ===== Show Video Modal =====
function showVideoModal() {
    // Clear previous content
    videoContainer.innerHTML = '';

    // Start a random mini-game!
    GAMES.start(videoContainer);

    // Show modal
    videoModal.classList.add('active');
}

// ===== Hide Video Modal =====
function hideVideoModal() {
    videoModal.classList.remove('active');

    // Stop any running game
    GAMES.stop();

    // Stop any playing videos
    const video = videoContainer.querySelector('video');
    if (video) {
        video.pause();
        video.src = '';
    }

    // Clear container
    videoContainer.innerHTML = '';
}

// ===== Call Mistral API =====
async function callMistralAPI(userMessage) {
    const response = await fetch(CONFIG.MISTRAL_API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${CONFIG.MISTRAL_API_KEY}`
        },
        body: JSON.stringify({
            model: CONFIG.MISTRAL_MODEL,
            messages: conversationHistory,
            temperature: 0.7,
            max_tokens: 1024
        })
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `API Error: ${response.status}`);
    }

    const data = await response.json();

    if (data.choices && data.choices.length > 0) {
        return data.choices[0].message.content;
    }

    throw new Error('No response from API');
}

// ===== Keyboard Shortcuts =====
document.addEventListener('keydown', (e) => {
    // Escape to close video modal (if somehow needed)
    if (e.key === 'Escape' && videoModal.classList.contains('active')) {
        // Don't close during API call - just for safety
    }
});
