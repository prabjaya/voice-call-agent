# Integration Guide: Text to Voice Conversation

This guide explains how `agent_voice_conversation.py` integrates MongoDB, Twilio, and ElevenLabs with the conversational AI logic from `agent_conversation.py`.

## 🔄 Key Integrations

### 1. MongoDB Integration

**From:** `database.py`  
**Purpose:** Persistent storage for call sessions and collected data

```python
# Initialize database
db = CallDatabase()

# Save call session
db.save_call(call_sid, session)

# Save collected data
db.save_collected_data(call_sid, agent_type, collected_data)

# Retrieve call (for server restarts)
call_data = db.get_call(call_sid)
```

**Benefits:**
- Calls survive server restarts
- Historical data for analytics
- Fallback to in-memory if MongoDB unavailable

### 2. Twilio Integration

**From:** `main.py` (original ERP system)  
**Purpose:** Voice call handling

```python
# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Start call
call = twilio_client.calls.create(
    to=phone_number,
    from_=TWILIO_PHONE_NUMBER,
    url=f"{WEBHOOK_BASE_URL}/voice?agent_type={agent_type}",
    method='POST'
)

# Generate TwiML response
response = VoiceResponse()
gather = response.gather(
    input='speech',
    action='/process-response',
    method='POST',
    timeout=10,
    speech_timeout='auto',
    language=get_twilio_language_code(language)
)
```

**Benefits:**
- Real phone call handling
- Speech-to-text conversion
- Multi-language support

### 3. ElevenLabs Integration

**From:** `elevenlabs_service.py`  
**Purpose:** Natural voice generation

```python
# Initialize ElevenLabs TTS
elevenlabs_tts = ElevenLabsTTS()

# Generate audio URL
audio_url = elevenlabs_tts.generate_audio_url(message, language)

# Use in TwiML
if audio_url:
    gather.play(audio_url)  # ElevenLabs voice
else:
    gather.say(message)     # Twilio TTS fallback
```

**Benefits:**
- Natural, human-like voice
- Multi-language support
- Audio caching for performance
- Automatic fallback to Twilio TTS

### 4. Conversational AI Logic

**From:** `agent_conversation.py`  
**Purpose:** Flexible LLM conversation handling

```python
# Build system prompt (from agent_config.py)
system_prompt = build_system_prompt(agent_type)

# Process user input with LLM
llm_output = process_llm_response(user_input, session)

# Handle response types
if llm_output.response_type == "THANK_YOU_RESPONSE":
    # All info collected
    db.save_collected_data(call_sid, agent_type, collected_data)
    # End call with thank you message
elif llm_output.response_type == "NEED_MORE_INFO":
    # Ask follow-up question
    twiml = generate_twiml(llm_output.feedback, "/process-response", language)
elif llm_output.response_type == "HANDOVER_TO_HUMAN":
    # Transfer to human agent
```

**Benefits:**
- Handles ANY user input (not hardcoded)
- Natural conversation flow
- Intelligent field extraction
- Multi-agent support via configuration

## 📊 Data Flow

```
User Phone Call
    ↓
Twilio (Speech-to-Text)
    ↓
agent_voice_conversation.py
    ↓
Gemini LLM (Conversational AI)
    ↓
Extract Fields (charge, time, etc.)
    ↓
MongoDB (Save Session)
    ↓
ElevenLabs (Text-to-Speech)
    ↓
Twilio (Play Audio)
    ↓
User Hears Response
```

## 🔧 Configuration (No Hardcoding)

### Agent Configuration (`agent_config.py`)

```python
AGENT_METADATA = {
    "LOGISTICS": {
        "system_prompt": "...",
        "welcome_msg": {"English": "...", "Tamil": "...", "Malayalam": "..."},
        "positive_thank_you_msg": "...",
        "negative_thank_you_msg": "...",
        "language_selection": ["English", "Tamil", "Malayalam"]
    }
}
```

### Environment Configuration (`.env`)

```env
GEMINI_API_KEY=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
MONGODB_URL=...
WEBHOOK_BASE_URL=...
```

## 🆚 Code Comparison

### Text Conversation (agent_conversation.py)

```python
# CLI input
user_input = input("👤 You: ").strip()

# Process with LLM
result = self.process_user_input(user_input)

# CLI output
print(f"🤖 AI: {result.feedback}")
```

### Voice Conversation (agent_voice_conversation.py)

```python
# Twilio webhook receives speech
SpeechResult: str = Form(...)

# Process with LLM (same logic!)
llm_output = process_llm_response(SpeechResult, session)

# Generate TwiML with voice
twiml = generate_twiml(llm_output.feedback, "/process-response", language)
return Response(content=twiml, media_type="application/xml")
```

**Key Insight:** The LLM processing logic is identical! Only the input/output methods differ.

## 🎯 Session Management

### In-Memory Cache (Fast Access)

```python
active_calls: Dict[str, Dict[str, Any]] = {}

# Store session
active_calls[call_sid] = {
    "agent_type": agent_type,
    "stage": "collecting",
    "language": "English",
    "history": [...],
    "collected_data": {...}
}
```

### MongoDB Persistence (Survives Restarts)

```python
# Save to database
db.save_call(call_sid, active_calls[call_sid])

# Load from database (if not in memory)
if call_sid not in active_calls:
    call_data = db.get_call(call_sid)
    if call_data:
        active_calls[call_sid] = call_data
```

## 🔄 Call Stages

1. **language_selection**
   - Ask user to select language
   - Detect language from speech

2. **welcome**
   - Greet user in selected language
   - Explain purpose

3. **collecting**
   - Process user responses with LLM
   - Extract required fields
   - Ask follow-up questions

4. **completed**
   - All info collected
   - Save to database
   - Thank user and end call

## 🎨 Adding Custom Fields

### 1. Update `agent_config.py`

```python
"YOUR_AGENT": {
    "system_prompt": "Extract: field1, field2, field3",
    ...
}
```

### 2. Update `LLMOutput` Model

```python
class LLMOutput(BaseModel):
    response_type: Literal[...]
    
    # Add your fields
    field1: Optional[str] = None
    field2: Optional[str] = None
    field3: Optional[str] = None
    
    feedback: str
```

### 3. Update `build_system_prompt()`

```python
if agent_type == "YOUR_AGENT":
    conversational_prompt += """
  "field1": "extracted value or null",
  "field2": "extracted value or null",
  "field3": "extracted value or null",
"""
```

### 4. Update `process_llm_response()`

```python
elif agent_type == "YOUR_AGENT":
    if llm_output.field1:
        collected_data["field1"] = llm_output.field1
    if llm_output.field2:
        collected_data["field2"] = llm_output.field2
    if llm_output.field3:
        collected_data["field3"] = llm_output.field3
```

## 🚀 Deployment Checklist

- [ ] Configure `.env` with all API keys
- [ ] Start MongoDB server
- [ ] Expose server with ngrok: `ngrok http 8000`
- [ ] Update `WEBHOOK_BASE_URL` in `.env`
- [ ] Configure Twilio webhook URLs
- [ ] Test with `/start-call` endpoint
- [ ] Monitor logs for errors
- [ ] Check MongoDB for saved data

## 📈 Monitoring

### Check Active Calls

```python
@app.get("/active-calls")
async def get_active_calls():
    return {
        "active_calls": len(active_calls),
        "calls": list(active_calls.keys())
    }
```

### Check Database

```python
@app.get("/all-calls")
async def get_all_calls(limit: int = 50):
    calls = db.get_all_calls(limit)
    return {"total": len(calls), "calls": calls}
```

### Check Analytics

```python
@app.get("/analytics")
async def get_analytics():
    return db.get_analytics()
```

## 🎓 Learning Resources

- **Twilio Voice**: https://www.twilio.com/docs/voice
- **ElevenLabs API**: https://elevenlabs.io/docs
- **Gemini LLM**: https://ai.google.dev/docs
- **MongoDB**: https://www.mongodb.com/docs
- **FastAPI**: https://fastapi.tiangolo.com

## 💡 Tips

1. **Test Text First**: Use `agent_conversation.py` to test conversation logic before voice
2. **Use ngrok**: Essential for Twilio webhook testing
3. **Monitor Logs**: Watch for LLM parsing errors
4. **Cache Audio**: ElevenLabs audio files are cached for performance
5. **Fallback Strategy**: System gracefully handles service failures

## 🐛 Common Issues

### Issue: Call connects but no audio
**Solution:** Check `WEBHOOK_BASE_URL` is publicly accessible

### Issue: LLM returns invalid JSON
**Solution:** Check system prompt format, add fallback parsing

### Issue: MongoDB connection failed
**Solution:** System uses in-memory storage, check `MONGODB_URL`

### Issue: ElevenLabs quota exceeded
**Solution:** System falls back to Twilio TTS automatically

## 🎉 Success Criteria

✅ Call connects successfully  
✅ Language selection works  
✅ LLM processes user input  
✅ Fields extracted correctly  
✅ Data saved to MongoDB  
✅ Voice sounds natural (ElevenLabs)  
✅ Call ends gracefully  

---

**Ready to integrate?** Start with `agent_voice_conversation.py` and follow this guide!
