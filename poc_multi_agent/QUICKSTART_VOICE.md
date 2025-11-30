# Quick Start: Voice Conversation System

Get your multi-agent voice conversation system running in 5 minutes!

## 🚀 Step 1: Install Dependencies (1 min)

```bash
cd poc_multi_agent
pip install fastapi uvicorn twilio pymongo langchain-google-genai elevenlabs requests python-dotenv pydantic
```

## 🔧 Step 2: Configure Environment (2 min)

Update your `.env` file:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Optional (will use fallbacks if not set)
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_voice_id
MONGODB_URL=mongodb://localhost:27017/multi_agent_poc

# Will be updated after ngrok
WEBHOOK_BASE_URL=http://localhost:8000
```

## ✅ Step 3: Test System (1 min)

```bash
python test_voice_system.py
```

Expected output:
```
✅ GEMINI_API_KEY: Gemini LLM
✅ TWILIO_ACCOUNT_SID: Twilio Voice
✅ TWILIO_AUTH_TOKEN: Twilio Voice
✅ TWILIO_PHONE_NUMBER: Twilio Voice
✅ MongoDB connected successfully
✅ ElevenLabs audio generated
✅ API server is running

🎉 All tests passed! System is ready.
```

## 🌐 Step 4: Start Server (30 sec)

```bash
python agent_voice_conversation.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 🔗 Step 5: Expose with ngrok (30 sec)

In a new terminal:

```bash
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`) and update `.env`:

```env
WEBHOOK_BASE_URL=https://abc123.ngrok.io
```

Restart the server (Ctrl+C and run again).

## 📞 Step 6: Make a Test Call!

```bash
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+919876543210"
```

Replace `+919876543210` with your actual phone number!

## 🎉 Success!

You should receive a call that:
1. Asks for language selection
2. Greets you in selected language
3. Collects required information
4. Thanks you and ends call

## 📊 Monitor Your Call

### Check call status
```bash
curl http://localhost:8000/call-status/CAxxxx
```

### View all active calls
```bash
curl http://localhost:8000/active-calls
```

### Check collected data
```bash
curl http://localhost:8000/collected-data
```

## 🐛 Troubleshooting

### Call not connecting?
- ✅ Check Twilio credentials in `.env`
- ✅ Verify phone number format: `+1234567890`
- ✅ Ensure ngrok is running
- ✅ Check `WEBHOOK_BASE_URL` is correct

### No audio?
- ✅ Check `WEBHOOK_BASE_URL` is publicly accessible
- ✅ Verify ngrok HTTPS URL
- ✅ Check Twilio console for errors

### LLM not responding?
- ✅ Verify `GEMINI_API_KEY` is correct
- ✅ Check API quota/limits
- ✅ Look at server logs for errors

### MongoDB connection failed?
- ✅ System will use in-memory storage (OK for testing)
- ✅ To fix: Start MongoDB or update `MONGODB_URL`

## 🎯 Next Steps

### Test Different Agents

```bash
# Pizza agent
curl -X POST "http://localhost:8000/start-call?agent_type=PIZZA&phone_number=+91xxx"

# Logistics agent
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"
```

### Add Your Own Agent

1. Edit `agent_config.py`:
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

2. Update `LLMOutput` model in `agent_voice_conversation.py`

3. Test it!

### Test Conversation Logic First

Before making actual calls, test the conversation logic with text:

```bash
python agent_conversation.py
```

This is faster and cheaper for development!

## 📚 Documentation

- **Full Guide**: `VOICE_CONVERSATION_README.md`
- **Integration Details**: `INTEGRATION_GUIDE.md`
- **Comparison**: `COMPARISON.md`
- **Original Quickstart**: `QUICKSTART.md`

## 💡 Pro Tips

1. **Test text first**: Use `agent_conversation.py` before voice
2. **Monitor logs**: Watch for LLM parsing errors
3. **Use ngrok**: Essential for Twilio webhooks
4. **Cache audio**: ElevenLabs files are cached automatically
5. **Fallback strategy**: System handles service failures gracefully

## 🎓 Example Call Flow

```
1. System calls: +919876543210
2. User answers: "Hello?"
3. System: "Please select your language: English, Tamil, Malayalam"
4. User: "English"
5. System: "Hello, this is an automated call from your ERP system..."
6. User: "The charge is 500 rupees and I'm available from 2pm to 5pm"
7. System: "Thank you! I have charges as ₹500 and availability as 2pm to 5pm. Is this correct?"
8. User: "Yes"
9. System: "Thank you! Your information has been updated in our ERP system."
10. Call ends
```

## ✨ Features You Get

- ✅ Multi-agent support (PIZZA, LOGISTICS, custom)
- ✅ Multi-language (English, Tamil, Malayalam)
- ✅ Natural voice (ElevenLabs + Twilio TTS fallback)
- ✅ Conversational AI (handles ANY user input)
- ✅ Persistent storage (MongoDB)
- ✅ Session recovery (survives server restarts)
- ✅ Audio caching (performance optimization)
- ✅ No hardcoding (all config-driven)

## 🎊 You're Ready!

Your multi-agent voice conversation system is now running. Make some test calls and see the magic happen!

Need help? Check the documentation files or run the test script again.

---

**Happy calling! 📞**
