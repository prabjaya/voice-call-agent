# Multi-Agent Voice Conversation System

A fully integrated voice conversation system combining the conversational AI logic from `agent_conversation.py` with MongoDB, Twilio, and ElevenLabs services - **NO HARDCODING**.

## 🎯 Features

- **Multi-Agent Support**: PIZZA, LOGISTICS, and more via `agent_config.py`
- **Conversational AI**: Flexible LLM that handles ANY user input (Gemini 2.0 Flash)
- **Voice Integration**: Twilio for calls + ElevenLabs for natural voice
- **Persistent Storage**: MongoDB for call sessions and collected data
- **Multi-Language**: English, Tamil, Malayalam support
- **No Hardcoding**: All configuration via `agent_config.py` and `.env`

## 📁 Architecture

```
agent_voice_conversation.py  ← NEW! Voice-enabled conversation system
├── agent_conversation.py    ← Text-based conversational logic
├── agent_config.py          ← Agent metadata (PIZZA, LOGISTICS)
├── database.py              ← MongoDB integration
├── elevenlabs_service.py    ← Natural voice generation
└── .env                     ← Configuration
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn twilio pymongo langchain-google-genai elevenlabs requests python-dotenv pydantic
```

### 2. Configure Environment

Update your `.env` file:

```env
# Gemini LLM
GEMINI_API_KEY=your_gemini_api_key

# Twilio Voice
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# ElevenLabs Voice
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_voice_id

# MongoDB
MONGODB_URL=mongodb://localhost:27017/multi_agent_poc

# Webhook URL (for Twilio callbacks)
WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok.io
```

### 3. Start the Server

```bash
cd poc_multi_agent
python agent_voice_conversation.py
```

Server runs on `http://0.0.0.0:8000`

### 4. Make a Test Call

```bash
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+919876543210"
```

## 🔄 How It Works

### Call Flow

1. **Language Selection**
   - System asks: "Please select your language: English, Tamil, Malayalam"
   - User responds with language preference

2. **Welcome Message**
   - System greets in selected language
   - Explains purpose (from `agent_config.py`)

3. **Information Collection**
   - LLM processes user responses conversationally
   - Extracts required fields based on agent type:
     - **LOGISTICS**: `charge`, `availability_time`
     - **PIZZA**: `pizza_type`, `size`, `delivery_address`, `delivery_time`

4. **Completion**
   - When all info collected → Thank you message
   - Data saved to MongoDB
   - Call ends gracefully

### LLM Response Types

```json
{
  "response_type": "NEED_MORE_INFO",  // or "THANK_YOU_RESPONSE" or "HANDOVER_TO_HUMAN"
  "charge": "₹500",
  "availability_time": "2pm to 5pm",
  "feedback": "Thank you! I have the charges. What are your available time slots?"
}
```

## 🎨 Adding New Agents

Simply update `agent_config.py`:

```python
AGENT_METADATA = {
    "YOUR_AGENT": {
        "system_prompt": "You are an AI assistant for...",
        "positive_thank_you_msg": "Thank you!",
        "negative_thank_you_msg": "No problem!",
        "welcome_msg": {
            "English": "Hello! Welcome to...",
            "Tamil": "வணக்கம்!...",
            "Malayalam": "നമസ്കാരം!..."
        },
        "language_selection": ["English", "Tamil", "Malayalam"]
    }
}
```

Then update the `LLMOutput` model in `agent_voice_conversation.py` to include your custom fields.

## 📊 API Endpoints

### Start Call
```bash
POST /start-call?agent_type=LOGISTICS&phone_number=+91xxx
```

### Get Call Status
```bash
GET /call-status/{call_sid}
```

### Serve Audio Files
```bash
GET /audio/{filename}
```

### Health Check
```bash
GET /
```

## 🗄️ Database Schema

### Calls Collection
```json
{
  "call_sid": "CAxxxx",
  "agent_type": "LOGISTICS",
  "stage": "collecting",
  "language": "English",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "collected_data": {
    "charge": "₹500",
    "availability_time": "2pm to 5pm"
  },
  "created_at": "2025-11-19T10:00:00Z",
  "updated_at": "2025-11-19T10:05:00Z"
}
```

### Collected Data Collection
```json
{
  "call_sid": "CAxxxx",
  "agent_type": "LOGISTICS",
  "data": {
    "charge": "₹500",
    "availability_time": "2pm to 5pm"
  },
  "collected_at": "2025-11-19T10:05:00Z"
}
```

## 🔧 Configuration Options

### Twilio Language Codes
- English: `en-US`
- Tamil: `ta-IN`
- Malayalam: `ml-IN`

### Twilio Voices
- English: `Polly.Joanna-Neural`
- Tamil: `Polly.Aditi-Neural`
- Malayalam: `Polly.Aditi-Neural`

### ElevenLabs Voice Settings
```python
{
    "stability": 0.5,
    "similarity_boost": 0.75
}
```

## 🆚 Comparison with Original Files

| Feature | agent_conversation.py | agent_voice_conversation.py |
|---------|----------------------|----------------------------|
| Interface | Text (CLI) | Voice (Twilio) |
| LLM | ✅ Gemini 2.0 Flash | ✅ Gemini 2.0 Flash |
| MongoDB | ❌ | ✅ |
| Twilio | ❌ | ✅ |
| ElevenLabs | ❌ | ✅ |
| Multi-Agent | ✅ | ✅ |
| Multi-Language | ✅ | ✅ |
| Conversational AI | ✅ | ✅ |

## 🧪 Testing

### Test with Text (CLI)
```bash
python agent_conversation.py
```

### Test with Voice (Twilio)
```bash
python agent_voice_conversation.py
# Then make a call via /start-call endpoint
```

## 📝 Notes

- **ElevenLabs Fallback**: If ElevenLabs fails, system automatically uses Twilio TTS
- **MongoDB Fallback**: If MongoDB unavailable, uses in-memory storage
- **Session Persistence**: Calls survive server restarts (stored in MongoDB)
- **Audio Caching**: Generated audio files cached in `temp_audio/` folder

## 🐛 Troubleshooting

### Call Not Connecting
- Check Twilio credentials in `.env`
- Verify `WEBHOOK_BASE_URL` is publicly accessible (use ngrok)
- Check Twilio phone number format: `+1234567890`

### LLM Not Responding
- Verify `GEMINI_API_KEY` in `.env`
- Check API quota/limits

### MongoDB Connection Failed
- System will use in-memory storage
- Check `MONGODB_URL` format
- Ensure MongoDB is running

### ElevenLabs Voice Not Working
- System will fallback to Twilio TTS
- Check `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID`
- Verify API quota

## 🎯 Next Steps

1. Add more agents in `agent_config.py`
2. Customize voice settings in `elevenlabs_service.py`
3. Add analytics dashboard
4. Implement retry logic for failed calls
5. Add SMS notifications

## 📚 Related Files

- `main.py` - Original ERP voice call system
- `agent_conversation.py` - Text-based conversational AI
- `agent_config.py` - Agent metadata configuration
- `database.py` - MongoDB integration
- `elevenlabs_service.py` - Voice generation service
