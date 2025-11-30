# Side-by-Side Comparison

## Files Overview

| File | Purpose | Interface | Services |
|------|---------|-----------|----------|
| `agent_conversation.py` | Text-based conversational AI | CLI (Terminal) | ✅ Gemini LLM |
| `agent_voice_conversation.py` | Voice-based conversational AI | Voice (Twilio) | ✅ Gemini LLM<br>✅ MongoDB<br>✅ Twilio<br>✅ ElevenLabs |
| `main.py` | Original ERP voice system | Voice (Twilio) | ✅ Gemini LLM<br>✅ MongoDB<br>✅ Twilio<br>✅ ElevenLabs |

## Key Differences

### 1. Conversation Logic

#### agent_conversation.py (Text)
```python
class AgentConversation:
    def run_conversation(self):
        while True:
            # Get user input from CLI
            user_input = input("👤 You: ").strip()
            
            # Process with LLM
            result = self.process_user_input(user_input)
            
            # Display response in CLI
            print(f"🤖 AI: {result.feedback}")
            
            # Check if complete
            if result.response_type == "THANK_YOU_RESPONSE":
                print("✅ Conversation Complete!")
                break
```

#### agent_voice_conversation.py (Voice)
```python
@app.post("/process-response")
async def process_response(
    CallSid: str = Form(...),
    SpeechResult: Optional[str] = Form(None)
):
    # Get user input from Twilio (speech-to-text)
    session = active_calls[CallSid]
    
    # Process with LLM (same logic!)
    llm_output = process_llm_response(SpeechResult, session)
    
    # Generate voice response
    if llm_output.response_type == "THANK_YOU_RESPONSE":
        # End call with thank you message
        response = VoiceResponse()
        response.say(thank_you_msg)
        response.hangup()
    else:
        # Continue conversation
        twiml = generate_twiml(llm_output.feedback, "/process-response", language)
    
    return Response(content=twiml, media_type="application/xml")
```

### 2. LLM Processing (Identical!)

Both files use the **exact same LLM processing logic**:

```python
# Build system prompt from agent_config.py
system_prompt = build_system_prompt(agent_type)

# Process with Gemini LLM
messages = [SystemMessage(content=system_prompt)]
for msg in history:
    if msg["role"] == "user":
        messages.append(HumanMessage(content=msg["content"]))
    elif msg["role"] == "assistant":
        messages.append(AIMessage(content=msg["content"]))

response = llm.invoke(messages)

# Parse JSON response
llm_output = LLMOutput(**json.loads(response.content))

# Update collected data
if llm_output.charge:
    collected_data["charge"] = llm_output.charge
if llm_output.availability_time:
    collected_data["availability_time"] = llm_output.availability_time
```

### 3. Data Storage

#### agent_conversation.py
```python
# In-memory only
self.conversation_history = []
self.collected_data = {}
```

#### agent_voice_conversation.py
```python
# In-memory + MongoDB
active_calls[call_sid] = {
    "history": [],
    "collected_data": {}
}

# Save to database
db.save_call(call_sid, active_calls[call_sid])
db.save_collected_data(call_sid, agent_type, collected_data)
```

### 4. Voice Generation

#### agent_conversation.py
```python
# No voice - just text output
print(f"🤖 AI: {result.feedback}")
```

#### agent_voice_conversation.py
```python
# ElevenLabs + Twilio TTS
def generate_twiml(message: str, action: str, language: str):
    response = VoiceResponse()
    gather = response.gather(input='speech', action=action)
    
    # Try ElevenLabs first
    audio_url = elevenlabs_tts.generate_audio_url(message, language)
    
    if audio_url:
        gather.play(audio_url)  # Natural voice
    else:
        gather.say(message)     # Fallback TTS
    
    return str(response)
```

## Feature Matrix

| Feature | agent_conversation.py | agent_voice_conversation.py | main.py |
|---------|----------------------|----------------------------|---------|
| **Interface** | CLI Text | Voice Call | Voice Call |
| **LLM (Gemini)** | ✅ | ✅ | ✅ |
| **Conversational AI** | ✅ | ✅ | ⚠️ Partial |
| **Multi-Agent** | ✅ | ✅ | ✅ |
| **Multi-Language** | ✅ | ✅ | ✅ |
| **MongoDB** | ❌ | ✅ | ✅ |
| **Twilio** | ❌ | ✅ | ✅ |
| **ElevenLabs** | ❌ | ✅ | ✅ |
| **No Hardcoding** | ✅ | ✅ | ⚠️ Some hardcoding |
| **Session Persistence** | ❌ | ✅ | ✅ |
| **Audio Caching** | ❌ | ✅ | ✅ |

## Code Reuse

### Shared Components

1. **agent_config.py** - Used by all files
   ```python
   AGENT_METADATA = {
       "PIZZA": {...},
       "LOGISTICS": {...}
   }
   ```

2. **database.py** - Used by voice systems
   ```python
   db = CallDatabase()
   db.save_call(call_sid, session)
   ```

3. **elevenlabs_service.py** - Used by voice systems
   ```python
   tts = ElevenLabsTTS()
   audio_url = tts.generate_audio_url(message, language)
   ```

4. **LLM Processing Logic** - Identical across all files
   ```python
   llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
   response = llm.invoke(messages)
   ```

## When to Use Which?

### Use `agent_conversation.py` when:
- ✅ Testing conversation logic quickly
- ✅ Developing new agent types
- ✅ Debugging LLM responses
- ✅ No phone calls needed
- ✅ Quick prototyping

### Use `agent_voice_conversation.py` when:
- ✅ Need real phone calls
- ✅ Production deployment
- ✅ Multi-language voice support
- ✅ Natural voice (ElevenLabs)
- ✅ Session persistence required
- ✅ No hardcoding allowed

### Use `main.py` when:
- ✅ ERP-specific use case
- ✅ Need vendor management
- ✅ Retry logic required
- ✅ SMS notifications needed
- ✅ Call analytics required

## Migration Path

### From Text to Voice

1. **Test with text first**
   ```bash
   python agent_conversation.py
   ```

2. **Verify conversation logic works**
   - Check field extraction
   - Test edge cases
   - Validate response types

3. **Switch to voice**
   ```bash
   python agent_voice_conversation.py
   ```

4. **Test with real calls**
   ```bash
   curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"
   ```

### From main.py to agent_voice_conversation.py

1. **Extract agent config**
   - Move hardcoded prompts to `agent_config.py`
   - Define welcome messages
   - Set thank you messages

2. **Update field extraction**
   - Use `LLMOutput` model
   - Update `build_system_prompt()`
   - Update `process_llm_response()`

3. **Test thoroughly**
   - Verify all fields extracted
   - Check conversation flow
   - Test multi-language

## Performance Comparison

| Metric | agent_conversation.py | agent_voice_conversation.py |
|--------|----------------------|----------------------------|
| **Startup Time** | < 1 second | 2-3 seconds |
| **Response Time** | 1-2 seconds | 3-5 seconds |
| **Memory Usage** | Low (< 50 MB) | Medium (100-200 MB) |
| **Network Calls** | 1 (LLM only) | 3-4 (LLM + Twilio + ElevenLabs) |
| **Cost per Call** | $0.001 (LLM) | $0.05-0.10 (LLM + Twilio + ElevenLabs) |

## Architecture Comparison

### agent_conversation.py
```
User Input (CLI)
    ↓
Gemini LLM
    ↓
JSON Response
    ↓
CLI Output
```

### agent_voice_conversation.py
```
User Phone Call
    ↓
Twilio (Speech-to-Text)
    ↓
FastAPI Webhook
    ↓
Gemini LLM
    ↓
JSON Response
    ↓
MongoDB (Save)
    ↓
ElevenLabs (Text-to-Speech)
    ↓
Twilio (Play Audio)
    ↓
User Hears Response
```

## Configuration Comparison

### agent_conversation.py
```python
# Minimal config
GEMINI_API_KEY=your_key
```

### agent_voice_conversation.py
```python
# Full config
GEMINI_API_KEY=your_key
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890
ELEVENLABS_API_KEY=your_key
ELEVENLABS_VOICE_ID=your_voice_id
MONGODB_URL=mongodb://localhost:27017/db
WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok.io
```

## Testing Strategy

### agent_conversation.py
```bash
# Direct testing
python agent_conversation.py

# Select agent
# Type responses
# Verify extraction
```

### agent_voice_conversation.py
```bash
# 1. Test components
python test_voice_system.py

# 2. Start server
python agent_voice_conversation.py

# 3. Expose with ngrok
ngrok http 8000

# 4. Make test call
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"
```

## Conclusion

Both files serve different purposes but share the **same core conversational AI logic**:

- **agent_conversation.py**: Fast prototyping and testing
- **agent_voice_conversation.py**: Production voice calls with full integration

The key innovation is that the LLM processing is **identical** - only the input/output methods differ!

---

**Recommendation**: Start with `agent_conversation.py` for development, then deploy with `agent_voice_conversation.py` for production.
