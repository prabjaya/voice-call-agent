# 🚀 START HERE - Multi-Agent Voice Conversation System

## What is this?

An AI-powered voice call system that:
- 📞 Makes automated phone calls
- 🧠 Has natural conversations using Gemini LLM
- 🎤 Uses natural voice (ElevenLabs)
- 💾 Stores data in MongoDB
- 🌍 Supports multiple languages (English, Tamil, Malayalam)
- 🤖 Supports multiple agents (PIZZA, LOGISTICS, custom)
- ✨ NO HARDCODING - All configuration-driven!

## 🎯 Choose Your Path

### Path 1: I Want to Execute NOW! ⚡
**→ [EXECUTE_NOW.md](EXECUTE_NOW.md)**
- 5 commands to get started
- Fastest way to make your first call
- Perfect for: Quick testing

### Path 2: I Want Step-by-Step Guide 📚
**→ [HOW_TO_EXECUTE.md](HOW_TO_EXECUTE.md)**
- Complete execution guide
- Troubleshooting included
- Testing and monitoring
- Perfect for: First-time setup

### Path 3: I Want to Understand How It Works 🧠
**→ [FLOW_EXPLANATION.md](FLOW_EXPLANATION.md)**
- Detailed flow explanation
- Step-by-step breakdown
- Code examples
- Perfect for: Developers

### Path 4: I Want Visual Diagrams 📊
**→ [VISUAL_FLOW.md](VISUAL_FLOW.md)**
- ASCII flow diagrams
- Component interactions
- Session lifecycle
- Perfect for: Visual learners

### Path 5: I Want All Documentation 📖
**→ [INDEX.md](INDEX.md)**
- Complete documentation index
- All guides and references
- Perfect for: Comprehensive learning

## ⚡ Super Quick Start (30 seconds)

```bash
# 1. Install
pip install fastapi uvicorn twilio pymongo langchain-google-genai elevenlabs requests python-dotenv pydantic

# 2. Configure .env (add your API keys)
nano .env

# 3. Test
python test_voice_system.py

# 4. Start server
python agent_voice_conversation.py

# 5. In new terminal - Start ngrok
ngrok http 8000

# 6. Update WEBHOOK_BASE_URL in .env with ngrok URL

# 7. Restart server

# 8. Make call
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"
```

## 📋 What You Need

### Required
- Python 3.8+
- Gemini API key (https://ai.google.dev/)
- Twilio account (https://www.twilio.com/)
- ngrok (https://ngrok.com/)

### Optional
- ElevenLabs API key (https://elevenlabs.io/) - for natural voice
- MongoDB (https://www.mongodb.com/) - for persistent storage

## 🎯 Key Features

✅ Multi-agent support (PIZZA, LOGISTICS, custom)  
✅ Multi-language support (English, Tamil, Malayalam)  
✅ Conversational AI (handles ANY user input)  
✅ Natural voice (ElevenLabs + Twilio TTS fallback)  
✅ Persistent storage (MongoDB + in-memory fallback)  
✅ Audio caching (performance optimization)  
✅ Automatic cleanup (disk space management)  
✅ No hardcoding (all configuration-driven)  

## 📞 Example Call Flow

```
System: "Please select your language: English, Tamil, Malayalam"
You: "English"
System: "Hello, this is an automated call from your ERP system..."
You: "The charge is 500 rupees and I'm available from 2pm to 5pm"
System: "Thank you! Your information has been updated."
[Call ends]
```

## 🗂️ Project Structure

```
poc_multi_agent/
├── agent_voice_conversation.py  ← Main voice system
├── agent_conversation.py        ← Text-based testing
├── agent_config.py              ← Agent configuration
├── database.py                  ← MongoDB integration
├── elevenlabs_service.py        ← Voice generation
├── audio_storage.py             ← Audio file management
├── test_voice_system.py         ← Testing script
├── .env                         ← Configuration
└── Documentation/
    ├── EXECUTE_NOW.md           ← Ultra quick start
    ├── HOW_TO_EXECUTE.md        ← Detailed execution
    ├── FLOW_EXPLANATION.md      ← How it works
    ├── VISUAL_FLOW.md           ← Visual diagrams
    └── INDEX.md                 ← All documentation
```

## 🎨 Adding Custom Agent

```python
# Edit agent_config.py
AGENT_METADATA = {
    "YOUR_AGENT": {
        "system_prompt": "You are an AI assistant for...",
        "welcome_msg": {
            "English": "Hello! Welcome to...",
            "Tamil": "வணக்கம்!...",
            "Malayalam": "നമസ്കാരം!..."
        },
        "positive_thank_you_msg": "Thank you!",
        "negative_thank_you_msg": "No problem!",
        "language_selection": ["English", "Tamil", "Malayalam"]
    }
}
```

Then make a call:
```bash
curl -X POST "http://localhost:8000/start-call?agent_type=YOUR_AGENT&phone_number=+91xxx"
```

## 🧪 Testing

### Test Text Conversation (Recommended First!)
```bash
python agent_conversation.py
```
- Faster than voice calls
- Cheaper (no call costs)
- Same LLM logic
- Perfect for development

### Test Voice Conversation
```bash
python agent_voice_conversation.py
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"
```

### Test All Components
```bash
python test_voice_system.py
```

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| Call not connecting | Check Twilio config & ngrok |
| No audio | Verify WEBHOOK_BASE_URL |
| LLM not responding | Check GEMINI_API_KEY |
| MongoDB failed | Uses in-memory fallback (OK) |
| ElevenLabs failed | Uses Twilio TTS fallback (OK) |

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **EXECUTE_NOW.md** | Ultra quick start (5 commands) |
| **HOW_TO_EXECUTE.md** | Complete execution guide |
| **FLOW_EXPLANATION.md** | How the system works |
| **VISUAL_FLOW.md** | Visual flow diagrams |
| **INTEGRATION_GUIDE.md** | Integration details |
| **ELEVENLABS_INTEGRATION.md** | Audio storage details |
| **COMPARISON.md** | File comparison |
| **INDEX.md** | Complete documentation index |

## 🎯 Next Steps

1. **Execute**: Follow [EXECUTE_NOW.md](EXECUTE_NOW.md)
2. **Test**: Make your first call
3. **Customize**: Add your own agent
4. **Deploy**: Move to production

## 💡 Pro Tips

1. Test with text first (`agent_conversation.py`)
2. Keep ngrok running in separate terminal
3. Monitor server logs for errors
4. Check `temp_audio/` for cached audio files
5. Use your own phone for testing

## 🎉 Success Criteria

✅ Server running  
✅ ngrok exposing server  
✅ Test call made  
✅ Phone rings  
✅ Conversation works  
✅ Data saved  

## 🆘 Need Help?

1. Check [HOW_TO_EXECUTE.md](HOW_TO_EXECUTE.md) for troubleshooting
2. Check [FLOW_EXPLANATION.md](FLOW_EXPLANATION.md) to understand how it works
3. Check [INDEX.md](INDEX.md) for all documentation

---

## 🚀 Ready to Start?

Choose your path above and start building! 

**Fastest way:** [EXECUTE_NOW.md](EXECUTE_NOW.md) ⚡

**Most detailed:** [HOW_TO_EXECUTE.md](HOW_TO_EXECUTE.md) 📚

**Happy calling! 📞**
