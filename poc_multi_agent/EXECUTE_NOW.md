# Execute NOW - Ultra Quick Guide

## ⚡ 5 Commands to Get Started

```bash
# 1. Install (2 min)
pip install fastapi uvicorn twilio pymongo langchain-google-genai elevenlabs requests python-dotenv pydantic

# 2. Configure .env (add your API keys)
nano .env

# 3. Test (1 min)
python test_voice_system.py

# 4. Start Server (keep running)
python agent_voice_conversation.py

# 5. In NEW terminal - Start ngrok (keep running)
ngrok http 8000
```

## 📝 Update .env with ngrok URL

```env
WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok.io
```

Restart server (Ctrl+C and run again)

## 📞 Make Your First Call

```bash
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+919876543210"
```

**Replace with YOUR phone number!**

## ✅ Done!

Your phone should ring! Answer and talk to the AI.

---

## 🎯 What You Need

### Required API Keys (in .env)
```env
GEMINI_API_KEY=your_key          # Get from: https://ai.google.dev/
TWILIO_ACCOUNT_SID=your_sid      # Get from: https://www.twilio.com/console
TWILIO_AUTH_TOKEN=your_token     # Get from: https://www.twilio.com/console
TWILIO_PHONE_NUMBER=+1234567890  # Get from: https://www.twilio.com/console
```

### Optional (will use fallbacks)
```env
ELEVENLABS_API_KEY=your_key      # Get from: https://elevenlabs.io/
ELEVENLABS_VOICE_ID=your_id      # Get from: https://elevenlabs.io/
MONGODB_URL=mongodb://localhost:27017/db
```

---

## 🐛 Quick Fixes

### Call not connecting?
- Check phone number format: `+919876543210` (with +)
- Check ngrok is running
- Check WEBHOOK_BASE_URL in .env

### No audio?
- Check WEBHOOK_BASE_URL is correct
- Restart server after updating .env

### LLM not working?
- Check GEMINI_API_KEY in .env

---

## 📚 More Help?

- **Detailed Guide**: `HOW_TO_EXECUTE.md`
- **Flow Explanation**: `FLOW_EXPLANATION.md`
- **Visual Diagrams**: `VISUAL_FLOW.md`
- **All Docs**: `INDEX.md`

---

**That's it! Start calling! 📞🚀**
