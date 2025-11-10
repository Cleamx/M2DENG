const chatForm = document.getElementById('chatForm');
const questionInput = document.getElementById('questionInput');
const chatMessages = document.getElementById('chatMessages');
const sendButton = document.getElementById('sendButton');
const buttonText = document.getElementById('buttonText');
const buttonLoader = document.getElementById('buttonLoader');
const API_URL = 'http://localhost:3000';


function addMessage(content, isUser = false, sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    if (isUser) {
        messageContent.innerHTML = `<strong>Vous:</strong><p>${escapeHtml(content)}</p>`;
    } else {
        messageContent.innerHTML = `<strong>Assistant:</strong><p>${escapeHtml(content)}</p>`;

        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources';
            sourcesDiv.innerHTML = '<h4>📚 Sources utilisées:</h4>';

            sources.forEach((source, index) => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                sourceItem.innerHTML = `
                    <div class="source-similarity">Similarité: ${(source.similarity * 100).toFixed(1)}%</div>
                    <div>${escapeHtml(source.text.substring(0, 150))}${source.text.length > 150 ? '...' : ''}</div>
                `;
                sourcesDiv.appendChild(sourceItem);
            });

            messageContent.appendChild(sourcesDiv);
        }
    }

    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function setLoading(loading) {
    sendButton.disabled = loading;
    questionInput.disabled = loading;
    if (loading) {
        buttonText.classList.add('hidden');
        buttonLoader.classList.remove('hidden');
    } else {
        buttonText.classList.remove('hidden');
        buttonLoader.classList.add('hidden');
    }
}

async function sendQuestion(question) {
    try {
        setLoading(true);

        const response = await fetch(`${API_URL}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });

        if (!response.ok) {
            throw new Error('Erreur lors de la communication avec le serveur');
        }

        const data = await response.json();
        if (data.success) {
            addMessage(data.answer, false, data.sources);
        } else {
            addMessage('Désolé, une erreur est survenue: ' + data.error, false);
        }

    } catch (error) {
        console.error('Erreur:', error);
        addMessage('Désolé, je n\'ai pas pu traiter votre question. Vérifiez que le serveur est bien démarré.', false);
    } finally {
        setLoading(false);
    }
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const question = questionInput.value.trim();
    if (question === '') {
        return;
    }

    addMessage(question, true);
    questionInput.value = '';
    await sendQuestion(question);
});

questionInput.focus();
