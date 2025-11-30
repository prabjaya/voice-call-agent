# How to Execute - Step by Step Guide

## 🚀 Complete Execution Steps

### Step 1: Install Dependencies (2 minutes)

```bash
cd poc_multi_agent

pip install fastapi uvicorn twilio pymongo langchain-google-genai elevenlabs requests python-dotenv pydantic
```

Or use requirements.txt if available:
```bash
pip install -r requirements.txt
```

---

### Step 2: Configure Environment Variables (3 minutes)

Edit your `.env` file:

```bash
# Open .env file
nano .env
# or
code .env
```

Add these values:

```env
# Required - Gemini LLM
GEMINI_API_KEY=your_gemini_api_key_here

# Required - Twilio Voice
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Optional - ElevenLabs (will use Twilio TTS if not set)
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_voice_id

# Optional - MongoDB (will use in-memory if not set)
MONGODB_URL=mongodb://localhost:27017/multi_agent_poc

# Will update this after ngrok
WEBHOOK_BASE_URL=http://localhost:8000
```

**Where to get API keys:**
- **Gemini**: https://ai.google.dev/
- **Twilio**: https://www.twilio.com/console
- **ElevenLabs**: https://elevenlabs.io/app/settings/api-keys

---

### Step 3: Test Your Setup (1 minute)

```bash
python test_voice_system.py
```

**Expected output:**
```
✅ GEMINI_API_KEY: Gemini LLM
✅ TWILIO_ACCOUNT_SID: Twilio Voice
✅ TWILIO_AUTH_TOKEN: Twilio Voice
✅ MongoDB connected successfully
✅ Audio storage initialized
✅ ElevenLabs audio generated

🎉 All tests passed! System is ready.
```

If you see errors, fix them before continuing.

---

### Step 4: Start the Server (30 seconds)

```bash
python agent_voice_conversation.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Starting Multi-Agent Voice Conversation System
INFO:     MongoDB connection: Connected
INFO:     Audio storage: temp_audio
INFO:     ElevenLabs: Configured
INFO:     Active calls in memory: 0
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!**

---

### Step 5: Expose Server with ngrok (1 minute)

**Open a NEW terminal** and run:

```bash
ngrok http 8000
```

**Expected output:**
```
Session Status                online
Account                       Your Name
Version                       3.x.x
Region                        United States (us)
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

---

### Step 6: Update Webhook URL (30 seconds)

1. **Stop the server** (Ctrl+C in first terminal)

2. **Update .env file:**
```env
WEBHOOK_BASE_URL=https://abc123.ngrok.io
```
(Replace with your actual ngrok URL)

3. **Restart the server:**
```bash
python agent_voice_conversation.py
```

---

### Step 7: Make Your First Call! 🎉

**In a NEW terminal**, run:

```bash
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+919876543210"
```

**Replace `+919876543210` with your actual phone number!**

**Expected response:**
```json
{
  "success": true,
  "call_sid": "CAxxxxxxxxxxxxxxxxxxxx",
  "agent_type": "LOGISTICS",
  "phone_number": "+919876543210"
}
```

**Your phone should ring!** 📞

---

## 📞 What Happens During the Call

1. **System:** "Please select your language: English, Tamil, Malayalam"
2. **You:** "English"
3. **System:** "Hello, this is an automated call from your ERP system regarding route R123. I need shipment charges and time availability."
4. **You:** "The charge is 500 rupees and I'm available from 2pm to 5pm"
5. **System:** "Thank you! Your information has been updated in our ERP system."
6. **Call ends**

---

## 🎯 Testing Different Agents

### Test PIZZA Agent
```bash
curl -X POST "http://localhost:8000/start-call?agent_type=PIZZA&phone_number=+91xxx"
```

### Test LOGISTICS Agent
```bash
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"
```

---

## 🔍 Monitoring Your Calls

### Check Call Status
```bash
curl http://localhost:8000/call-status/CAxxxxxxxxxxxx
```
(Replace with your actual call_sid)

### Check Server Health
```bash
curl http://localhost:8000/
```

### View Audio Files
```bash
ls -la temp_audio/
```

### Check MongoDB Data
```bash
# If you have MongoDB installed
mongo
use multi_agent_poc
db.calls.find().pretty()
db.collected_data.find().pretty()
```

---

## 🐛 Troubleshooting

### Issue: "Call not connecting"

**Solution:**
1. Check Twilio credentials in `.env`
2. Verify phone number format: `+919876543210` (with country code)
3. Check ngrok is running
4. Verify `WEBHOOK_BASE_URL` is correct

### Issue: "No audio during call"

**Solution:**
1. Check `WEBHOOK_BASE_URL` is publicly accessible
2. Verify ngrok HTTPS URL is correct
3. Check server logs for errors
4. Try restarting ngrok and server

### Issue: "LLM not responding"

**Solution:**
1. Verify `GEMINI_API_KEY` is correct
2. Check API quota/limits
3. Check server logs for errors

### Issue: "MongoDB connection failed"

**Solution:**
- System will use in-memory storage (this is OK for testing!)
- To fix: Start MongoDB or update `MONGODB_URL`

### Issue: "ElevenLabs not working"

**Solution:**
- System will use Twilio TTS fallback (this is OK!)
- To fix: Check `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID`

---

## 📊 View Logs

### Server Logs
Watch the terminal where you ran `python agent_voice_conversation.py`

You'll see:
```
INFO: Call connected: CAxxxx, Agent: LOGISTICS
INFO: CallSid: CAxxxx, Stage: language_selection, Speech: English
INFO: Processing vendor response: The charge is 500 rupees...
INFO: ✅ Call completed. Data: {'charge': '₹500', 'availability_time': '2pm to 5pm'}
```

### Twilio Logs
Visit: https://console.twilio.com/us1/monitor/logs/calls

---

## 🎨 Testing Text Conversation First (Recommended!)

Before making actual calls, test the conversation logic with text:

```bash
python agent_conversation.py
```

This is:
- ✅ Faster
- ✅ Cheaper (no call costs)
- ✅ Easier to debug
- ✅ Same LLM logic

**Example:**
```
🤖 Multi-Agent Conversational AI

Available Agents:
  1. PIZZA
  2. LOGISTICS

Select agent (1, 2, etc.) or press Enter for LOGISTICS: 2

Selected: LOGISTICS

🤖 AI: Hello, this is an automated call from your ERP system...

👤 You: The charge is 500 rupees and I'm available from 2pm to 5pm

🤖 AI: Thank you! I have charges as ₹500 and availability as 2pm to 5pm. Is this correct?

👤 You: yes

✅ Conversation Complete!
```

---

## 🔄 Complete Workflow

```
1. Install dependencies
   ↓
2. Configure .env
   ↓
3. Test with: python test_voice_system.py
   ↓
4. Start server: python agent_voice_conversation.py
   ↓
5. Start ngrok: ngrok http 8000
   ↓
6. Update WEBHOOK_BASE_URL in .env
   ↓
7. Restart server
   ↓
8. Make call: curl -X POST "http://localhost:8000/start-call..."
   ↓
9. Answer phone and talk!
   ↓
10. Check logs and MongoDB
```

---

## 📝 Quick Commands Reference

```bash
# Install
pip install -r requirements.txt

# Test
python test_voice_system.py

# Start server
python agent_voice_conversation.py

# Start ngrok (new terminal)
ngrok http 8000

# Make call (new terminal)
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"

# Check status
curl http://localhost:8000/call-status/CAxxxx

# View audio files
ls -la temp_audio/

# Test text conversation
python agent_conversation.py
```

---

## 🎯 Success Checklist

- [ ] Dependencies installed
- [ ] .env configured with API keys
- [ ] test_voice_system.py passes
- [ ] Server running on port 8000
- [ ] ngrok running and HTTPS URL copied
- [ ] WEBHOOK_BASE_URL updated in .env
- [ ] Server restarted
- [ ] Test call made
- [ ] Phone rings
- [ ] Conversation works
- [ ] Data saved to MongoDB

---

## 🎉 You're Done!

Your multi-agent voice conversation system is now running!

**Next Steps:**
- Add custom agents in `agent_config.py`
- Customize prompts and messages
- Add more languages
- Deploy to production

**Need Help?**
- Check `FLOW_EXPLANATION.md` for how it works
- Check `VISUAL_FLOW.md` for diagrams
- Check `TROUBLESHOOTING.md` for common issues
- Check `INDEX.md` for all documentation

---

## 💡 Pro Tips

1. **Test text first**: Use `agent_conversation.py` before voice calls
2. **Keep ngrok running**: Don't close the ngrok terminal
3. **Monitor logs**: Watch server terminal for errors
4. **Check audio files**: `ls temp_audio/` to see cached audio
5. **Use test phone**: Test with your own phone first

---

**Happy calling! 📞🚀**
