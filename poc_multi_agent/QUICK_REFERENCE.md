# Quick Reference Card

## 🚀 Getting Started

```bash
# 1. Install dependencies
pip install fastapi uvicorn twilio pymongo langchain-google-genai elevenlabs requests python-dotenv pydantic

# 2. Configure .env
# Add your API keys (see .env.example)

# 3. Test system
python test_voice_system.py

# 4. Start server
python agent_voice_conversation.py

# 5. Expose with ngrok
ngrok http 8000

# 6. Make a call
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `agent_voice_conversation.py` | Main voice system (like original) |
| `audio_storage.py` | Audio file management (NEW!) |
| `elevenlabs_service.py` | Voice generation |
| `database.py` | MongoDB integration |
| `agent_config.py` | Agent configuration |

## 🔧 Configuration (.env)

```env
GEMINI_API_KEY=your_key
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890
ELEVENLABS_API_KEY=your_key
ELEVENLABS_VOICE_ID=your_voice_id
MONGODB_URL=mongodb://localhost:27017/db
WEBHOOK_BASE_URL=https://your-ngrok.ngrok.io
```

## 🎯 API Endpoints

```bash
# Start call
POST /start-call?agent_type=LOGISTICS&phone_number=+91xxx

# Get call status
GET /call-status/{call_sid}

# Serve audio
GET /audio/{filename}

# Health check
GET /
```

## 🤖 Available Agents

- **LOGISTICS** - Shipment charges & availability
- **PIZZA** - Pizza orders
- **Custom** - Add your own in `agent_config.py`

## 🌍 Supported Languages

- English
- Tamil
- Malayalam

## 🔄 Call Flow

1. Language Selection
2. Welcome Message
3. Information Collection (conversational AI)
4. Completion / Transfer

## 📊 Architecture

```
Phone Call → Twilio → FastAPI → Gemini LLM → MongoDB
                ↓                    ↓
           ElevenLabs ← audio_storage
```

## 🧪 Testing

```bash
# Test all components
python test_voice_system.py

# Test text conversation (faster)
python agent_conversation.py

# Test voice conversation
python agent_voice_conversation.py
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **QUICKSTART_VOICE.md** | 5-minute setup |
| **ELEVENLABS_INTEGRATION.md** | Audio storage details |
| **VOICE_CONVERSATION_README.md** | Complete docs |
| **INTEGRATION_GUIDE.md** | Integration details |
| **COMPARISON.md** | File comparison |
| **INDEX.md** | Documentation index |

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Call not connecting | Check Twilio config & ngrok |
| No audio | Verify WEBHOOK_BASE_URL |
| LLM not responding | Check GEMINI_API_KEY |
| MongoDB failed | Uses in-memory fallback |
| ElevenLabs failed | Uses Twilio TTS fallback |

## 💡 Pro Tips

1. **Test text first**: Use `agent_conversation.py`
2. **Use ngrok**: Essential for webhooks
3. **Monitor logs**: Watch for errors
4. **Check audio files**: `ls temp_audio/`
5. **Cleanup**: Automatic on shutdown

## 🎨 Adding Custom Agent

```python
# 1. Edit agent_config.py
AGENT_METADATA = {
    "YOUR_AGENT": {
        "system_prompt": "...",
        "welcome_msg": {"English": "...", "Tamil": "...", "Malayalam": "..."},
        "positive_thank_you_msg": "...",
        "negative_thank_you_msg": "...",
        "language_selection": ["English", "Tamil", "Malayalam"]
    }
}

# 2. Update LLMOutput model in agent_voice_conversation.py
class LLMOutput(BaseModel):
    # Add your fields
    your_field: Optional[str] = None

# 3. Update build_system_prompt() and process_llm_response()

# 4. Test it!
curl -X POST "http://localhost:8000/start-call?agent_type=YOUR_AGENT&phone_number=+91xxx"
```

## 🔍 Monitoring

```bash
# Check active calls
curl http://localhost:8000/active-calls

# Check call status
curl http://localhost:8000/call-status/CAxxxx

# Check collected data
curl http://localhost:8000/collected-data

# Check audio files
ls -la temp_audio/
```

## ✅ What's New (ElevenLabs Update)

- ✅ Added `audio_storage.py` module
- ✅ Updated `elevenlabs_service.py` to use audio_storage
- ✅ Added startup/shutdown events
- ✅ Automatic file caching
- ✅ Automatic cleanup (24 hours)
- ✅ Matches original `app/main.py` implementation

## 🎯 Key Features

- ✅ Multi-agent support
- ✅ Multi-language support
- ✅ Conversational AI (handles ANY input)
- ✅ Natural voice (ElevenLabs)
- ✅ Persistent storage (MongoDB)
- ✅ Audio caching
- ✅ Automatic cleanup
- ✅ No hardcoding

## 📞 Example Call

```
System: "Please select your language: English, Tamil, Malayalam"
User: "English"
System: "Hello, this is an automated call from your ERP system..."
User: "The charge is 500 rupees and I'm available from 2pm to 5pm"
System: "Thank you! I have charges as ₹500 and availability as 2pm to 5pm. Is this correct?"
User: "Yes"
System: "Thank you! Your information has been updated."
[Call ends]
```

## 🎉 Success Criteria

✅ Call connects  
✅ Language selection works  
✅ LLM processes input  
✅ Fields extracted correctly  
✅ Data saved to MongoDB  
✅ Voice sounds natural  
✅ Audio files cached  
✅ Call ends gracefully  

---

**Need more details?** Check [INDEX.md](INDEX.md) for complete documentation.

**Ready to start?** Run `python test_voice_system.py` then `python agent_voice_conversation.py`!
