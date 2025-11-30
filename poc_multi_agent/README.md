# Multi-Agent Voice Call POC

Minimal POC for multi-agent voice call system with Twilio + Gemini LLM.

## Features

- ✅ Multiple agent types (PIZZA, LOGISTICS)
- ✅ Dynamic conversation flow based on agent type
- ✅ Language selection (English, Tamil, Malayalam)
- ✅ LLM-powered information extraction
- ✅ Intelligent follow-up questions
- ✅ Session state management

## Quick Start

### 1. Install Dependencies
```bash
cd poc_multi_agent
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Application
```bash
uvicorn main:app --reload --port 8001
```

### 4. Start ngrok
```bash
ngrok http 8001
# Update WEBHOOK_BASE_URL in .env with ngrok URL
```

### 5. Test Call

**LOGISTICS Agent:**
```bash
curl -X POST "http://localhost:8001/start-call?agent_type=LOGISTICS&phone_number=+919876543210"
```

**PIZZA Agent:**
```bash
curl -X POST "http://localhost:8001/start-call?agent_type=PIZZA&phone_number=+919876543210"
```

## Conversation Flow

### Stage 1: Language Selection
```
System: "Please select your language: English, Tamil, Malayalam"
User: "English"
```

### Stage 2: Welcome
```
System: "Hello, this is an automated call from your ERP system..."
User: "Let's go"
```

### Stage 3: Information Collection
```
System: "I need shipment charges and time availability"
User: "500 rupees, available 9 AM to 5 PM"
```

**LLM Processing:**
- Extracts: charges="₹500", availability_time="9 AM to 5 PM"
- Response: "THANK_YOU_RESPONSE"

### Stage 4: Completion
```
System: "Thank you! Information updated in ERP system."
[Call ends]
```

## LLM Response Types

### 1. NEED_MORE_INFO
When partial information is collected:
```json
{
  "response_type": "NEED_MORE_INFO",
  "charges": "₹500",
  "availability_time": null,
  "feedback": "Thank you. What is your time availability?"
}
```

### 2. THANK_YOU_RESPONSE
When all information is collected:
```json
{
  "response_type": "THANK_YOU_RESPONSE",
  "charges": "₹500",
  "availability_time": "9 AM to 5 PM",
  "feedback": ""
}
```

### 3. HANDOVER_TO_HUMAN
When user requests human agent:
```json
{
  "response_type": "HANDOVER_TO_HUMAN",
  "feedback": "Transferring to human agent"
}
```

## API Endpoints

- `POST /start-call` - Start a call
- `POST /voice` - Twilio voice webhook
- `POST /process-response` - Process user responses
- `GET /call-status/{call_sid}` - Get call status
- `GET /active-calls` - View active calls
- `GET /health` - Health check

## Session State

```python
active_calls[call_sid] = {
    "agent_type": "LOGISTICS",
    "stage": "collecting",  # language_selection, welcome, collecting, completed
    "language": "English",
    "history": [
        {"role": "user", "content": "500 rupees"},
        {"role": "assistant", "content": "What is your availability?"}
    ],
    "data": {
        "charges": "₹500",
        "availability_time": "9 AM to 5 PM"
    }
}
```

## Adding New Agents

Edit `agent_config.py`:

```python
AGENT_METADATA["NEW_AGENT"] = {
    "system_prompt": "Your agent instructions...",
    "positive_thank_you_msg": "Thank you message",
    "negative_thank_you_msg": "Goodbye message",
    "welcome_msg": {
        "English": "Welcome message in English",
        "Tamil": "Welcome in Tamil"
    },
    "language_selection": ["English", "Tamil"]
}
```

## Testing

```bash
# Health check
curl http://localhost:8001/health

# Start LOGISTICS call
curl -X POST "http://localhost:8001/start-call?agent_type=LOGISTICS&phone_number=+919876543210"

# Check call status
curl http://localhost:8001/call-status/CAxxxx

# View active calls
curl http://localhost:8001/active-calls
```

## Architecture

```
User Phone
    ↓
Twilio (Voice Call)
    ↓
FastAPI Webhooks
    ↓
Gemini LLM (Information Extraction)
    ↓
Session State Management
    ↓
Response Generation
```

## Folder Structure

```
poc_multi_agent/
├── main.py              # FastAPI application
├── agent_config.py      # Agent configurations
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
└── README.md           # This file
```

## Notes

- This is a minimal POC - no database persistence
- Sessions stored in memory only
- For production: add MongoDB, error handling, logging
- Supports dynamic agent types via configuration
