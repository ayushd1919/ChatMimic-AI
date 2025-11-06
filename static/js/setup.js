// Step navigation
let currentStep = 1;
let selectedFile = null;
let selectedPhoto = null;

// DOM Elements
const fileInput = document.getElementById('chat-file');
const fileUploadArea = document.getElementById('file-upload-area');
const browseButton = document.getElementById('browse-button');
const selectedFileDiv = document.getElementById('selected-file');
const removeFileButton = document.getElementById('remove-file');
const loadingOverlay = document.getElementById('loading-overlay');
const loadingText = document.getElementById('loading-text');

// Step buttons
const nextStep1 = document.getElementById('next-step-1');
const skipUpload = document.getElementById('skip-upload');
const nextStep2 = document.getElementById('next-step-2');
const prevStep2 = document.getElementById('prev-step-2');
const prevStep3 = document.getElementById('prev-step-3');
const submitButton = document.getElementById('submit-button');

// Profile photo elements
const profilePicInput = document.getElementById('profile-pic');
const photoUploadBtn = document.getElementById('photo-upload-btn');
const photoPreview = document.getElementById('photo-preview');
const previewImg = document.getElementById('preview-img');
const removePhotoBtn = document.getElementById('remove-photo');

// File upload handling
browseButton.addEventListener('click', () => {
    fileInput.click();
});

fileUploadArea.addEventListener('click', (e) => {
    if (e.target !== removeFileButton && !selectedFile) {
        fileInput.click();
    }
});

fileUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUploadArea.classList.add('drag-over');
});

fileUploadArea.addEventListener('dragleave', () => {
    fileUploadArea.classList.remove('drag-over');
});

fileUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUploadArea.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    // Validate file
    if (!file.name.endsWith('.txt')) {
        alert('Please select a .txt file');
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
    }

    selectedFile = file;
    console.log('File selected:', file.name, 'Size:', file.size, 'bytes');

    // Update UI
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-size').textContent = formatFileSize(file.size);
    fileUploadArea.style.display = 'none';
    selectedFileDiv.style.display = 'flex';
}

removeFileButton.addEventListener('click', (e) => {
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = '';
    console.log('File removed');
    fileUploadArea.style.display = 'block';
    selectedFileDiv.style.display = 'none';
});

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// Profile photo handling
photoUploadBtn.addEventListener('click', () => {
    profilePicInput.click();
});

profilePicInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        const file = e.target.files[0];

        // Validate file type
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file');
            return;
        }

        // Validate file size (5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('Image size must be less than 5MB');
            return;
        }

        selectedPhoto = file;

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            photoUploadBtn.style.display = 'none';
            photoPreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
});

removePhotoBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    selectedPhoto = null;
    profilePicInput.value = '';
    photoUploadBtn.style.display = 'inline-flex';
    photoPreview.style.display = 'none';
    previewImg.src = '';
});

// Step navigation
function goToStep(step) {
    // Hide all steps
    document.querySelectorAll('.step-content').forEach(content => {
        content.classList.remove('active');
    });

    // Show target step
    document.querySelector(`.step-content[data-step="${step}"]`).classList.add('active');

    // Update progress bar
    document.querySelectorAll('.progress-step').forEach(progressStep => {
        const stepNum = parseInt(progressStep.dataset.step);
        progressStep.classList.remove('active', 'completed');

        if (stepNum < step) {
            progressStep.classList.add('completed');
        } else if (stepNum === step) {
            progressStep.classList.add('active');
        }
    });

    currentStep = step;
    window.scrollTo(0, 0);
}

nextStep1.addEventListener('click', () => {
    // File is now optional - can proceed with or without file
    if (!selectedFile) {
        const confirm = window.confirm('You haven\'t uploaded a chat file. The bot will only use your manual persona description.\n\nFor best results, upload your WhatsApp chat for AI analysis.\n\nContinue without file?');
        if (!confirm) {
            return;
        }
    }
    goToStep(2);
});

// Skip upload button - go directly to next step
skipUpload.addEventListener('click', () => {
    selectedFile = null;
    // Hide selected file if any
    selectedFileDiv.style.display = 'none';
    fileUploadArea.style.display = 'flex';
    goToStep(2);
});

nextStep2.addEventListener('click', () => {
    // Validate step 2
    const userName = document.getElementById('user-name').value.trim();
    const botName = document.getElementById('bot-name').value.trim();
    const relation = document.getElementById('relation').value.trim();
    const apiKey = document.getElementById('api-key').value.trim();

    if (!userName || !botName || !relation || !apiKey) {
        alert('Please fill in all required fields');
        return;
    }

    goToStep(3);
});

prevStep2.addEventListener('click', () => {
    goToStep(1);
});

prevStep3.addEventListener('click', () => {
    goToStep(2);
});

// Persona templates
const personaTemplates = {
    friend: `You are a fun, supportive, and slightly sarcastic best friend.

You're always there for your friend - celebrating their wins and comforting them during tough times.

Common phrases you use:
- "Dude, seriously?"
- "OMG yes!"
- "I'm so proud of you!"
- "That sucks, but you got this"

Your favorite emojis: 😂 😊 🎉 ❤️ 👏

You reply in short, casual messages like texting.

When happy: "Yesss! That's amazing! 🎉"
When supportive: "Hey, you're doing great. Don't be so hard on yourself ❤️"
When teasing: "Oh please, we both know you loved it 😂"`,

    romantic: `You are a loving, caring, and sometimes playful romantic partner.

You express affection warmly but not overly dramatic. You care deeply and show it through your words.

Common phrases you use:
- "Love you ❤️"
- "Miss you"
- "Can't wait to see you"
- "You make me smile"

Your favorite emojis: ❤️ 😘 🥰 ✨ 💕

You reply warmly and affectionately.

When loving: "Just thinking about you ❤️ Hope your day is going well"
When playful: "You're such a dork 😂 but you're MY dork 💕"
When caring: "Are you okay? Want to talk about it? I'm here for you ✨"`,

    professional: `You are a professional, courteous, and efficient colleague.

You communicate clearly and respectfully, focusing on work-related matters while maintaining a friendly tone.

Common phrases you use:
- "Thanks for reaching out"
- "Let me check on that"
- "Happy to help"
- "Looking forward to it"

Your emojis: 👍 ✅ 📧 💼 (used sparingly)

You reply professionally but warmly.

When responding: "Thanks for the update! I'll review and get back to you soon 👍"
When helping: "Happy to help with that. Let me know if you need anything else"
When confirming: "Got it, will work on this today ✅"`
};

document.querySelectorAll('.template-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const template = btn.dataset.template;
        document.getElementById('persona-description').value = personaTemplates[template];
    });
});

// Form submission
document.getElementById('setup-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    // Validate persona
    const personaDescription = document.getElementById('persona-description').value.trim();
    if (!personaDescription) {
        alert('Please provide a persona description');
        return;
    }

    // Show loading
    loadingOverlay.style.display = 'flex';
    if (selectedFile) {
        loadingText.textContent = 'Processing and analyzing your chat...';
    } else {
        loadingText.textContent = 'Creating your chatbot...';
    }

    // Prepare form data
    const formData = new FormData();

    // Add file only if selected (now optional)
    if (selectedFile) {
        console.log('Adding file to form data:', selectedFile.name);
        formData.append('file', selectedFile);
    } else {
        console.log('No file selected, proceeding without chat upload');
    }

    formData.append('user_name', document.getElementById('user-name').value.trim());
    formData.append('bot_name', document.getElementById('bot-name').value.trim());
    formData.append('user_gender', document.getElementById('user-gender').value);
    formData.append('bot_gender', document.getElementById('bot-gender').value);
    formData.append('relation', document.getElementById('relation').value.trim());
    formData.append('language', document.getElementById('language').value);
    formData.append('persona_description', personaDescription);
    formData.append('api_key', document.getElementById('api-key').value.trim());

    // Add profile photo if selected
    if (selectedPhoto) {
        console.log('Adding profile photo:', selectedPhoto.name);
        formData.append('profile_pic', selectedPhoto);
    }

    try {
        if (selectedFile) {
            loadingText.textContent = 'Analyzing conversation patterns with AI...';
        }

        console.log('Sending form data to server...');
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        console.log('Server response status:', response.status);

        const result = await response.json();

        if (result.success) {
            // Display success message
            if (result.has_chat_analysis) {
                loadingText.textContent = `Success! Analyzed ${result.total_messages} messages with deep AI learning!`;
            } else if (result.total_pairs > 0) {
                loadingText.textContent = `Success! Found ${result.total_pairs} conversation pairs!`;
            } else {
                loadingText.textContent = 'ChatBot created successfully!';
            }

            // Store user_id in localStorage
            localStorage.setItem('user_id', result.user_id);
            localStorage.setItem('bot_name', result.bot_name);

            // Redirect to chat page after 2 seconds
            setTimeout(() => {
                window.location.href = '/chat';
            }, 2000);
        } else {
            throw new Error(result.error || 'Failed to process chat');
        }
    } catch (error) {
        console.error('Error:', error);
        loadingOverlay.style.display = 'none';

        // Show detailed error with available names if present
        if (error.message && error.message.includes('participants in the chat')) {
            showDetailedError(error.message);
        } else {
            alert('Error: ' + error.message);
        }
    }
});

// Show detailed error with formatting
function showDetailedError(errorMessage) {
    const modal = document.createElement('div');
    modal.className = 'error-modal';
    modal.innerHTML = `
        <div class="error-modal-content">
            <div class="error-modal-header">
                <span class="material-icons">error_outline</span>
                <h3>Name Mismatch</h3>
            </div>
            <div class="error-modal-body">
                <pre>${errorMessage}</pre>
            </div>
            <div class="error-modal-footer">
                <button class="btn btn-primary" onclick="this.closest('.error-modal').remove()">Got it!</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// API Key Validation
const apiKeyInput = document.getElementById('api-key');
const apiKeyStatus = document.getElementById('api-key-status');
const statusIcon = document.getElementById('status-icon');
const statusText = document.getElementById('status-text');

let validationTimeout = null;
let isApiKeyValid = false;

apiKeyInput.addEventListener('input', () => {
    const apiKey = apiKeyInput.value.trim();

    // Clear previous timeout
    if (validationTimeout) {
        clearTimeout(validationTimeout);
    }

    // Hide status if empty
    if (!apiKey) {
        apiKeyStatus.classList.remove('visible', 'validating', 'valid', 'invalid');
        isApiKeyValid = false;
        return;
    }

    // Show validating status
    apiKeyStatus.classList.remove('valid', 'invalid');
    apiKeyStatus.classList.add('visible', 'validating');
    statusIcon.innerHTML = '⟳';
    statusIcon.classList.add('loading');
    statusText.textContent = 'Validating...';

    // Debounce validation - wait 1 second after user stops typing
    validationTimeout = setTimeout(() => {
        validateApiKey(apiKey);
    }, 1000);
});

async function validateApiKey(apiKey) {
    try {
        const response = await fetch('/api/validate-key', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ api_key: apiKey })
        });

        const result = await response.json();

        statusIcon.classList.remove('loading');

        if (result.valid) {
            // Valid API key
            apiKeyStatus.classList.remove('validating', 'invalid');
            apiKeyStatus.classList.add('valid');
            statusIcon.innerHTML = '✓';
            statusText.textContent = 'Valid!';
            isApiKeyValid = true;
        } else {
            // Invalid API key
            apiKeyStatus.classList.remove('validating', 'valid');
            apiKeyStatus.classList.add('invalid');
            statusIcon.innerHTML = '✗';
            statusText.textContent = result.error || 'Invalid';
            isApiKeyValid = false;
        }
    } catch (error) {
        console.error('Error validating API key:', error);
        statusIcon.classList.remove('loading');
        apiKeyStatus.classList.remove('validating', 'valid');
        apiKeyStatus.classList.add('invalid');
        statusIcon.innerHTML = '✗';
        statusText.textContent = 'Validation failed';
        isApiKeyValid = false;
    }
}

// Update next-step-2 button to check API key validation
const originalNextStep2Handler = nextStep2.onclick;
nextStep2.addEventListener('click', (e) => {
    const apiKey = document.getElementById('api-key').value.trim();

    // If API key is entered but not validated yet, show message
    if (apiKey && !isApiKeyValid) {
        e.preventDefault();
        alert('Please wait for API key validation to complete, or check if the key is valid.');
        return;
    }
});

// Initialize
goToStep(1);
