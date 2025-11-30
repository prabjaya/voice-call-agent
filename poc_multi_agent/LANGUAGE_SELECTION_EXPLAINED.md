# Language Selection - Complete Explanation

## 🌍 How Language Selection Works

The system asks the user to select their preferred language at the beginning of the call, then uses that language throughout the entire conversation.

---

## 📞 Step-by-Step Flow

### Step 1: Call Connects (Initial Stage)

```python
@app.post("/voice")
async def voice_webhook(request: Request):
    # When call connects, initialize session
    active_calls[call_sid] = {
        "agent_type": "LOGISTICS",
        "stage": "language_selection",  # ← First stage
        "language": None,                # ← Not selected yet
        "system_prompt": build_system_prompt(agent_type),
        "history": [],
        "collected_data": {}
    }
    
    # Get supported languages from agent_config.py
    languages = AGENT_METADATA[agent_type]["language_selection"]
    # Returns: ["English", "Tamil", "Malayalam"]
    
    # Create message
    lang_text = ", ".join(languages)
    message = f"Please select your language: {lang_text}"
    # Result: "Please select your language: English, Tamil, Malayalam"
    
    # Ask user
    twiml = generate_twiml(message, '/process-response', "English")
    return Response(content=twiml, media_type="application/xml")
```

**What User Hears:**
```
"Please select your language: English, Tamil, Malayalam"
```

---

### Step 2: User Responds with Language

**User says:** "Tamil" (or "English" or "Malayalam")

**Twilio converts speech to text** and sends to `/process-response`:
```python
SpeechResult = "Tamil"  # What user said
```

---

### Step 3: Language Detection

```python
@app.post("/process-response")
async def process_response(CallSid: str, SpeechResult: str):
    session = active_calls[CallSid]
    stage = session["stage"]  # "language_selection"
    
    if stage == "language_selection":
        # Detect language from user's speech
        language = detect_language(
            SpeechResult, 
            AGENT_METADATA[agent_type]["language_selection"]
        )
        # Returns: "Tamil"
```

**The `detect_language()` function:**

```python
def detect_language(speech: str, supported_languages: list) -> str:
    """Detect language from user speech"""
    speech_lower = speech.lower()  # Convert to lowercase
    
    # Check for Tamil
    if "tamil" in speech_lower or "தமிழ்" in speech:
        return "Tamil"
    
    # Check for Malayalam
    elif "malayalam" in speech_lower or "മലയാളം" in speech:
        return "Malayalam"
    
    # Default to English
    else:
        return "English"
```

**How it works:**
- User says "Tamil" → `speech_lower = "tamil"` → Returns "Tamil"
- User says "தமிழ்" → Detects Tamil script → Returns "Tamil"
- User says "Malayalam" → `speech_lower = "malayalam"` → Returns "Malayalam"
- User says "മലയാളം" → Detects Malayalam script → Returns "Malayalam"
- User says "English" or anything else → Returns "English"

---

### Step 4: Store Language in Session

```python
# Save detected language
session["language"] = "Tamil"  # ← Stored here!
session["stage"] = "welcome"   # Move to next stage

# Add to history
session["history"].append({
    "role": "user", 
    "content": "Selected language: Tamil"
})

# Save to database
db.save_call(CallSid, session)
```

**Session now looks like:**
```python
{
    "agent_type": "LOGISTICS",
    "stage": "welcome",
    "language": "Tamil",  # ← Language is stored!
    "history": [
        {"role": "user", "content": "Selected language: Tamil"}
    ],
    "collected_data": {}
}
```

---

### Step 5: Use Language for All Messages

```python
# Get welcome message in selected language
welcome_msg = AGENT_METADATA[agent_type]["welcome_msg"].get(language, "")
# Gets: "வணக்கம், ERP அமைப்பிலிருந்து ரூட் R123 பற்றிய அழைப்பு..."

# Add to history
session["history"].append({
    "role": "assistant", 
    "content": welcome_msg
})

# Generate voice in selected language
twiml = generate_twiml(welcome_msg, "/process-response", language)
```

**What User Hears (in Tamil):**
```
"வணக்கம், ERP அமைப்பிலிருந்து ரூட் R123 பற்றிய அழைப்பு. ஏற்றுமதி கட்டணம் மற்றும் நேரம் தேவை."
```

---

### Step 6: Language Used Throughout Call

From this point on, **every message** uses the selected language:

```python
# Get language from session
language = session.get("language", "English")  # "Tamil"

# Confirmation message
confirmation_msg = AGENT_METADATA[agent_type]["confirmation_msg"].get(language, "")
# Gets Tamil version: "நான் சேகரித்த தகவல்: கட்டணம் {charge}..."

# Retry message
retry_msg = AGENT_METADATA[agent_type]["retry_msg"].get(language, "")
# Gets Tamil version: "புரிந்தது. மீண்டும் தகவல் சேகரிக்கிறேன்..."

# Thank you message
thank_you_msg = AGENT_METADATA[agent_type]["positive_thank_you_msg"]
# Gets: "Thank you! Your information has been updated."
```

---

## 🎯 Complete Example Call

### English Call
```
System: "Please select your language: English, Tamil, Malayalam"
User: "English"
    ↓
System detects: "English"
    ↓
System: "Hello, this is an automated call from your ERP system..."
User: "500 rupees, 2pm to 5pm"
    ↓
System: "Let me confirm. Charges are ₹500, time is 2pm to 5pm. Correct?"
User: "Yes"
    ↓
System: "Thank you! Your information has been updated."
```

### Tamil Call
```
System: "Please select your language: English, Tamil, Malayalam"
User: "Tamil" or "தமிழ்"
    ↓
System detects: "Tamil"
    ↓
System: "வணக்கம், ERP அமைப்பிலிருந்து ரூட் R123 பற்றிய அழைப்பு..."
User: "500 ரூபாய், 2pm to 5pm"
    ↓
System: "நான் சேகரித்த தகவல்: கட்டணம் ₹500, நேரம் 2pm to 5pm. சரியா?"
User: "ஆம்" or "Yes"
    ↓
System: "Thank you! Your information has been updated."
```

### Malayalam Call
```
System: "Please select your language: English, Tamil, Malayalam"
User: "Malayalam" or "മലയാളം"
    ↓
System detects: "Malayalam"
    ↓
System: "നമസ്കാരം, ERP സിസ്റ്റത്തിൽ നിന്ന് റൂട്ട് R123 സംബന്ധിച്ച് കോൾ..."
User: "500 രൂപ, 2pm to 5pm"
    ↓
System: "ഞാൻ ശേഖരിച്ച വിവരങ്ങൾ: ചാർജ് ₹500, സമയം 2pm to 5pm. ശരിയാണോ?"
User: "അതെ" or "Yes"
    ↓
System: "Thank you! Your information has been updated."
```

---

## 🔍 Where Language is Used

### 1. Welcome Message
```python
welcome_msg = AGENT_METADATA[agent_type]["welcome_msg"].get(language, "")
```

### 2. Confirmation Message
```python
confirmation_template = AGENT_METADATA[agent_type]["confirmation_msg"].get(language, "")
```

### 3. Retry Message
```python
retry_msg = AGENT_METADATA[agent_type]["retry_msg"].get(language, "")
```

### 4. Clarify Message
```python
clarify_msg = AGENT_METADATA[agent_type]["clarify_msg"].get(language, "")
```

### 5. Voice Generation
```python
# Twilio language code for speech recognition
language_code = get_twilio_language_code(language)
# "Tamil" → "ta-IN"

# Twilio voice for TTS
voice = get_twilio_voice(language)
# "Tamil" → "Polly.Aditi-Neural"

# ElevenLabs voice generation
audio_url = elevenlabs_tts.generate_audio_url(message, language)
```

---

## 📊 Language Mapping

### Twilio Language Codes
```python
def get_twilio_language_code(language: str) -> str:
    """Get Twilio language code for speech recognition"""
    language_map = {
        "English": "en-US",
        "Tamil": "ta-IN",
        "Malayalam": "ml-IN"
    }
    return language_map.get(language, "en-US")
```

**What it does:**
- Tells Twilio which language to expect for speech recognition
- "Tamil" → Twilio listens for Tamil speech
- "Malayalam" → Twilio listens for Malayalam speech

### Twilio Voice Selection
```python
def get_twilio_voice(language: str) -> str:
    """Get Twilio voice for TTS fallback"""
    voice_map = {
        "English": "Polly.Joanna-Neural",
        "Tamil": "Polly.Aditi-Neural",
        "Malayalam": "Polly.Aditi-Neural"
    }
    return voice_map.get(language, "Polly.Joanna-Neural")
```

**What it does:**
- Selects appropriate voice for text-to-speech
- Used when ElevenLabs is not available

---

## 🎨 How Messages are Retrieved

### From agent_config.py:
```python
AGENT_METADATA = {
    "LOGISTICS": {
        "welcome_msg": {
            "English": "Hello, this is...",
            "Tamil": "வணக்கம்...",
            "Malayalam": "നമസ്കാരം..."
        }
    }
}
```

### In Code:
```python
# Get the language from session
language = session["language"]  # "Tamil"

# Get the message for that language
message = AGENT_METADATA["LOGISTICS"]["welcome_msg"].get("Tamil", "")
# Returns: "வணக்கம்..."
```

---

## 🔄 Language Persistence

The language is stored in **three places**:

### 1. In-Memory (Fast Access)
```python
active_calls[call_sid] = {
    "language": "Tamil"  # ← Stored here
}
```

### 2. MongoDB (Persistent)
```python
db.save_call(call_sid, session)
# Saves to database:
# {
#   "call_sid": "CAxxxx",
#   "language": "Tamil",  # ← Stored here
#   ...
# }
```

### 3. Conversation History
```python
session["history"].append({
    "role": "user",
    "content": "Selected language: Tamil"  # ← Recorded here
})
```

**Why?**
- In-memory: Fast access during call
- MongoDB: Survives server restarts
- History: Audit trail

---

## 🧪 Testing Language Selection

### Test English
```bash
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"
# When asked, say: "English"
```

### Test Tamil
```bash
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"
# When asked, say: "Tamil" or "தமிழ்"
```

### Test Malayalam
```bash
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"
# When asked, say: "Malayalam" or "മലയാളം"
```

---

## 💡 Key Points

1. **Language is asked first** - Before any other interaction
2. **Language is stored in session** - Used throughout the call
3. **Language affects everything** - All messages, voice, speech recognition
4. **Language is configurable** - All messages in `agent_config.py`
5. **Language is persistent** - Saved to MongoDB

---

## 🎯 Adding New Language

To add Hindi support:

### 1. Update agent_config.py
```python
"language_selection": ["English", "Tamil", "Malayalam", "Hindi"]

"welcome_msg": {
    "English": "Hello...",
    "Tamil": "வணக்கம்...",
    "Malayalam": "നമസ്കാരം...",
    "Hindi": "नमस्ते..."  # ← Add Hindi
}
```

### 2. Update detect_language()
```python
def detect_language(speech: str, supported_languages: list) -> str:
    speech_lower = speech.lower()
    if "tamil" in speech_lower:
        return "Tamil"
    elif "malayalam" in speech_lower:
        return "Malayalam"
    elif "hindi" in speech_lower:  # ← Add Hindi
        return "Hindi"
    else:
        return "English"
```

### 3. Update language mappings
```python
def get_twilio_language_code(language: str) -> str:
    language_map = {
        "English": "en-US",
        "Tamil": "ta-IN",
        "Malayalam": "ml-IN",
        "Hindi": "hi-IN"  # ← Add Hindi
    }
    return language_map.get(language, "en-US")
```

**That's it!** Hindi is now supported.

---

## ✅ Summary

**Language Selection Process:**

1. Call connects → System asks for language
2. User says language name → System detects it
3. Language stored in session → Used for all messages
4. All messages retrieved from agent_config.py in selected language
5. Voice generated in selected language
6. Speech recognition configured for selected language

**Everything is automatic after user selects language!** 🎉
