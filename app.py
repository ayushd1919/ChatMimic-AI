import os
import re
import json
import random
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)  # For session management

# CORS Configuration
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True,
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Configuration
UPLOAD_FOLDER = 'uploads'
USER_DATA_FOLDER = 'user_data'
PROFILE_PICS_FOLDER = 'static/images/profiles'
ALLOWED_EXTENSIONS = {'txt'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['USER_DATA_FOLDER'] = USER_DATA_FOLDER
app.config['PROFILE_PICS_FOLDER'] = PROFILE_PICS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Gemini API Configuration
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL = "gemini-2.0-flash-exp"
API_TIMEOUT_SECONDS = 30

# Fallback messages
FALLBACK_MESSAGES = [
    "Hmm, I didn't get that.",
    "Can you say that again?",
    "Sorry, something went wrong.",
    "Let me think... try again?"
]

DEBUG_MODE = os.environ.get("FLASK_DEBUG_MODE", "True").lower() == "true"

# Ensure necessary directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(USER_DATA_FOLDER, exist_ok=True)
os.makedirs(PROFILE_PICS_FOLDER, exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/images', exist_ok=True)


def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_image(filename):
    """Check if uploaded image has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def extract_sender_names(file_path):
    """Extract all unique sender names from WhatsApp chat - flexible version"""
    sender_names = set()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # More flexible patterns matching the parser
        patterns = [
            r'\[(?:\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}),?\s*(?:\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\]\s*([^:]+?):',
            r'(?:\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}),?\s*(?:\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\s*[-–]\s*([^:]+?):',
            r'\[(?:\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s+(?:\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:]+?):',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches and len(matches) > 5:
                for sender in matches:
                    sender = sender.strip()
                    if sender and len(sender) > 0 and len(sender) < 100:  # Reasonable name length
                        sender_names.add(sender)
                break

        return list(sender_names)
    except Exception as e:
        print(f"ERROR: Failed to extract sender names: {e}")
        return []


def fuzzy_match_name(input_name, actual_names):
    """
    Try to match input name with actual names using fuzzy matching
    Returns the best match or None
    """
    input_lower = input_name.lower().strip()

    # First try exact match (case insensitive)
    for name in actual_names:
        if name.lower().strip() == input_lower:
            return name

    # Try partial match - if input is contained in any name
    for name in actual_names:
        if input_lower in name.lower():
            return name

    # Try if any name is contained in input
    for name in actual_names:
        if name.lower().strip() in input_lower:
            return name

    # Try first word match
    input_first = input_lower.split()[0] if input_lower else ""
    for name in actual_names:
        name_first = name.lower().strip().split()[0] if name else ""
        if input_first and name_first and input_first == name_first:
            return name

    return None


def parse_whatsapp_chat(file_path, user_name, bot_name):
    """
    Parse WhatsApp chat export and extract conversation pairs
    Now more flexible - tries multiple formats and auto-detects participants
    """
    qa_pairs = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if DEBUG_MODE:
            print(f"DEBUG: File size: {len(content)} characters")
            # Safely print first 500 chars (handle unicode)
            try:
                sample = content[:500].encode('utf-8', errors='replace').decode('utf-8')
                print(f"DEBUG: First 500 chars:\n{sample}")
            except:
                print(f"DEBUG: First 500 chars contain special characters, skipping display")

        # Try multiple WhatsApp date/time patterns (more flexible)
        patterns = [
            # Format: M/D/YY, HH:MM - Name: Message (YOUR FORMAT - US style with dash)
            r'(\d{1,2}/\d{1,2}/\d{2}),\s*(\d{1,2}:\d{2})\s*-\s*([^:]+?):\s*(.+?)(?=\n\d{1,2}/|\Z)',
            # Format: [DD/MM/YY, HH:MM:SS AM/PM] Name: Message
            r'\[(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\]\s*([^:]+?):\s*(.+?)(?=\n\[|\Z)',
            # Format: DD/MM/YY, HH:MM AM/PM - Name: Message
            r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\s*[-–]\s*([^:]+?):\s*(.+?)(?=\n\d{1,2}[\/\-\.]|\Z)',
            # Format: DD/MM/YYYY, HH:MM - Name: Message (24-hour)
            r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4}),?\s*(\d{1,2}:\d{2})\s*[-–]\s*([^:]+?):\s*(.+?)(?=\n\d{1,2}[\/\-\.]|\Z)',
            # Format: [DD/MM/YYYY HH:MM:SS] Name: Message
            r'\[(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s+(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:]+?):\s*(.+?)(?=\n\[|\Z)',
        ]

        messages = []
        matched_pattern = None

        for pattern_idx, pattern in enumerate(patterns):
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            if matches and len(matches) > 5:  # Need at least 5 messages
                if DEBUG_MODE:
                    print(f"DEBUG: Pattern {pattern_idx + 1} matched! Found {len(matches)} messages")

                for match in matches:
                    if len(match) >= 4:
                        date, time, sender, message = match[0], match[1], match[2], match[3]
                        message = message.strip()
                        sender = sender.strip()

                        # Skip empty messages
                        if not message:
                            continue

                        # Skip system messages
                        if any(skip in message.lower() for skip in [
                            'media omitted', 'deleted this message', 'missed voice call',
                            'missed video call', 'changed the subject', 'changed this group',
                            'left', 'added', 'removed', 'security code changed', 'message deleted',
                            'end-to-end encrypted', 'disappearing messages'
                        ]):
                            continue

                        if len(message) > 0 and len(sender) > 0:
                            messages.append({
                                'sender': sender,
                                'message': message
                            })

                matched_pattern = pattern_idx + 1
                break

        if DEBUG_MODE:
            print(f"DEBUG: Total valid messages extracted: {len(messages)}", flush=True)

        if len(messages) == 0:
            # Try to extract at least some sample to show user
            sample_lines = content.split('\n')[:20]

            # Write debug file to help diagnose
            try:
                debug_file = os.path.join(USER_DATA_FOLDER, 'debug_chat_format.txt')
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write("First 50 lines of uploaded chat:\n")
                    f.write("="*50 + "\n")
                    f.write('\n'.join(content.split('\n')[:50]))
                print(f"DEBUG: Wrote sample to {debug_file}")
            except Exception as e:
                print(f"DEBUG: Could not write debug file: {e}")

            return [], 0, [], sample_lines

        # Count messages per sender
        sender_counts = {}
        for msg in messages:
            sender = msg['sender']
            sender_counts[sender] = sender_counts.get(sender, 0) + 1

        # Get top 2 senders (most active participants)
        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        all_senders = [s[0] for s in top_senders]

        if DEBUG_MODE:
            # Print without emojis to avoid console encoding issues
            try:
                print(f"DEBUG: Top participants (count): {[(s[0].encode('ascii', 'ignore').decode(), s[1]) for s in top_senders]}", flush=True)
            except:
                print(f"DEBUG: Found {len(top_senders)} participants", flush=True)

        # Try to match the input names with actual names (fuzzy matching)
        matched_user_name = fuzzy_match_name(user_name, all_senders) if user_name else None
        matched_bot_name = fuzzy_match_name(bot_name, all_senders) if bot_name else None

        if DEBUG_MODE:
            print(f"DEBUG: Fuzzy match - User input: '{user_name}', Bot input: '{bot_name}'", flush=True)
            print(f"DEBUG: Match found: User={matched_user_name is not None}, Bot={matched_bot_name is not None}", flush=True)

        # If no match found, try to use top 2 participants
        if not matched_user_name and len(all_senders) > 0:
            matched_user_name = all_senders[0]
            if DEBUG_MODE:
                print(f"DEBUG: Auto-selected user as top participant (has emoji)", flush=True)

        if not matched_bot_name and len(all_senders) > 1:
            matched_bot_name = all_senders[1]
            if DEBUG_MODE:
                print(f"DEBUG: Auto-selected bot as 2nd top participant (has emoji)", flush=True)

        if DEBUG_MODE:
            try:
                user_safe = matched_user_name.encode('ascii', 'ignore').decode() if matched_user_name else None
                bot_safe = matched_bot_name.encode('ascii', 'ignore').decode() if matched_bot_name else None
                print(f"DEBUG: Final match - User: '{user_safe}', Bot: '{bot_safe}'", flush=True)
            except:
                print(f"DEBUG: Matched user and bot names (contain emojis)", flush=True)

        # Create conversation pairs
        for i in range(len(messages) - 1):
            current = messages[i]
            next_msg = messages[i + 1]

            # Check if it's a user->bot conversation pair
            if (current['sender'] == matched_user_name and
                next_msg['sender'] == matched_bot_name):
                qa_pairs.append({
                    'user_message': current['message'],
                    'bot_reply': next_msg['message']
                })

        if DEBUG_MODE:
            print(f"DEBUG: Extracted {len(qa_pairs)} conversation pairs", flush=True)

        return qa_pairs, len(messages), all_senders, []

    except Exception as e:
        print(f"ERROR: Failed to parse WhatsApp chat: {e}")
        import traceback
        traceback.print_exc()
        return [], 0, [], []


def save_qa_pairs_to_file(qa_pairs, user_id):
    """Save QA pairs in the same format as original project"""
    file_path = os.path.join(USER_DATA_FOLDER, f"{user_id}_qa_pairs.txt")

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for idx, pair in enumerate(qa_pairs, 1):
                f.write(f"--- Pair {idx} ---\n")
                f.write(f"User: {pair['user_message']}\n")
                f.write(f"{pair.get('bot_name', 'Bot')}: {pair['bot_reply']}\n")
                f.write("-" * 20 + "\n")

        if DEBUG_MODE:
            print(f"DEBUG: Saved {len(qa_pairs)} pairs to {file_path}")

        return file_path
    except Exception as e:
        print(f"ERROR: Failed to save QA pairs: {e}")
        return None


def load_qa_pairs_from_file(file_path):
    """Load QA pairs from file"""
    qa_pairs = []
    try:
        if not os.path.exists(file_path):
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        pair_pattern = re.compile(r'User: (.*?)\n(.*?): (.*?)(?:\n--- Pair \d+ ---|\n-{20,}|\Z)', re.DOTALL)
        matches = pair_pattern.findall(content)

        for user_msg, bot_name, bot_reply in matches:
            qa_pairs.append({
                'user_message': user_msg.strip(),
                'bot_reply': bot_reply.strip()
            })

        return qa_pairs
    except Exception as e:
        print(f"ERROR: Could not load QA pairs: {e}")
        return []


def save_user_config(user_id, config_data):
    """Save user configuration (names, gender, relation, persona)"""
    file_path = os.path.join(USER_DATA_FOLDER, f"{user_id}_config.json")

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        if DEBUG_MODE:
            print(f"DEBUG: Saved user config to {file_path}")

        return True
    except Exception as e:
        print(f"ERROR: Failed to save user config: {e}")
        return False


def load_user_config(user_id):
    """Load user configuration"""
    file_path = os.path.join(USER_DATA_FOLDER, f"{user_id}_config.json")

    try:
        if not os.path.exists(file_path):
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return config
    except Exception as e:
        print(f"ERROR: Failed to load user config: {e}")
        return None


def analyze_chat_deeply(file_path, user_name, bot_name, api_key):
    """
    Deeply analyze the WhatsApp chat to understand personality, topics, and patterns.
    Returns a comprehensive analysis of how the bot person talks and behaves.
    """
    try:
        # Read chat file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Limit content size for API (take a representative sample if too large)
        max_chars = 100000  # ~25k tokens
        if len(content) > max_chars:
            # Take from beginning, middle, and end for better representation
            segment_size = max_chars // 3
            sample_content = (
                content[:segment_size] +
                "\n[... middle section ...]\n" +
                content[len(content)//2 - segment_size//2:len(content)//2 + segment_size//2] +
                "\n[... later section ...]\n" +
                content[-segment_size:]
            )
        else:
            sample_content = content

        # Create analysis prompt for Gemini
        analysis_prompt = f"""Analyze this WhatsApp chat conversation and provide a COMPREHENSIVE personality and communication analysis.

The chat is between:
- {user_name} (the user)
- {bot_name} (the person to mimic)

Focus your analysis ONLY on how {bot_name} communicates, their personality traits, and conversational patterns.

Please provide a detailed analysis in the following format:

## Communication Style
Describe how {bot_name} texts (sentence length, formality, energy level, etc.)

## Personality Traits
Key personality characteristics evident from messages

## Common Topics
What does {bot_name} usually talk about? What are their interests?

## Typical Phrases & Expressions
List specific phrases, catchphrases, or words {bot_name} uses frequently

## Emoji Usage
Which emojis does {bot_name} use and when?

## Language Patterns
Any code-switching, slang, unique grammar, or language mixing?

## Emotional Range
How does {bot_name} express different emotions (happy, sad, angry, playful)?

## Conversational Habits
Any unique habits like using specific greetings, asking certain questions, or ending messages in a particular way?

## Response Patterns
How does {bot_name} typically respond to different types of messages?

## Relationship Dynamics
How does {bot_name} interact with {user_name}? Tone of the relationship?

---

CHAT DATA:
{sample_content}

---

Provide a thorough analysis that captures the essence of {bot_name}'s communication style."""

        # Call Gemini API for analysis
        headers = {'Content-Type': 'application/json'}
        api_url = f"{GEMINI_API_BASE_URL}/{GEMINI_MODEL}:generateContent?key={api_key}"

        payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": analysis_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,  # Lower temperature for more analytical response
                "maxOutputTokens": 2048,
                "topP": 0.95,
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        }

        if DEBUG_MODE:
            print("DEBUG: Analyzing chat with Gemini...")

        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()

        if result and 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0].get('content', {})
            parts = content.get('parts', [])
            if parts and len(parts) > 0:
                analysis = parts[0].get('text', '')
                if analysis and analysis.strip():
                    if DEBUG_MODE:
                        print(f"DEBUG: Chat analysis completed ({len(analysis)} characters)")
                    return analysis.strip()

        return None

    except Exception as e:
        print(f"ERROR: Chat analysis failed: {e}")
        return None


def build_persona_prompt(config):
    """Build persona prompt from user configuration"""
    bot_name = config.get('bot_name', 'Bot')
    bot_gender = config.get('bot_gender', 'neutral')
    user_name = config.get('user_name', 'User')
    user_gender = config.get('user_gender', 'neutral')
    relation = config.get('relation', 'friend')
    persona_description = config.get('persona_description', '')
    language = config.get('language', 'English')

    # Gender pronouns
    bot_pronoun = "she/her" if bot_gender.lower() == "female" else "he/him" if bot_gender.lower() == "male" else "they/them"
    user_pronoun = "he/him" if user_gender.lower() == "male" else "she/her" if user_gender.lower() == "female" else "they/them"

    # Language instruction
    language_instruction = ""
    if language == "Marathi (Manglish)":
        language_instruction = "You primarily speak in Marathi but write in English/Latin alphabet (Manglish). Mix Marathi words naturally."
    elif language == "Hindi + English (Hinglish)":
        language_instruction = "You mix Hindi and English naturally (Hinglish). Use both languages in the same sentence when appropriate."
    elif language == "English":
        language_instruction = "You speak in English, but may use casual slang and informal expressions."
    elif language == "Mixed (All)":
        language_instruction = "You mix Marathi (Manglish), Hindi (Hinglish), and English naturally based on context and emotion."

    chat_analysis = config.get('chat_analysis', None)

    persona_prompt = f"""
You are playing the role of "{bot_name}", a real person based on WhatsApp chat history.

Identity: {bot_name} ({bot_pronoun})
Relationship: {bot_name} is the {relation} of {user_name} ({user_pronoun})

Language Style: {language_instruction}

{persona_description}
"""

    # Add deep chat analysis if available (from uploaded WhatsApp chat)
    if chat_analysis:
        persona_prompt += f"""
---
LEARNED FROM ACTUAL CONVERSATIONS:

{chat_analysis}

Use the above analysis to authentically mimic {bot_name}'s communication style, personality, topics, phrases, and emotional expressions.
---
"""

    persona_prompt += f"""
Important instructions:
- Reply in short, natural messages like you would in WhatsApp
- Remember you are {bot_pronoun} and you're talking to {user_name} who is {user_pronoun}
- Don't overexplain things. Keep replies warm, authentic, and light
- Match the tone and style from the persona description above
- Use emojis naturally as described in the persona
- Maintain the language mixing patterns as specified
- Be conversational and natural, like texting a {relation}
- Don't repeat phrases or sentence structures too frequently
- Vary your responses based on context and emotion
- Respond naturally to the gender context when relevant (e.g., compliments, pet names)
"""

    return persona_prompt


def get_bot_response(user_message, chat_history_list, user_id, api_key):
    """Get response from Gemini API"""

    if not api_key:
        return {"reply": random.choice(FALLBACK_MESSAGES), "success": False, "error": "API Key not configured"}

    # Load user config and QA pairs
    config = load_user_config(user_id)
    if not config:
        return {"reply": "Please complete setup first.", "success": False, "error": "Config not found"}

    qa_pairs_file = os.path.join(USER_DATA_FOLDER, f"{user_id}_qa_pairs.txt")
    qa_pairs = load_qa_pairs_from_file(qa_pairs_file)

    # Build persona prompt
    persona_prompt = build_persona_prompt(config)

    # Build messages for Gemini API
    messages = []

    # Add persona and few-shot examples
    messages.append({
        "role": "user",
        "parts": [{"text": persona_prompt + "\n\nHere are some past conversations to learn from:"}]
    })
    messages.append({
        "role": "model",
        "parts": [{"text": f"Okay, I understand. I will reply as {config.get('bot_name', 'Bot')}."}]
    })

    # Add few-shot examples (limit to 50 to avoid token limit)
    max_pairs = min(50, len(qa_pairs))
    if qa_pairs:
        for pair in qa_pairs[:max_pairs]:
            messages.append({"role": "user", "parts": [{"text": pair['user_message']}]})
            messages.append({"role": "model", "parts": [{"text": pair['bot_reply']}]})

    # Add recent chat history
    for msg in chat_history_list:
        if msg.get('role') == 'user':
            messages.append({"role": "user", "parts": [{"text": msg.get('content', '')}]})
        elif msg.get('role') == 'assistant':
            messages.append({"role": "model", "parts": [{"text": msg.get('content', '')}]})

    # Add current user message
    messages.append({"role": "user", "parts": [{"text": user_message}]})

    # Prepare API payload
    payload = {
        "contents": messages,
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 150,
            "topP": 1.0,
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    }

    headers = {'Content-Type': 'application/json'}
    api_url = f"{GEMINI_API_BASE_URL}/{GEMINI_MODEL}:generateContent?key={api_key}"

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=API_TIMEOUT_SECONDS)
        response.raise_for_status()
        result = response.json()

        if result and 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0].get('content', {})
            parts = content.get('parts', [])
            if parts and len(parts) > 0:
                bot_reply = parts[0].get('text', '')
                if bot_reply and bot_reply.strip():
                    return {"reply": bot_reply.strip(), "success": True}

        return {"reply": random.choice(FALLBACK_MESSAGES), "success": False, "error": "Empty response"}

    except requests.exceptions.Timeout:
        return {"reply": random.choice(FALLBACK_MESSAGES), "success": False, "error": "API timeout"}
    except requests.exceptions.HTTPError as e:
        return {"reply": random.choice(FALLBACK_MESSAGES), "success": False, "error": str(e)}
    except Exception as e:
        return {"reply": random.choice(FALLBACK_MESSAGES), "success": False, "error": str(e)}


# --- Flask Routes ---

@app.route('/')
def serve_landing():
    """Serve landing page"""
    return send_from_directory(app.template_folder, 'landing.html')


@app.route('/setup')
def serve_index():
    """Serve setup page"""
    return send_from_directory(app.template_folder, 'index.html')


@app.route('/chat')
def serve_chat():
    """Serve chat page"""
    return send_from_directory(app.template_folder, 'chat.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(app.static_folder, filename)


@app.route('/api/upload', methods=['POST'])
def upload_chat():
    """Handle WhatsApp chat file upload (now optional - can skip file upload)"""

    # File upload is now optional
    has_file = 'file' in request.files and request.files['file'].filename != ''

    if DEBUG_MODE:
        try:
            print(f"DEBUG: Upload request received", flush=True)
            print(f"DEBUG: Has file in request: {'file' in request.files}", flush=True)
            if 'file' in request.files:
                filename = request.files['file'].filename
                safe_filename = filename.encode('ascii', 'ignore').decode() if filename else 'None'
                print(f"DEBUG: File filename: {safe_filename}", flush=True)
            print(f"DEBUG: has_file = {has_file}", flush=True)
        except Exception as e:
            print(f"DEBUG: Error in debug logging (ignoring): {e}", flush=True)

    file = None
    if has_file:
        file = request.files['file']
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Only .txt files allowed"}), 400
        if DEBUG_MODE:
            try:
                safe_filename = file.filename.encode('ascii', 'ignore').decode() if file.filename else 'None'
                print(f"DEBUG: File validated: {safe_filename}", flush=True)
            except:
                print(f"DEBUG: File validated (filename contains special chars)", flush=True)

    try:
        # Get form data
        data = request.form
        user_name = data.get('user_name', '').strip()
        bot_name = data.get('bot_name', '').strip()
        user_gender = data.get('user_gender', '').strip()
        bot_gender = data.get('bot_gender', '').strip()
        relation = data.get('relation', '').strip()
        persona_description = data.get('persona_description', '').strip()
        api_key = data.get('api_key', '').strip()
        language = data.get('language', 'English').strip()

        if not all([user_name, bot_name, persona_description, api_key]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        # Generate unique user ID
        user_id = f"{user_name}_{bot_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        user_id = secure_filename(user_id)

        # Handle profile photo upload (optional)
        profile_pic_path = None
        if 'profile_pic' in request.files:
            profile_pic = request.files['profile_pic']
            if profile_pic.filename != '' and allowed_image(profile_pic.filename):
                # Save the file temporarily to check size
                pic_filename = secure_filename(f"{user_id}_profile.{profile_pic.filename.rsplit('.', 1)[1].lower()}")
                pic_path = os.path.join(app.config['PROFILE_PICS_FOLDER'], pic_filename)
                profile_pic.save(pic_path)

                # Check file size after saving
                file_size = os.path.getsize(pic_path)
                if file_size <= MAX_IMAGE_SIZE:
                    profile_pic_path = f"/static/images/profiles/{pic_filename}"
                    if DEBUG_MODE:
                        print(f"DEBUG: Saved profile picture to {pic_path} (size: {file_size} bytes)")
                else:
                    # Remove file if too large
                    os.remove(pic_path)
                    if DEBUG_MODE:
                        print(f"DEBUG: Profile picture too large ({file_size} bytes), removed")

        # Process chat file if uploaded
        qa_pairs = []
        total_messages = 0
        chat_analysis = None
        file_path = None

        if has_file:
            # Save uploaded file
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{user_id}_{filename}")
            file.save(file_path)

            # Parse WhatsApp chat
            qa_pairs, total_messages, all_senders, sample_lines = parse_whatsapp_chat(file_path, user_name, bot_name)

            if len(qa_pairs) == 0:
                # Create helpful error message with name suggestions
                error_msg = f"Could not extract conversation pairs. Found {total_messages} messages."

                if total_messages == 0:
                    # No messages found at all - show sample of file format
                    error_msg = "Unable to parse this file. The format doesn't match any known WhatsApp export format."
                    if sample_lines:
                        error_msg += "\n\nFirst few lines of your file:\n"
                        error_msg += "\n".join(sample_lines[:10])
                        error_msg += "\n\n✓ Expected WhatsApp format examples:"
                        error_msg += "\n  [31/12/24, 10:30:45 PM] John: Hello"
                        error_msg += "\n  31/12/24, 10:30 PM - John: Hello"
                        error_msg += "\n  31/12/2024, 22:30 - John: Hello"
                        error_msg += "\n\nMake sure you exported without media!"
                elif all_senders:
                    error_msg += f"\n\nFound {len(all_senders)} participants in the chat:\n"
                    for i, name in enumerate(all_senders[:10], 1):  # Show max 10 names
                        error_msg += f"\n{i}. {name}"

                    if len(all_senders) > 10:
                        error_msg += f"\n... and {len(all_senders) - 10} more"

                    error_msg += f"\n\nYou entered:\n- Your name: {user_name}\n- Their name: {bot_name}"
                    error_msg += "\n\nPlease use the EXACT names as shown above (copy-paste recommended)."
                else:
                    error_msg += f" Unable to find any valid participants. Please check if this is a valid WhatsApp chat export."

                return jsonify({
                    "success": False,
                    "error": error_msg,
                    "available_names": all_senders
                }), 400

            # Deep chat analysis with Gemini
            if DEBUG_MODE:
                print(f"DEBUG: Starting deep chat analysis...")

            chat_analysis = analyze_chat_deeply(file_path, user_name, bot_name, api_key)

            if chat_analysis and DEBUG_MODE:
                print(f"DEBUG: Chat analysis successful!")
            elif DEBUG_MODE:
                print(f"DEBUG: Chat analysis failed, continuing without it")

            # Save QA pairs (only if file was uploaded)
            qa_file = save_qa_pairs_to_file(qa_pairs, user_id)
            if not qa_file:
                return jsonify({"success": False, "error": "Failed to save conversation pairs"}), 500

        else:
            # No file uploaded - create empty QA pairs file
            if DEBUG_MODE:
                print(f"DEBUG: No chat file uploaded, creating bot without conversation history")

        # Save user configuration
        config = {
            'user_id': user_id,
            'user_name': user_name,
            'bot_name': bot_name,
            'user_gender': user_gender,
            'bot_gender': bot_gender,
            'relation': relation,
            'persona_description': persona_description,
            'language': language,
            'api_key': api_key,
            'profile_pic': profile_pic_path,
            'chat_analysis': chat_analysis,  # Deep analysis from uploaded chat
            'created_at': datetime.now().isoformat(),
            'total_pairs': len(qa_pairs),
            'total_messages': total_messages,
            'has_chat_file': has_file
        }

        if not save_user_config(user_id, config):
            return jsonify({"success": False, "error": "Failed to save configuration"}), 500

        # Clean up uploaded file (if it was uploaded)
        if file_path:
            try:
                os.remove(file_path)
            except:
                pass

        # Create response message
        if has_file:
            message = f"Successfully created chatbot! Analyzed {total_messages} messages and extracted {len(qa_pairs)} conversation pairs."
            if chat_analysis:
                message += " Deep personality analysis completed!"
        else:
            message = "ChatBot created successfully without conversation history. It will rely on your persona description."

        return jsonify({
            "success": True,
            "user_id": user_id,
            "bot_name": bot_name,
            "total_pairs": len(qa_pairs),
            "total_messages": total_messages,
            "has_chat_analysis": chat_analysis is not None,
            "message": message
        })

    except Exception as e:
        print(f"ERROR: Upload failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""

    try:
        data = request.get_json(force=True) or {}
        user_message = data.get('message', '').strip()
        chat_history = data.get('history', [])
        user_id = data.get('user_id', '').strip()

        if not user_message:
            return jsonify({"reply": "No message provided.", "success": False, "error": "Empty message"}), 400

        if not user_id:
            return jsonify({"reply": "Session not found.", "success": False, "error": "No user_id"}), 400

        # Load config to get API key
        config = load_user_config(user_id)
        if not config:
            return jsonify({"reply": "Configuration not found.", "success": False, "error": "Config missing"}), 404

        api_key = config.get('api_key')
        if not api_key:
            return jsonify({"reply": "API key not found.", "success": False, "error": "No API key"}), 500

        response_data = get_bot_response(user_message, chat_history, user_id, api_key)
        return jsonify(response_data), 200

    except Exception as e:
        print(f"ERROR in /api/chat: {e}")
        return jsonify({
            "reply": random.choice(FALLBACK_MESSAGES),
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/validate-key', methods=['POST'])
def validate_api_key():
    """Validate Gemini API key by making a test request"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()

        if not api_key:
            return jsonify({
                "valid": False,
                "error": "API key is required"
            }), 400

        # Make a simple test request to Gemini API
        test_payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": "Hi"}]
            }],
            "generationConfig": {
                "temperature": 0.9,
                "maxOutputTokens": 10,
            }
        }

        headers = {'Content-Type': 'application/json'}
        api_url = f"{GEMINI_API_BASE_URL}/{GEMINI_MODEL}:generateContent?key={api_key}"

        response = requests.post(api_url, headers=headers, json=test_payload, timeout=10)

        # Check if request was successful
        if response.status_code == 200:
            result = response.json()
            if result and 'candidates' in result:
                return jsonify({
                    "valid": True,
                    "message": "API key is valid!"
                })
            else:
                return jsonify({
                    "valid": False,
                    "error": "Invalid API response format"
                })
        elif response.status_code == 400:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Invalid API key')
            return jsonify({
                "valid": False,
                "error": error_message
            })
        elif response.status_code == 403:
            return jsonify({
                "valid": False,
                "error": "API key is invalid or doesn't have permission"
            })
        else:
            return jsonify({
                "valid": False,
                "error": f"API returned status code {response.status_code}"
            })

    except requests.exceptions.Timeout:
        return jsonify({
            "valid": False,
            "error": "Request timeout - please check your internet connection"
        })
    except requests.exceptions.RequestException as e:
        return jsonify({
            "valid": False,
            "error": f"Network error: {str(e)}"
        })
    except Exception as e:
        return jsonify({
            "valid": False,
            "error": f"Validation error: {str(e)}"
        }), 500


@app.route('/api/config/<user_id>', methods=['GET'])
def get_config(user_id):
    """Get user configuration"""
    config = load_user_config(user_id)
    if not config:
        return jsonify({"success": False, "error": "Configuration not found"}), 404

    # Don't send API key to frontend
    safe_config = {k: v for k, v in config.items() if k != 'api_key'}

    return jsonify({"success": True, "config": safe_config})


if __name__ == '__main__':
    # Use PORT environment variable for production (Render sets this)
    port = int(os.environ.get('PORT', 5000))

    # Detect if running in production
    is_production = os.environ.get('FLASK_ENV') == 'production'

    if is_production:
        print("Starting ChatMimic AI Server in PRODUCTION mode...")
        print(f"Port: {port}")
        # In production, gunicorn will handle this
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("Starting Personal ChatBot Server in DEVELOPMENT mode...")
        print(f"Debug Mode: {'ON' if DEBUG_MODE else 'OFF'}")
        app.run(host='0.0.0.0', port=port, debug=DEBUG_MODE)
