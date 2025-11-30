# Detailed Code Changes - Line by Line

## 📍 Location 1: Added Confirmation Message Builder Function

**File:** `agent_voice_conversation.py`  
**Line:** After `detect_language()` function (around line 330)

```python
def build_confirmation_message(collected_data: Dict[str, Any], agent_type: str, language: str) -> str:
    """Build confirmation message based on collected data"""
    
    if agent_type == "LOGISTICS":
        charge = collected_data.get("charge", "not provided")
        time = collected_data.get("availability_time", "not provided")
        
        if language == "Tamil":
            return f"நான் சேகரித்த தகவல்: கட்டணம் {charge}, கிடைக்கும் நேரம் {time}. இது சரியா?"
        elif language == "Malayalam":
            return f"ഞാൻ ശേഖരിച്ച വിവരങ്ങൾ: ചാർജ് {charge}, ലഭ്യമായ സമയം {time}. ഇത് ശരിയാണോ?"
        else:
            return f"Let me confirm the information I collected. The charges are {charge}, and your availability time is {time}. Is this correct? Please say yes or no."
    
    elif agent_type == "PIZZA":
        pizza_type = collected_data.get("pizza_type", "not provided")
        size = collected_data.get("size", "not provided")
        address = collected_data.get("delivery_address", "not provided")
        time = collected_data.get("delivery_time", "not provided")
        
        if language == "Tamil":
            return f"உங்கள் ஆர்டர்: {size} {pizza_type} பீட்சா, முகவரி {address}, நேரம் {time}. இது சரியா?"
        elif language == "Malayalam":
            return f"നിങ്ങളുടെ ഓർഡർ: {size} {pizza_type} പിസ്സ, വിലാസം {address}, സമയം {time}. ഇത് ശരിയാണോ?"
        else:
            return f"Let me confirm your order. You want a {size} {pizza_type} pizza, delivered to {address} at {time}. Is this correct? Please say yes or no."
    
    else:
        return "Let me confirm the information I collected. Is this correct? Please say yes or no."
```

---

## 📍 Location 2: Improved Error Handling in start_call()

**File:** `agent_voice_conversation.py`  
**Line:** In `start_call()` function (around line 360)

### BEFORE:
```python
@app.post("/start-call")
async def start_call(agent_type: str = "LOGISTICS", phone_number: str = "+919876543210"):
    """Start a call with specified agent type"""
    
    if agent_type not in AGENT_METADATA:
        return {"error": f"Invalid agent_type. Choose: {list(AGENT_METADATA.keys())}"}
    
    if not twilio_client:
        return {"error": "Twilio not configured"}
    
    try:
        call = twilio_client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{WEBHOOK_BASE_URL}/voice?agent_type={agent_type}",
            method='POST'
        )
        
        return {
            "success": True,
            "call_sid": call.sid,
            "agent_type": agent_type,
            "phone_number": phone_number
        }
    except Exception as e:
        logger.error(f"Error starting call: {e}")
        return {"success": False, "error": str(e)}
```

### AFTER:
```python
@app.post("/start-call")
async def start_call(agent_type: str = "LOGISTICS", phone_number: str = "+919876543210"):
    """Start a call with specified agent type"""
    
    if agent_type not in AGENT_METADATA:
        logger.error(f"❌ Invalid agent_type: {agent_type}")  # ✅ ADDED LOGGING
        return {"error": f"Invalid agent_type. Choose: {list(AGENT_METADATA.keys())}"}
    
    if not twilio_client:
        logger.error("❌ Twilio client not configured")  # ✅ ADDED LOGGING
        return {"error": "Service temporarily unavailable. Twilio is not configured. Please contact support."}  # ✅ BETTER ERROR MESSAGE
    
    try:
        logger.info(f"📞 Initiating call - Agent: {agent_type}, Phone: {phone_number}")  # ✅ ADDED LOGGING
        
        call = twilio_client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{WEBHOOK_BASE_URL}/voice?agent_type={agent_type}",
            method='POST'
        )
        
        logger.info(f"✅ Call initiated successfully - CallSid: {call.sid}")  # ✅ ADDED LOGGING
        
        return {
            "success": True,
            "call_sid": call.sid,
            "agent_type": agent_type,
            "phone_number": phone_number
        }
    except Exception as e:
        logger.error(f"❌ Error starting call: {e}", exc_info=True)  # ✅ ADDED STACK TRACE
        return {
            "success": False, 
            "error": "Service temporarily unavailable. Unable to initiate call. Please try again later or contact support."  # ✅ BETTER ERROR MESSAGE
        }
```

---

## 📍 Location 3: Added Confirmation Logic in process_response()

**File:** `agent_voice_conversation.py`  
**Line:** In `process_response()` function, in the collecting stage (around line 480)

### BEFORE:
```python
# Stage 2 & 3: Welcome + Collecting Information
if stage in ["welcome", "collecting"]:
    session["stage"] = "collecting"
    session["history"].append({"role": "user", "content": SpeechResult})
    
    # Process with LLM
    try:
        llm_output = process_llm_response(SpeechResult, session)
        
        # Add AI response to history
        session["history"].append({"role": "assistant", "content": llm_output.feedback})
        
        # Save to database
        active_calls[CallSid] = session
        db.save_call(CallSid, session)
        
        language = session.get("language", "English")
        
        # Handle response type
        if llm_output.response_type == "THANK_YOU_RESPONSE":
            # All info collected
            session["stage"] = "completed"
            thank_you_msg = AGENT_METADATA[agent_type]["positive_thank_you_msg"]
            
            # Save collected data
            db.save_collected_data(CallSid, agent_type, session["collected_data"])
            
            logger.info(f"✅ Call completed. Data: {session['collected_data']}")
            
            # End call
            response = VoiceResponse()
            response.say(thank_you_msg, voice=get_twilio_voice(language), language=get_twilio_language_code(language))
            response.hangup()
            return Response(content=str(response), media_type="application/xml")
```

### AFTER:
```python
# Stage 2 & 3: Welcome + Collecting Information
if stage in ["welcome", "collecting"]:
    session["stage"] = "collecting"
    session["history"].append({"role": "user", "content": SpeechResult})
    
    # Process with LLM
    try:
        llm_output = process_llm_response(SpeechResult, session)
        
        # ✅ ADDED: Log LLM response
        logger.info(f"📝 LLM Response - Type: {llm_output.response_type}, Feedback: {llm_output.feedback[:100]}...")
        
        # Add AI response to history
        session["history"].append({"role": "assistant", "content": llm_output.feedback})
        
        # Save to database
        active_calls[CallSid] = session
        db.save_call(CallSid, session)
        
        language = session.get("language", "English")
        
        # Handle response type
        if llm_output.response_type == "THANK_YOU_RESPONSE":
            # ✅ CHANGED: Instead of ending call, go to confirmation stage
            session["stage"] = "confirmation"
            
            # ✅ ADDED: Build confirmation message
            confirmation_msg = build_confirmation_message(session["collected_data"], agent_type, language)
            
            # ✅ ADDED: Log confirmation
            logger.info(f"📋 Confirmation Stage - Data: {session['collected_data']}")
            logger.info(f"🔊 Confirmation Message: {confirmation_msg}")
            
            # Save to database
            db.save_call(CallSid, session)
            
            # ✅ ADDED: Ask for confirmation
            twiml = generate_twiml(confirmation_msg, "/process-response", language)
            return Response(content=twiml, media_type="application/xml")
```

---

## 📍 Location 4: Added Handover Logging

**File:** `agent_voice_conversation.py`  
**Line:** In `process_response()` function, handover section (around line 510)

### BEFORE:
```python
elif llm_output.response_type == "HANDOVER_TO_HUMAN":
    # Transfer to human
    negative_msg = AGENT_METADATA[agent_type]["negative_thank_you_msg"]
    response = VoiceResponse()
    response.say(negative_msg, voice=get_twilio_voice(language), language=get_twilio_language_code(language))
    response.hangup()
    return Response(content=str(response), media_type="application/xml")
```

### AFTER:
```python
elif llm_output.response_type == "HANDOVER_TO_HUMAN":
    # Transfer to human
    logger.info(f"📞 Handover to human requested - CallSid: {CallSid}")  # ✅ ADDED LOGGING
    negative_msg = AGENT_METADATA[agent_type]["negative_thank_you_msg"]
    logger.info(f"🔊 Response Message: {negative_msg}")  # ✅ ADDED LOGGING
    
    response = VoiceResponse()
    response.say(negative_msg, voice=get_twilio_voice(language), language=get_twilio_language_code(language))
    response.hangup()
    return Response(content=str(response), media_type="application/xml")
```

---

## 📍 Location 5: Added Need More Info Logging

**File:** `agent_voice_conversation.py`  
**Line:** In `process_response()` function, need more info section (around line 520)

### BEFORE:
```python
else:
    # Need more info
    twiml = generate_twiml(llm_output.feedback, "/process-response", language)
    return Response(content=twiml, media_type="application/xml")
```

### AFTER:
```python
else:
    # Need more info
    logger.info(f"❓ Need more info - CallSid: {CallSid}")  # ✅ ADDED LOGGING
    logger.info(f"🔊 Response Message: {llm_output.feedback}")  # ✅ ADDED LOGGING
    
    twiml = generate_twiml(llm_output.feedback, "/process-response", language)
    return Response(content=twiml, media_type="application/xml")
```

---

## 📍 Location 6: Improved Error Handling in Collecting Stage

**File:** `agent_voice_conversation.py`  
**Line:** In `process_response()` function, exception handler (around line 530)

### BEFORE:
```python
except Exception as e:
    logger.error(f"Error processing response: {str(e)}")
    message = "I'm sorry, there was a technical issue. Could you please repeat?"
    language = session.get("language", "English")
    twiml = generate_twiml(message, "/process-response", language)
    return Response(content=twiml, media_type="application/xml")
```

### AFTER:
```python
except Exception as e:
    # ✅ CHANGED: Better error logging with stack trace
    logger.error(f"❌ Error processing response for CallSid {CallSid}: {str(e)}", exc_info=True)
    
    # ✅ CHANGED: Better error message
    message = "I apologize, but our system is experiencing technical difficulties. Please try again later or contact support."
    language = session.get("language", "English")
    logger.info(f"🔊 Error Response Message: {message}")  # ✅ ADDED LOGGING
    
    twiml = generate_twiml(message, "/process-response", language)
    return Response(content=twiml, media_type="application/xml")
```

---

## 📍 Location 7: Added Complete Confirmation Stage Handler

**File:** `agent_voice_conversation.py`  
**Line:** After collecting stage, before default handler (around line 540)

### COMPLETELY NEW CODE ADDED:
```python
# ✅ NEW STAGE: Confirmation
if stage == "confirmation":
    session["history"].append({"role": "user", "content": SpeechResult})
    
    try:
        # Check if user confirmed
        confirmation_response = SpeechResult.lower()
        logger.info(f"✅ Confirmation Response - CallSid: {CallSid}, Response: {SpeechResult}")
        
        if any(word in confirmation_response for word in ["yes", "correct", "right", "confirm", "ok", "okay", "yeah", "yep"]):
            # Confirmed - End call
            session["stage"] = "completed"
            thank_you_msg = AGENT_METADATA[agent_type]["positive_thank_you_msg"]
            
            # Save collected data
            db.save_collected_data(CallSid, agent_type, session["collected_data"])
            
            logger.info(f"✅ Call completed successfully - CallSid: {CallSid}")
            logger.info(f"📊 Final Data: {session['collected_data']}")
            logger.info(f"🔊 Thank You Message: {thank_you_msg}")
            
            # End call
            response = VoiceResponse()
            response.say(thank_you_msg, voice=get_twilio_voice(language), language=get_twilio_language_code(language))
            response.hangup()
            return Response(content=str(response), media_type="application/xml")
        
        elif any(word in confirmation_response for word in ["no", "wrong", "incorrect", "change", "modify"]):
            # Not confirmed - Go back to collecting
            logger.info(f"🔄 User wants to modify - CallSid: {CallSid}")
            
            session["stage"] = "collecting"
            session["collected_data"] = {}  # Clear collected data
            
            retry_msg = "I understand. Let me collect the information again. Please provide the details."
            logger.info(f"🔊 Retry Message: {retry_msg}")
            
            # Save to database
            db.save_call(CallSid, session)
            
            twiml = generate_twiml(retry_msg, "/process-response", language)
            return Response(content=twiml, media_type="application/xml")
        
        else:
            # Unclear response - Ask again
            logger.info(f"❓ Unclear confirmation response - CallSid: {CallSid}")
            
            clarify_msg = "I didn't understand. Please say 'yes' if the information is correct, or 'no' if you want to change it."
            logger.info(f"🔊 Clarification Message: {clarify_msg}")
            
            twiml = generate_twiml(clarify_msg, "/process-response", language)
            return Response(content=twiml, media_type="application/xml")
    
    except Exception as e:
        # Better error handling for confirmation stage
        logger.error(f"❌ Error processing confirmation for CallSid {CallSid}: {str(e)}", exc_info=True)
        
        message = "I apologize, but our system is experiencing technical difficulties. Your information has been saved. We will contact you shortly."
        language = session.get("language", "English")
        logger.info(f"🔊 Error Response Message: {message}")
        
        response = VoiceResponse()
        response.say(message, voice=get_twilio_voice(language), language=get_twilio_language_code(language))
        response.hangup()
        return Response(content=str(response), media_type="application/xml")
```

---

## 📊 Summary of Changes

| Location | Change Type | Lines Added | Description |
|----------|-------------|-------------|-------------|
| After `detect_language()` | New Function | ~30 lines | `build_confirmation_message()` function |
| `start_call()` | Improved Logging | ~5 lines | Added logging and better error messages |
| Collecting Stage | Confirmation Logic | ~10 lines | Changed to go to confirmation instead of ending |
| Handover Section | Logging | ~2 lines | Added logging for handover |
| Need More Info | Logging | ~2 lines | Added logging for follow-up questions |
| Error Handler | Better Errors | ~3 lines | Improved error messages and logging |
| New Stage | Confirmation Handler | ~60 lines | Complete confirmation stage logic |

**Total Lines Added:** ~112 lines  
**Total Lines Modified:** ~20 lines  
**New Functions:** 1 (`build_confirmation_message`)  
**New Stages:** 1 (`confirmation`)

---

## 🎯 Key Code Patterns Added

### Pattern 1: Logging with Emojis
```python
logger.info(f"📞 Initiating call...")
logger.info(f"✅ Success...")
logger.error(f"❌ Error...")
logger.info(f"🔊 Response Message: {message}")
```

### Pattern 2: Better Error Messages
```python
# Instead of:
return {"error": "Twilio not configured"}

# Now:
return {"error": "Service temporarily unavailable. Twilio is not configured. Please contact support."}
```

### Pattern 3: Confirmation Flow
```python
if llm_output.response_type == "THANK_YOU_RESPONSE":
    session["stage"] = "confirmation"  # Go to confirmation
    confirmation_msg = build_confirmation_message(...)
    twiml = generate_twiml(confirmation_msg, "/process-response", language)
```

All changes are in `poc_multi_agent/agent_voice_conversation.py`! 🚀
