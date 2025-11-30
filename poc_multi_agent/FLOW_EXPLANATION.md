# Complete Flow Explanation - Voice Conversation System

## 🎯 Overview

The system makes automated phone calls, has natural conversations with users, extracts information using AI, and stores it in a database - all without hardcoding!

## 📞 Complete Call Flow (Step by Step)

### Step 1: Initiating a Call

```bash
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+919876543210"
```

**What Happens:**
```python
# In agent_voice_conversation.py

@app.post("/start-call")
async def start_call(agent_type: str, phone_number: str):
    # 1. Validate agent type exists in agent_config.py
    if agent_type not in AGENT_METADATA:
        return {"error": "Invalid agent_type"}
    
    # 2. Make Twilio API call to initiate phone call
    call = twilio_client.calls.create(
        to=phone_number,                    # User's phone number
        from_=TWILIO_PHONE_NUMBER,          # Your Twilio number
        url=f"{WEBHOOK_BASE_URL}/voice?agent_type={agent_type}",  # Webhook URL
        method='POST'
    )
    
    # 3. Return call SID (unique identifier)
    return {"success": True, "call_sid": call.sid}
```

**Result:** Twilio starts calling the phone number

---

### Step 2: Call Connects (Voice Webhook)

**When:** User answers the phone

**Twilio calls:** `POST /voice?agent_type=LOGISTICS`

```python
@app.post("/voice")
async def voice_webhook(request: Request):
    # 1. Get call details from Twilio
    form_data = await request.form()
    call_sid = form_data.get("CallSid")        # Unique call ID
    agent_type = request.query_params.get("agent_type")  # LOGISTICS
    
    # 2. Initialize call session in memory
    active_calls[call_sid] = {
        "agent_type": "LOGISTICS",
        "stage": "language_selection",         # First stage
        "language": None,                      # Not selected yet
        "system_prompt": build_system_prompt("LOGISTICS"),  # AI instructions
        "history": [],                         # Conversation history
        "collected_data": {}                   # Extracted information
    }
    
    # 3. Save to MongoDB (persistent storage)
    db.save_call(call_sid, active_calls[call_sid])
    
    # 4. Ask for language selection
    languages = ["English", "Tamil", "Malayalam"]
    message = "Please select your language: English, Tamil, Malayalam"
    
    # 5. Generate TwiML (Twilio's XML format)
    twiml = generate_twiml(message, '/process-response', "English")
    
    # 6. Return TwiML to Twilio
    return Response(content=twiml, media_type="application/xml")
```

**What User Hears:** "Please select your language: English, Tamil, Malayalam"

**TwiML Generated:**
```xml
<Response>
  <Gather input="speech" action="/process-response" timeout="10">
    <Play>https://your-server.com/audio/elevenlabs_abc123_english.mp3</Play>
  </Gather>
</Response>
```

---

### Step 3: Language Selection

**User Says:** "English"

**Twilio calls:** `POST /process-response` with `SpeechResult="English"`

```python
@app.post("/process-response")
async def process_response(CallSid: str, SpeechResult: str):
    # 1. Get call session
    session = active_calls[CallSid]
    stage = session["stage"]  # "language_selection"
    
    # 2. Detect language from speech
    if stage == "language_selection":
        language = detect_language(SpeechResult, ["English", "Tamil", "Malayalam"])
        # Returns: "English"
        
        # 3. Update session
        session["language"] = "English"
        session["stage"] = "welcome"
        session["history"].append({
            "role": "user", 
            "content": "Selected language: English"
        })
        
        # 4. Save to database
        db.save_call(CallSid, session)
        
        # 5. Get welcome message from agent_config.py
        welcome_msg = AGENT_METADATA["LOGISTICS"]["welcome_msg"]["English"]
        # "Hello, this is an automated call from your ERP system..."
        
        # 6. Add to history
        session["history"].append({
            "role": "assistant",
            "content": welcome_msg
        })
        
        # 7. Generate voice response
        twiml = generate_twiml(welcome_msg, "/process-response", "English")
        
        return Response(content=twiml, media_type="application/xml")
```

**What User Hears:** "Hello, this is an automated call from your ERP system regarding route R123. I need shipment charges and time availability."

---

### Step 4: Information Collection (The Magic Part!)

**User Says:** "The charge is 500 rupees and I'm available from 2pm to 5pm"

**Twilio calls:** `POST /process-response` with full speech

```python
@app.post("/process-response")
async def process_response(CallSid: str, SpeechResult: str):
    session = active_calls[CallSid]
    stage = session["stage"]  # Now "welcome" or "collecting"
    
    if stage in ["welcome", "collecting"]:
        # 1. Update stage
        session["stage"] = "collecting"
        
        # 2. Add user input to history
        session["history"].append({
            "role": "user",
            "content": "The charge is 500 rupees and I'm available from 2pm to 5pm"
        })
        
        # 3. Process with Gemini LLM (THE BRAIN!)
        llm_output = process_llm_response(SpeechResult, session)
        
        # ... (see next section for LLM processing)
```

---

### Step 5: LLM Processing (Conversational AI)

```python
def process_llm_response(user_input: str, session: Dict) -> LLMOutput:
    # 1. Get system prompt (from agent_config.py)
    system_prompt = session["system_prompt"]
    # Contains instructions like:
    # "You are an AI assistant for ERP Logistics.
    #  Extract: charges, availability_time.
    #  Return JSON with response_type, charge, availability_time, feedback"
    
    # 2. Build conversation messages
    messages = [
        SystemMessage(content=system_prompt),
        # Add all conversation history
        HumanMessage(content="Selected language: English"),
        AIMessage(content="Hello, this is an automated call..."),
        HumanMessage(content="The charge is 500 rupees and I'm available from 2pm to 5pm"),
        HumanMessage(content="Current collected data: {}")
    ]
    
    # 3. Call Gemini LLM
    response = llm.invoke(messages)
    
    # 4. LLM returns JSON
    # {
    #   "response_type": "THANK_YOU_RESPONSE",
    #   "charge": "₹500",
    #   "availability_time": "2pm to 5pm",
    #   "feedback": "Thank you! I have charges as ₹500 and availability as 2pm to 5pm."
    # }
    
    # 5. Parse JSON
    result_dict = json.loads(response.content)
    llm_output = LLMOutput(**result_dict)
    
    # 6. Update collected data
    if llm_output.charge:
        session["collected_data"]["charge"] = "₹500"
    if llm_output.availability_time:
        session["collected_data"]["availability_time"] = "2pm to 5pm"
    
    return llm_output
```

**LLM Intelligence:**
- Understands natural language (not hardcoded!)
- Extracts specific fields (charge, time)
- Decides if more info needed
- Generates natural responses

---

### Step 6: Response Handling

```python
# Back in process_response()

llm_output = process_llm_response(SpeechResult, session)
# llm_output.response_type = "THANK_YOU_RESPONSE"
# llm_output.feedback = "Thank you! I have charges as ₹500..."

# Add AI response to history
session["history"].append({
    "role": "assistant",
    "content": llm_output.feedback
})

# Save to database
db.save_call(CallSid, session)

language = session["language"]  # "English"

# Check response type
if llm_output.response_type == "THANK_YOU_RESPONSE":
    # ✅ ALL INFO COLLECTED!
    
    session["stage"] = "completed"
    thank_you_msg = AGENT_METADATA["LOGISTICS"]["positive_thank_you_msg"]
    # "Thank you! Your information has been updated in our ERP system."
    
    # Save collected data to database
    db.save_collected_data(CallSid, "LOGISTICS", session["collected_data"])
    # Saves: {"charge": "₹500", "availability_time": "2pm to 5pm"}
    
    # End call
    response = VoiceResponse()
    response.say(thank_you_msg)
    response.hangup()
    return Response(content=str(response), media_type="application/xml")

elif llm_output.response_type == "NEED_MORE_INFO":
    # ❓ MISSING INFORMATION
    
    # Ask follow-up question
    twiml = generate_twiml(llm_output.feedback, "/process-response", language)
    return Response(content=twiml, media_type="application/xml")

elif llm_output.response_type == "HANDOVER_TO_HUMAN":
    # 📞 USER WANTS HUMAN
    
    negative_msg = AGENT_METADATA["LOGISTICS"]["negative_thank_you_msg"]
    response = VoiceResponse()
    response.say(negative_msg)
    response.hangup()
    return Response(content=str(response), media_type="application/xml")
```

**What User Hears:** "Thank you! Your information has been updated in our ERP system."

**Call Ends**

---

### Step 7: Voice Generation (ElevenLabs + Audio Storage)

```python
def generate_twiml(message: str, action: str, language: str):
    # 1. Create TwiML response
    response = VoiceResponse()
    gather = response.gather(
        input='speech',
        action=action,
        timeout=10,
        language='en-US'  # For speech recognition
    )
    
    # 2. Try to generate ElevenLabs audio
    audio_url = elevenlabs_tts.generate_audio_url(message, language)
    
    if audio_url:
        # ✅ Use natural ElevenLabs voice
        gather.play(audio_url)
    else:
        # ⚠️ Fallback to Twilio TTS
        gather.say(message)
    
    return str(response)
```

**ElevenLabs Audio Generation:**
```python
# In elevenlabs_service.py

def generate_audio_url(text: str, language: str):
    # 1. Generate unique filename
    message_hash = hashlib.md5(text.encode()).hexdigest()
    filename = f"elevenlabs_{message_hash}_english.mp3"
    
    # 2. Check if file already exists (CACHING!)
    if audio_storage.file_exists(filename):
        return audio_storage.get_file_url(filename)
        # Returns: "https://your-server.com/audio/elevenlabs_abc123_english.mp3"
    
    # 3. Call ElevenLabs API
    response = requests.post(
        "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": ELEVENLABS_API_KEY},
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
    )
    
    # 4. Save audio file using audio_storage
    if response.status_code == 200:
        public_url = audio_storage.save_audio_file(response.content, filename)
        # Saves to: temp_audio/elevenlabs_abc123_english.mp3
        # Returns: "https://your-server.com/audio/elevenlabs_abc123_english.mp3"
        return public_url
```

**Audio Storage:**
```python
# In audio_storage.py

def save_audio_file(audio_content: bytes, filename: str):
    # 1. Save to file system
    file_path = "temp_audio/elevenlabs_abc123_english.mp3"
    with open(file_path, 'wb') as f:
        f.write(audio_content)
    
    # 2. Return public URL
    return f"{WEBHOOK_BASE_URL}/audio/{filename}"
```

**Serving Audio:**
```python
@app.get("/audio/{filename}")
async def serve_audio_file(filename: str):
    file_path = os.path.join("temp_audio", filename)
    
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    else:
        return {"error": "Audio file not found"}
```

---

## 🔄 Complete Flow Diagram

```
1. API Call: POST /start-call
   ↓
2. Twilio initiates phone call
   ↓
3. User answers → Twilio calls: POST /voice
   ↓
4. System: "Select language"
   ↓
5. User: "English" → Twilio calls: POST /process-response
   ↓
6. System: "Hello, I need charges and time"
   ↓
7. User: "500 rupees, 2pm to 5pm" → Twilio calls: POST /process-response
   ↓
8. Gemini LLM processes input
   ↓
9. LLM extracts: charge="₹500", time="2pm to 5pm"
   ↓
10. LLM decides: response_type="THANK_YOU_RESPONSE"
   ↓
11. Save to MongoDB
   ↓
12. System: "Thank you! Updated."
   ↓
13. Call ends
```

---

## 🧠 Key Components

### 1. **Twilio** (Voice Infrastructure)
- Makes phone calls
- Converts speech to text
- Plays audio responses
- Manages call flow

### 2. **Gemini LLM** (The Brain)
- Understands natural language
- Extracts information
- Decides next action
- Generates responses

### 3. **ElevenLabs** (Natural Voice)
- Converts text to natural speech
- Multi-language support
- High-quality voice

### 4. **Audio Storage** (File Management)
- Saves audio files
- Caches for reuse
- Automatic cleanup

### 5. **MongoDB** (Persistent Storage)
- Stores call sessions
- Stores collected data
- Survives server restarts

### 6. **Agent Config** (No Hardcoding!)
- Defines agent types
- Defines prompts
- Defines messages
- Easy to customize

---

## 💡 Example Scenarios

### Scenario 1: User Provides All Info at Once

```
System: "I need charges and time"
User: "500 rupees, 2pm to 5pm"
LLM: Extracts both → response_type="THANK_YOU_RESPONSE"
System: "Thank you!" → Call ends
```

### Scenario 2: User Provides Partial Info

```
System: "I need charges and time"
User: "500 rupees"
LLM: Extracts charge only → response_type="NEED_MORE_INFO"
System: "Thank you! What about availability time?"
User: "2pm to 5pm"
LLM: Extracts time → response_type="THANK_YOU_RESPONSE"
System: "Thank you!" → Call ends
```

### Scenario 3: User Asks Question

```
System: "I need charges and time"
User: "What route is this for?"
LLM: Detects question → response_type="NEED_MORE_INFO"
System: "This is for route R123. What are the charges?"
User: "500 rupees, 2pm to 5pm"
LLM: Extracts both → response_type="THANK_YOU_RESPONSE"
System: "Thank you!" → Call ends
```

### Scenario 4: User Wants Human

```
System: "I need charges and time"
User: "I want to speak to a human"
LLM: Detects transfer request → response_type="HANDOVER_TO_HUMAN"
System: "Transferring you..." → Call ends
```

---

## 🎯 Why This Works

### 1. **No Hardcoding**
- All prompts in `agent_config.py`
- LLM handles ANY user input
- Easy to add new agents

### 2. **Intelligent Conversation**
- LLM understands context
- Handles questions, confusion
- Natural follow-ups

### 3. **Reliable Storage**
- MongoDB for persistence
- In-memory for speed
- Survives restarts

### 4. **Natural Voice**
- ElevenLabs for quality
- Audio caching for speed
- Twilio TTS fallback

### 5. **Production Ready**
- Error handling
- Automatic cleanup
- Logging
- Monitoring

---

## 📊 Data Flow Summary

```
User Speech
    ↓
Twilio (Speech-to-Text)
    ↓
FastAPI Webhook
    ↓
Session Management (active_calls + MongoDB)
    ↓
Gemini LLM (Conversational AI)
    ↓
Field Extraction (charge, time, etc.)
    ↓
Response Generation (JSON)
    ↓
ElevenLabs (Text-to-Speech)
    ↓
Audio Storage (Caching)
    ↓
Twilio (Play Audio)
    ↓
User Hears Response
```

---

## 🎉 Summary

The system creates a **natural, intelligent conversation** by:

1. ✅ Using Twilio for voice infrastructure
2. ✅ Using Gemini LLM for understanding and intelligence
3. ✅ Using ElevenLabs for natural voice
4. ✅ Using MongoDB for reliable storage
5. ✅ Using audio_storage for efficient file management
6. ✅ Using agent_config.py for easy customization

**Result:** A production-ready voice AI system that can handle ANY conversation naturally, without hardcoding! 🚀
