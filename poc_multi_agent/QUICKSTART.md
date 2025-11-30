# Quick Start - Multi-Agent Voice POC

## 🚀 Run in 5 Minutes

### Step 1: Setup
```bash
cd poc_multi_agent
pip install -r requirements.txt
cp .env.example .env
```

### Step 2: Configure .env
```bash
nano .env
```

Add your credentials:
```env
GEMINI_API_KEY=AIzaSy...
TWILIO_ACCOUNT_SID=ACxxxx...
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890
WEBHOOK_BASE_URL=http://localhost:8001
```

### Step 3: Start Application
```bash
uvicorn main:app --reload --port 8001
```

### Step 4: Start ngrok (New Terminal)
```bash
ngrok http 8001
```

Copy the HTTPS URL and update `.env`:
```env
WEBHOOK_BASE_URL=https://abc123.ngrok.io
```

Restart the app.

### Step 5: Make a Test Call

**LOGISTICS Agent:**
```bash
curl -X POST "http://localhost:8001/start-call?agent_type=LOGISTICS&phone_number=+919876543210"
```

**PIZZA Agent:**
```bash
curl -X POST "http://localhost:8001/start-call?agent_type=PIZZA&phone_number=+919876543210"
```

## 📞 What Happens

### LOGISTICS Call Flow:
1. **System**: "Please select your language: English, Tamil, Malayalam"
2. **You**: "English"
3. **System**: "Hello, this is an automated call from your ERP system regarding route R123..."
4. **You**: "Let's go"
5. **System**: "I need shipment charges and time availability"
6. **You**: "500 rupees, available 9 AM to 5 PM"
7. **System**: "Thank you! Information updated in ERP system." [Hangs up]

### PIZZA Call Flow:
1. **System**: "Please select your language..."
2. **You**: "English"
3. **System**: "Hello! This is Pizza Paradise. What would you like to order?"
4. **You**: "Large pepperoni pizza"
5. **System**: "Great! What's your delivery address?"
6. **You**: "123 Main Street"
7. **System**: "When would you like delivery?"
8. **You**: "7 PM"
9. **System**: "Thank you for your order!" [Hangs up]

## 🔍 Monitor Calls

```bash
# Check health
curl http://localhost:8001/health

# View active calls
curl http://localhost:8001/active-calls

# Get call status
curl http://localhost:8001/call-status/CAxxxx
```

## 🎯 Key Features

✅ **Multi-Agent Support**: PIZZA, LOGISTICS (easily add more)
✅ **Language Selection**: English, Tamil, Malayalam
✅ **Smart Extraction**: LLM extracts information automatically
✅ **Follow-up Questions**: Asks for missing information
✅ **Session Management**: Tracks conversation state

## 📝 Session State Example

```json
{
  "call_sid": "CAxxxx",
  "session": {
    "agent_type": "LOGISTICS",
    "stage": "completed",
    "language": "English",
    "history": [
      {"role": "user", "content": "500 rupees, 9 AM to 5 PM"}
    ],
    "data": {
      "charges": "₹500",
      "availability_time": "9 AM to 5 PM"
    }
  }
}
```

## 🛠️ Troubleshooting

**Call not connecting?**
- Check Twilio credentials in `.env`
- Verify phone number format: `+919876543210`
- Check ngrok URL matches `.env`

**LLM not extracting?**
- Verify GEMINI_API_KEY is correct
- Check logs for LLM errors
- Speak clearly with specific information

**Webhook errors?**
```bash
# Test webhook
curl https://your-ngrok-url.ngrok.io/health
```

## 🎨 Add New Agent

Edit `agent_config.py`:

```python
AGENT_METADATA["RESTAURANT"] = {
    "system_prompt": "You are a restaurant reservation assistant...",
    "positive_thank_you_msg": "Reservation confirmed!",
    "negative_thank_you_msg": "No problem!",
    "welcome_msg": {
        "English": "Hello! Welcome to our restaurant..."
    },
    "language_selection": ["English"]
}
```

Test it:
```bash
curl -X POST "http://localhost:8001/start-call?agent_type=RESTAURANT&phone_number=+91xxx"
```

That's it! Your multi-agent voice POC is ready! 🎉
