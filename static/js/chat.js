// Chat state
let userId = null;
let botName = null;
let chatHistory = [];

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const voiceButton = document.getElementById('voice-button');
const typingIndicator = document.getElementById('typing-indicator');
const contactNameEl = document.getElementById('contact-name');
const errorModal = document.getElementById('error-modal');
const errorMessage = document.getElementById('error-message');
const closeErrorButton = document.getElementById('close-error');

// Initialize
async function init() {
    // Get user_id from localStorage
    userId = localStorage.getItem('user_id');
    botName = localStorage.getItem('bot_name');

    if (!userId) {
        showError('No session found. Please complete setup first.');
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
        return;
    }

    // Load config
    try {
        const response = await fetch(`/api/config/${userId}`);
        const result = await response.json();

        if (result.success) {
            const config = result.config;
            botName = config.bot_name;
            contactNameEl.textContent = config.bot_name;
            localStorage.setItem('bot_name', botName);

            // Set profile photo if available
            if (config.profile_pic) {
                console.log('Profile pic path:', config.profile_pic);
                const profilePicEl = document.getElementById('profile-pic');
                const img = document.createElement('img');
                img.src = config.profile_pic;
                img.alt = botName;
                img.onerror = function() {
                    // If image fails to load, keep default icon
                    console.error('Failed to load profile picture:', config.profile_pic);
                };
                img.onload = function() {
                    // Replace content only when image loads successfully
                    console.log('Profile picture loaded successfully');
                    profilePicEl.innerHTML = '';
                    profilePicEl.appendChild(img);
                };
            } else {
                console.log('No profile picture in config');
            }

            // Add natural welcome message from bot
            sendWelcomeGreeting(config);
        } else {
            throw new Error('Failed to load configuration');
        }
    } catch (error) {
        console.error('Error loading config:', error);
        showError('Failed to load chat configuration');
    }

    // Focus input
    messageInput.focus();
}

async function sendWelcomeGreeting(config) {
    // Send a natural greeting from the bot using the API
    showTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: "Hi", // Simple trigger to get bot's natural greeting
                history: [],
                user_id: userId
            })
        });

        const text = await response.text();
        if (!text) {
            throw new Error('Empty response from server');
        }

        const result = JSON.parse(text);
        hideTypingIndicator();

        if (result.success && result.reply) {
            // Add bot's natural greeting
            setTimeout(() => {
                addMessage(result.reply, 'received');

                // Add to history
                chatHistory.push({
                    role: 'user',
                    content: "Hi"
                });
                chatHistory.push({
                    role: 'assistant',
                    content: result.reply
                });
            }, 300);
        } else {
            // Fallback if API fails
            setTimeout(() => {
                addMessage('Hi! 👋', 'received');
            }, 300);
        }
    } catch (error) {
        console.error('Error getting welcome greeting:', error);
        hideTypingIndicator();
        // Fallback greeting
        setTimeout(() => {
            addMessage('Hi! 👋', 'received');
        }, 300);
    }
}

// Message handling
function addMessage(text, type = 'sent') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = text;

    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = getCurrentTime();

    if (type === 'sent') {
        const checkIcon = document.createElement('span');
        checkIcon.className = 'material-icons';
        checkIcon.textContent = 'done_all';
        timeDiv.appendChild(checkIcon);
    }

    bubble.appendChild(messageText);
    bubble.appendChild(timeDiv);
    messageDiv.appendChild(bubble);

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function getCurrentTime() {
    const now = new Date();
    let hours = now.getHours();
    const minutes = now.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';

    hours = hours % 12;
    hours = hours ? hours : 12;
    const minutesStr = minutes < 10 ? '0' + minutes : minutes;

    return `${hours}:${minutesStr} ${ampm}`;
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    typingIndicator.style.display = 'block';
    scrollToBottom();
}

function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

function showError(message) {
    errorMessage.textContent = message;
    errorModal.style.display = 'flex';
}

function hideError() {
    errorModal.style.display = 'none';
}

// Send message
async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message) return;

    // Add user message to UI
    addMessage(message, 'sent');

    // Add to history
    chatHistory.push({
        role: 'user',
        content: message
    });

    // Clear input
    messageInput.value = '';
    toggleSendButton();

    // Show typing indicator
    showTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                history: chatHistory.slice(-10), // Send last 10 messages for context
                user_id: userId
            })
        });

        // Check if response is ok
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Check if response has content
        const text = await response.text();
        if (!text) {
            throw new Error('Empty response from server');
        }

        const result = JSON.parse(text);

        hideTypingIndicator();

        if (result.success && result.reply) {
            // Add bot reply to UI
            addMessage(result.reply, 'received');

            // Add to history
            chatHistory.push({
                role: 'assistant',
                content: result.reply
            });
        } else {
            throw new Error(result.error || 'Failed to get response');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        addMessage('Sorry, I encountered an error. Please try again.', 'received');
    }
}

// Input handling
messageInput.addEventListener('input', toggleSendButton);

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
    }
});

sendButton.addEventListener('click', sendMessage);

voiceButton.addEventListener('click', () => {
    // Voice message functionality - not implemented yet
    addMessage('Voice messages are not available yet!', 'received');
});

function toggleSendButton() {
    const hasText = messageInput.value.trim().length > 0;

    if (hasText) {
        sendButton.style.display = 'flex';
        voiceButton.style.display = 'none';
    } else {
        sendButton.style.display = 'none';
        voiceButton.style.display = 'flex';
    }
}

// Error modal
closeErrorButton.addEventListener('click', hideError);

errorModal.addEventListener('click', (e) => {
    if (e.target === errorModal) {
        hideError();
    }
});

// Update date
function updateDate() {
    const dateLabel = document.getElementById('date-label');
    const today = new Date();
    const options = { month: 'long', day: 'numeric', year: 'numeric' };
    dateLabel.textContent = today.toLocaleDateString('en-US', options);
}

// Initialize app
updateDate();
init();
