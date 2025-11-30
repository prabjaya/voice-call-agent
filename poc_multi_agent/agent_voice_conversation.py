"""
Multi-Agent Voice Conversation System
Integrates MongoDB, Twilio, and ElevenLabs with agent_conversation.py logic
No hardcoding - fully configurable via agent_config.py
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import Response, FileResponse
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agent_config import AGENT_METADATA
from elevenlabs_service import ElevenLabsTTS
from database import CallDatabase
from audio_storage import init_audio_storage
from dotenv import load_dotenv
import os
import json
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Agent Voice Conversation")

# Configuration from .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")

# Validate environment variables
if not GEMINI_API_KEY:
    logger.error("❌ GEMINI_API_KEY not found in .env file")
if not TWILIO_ACCOUNT_SID:
    logger.error("❌ TWILIO_ACCOUNT_SID not found in .env file")

# Initialize services
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else None
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.7
)

# Initialize audio storage (like original code)
audio_storage = init_audio_storage(WEBHOOK_BASE_URL)

# Initialize ElevenLabs with audio_storage (like original code)
elevenlabs_tts = ElevenLabsTTS(audio_storage=audio_storage)

# Initialize database
db = CallDatabase()

# Active calls storage
active_calls: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup (like original code)"""
    logger.info("Starting Multi-Agent Voice Conversation System")
    logger.info(f"MongoDB connection: {'Connected' if db.client else 'Using memory fallback'}")
    logger.info(f"Audio storage: {audio_storage.audio_dir}")
    logger.info(f"ElevenLabs: {'Configured' if elevenlabs_tts.api_key else 'Not configured (will use Twilio TTS)'}")
    logger.info(f"Active calls in memory: {len(active_calls)}")
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown (like original code)"""
    logger.info("Shutting down Multi-Agent Voice Conversation System")
    
    # Save any remaining active calls to database
    for call_sid, call_context in active_calls.items():
        try:
            db.save_call(call_sid, call_context)
            logger.info(f"Saved call {call_sid} to database on shutdown")
        except Exception as e:
            logger.error(f"Error saving call {call_sid} on shutdown: {str(e)}")
    
    # Close database connection
    if db.client:
        db.close_connection()
    
    # Cleanup old audio files
    try:
        audio_storage.cleanup_old_files(max_age_hours=24)
    except Exception as e:
        logger.error(f"Error cleaning up audio files: {str(e)}")
    
    logger.info("Application shutdown complete")


class LLMOutput(BaseModel):
    """Structured output from LLM"""
    response_type: Literal['THANK_YOU_RESPONSE', 'HANDOVER_TO_HUMAN', 'NEED_MORE_INFO']
    
    # LOGISTICS fields
    charge: Optional[str] = None
    availability_time: Optional[str] = None
    
    # PIZZA fields
    pizza_type: Optional[str] = None
    size: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_time: Optional[str] = None
    
    feedback: str


def build_system_prompt(agent_type: str) -> str:
    """Build system prompt based on agent type"""
    
    if agent_type not in AGENT_METADATA:
        raise ValueError(f"Invalid agent_type: {agent_type}")
    
    agent_config = AGENT_METADATA[agent_type]
    base_prompt = agent_config["system_prompt"]
    
    # Add conversational instructions
    conversational_prompt = f"""
{base_prompt}

CONVERSATION STYLE:
- Be natural, friendly, and conversational
- Adapt to user's responses
- Handle questions, greetings, confusion naturally
- Guide conversation to collect required information
- Be patient and understanding
- If user wants human, transfer them

RESPONSE FORMAT (JSON):
{{
  "response_type": "THANK_YOU_RESPONSE" | "NEED_MORE_INFO" | "HANDOVER_TO_HUMAN",
"""
    
    # Add fields based on agent type
    if agent_type == "LOGISTICS":
        conversational_prompt += """
  "charge": "extracted charge or null",
  "availability_time": "extracted time or null",
"""
    elif agent_type == "PIZZA":
        conversational_prompt += """
  "pizza_type": "extracted pizza type or null",
  "size": "extracted size or null",
  "delivery_address": "extracted address or null",
  "delivery_time": "extracted delivery time or null",
"""
    
    conversational_prompt += """
  "feedback": "Your natural conversational response"
}

CRITICAL RULES:
1. ALWAYS return ONLY valid JSON - no extra text before or after
2. When you have ALL required information → response_type = "THANK_YOU_RESPONSE"
3. When missing information → response_type = "NEED_MORE_INFO", ask naturally
4. When user wants human → response_type = "HANDOVER_TO_HUMAN"
5. If user is confused, explain clearly in feedback

IMPORTANT: Your entire response must be ONLY the JSON object, nothing else!"""
    
    return conversational_prompt


def process_llm_response(user_input: str, session: Dict[str, Any]) -> LLMOutput:
    """Process user input with LLM"""
    
    agent_type = session["agent_type"]
    system_prompt = session["system_prompt"]
    history = session["history"]
    collected_data = session["collected_data"]
    
    # Build messages for LLM
    messages = [SystemMessage(content=system_prompt)]
    
    # Add conversation history
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    
    # Add current user input
    messages.append(HumanMessage(content=user_input))
    
    # Add current collected data context
    context = f"\nCurrent collected data: {json.dumps(collected_data)}"
    messages.append(HumanMessage(content=context))
    
    # Call LLM
    response = llm.invoke(messages)
    
    # Parse JSON response
    content = response.content.strip()
    
    # Remove markdown code blocks if present
    if content.startswith('```json'):
        content = content.replace('```json', '').replace('```', '').strip()
    elif content.startswith('```'):
        content = content.replace('```', '').strip()
    
    # Try to find JSON in the response
    try:
        # Try direct parsing
        result_dict = json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON from text
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            result_dict = json.loads(json_match.group())
        else:
            # Fallback: Create a default response
            result_dict = {
                "response_type": "NEED_MORE_INFO",
                "feedback": content if content else "Could you please provide the information again?"
            }
    
    llm_output = LLMOutput(**result_dict)
    
    # Update collected data based on agent type
    if agent_type == "LOGISTICS":
        if llm_output.charge:
            collected_data["charge"] = llm_output.charge
        if llm_output.availability_time:
            collected_data["availability_time"] = llm_output.availability_time
    
    elif agent_type == "PIZZA":
        if llm_output.pizza_type:
            collected_data["pizza_type"] = llm_output.pizza_type
        if llm_output.size:
            collected_data["size"] = llm_output.size
        if llm_output.delivery_address:
            collected_data["delivery_address"] = llm_output.delivery_address
        if llm_output.delivery_time:
            collected_data["delivery_time"] = llm_output.delivery_time
    
    return llm_output


def generate_twiml(message: str, action: str, language: str = "English") -> str:
    """Generate TwiML response with ElevenLabs voice or Twilio TTS fallback"""
    response = VoiceResponse()
    gather = response.gather(
        input='speech',
        action=action,
        method='POST',
        timeout=10,
        speech_timeout='auto',
        language=get_twilio_language_code(language)
    )
    
    # Try to generate ElevenLabs audio
    audio_url = elevenlabs_tts.generate_audio_url(message, language)
    
    if audio_url:
        # Use ElevenLabs voice
        gather.play(audio_url)
    else:
        # Fallback to Twilio TTS
        gather.say(message, voice=get_twilio_voice(language), language=get_twilio_language_code(language))
    
    return str(response)


def get_twilio_language_code(language: str) -> str:
    """Get Twilio language code from configuration - No hardcoding!"""
    from agent_config import LANGUAGE_CONFIG
    return LANGUAGE_CONFIG.get(language, {}).get("twilio_code", "en-US")


def get_twilio_voice(language: str) -> str:
    """Get Twilio voice from configuration - No hardcoding!"""
    from agent_config import LANGUAGE_CONFIG
    return LANGUAGE_CONFIG.get(language, {}).get("twilio_voice", "Polly.Joanna-Neural")


def detect_language(speech: str, supported_languages: list) -> str:
    """Detect language from user speech - Configuration-driven, no hardcoding"""
    speech_lower = speech.lower()
    
    # Check each supported language
    for language in supported_languages:
        if language.lower() in speech_lower:
            return language
    
    # Default to first language in list (usually English)
    return supported_languages[0] if supported_languages else "English"


def build_confirmation_message(collected_data: Dict[str, Any], agent_type: str, language: str) -> str:
    """Build confirmation message based on collected data from agent_config.py"""
    
    # Get confirmation message template from agent_config.py
    agent_config = AGENT_METADATA.get(agent_type, {})
    confirmation_template = agent_config.get("confirmation_msg", {}).get(language, "")
    
    if not confirmation_template:
        # Fallback if not configured
        return "Let me confirm the information I collected. Is this correct? Please say yes or no."
    
    # Replace placeholders with actual collected data
    try:
        # Add default values for missing fields
        data_with_defaults = {key: value if value else "not provided" for key, value in collected_data.items()}
        return confirmation_template.format(**data_with_defaults)
    except KeyError as e:
        # If template has placeholders not in collected_data, use fallback
        logger.warning(f"Missing field in confirmation template: {e}")
        return "Let me confirm the information I collected. Is this correct? Please say yes or no."


@app.post("/start-call")
async def start_call(agent_type: str = "LOGISTICS", phone_number: str = "+919876543210"):
    """Start a call with specified agent type"""
    
    if agent_type not in AGENT_METADATA:
        logger.error(f"❌ Invalid agent_type: {agent_type}")
        return {"error": f"Invalid agent_type. Choose: {list(AGENT_METADATA.keys())}"}
    
    if not twilio_client:
        logger.error("❌ Twilio client not configured")
        return {"error": "Service temporarily unavailable. Twilio is not configured. Please contact support."}
    
    try:
        logger.info(f"📞 Initiating call - Agent: {agent_type}, Phone: {phone_number}")
        
        call = twilio_client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{WEBHOOK_BASE_URL}/voice?agent_type={agent_type}",
            method='POST'
        )
        
        logger.info(f"✅ Call initiated successfully - CallSid: {call.sid}")
        
        return {
            "success": True,
            "call_sid": call.sid,
            "agent_type": agent_type,
            "phone_number": phone_number
        }
    except Exception as e:
        logger.error(f"❌ Error starting call: {e}", exc_info=True)
        return {
            "success": False, 
            "error": "Service temporarily unavailable. Unable to initiate call. Please try again later or contact support."
        }


@app.post("/voice")
async def voice_webhook(request: Request):
    """Handle initial call connection - Optional Language Selection"""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    agent_type = request.query_params.get("agent_type", "LOGISTICS")
    
    logger.info(f"Call connected: {call_sid}, Agent: {agent_type}")
    
    # Get supported languages from agent_config.py
    supported_languages = AGENT_METADATA[agent_type].get("language_selection", ["English"])
    
    # Check if multi-language support is enabled (more than 1 language)
    if len(supported_languages) > 1:
        # Multi-language: Ask user to select
        logger.info(f"Multi-language enabled: {supported_languages}")
        
        # Initialize session with language selection stage
        active_calls[call_sid] = {
            "agent_type": agent_type,
            "stage": "language_selection",
            "language": None,
            "system_prompt": build_system_prompt(agent_type),
            "history": [],
            "collected_data": {}
        }
        
        # Save to database
        db.save_call(call_sid, active_calls[call_sid])
        
        # Ask for language
        lang_text = ", ".join(supported_languages)
        message = f"Please select your language: {lang_text}"
        
        twiml = generate_twiml(message, '/process-response', "English")
        return Response(content=twiml, media_type="application/xml")
    
    else:
        # Single language: Skip language selection, use default (English)
        default_language = supported_languages[0] if supported_languages else "English"
        logger.info(f"Single language mode: Using {default_language}")
        
        # Initialize session directly with welcome stage
        active_calls[call_sid] = {
            "agent_type": agent_type,
            "stage": "welcome",
            "language": default_language,
            "system_prompt": build_system_prompt(agent_type),
            "history": [],
            "collected_data": {}
        }
        
        # Save to database
        db.save_call(call_sid, active_calls[call_sid])
        
        # Send welcome message directly
        welcome_msg = AGENT_METADATA[agent_type]["welcome_msg"].get(default_language, "")
        active_calls[call_sid]["history"].append({"role": "assistant", "content": welcome_msg})
        
        logger.info(f"🔊 Welcome Message ({default_language}): {welcome_msg}")
        
        twiml = generate_twiml(welcome_msg, "/process-response", default_language)
        return Response(content=twiml, media_type="application/xml")


@app.post("/process-response")
async def process_response(CallSid: str = Form(...), SpeechResult: Optional[str] = Form(None)):
    """Process user response based on conversation stage"""
    
    if CallSid not in active_calls:
        # Try to load from database
        call_data = db.get_call(CallSid)
        if call_data:
            active_calls[CallSid] = call_data
        else:
            return Response(
                content="<Response><Say>Call not found</Say></Response>",
                media_type="application/xml"
            )
    
    session = active_calls[CallSid]
    agent_type = session["agent_type"]
    stage = session["stage"]
    
    logger.info(f"CallSid: {CallSid}, Stage: {stage}, Speech: {SpeechResult}")
    
    if not SpeechResult:
        message = "I didn't catch that. Please repeat."
        language = session.get("language", "English")
        twiml = generate_twiml(message, "/process-response", language)
        return Response(content=twiml, media_type="application/xml")
    
    # Stage 1: Language Selection
    if stage == "language_selection":
        language = detect_language(SpeechResult, AGENT_METADATA[agent_type]["language_selection"])
        session["language"] = language
        session["stage"] = "welcome"
        session["history"].append({"role": "user", "content": f"Selected language: {language}"})
        
        # Save to database
        active_calls[CallSid] = session
        db.save_call(CallSid, session)
        
        # Send welcome message
        welcome_msg = AGENT_METADATA[agent_type]["welcome_msg"].get(language, "")
        session["history"].append({"role": "assistant", "content": welcome_msg})
        
        twiml = generate_twiml(welcome_msg, "/process-response", language)
        return Response(content=twiml, media_type="application/xml")
    
    # Stage 2 & 3: Welcome + Collecting Information
    if stage in ["welcome", "collecting"]:
        session["stage"] = "collecting"
        session["history"].append({"role": "user", "content": SpeechResult})
        
        # Process with LLM
        try:
            llm_output = process_llm_response(SpeechResult, session)
            
            # Log LLM response
            logger.info(f"📝 LLM Response - Type: {llm_output.response_type}, Feedback: {llm_output.feedback[:100]}...")
            
            # Add AI response to history
            session["history"].append({"role": "assistant", "content": llm_output.feedback})
            
            # Save to database
            active_calls[CallSid] = session
            db.save_call(CallSid, session)
            
            language = session.get("language", "English")
            
            # Handle response type
            if llm_output.response_type == "THANK_YOU_RESPONSE":
                # ✅ CHANGE 1: Add confirmation step before ending call
                session["stage"] = "confirmation"
                
                # Build confirmation message with collected data
                confirmation_msg = build_confirmation_message(session["collected_data"], agent_type, language)
                
                logger.info(f"📋 Confirmation Stage - Data: {session['collected_data']}")
                logger.info(f"🔊 Confirmation Message: {confirmation_msg}")
                
                # Save to database
                db.save_call(CallSid, session)
                
                # Ask for confirmation (using same endpoint)
                twiml = generate_twiml(confirmation_msg, "/process-response", language)
                return Response(content=twiml, media_type="application/xml")
            
            elif llm_output.response_type == "HANDOVER_TO_HUMAN":
                # Transfer to human
                logger.info(f"📞 Handover to human requested - CallSid: {CallSid}")
                negative_msg = AGENT_METADATA[agent_type]["negative_thank_you_msg"]
                logger.info(f"🔊 Response Message: {negative_msg}")
                
                response = VoiceResponse()
                response.say(negative_msg, voice=get_twilio_voice(language), language=get_twilio_language_code(language))
                response.hangup()
                return Response(content=str(response), media_type="application/xml")
            
            else:
                # Need more info
                logger.info(f"❓ Need more info - CallSid: {CallSid}")
                logger.info(f"🔊 Response Message: {llm_output.feedback}")
                
                twiml = generate_twiml(llm_output.feedback, "/process-response", language)
                return Response(content=twiml, media_type="application/xml")
        
        except Exception as e:
            # ✅ CHANGE 3: Better error message
            logger.error(f"❌ Error processing response for CallSid {CallSid}: {str(e)}", exc_info=True)
            
            message = "I apologize, but our system is experiencing technical difficulties. Please try again later or contact support."
            language = session.get("language", "English")
            logger.info(f"🔊 Error Response Message: {message}")
            
            twiml = generate_twiml(message, "/process-response", language)
            return Response(content=twiml, media_type="application/xml")
    
    # Stage 4: Confirmation
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
                
                # Get retry message from agent_config.py
                retry_msg = AGENT_METADATA[agent_type]["retry_msg"].get(language, "I understand. Let me collect the information again. Please provide the details.")
                logger.info(f"🔊 Retry Message: {retry_msg}")
                
                # Save to database
                db.save_call(CallSid, session)
                
                twiml = generate_twiml(retry_msg, "/process-response", language)
                return Response(content=twiml, media_type="application/xml")
            
            else:
                # Unclear response - Ask again
                logger.info(f"❓ Unclear confirmation response - CallSid: {CallSid}")
                
                # Get clarify message from agent_config.py
                clarify_msg = AGENT_METADATA[agent_type]["clarify_msg"].get(language, "I didn't understand. Please say 'yes' if the information is correct, or 'no' if you want to change it.")
                logger.info(f"🔊 Clarification Message: {clarify_msg}")
                
                twiml = generate_twiml(clarify_msg, "/process-response", language)
                return Response(content=twiml, media_type="application/xml")
        
        except Exception as e:
            # ✅ CHANGE 3: Better error message
            logger.error(f"❌ Error processing confirmation for CallSid {CallSid}: {str(e)}", exc_info=True)
            
            message = "I apologize, but our system is experiencing technical difficulties. Your information has been saved. We will contact you shortly."
            language = session.get("language", "English")
            logger.info(f"🔊 Error Response Message: {message}")
            
            response = VoiceResponse()
            response.say(message, voice=get_twilio_voice(language), language=get_twilio_language_code(language))
            response.hangup()
            return Response(content=str(response), media_type="application/xml")
    
    # Default
    message = "Could you please repeat?"
    language = session.get("language", "English")
    twiml = generate_twiml(message, "/process-response", language)
    return Response(content=twiml, media_type="application/xml")


@app.get("/call-status/{call_sid}")
async def get_call_status(call_sid: str):
    """Get current call status and collected data"""
    if call_sid in active_calls:
        return {
            "call_sid": call_sid,
            "session": active_calls[call_sid]
        }
    
    # Try database
    call_data = db.get_call(call_sid)
    if call_data:
        return {
            "call_sid": call_sid,
            "session": call_data
        }
    
    return {"error": "Call not found"}


@app.get("/audio/{filename}")
async def serve_audio_file(filename: str):
    """Serve ElevenLabs generated audio files"""
    file_path = os.path.join("temp_audio", filename)
    
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type="audio/mpeg",
            headers={"Cache-Control": "public, max-age=3600"}
        )
    else:
        return {"error": "Audio file not found"}


@app.get("/")
async def root():
    """API information"""
    return {
        "service": "Multi-Agent Voice Conversation",
        "agents": list(AGENT_METADATA.keys()),
        "voice": "ElevenLabs TTS + Twilio",
        "llm": "Gemini 2.0 Flash",
        "database": "MongoDB",
        "endpoints": {
            "start_call": "POST /start-call?agent_type=PIZZA&phone_number=+91xxx",
            "call_status": "GET /call-status/{call_sid}",
            "audio": "GET /audio/{filename}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
