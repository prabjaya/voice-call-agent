"""
Multi-Agent Voice Call POC
Supports: PIZZA, LOGISTICS agents with Twilio + ElevenLabs + Gemini
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import Response, FileResponse
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from agent_config import AGENT_METADATA
from elevenlabs_service import ElevenLabsTTS
from database import CallDatabase
from dotenv import load_dotenv
import os
import json
import logging
from typing import Optional, Dict, Any

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Agent Voice POC")

# Configuration from .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8001")

# Validate required environment variables
if not GEMINI_API_KEY:
    logger.error("❌ GEMINI_API_KEY not found in .env file")
if not TWILIO_ACCOUNT_SID:
    logger.error("❌ TWILIO_ACCOUNT_SID not found in .env file")
if not TWILIO_AUTH_TOKEN:
    logger.error("❌ TWILIO_AUTH_TOKEN not found in .env file")
if not TWILIO_PHONE_NUMBER:
    logger.error("❌ TWILIO_PHONE_NUMBER not found in .env file")

# Initialize services
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.3
)
elevenlabs_tts = ElevenLabsTTS()
db = CallDatabase()

# Active calls: active_calls[sid] = {agent_type, stage, language, history, data}
active_calls: Dict[str, Dict[str, Any]] = {}


@app.post("/start-call")
async def start_call(agent_type: str = "LOGISTICS", phone_number: str = "+919876543210"):
    """Start a call with specified agent type"""
    
    if agent_type not in AGENT_METADATA:
        return {"error": f"Invalid agent_type. Choose: {list(AGENT_METADATA.keys())}"}
    
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


@app.post("/voice")
async def voice_webhook(request: Request):
    """Handle initial call connection - Language Selection"""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    agent_type = request.query_params.get("agent_type", "LOGISTICS")
    
    logger.info(f"Call connected: {call_sid}, Agent: {agent_type}")
    
    # Initialize session: Stage 1 - Language Selection
    active_calls[call_sid] = {
        "agent_type": agent_type,
        "stage": "language_selection",
        "language": None,
        "history": [],
        "data": {}
    }
    
    # Save to database
    db.save_call(call_sid, active_calls[call_sid])
    
    # Ask for language
    response = VoiceResponse()
    gather = response.gather(
        input='speech',
        action='/process-response',
        method='POST',
        timeout=5,
        language='en-US'
    )
    
    languages = AGENT_METADATA[agent_type]["language_selection"]
    lang_text = ", ".join(languages)
    gather.say(f"Please select your language: {lang_text}")
    
    return Response(content=str(response), media_type="application/xml")


@app.post("/process-response")
async def process_response(CallSid: str = Form(...), SpeechResult: Optional[str] = Form(None)):
    """Process user response based on conversation stage"""
    
    if CallSid not in active_calls:
        return Response(
            content="<Response><Say>Call not found</Say></Response>",
            media_type="application/xml"
        )
    
    session = active_calls[CallSid]
    agent_type = session["agent_type"]
    stage = session["stage"]
    
    logger.info(f"CallSid: {CallSid}, Stage: {stage}, Speech: {SpeechResult}")
    
    if not SpeechResult:
        return generate_twiml("I didn't catch that. Please repeat.", "/process-response")
    
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
        return generate_twiml(welcome_msg, "/process-response", language)
    
    # Stage 2 & 3: Welcome + Collecting Information
    if stage in ["welcome", "collecting"]:
        session["stage"] = "collecting"
        session["history"].append({"role": "user", "content": SpeechResult})
        
        # Save to database
        active_calls[CallSid] = session
        db.save_call(CallSid, session)
        
        # Process with LLM
        llm_response = process_with_llm(session, SpeechResult)
        
        return handle_llm_response(CallSid, session, llm_response)
    
    # Default
    return generate_twiml("Could you please repeat?", "/process-response")


def detect_language(speech: str, supported_languages: list) -> str:
    """Detect language from user speech"""
    speech_lower = speech.lower()
    if "tamil" in speech_lower or "தமிழ்" in speech:
        return "Tamil"
    elif "malayalam" in speech_lower or "മലയാളം" in speech:
        return "Malayalam"
    else:
        return "English"


def process_with_llm(session: Dict, user_input: str) -> Dict[str, Any]:
    """Process user input with Gemini LLM"""
    agent_type = session["agent_type"]
    system_prompt = AGENT_METADATA[agent_type]["system_prompt"]
    
    # Build LLM prompt
    extraction_prompt = """Extract information and respond in JSON format:
{
  "response_type": "NEED_MORE_INFO" | "THANK_YOU_RESPONSE" | "HANDOVER_TO_HUMAN",
  "charges": "extracted charges or null",
  "availability_time": "extracted time or null",
  "feedback": "text to ask user for missing info"
}

Rules:
- If you find BOTH charge AND availability_time: set response_type to "THANK_YOU_RESPONSE"
- If you find ONLY charge: return charge and ask for availability_time in feedback
- If you find ONLY availability_time: return it and ask for charge in feedback
- If nothing found: ask clarifying question in feedback with response_type "NEED_MORE_INFO"
"""
    
    try:
        # Build messages
        messages = [
            SystemMessage(content=system_prompt),
            SystemMessage(content=extraction_prompt)
        ]
        
        # Add conversation history
        for msg in session["history"]:
            messages.append(HumanMessage(content=msg["content"]))
        
        # Call Gemini
        response = llm.invoke(messages)
        
        # Parse JSON
        content = response.content.strip()
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        
        result = json.loads(content)
        logger.info(f"LLM Response: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        return {
            "response_type": "NEED_MORE_INFO",
            "feedback": "Could you please provide the information again?"
        }


def handle_llm_response(call_sid: str, session: Dict, llm_response: Dict) -> Response:
    """Handle LLM response and generate TwiML"""
    response_type = llm_response.get("response_type")
    agent_type = session["agent_type"]
    
    # Update session data
    if llm_response.get("charges"):
        session["data"]["charges"] = llm_response["charges"]
    if llm_response.get("availability_time"):
        session["data"]["availability_time"] = llm_response["availability_time"]
    
    # THANK_YOU_RESPONSE - All info collected
    if response_type == "THANK_YOU_RESPONSE":
        session["stage"] = "completed"
        thank_you_msg = AGENT_METADATA[agent_type]["positive_thank_you_msg"]
        
        logger.info(f"✅ Call completed. Data collected: {session['data']}")
        
        # Save to database
        active_calls[call_sid] = session
        db.save_call(call_sid, session)
        db.save_collected_data(call_sid, agent_type, session["data"])
        
        # End call
        response = VoiceResponse()
        response.say(thank_you_msg)
        response.hangup()
        return Response(content=str(response), media_type="application/xml")
    
    # HANDOVER_TO_HUMAN
    elif response_type == "HANDOVER_TO_HUMAN":
        negative_msg = AGENT_METADATA[agent_type]["negative_thank_you_msg"]
        response = VoiceResponse()
        response.say(negative_msg)
        response.hangup()
        return Response(content=str(response), media_type="application/xml")
    
    # NEED_MORE_INFO - Ask follow-up
    else:
        feedback = llm_response.get("feedback", "Could you provide more details?")
        session["history"].append({"role": "assistant", "content": feedback})
        language = session.get("language", "English")
        
        # Save to database
        active_calls[call_sid] = session
        db.save_call(call_sid, session)
        
        return generate_twiml(feedback, "/process-response", language)


def generate_twiml(message: str, action: str, language: str = "English") -> Response:
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
    
    return Response(content=str(response), media_type="application/xml")


def get_twilio_language_code(language: str) -> str:
    """Get Twilio language code"""
    language_map = {
        "English": "en-US",
        "Tamil": "ta-IN",
        "Malayalam": "ml-IN"
    }
    return language_map.get(language, "en-US")


def get_twilio_voice(language: str) -> str:
    """Get Twilio voice for fallback"""
    voice_map = {
        "English": "Polly.Joanna-Neural",
        "Tamil": "Polly.Aditi-Neural",
        "Malayalam": "Polly.Aditi-Neural"
    }
    return voice_map.get(language, "Polly.Joanna-Neural")


@app.get("/call-status/{call_sid}")
async def get_call_status(call_sid: str):
    """Get current call status and collected data"""
    if call_sid in active_calls:
        return {
            "call_sid": call_sid,
            "session": active_calls[call_sid]
        }
    return {"error": "Call not found"}


# @app.get("/active-calls")
# async def get_active_calls():
#     """Get all active calls"""
#     return {
#         "active_calls": len(active_calls),
#         "calls": list(active_calls.keys())
#     }


# @app.get("/all-calls")
# async def get_all_calls(limit: int = 50):
#     """Get all calls from database"""
#     calls = db.get_all_calls(limit)
#     return {
#         "total": len(calls),
#         "calls": calls
#     }


# @app.get("/collected-data")
# async def get_collected_data(agent_type: Optional[str] = None):
#     """Get all collected data"""
#     data = db.get_collected_data(agent_type)
#     return {
#         "total": len(data),
#         "agent_type": agent_type,
#         "data": data
#     }


# @app.get("/analytics")
# async def get_analytics():
#     """Get call analytics"""
#     analytics = db.get_analytics()
#     return analytics


# @app.get("/health")
# async def health():
#     """Health check"""
#     mongodb_status = "connected" if db.client else "disconnected (using memory)"
#     return {
#         "status": "healthy",
#         "service": "Multi-Agent Voice POC",
#         "agents": list(AGENT_METADATA.keys()),
#         "database": mongodb_status
#     }


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
        "service": "Multi-Agent Voice POC with ElevenLabs",
        "agents": list(AGENT_METADATA.keys()),
        "voice": "ElevenLabs TTS + Twilio",
        "endpoints": {
            "start_call": "POST /start-call?agent_type=PIZZA&phone_number=+91xxx",
            "health": "GET /health",
            "call_status": "GET /call-status/{call_sid}",
            "active_calls": "GET /active-calls",
            "audio": "GET /audio/{filename}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
