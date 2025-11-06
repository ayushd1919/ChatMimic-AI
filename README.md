# ChatMimic AI - WhatsApp Chat Clone Creator

Transform your WhatsApp conversations into an AI chatbot that perfectly mimics anyone's texting style! Upload your chat history and watch as the AI learns their personality, phrases, and communication patterns.

## 🌐 Branches

This repository has two branches for different use cases:

- **`local`** - For local development and testing on your machine
- **`deployment`** - Production-ready code optimized for cloud hosting on [Render](https://render.com)

📘 **Want to deploy online?** Check out the [Deployment Guide](DEPLOYMENT.md) for step-by-step instructions!

## Features

- **AI-Powered Chat Analysis**: Deep learning of conversation patterns, personality traits, and communication style from your actual chats
- **Optional Chat Upload**: Create a bot with just a persona description, or upload chats for maximum accuracy
- **Real-Time API Validation**: Instant validation of your Gemini API key with clear feedback
- **Smart Chat Parser**: Automatically extracts conversation pairs and analyzes messaging patterns
- **Profile Customization**: Upload profile photos and customize every detail
- **WhatsApp-like Interface**: Authentic WhatsApp chat experience with typing indicators
- **Powered by Gemini 2.0**: Uses Google's latest Gemini Flash model for natural, context-aware responses
- **Privacy-Focused**: All data stored locally, no third-party data collection

## Quick Start

### 1. Get Your Free Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (you'll use it in setup)

### 2. Run the Application

**Windows (Easy Start):**
```bash
# Double-click start.bat
start.bat
```

**Mac/Linux:**
```bash
chmod +x start.sh
./start.sh
```

**Manual Setup:**
```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

### 3. Open Your Browser
Navigate to: **http://localhost:5000**

### 4. Create Your Chatbot

**Step 1: Upload Chat (Optional)**
- Upload your WhatsApp chat export for AI analysis, OR
- Skip this step to create a bot with just a persona description
- Uploading chat = More accurate personality mimicry

**Step 2: Configure Details**
- Your name and their name (case-sensitive!)
- Gender selection
- Relationship type
- **Gemini API Key** (validated instantly with ✓ or ✗ feedback)
- Optional: Upload their profile photo

**Step 3: Define Persona**
- Describe their personality, texting style, and typical phrases
- Or use a template (Friend, Romantic, Professional)
- The more detail, the better the results!

## How to Export WhatsApp Chat

### Android:
1. Open WhatsApp → Select chat
2. Tap ⋮ (three dots) → **More** → **Export chat**
3. Choose **Without Media**
4. Save the .txt file

### iPhone:
1. Open WhatsApp → Select chat
2. Tap contact name → **Export Chat**
3. Choose **Without Media**
4. Save the .txt file

## New Features

### Real-Time API Key Validation
- **Instant Validation**: API key is tested immediately as you type
- **Clear Feedback**: Green checkmark for valid keys, red X with error message for invalid
- **Smart Debouncing**: Waits 1 second after you stop typing to validate
- **Prevents Errors**: Can't proceed with invalid API key

### Deep Chat Analysis
When you upload a chat, the AI analyzes:
- **Communication Style**: Formal, casual, playful, sarcastic, etc.
- **Personality Traits**: Sweet, caring, funny, dramatic, etc.
- **Common Topics**: What they talk about most
- **Typical Phrases**: Their catchphrases and expressions
- **Emoji Usage**: Which emojis they use and when
- **Language Patterns**: Code-switching, slang, mixing languages
- **Emotional Range**: How they express different emotions
- **Response Patterns**: How they typically reply in conversations

## Example Persona Description

```
You are a sweet, sarcastic, emotionally intelligent girl.

You often switch between Marathi and Hindi/English, especially in emotional moments.

Common phrases you use:
- "Khadyat jaa"
- "Dukkar 🐷"
- "Arey baba"
- "Gap bass"

Your favorite emojis: ❤️ 🤌🏻 🫶🏻 😂 ✨ 🐷

You reply in short, natural sentences like in WhatsApp.

Tone: Like a best friend - sometimes flirty, sometimes caring, sometimes brutally honest.

When happy/playful: "Dukkar! 😂 kay chalu aahe?"
When caring: "Important ahe re tu mzya sathi ❤️"
When teasing: "Tuch na? 😉"
```

## Project Structure

```
ChatMimic AI/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── start.bat / start.sh        # Quick start scripts
│
├── templates/
│   ├── index.html             # Setup/onboarding page
│   └── chat.html              # WhatsApp-like chat interface
│
├── static/
│   ├── css/
│   │   ├── setup.css          # Setup page styles
│   │   └── chat.css           # Chat interface styles
│   ├── js/
│   │   ├── setup.js           # Setup page logic + API validation
│   │   └── chat.js            # Chat functionality
│   ├── images/
│   │   └── profiles/          # User-uploaded profile photos
│   └── favicon.svg            # App icon
│
├── uploads/                   # Temporary chat files (auto-deleted)
└── user_data/                 # User configs and conversation pairs
    ├── {user_id}_config.json
    └── {user_id}_qa_pairs.txt
```

## Technical Details

### AI Model Configuration
- **Model**: Gemini 2.0 Flash Experimental
- **Few-Shot Learning**: Uses up to 50 conversation pairs as examples
- **Deep Analysis**: Comprehensive personality and pattern analysis
- **Temperature**: 0.9 (creative but consistent)
- **Max Tokens**: 150 (short, WhatsApp-style responses)

### Chat Parser Features
- Supports multiple WhatsApp export formats (Android, iPhone)
- Extracts message pairs (User → Bot reply)
- Filters system messages (media, calls, group actions)
- Case-sensitive name matching
- Handles emojis and special characters safely

### Data Storage
- **QA Pairs**: `user_data/{user_id}_qa_pairs.txt`
- **Config**: `user_data/{user_id}_config.json`
- **Chat Analysis**: Stored in config JSON
- **API Key**: Encrypted storage, never sent to frontend
- **Uploaded Files**: Auto-deleted after processing

## Tips for Best Results

1. **Upload Quality Chats**: More messages = better learning (50+ messages recommended)
2. **Be Specific**: The more detailed your persona description, the better
3. **Include Examples**: Show how they reply in different moods and situations
4. **Match Names Exactly**: Names are case-sensitive - must match the chat export
5. **Describe Patterns**: Language mixing, emoji usage, slang, typical responses
6. **Use Chat Analysis**: Upload chat for AI to analyze their actual style

## Troubleshooting

### API Key Issues
**"API key is invalid or doesn't have permission"**
- Generate a new key at [Google AI Studio](https://makersuite.google.com/app/apikey)
- Make sure you copied the entire key
- Check that Gemini API is enabled for your project

### Name Matching Errors
**"Could not extract conversation pairs"**
- Names are **case-sensitive** - check the exact spelling in your chat
- Make sure there are back-and-forth conversations (not just one person talking)
- The chat must be a proper WhatsApp export .txt file

### Upload Problems
**File not uploading / requires multiple attempts**
- Check file size (max 10MB for chats, 5MB for photos)
- Ensure file is .txt format for chats, image format for photos
- Try refreshing the page and uploading again
- Check browser console (F12) for errors

### Generic Responses
**Bot doesn't sound like the person**
- Add more details to the persona description
- Upload a chat with more conversation pairs
- Include specific examples of how they respond
- Describe their emoji usage and language patterns

### Chat Not Loading
- Clear browser localStorage and restart
- Ensure Flask server is running (check terminal)
- Try accessing http://127.0.0.1:5000 instead
- Check browser console for JavaScript errors (F12)

## Privacy & Security

- ✓ All chat data processed locally on your machine
- ✓ No third-party tracking or analytics
- ✓ API key stored locally, used only for Gemini API
- ✓ Uploaded files deleted immediately after processing
- ✓ User data stays in local `user_data/` folder
- ✓ No data sent anywhere except Google Gemini API

## Limitations

- Requires Google Gemini API key (free tier: 1500 requests/day)
- Works best with 50+ conversation pairs
- Name matching is case-sensitive
- Supports English, Hindi, Marathi, and mixed languages
- Cannot process media messages (images, videos, voice notes)
- Voice message feature not yet implemented

## Future Enhancements

- [ ] Support for multiple chat imports
- [ ] Voice message support
- [ ] Export conversation history
- [ ] Advanced personality fine-tuning
- [ ] Multi-user support
- [ ] Conversation analytics dashboard
- [ ] More language support

## Tech Stack

Built with:
- **Backend**: Flask (Python web framework)
- **AI**: Google Gemini 2.0 Flash
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **UI Design**: WhatsApp-inspired interface
- **Real-time Validation**: Fetch API with debouncing

## License & Usage

This project is for **educational and personal use only**.

**Important**: Please respect privacy and obtain explicit consent before creating AI chatbots that mimic real people. This tool is designed for fun, learning, and personal experimentation - not for deception or impersonation.

## Contributing

Found a bug or have a feature idea? Feel free to:
- Open an issue on GitHub
- Submit a pull request
- Share feedback and suggestions

---

**Made with ❤️ for creating authentic AI chat experiences**

Enjoy chatting with your AI clone! 🤖💬

For questions or support, check the troubleshooting section above or review the code comments in `app.py`.
