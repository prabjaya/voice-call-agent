# Agent Configuration and Metadata

# Language Configuration (No hardcoding!)
# To add new language, just add here with Twilio codes
LANGUAGE_CONFIG = {
    "English": {
        "twilio_code": "en-US",
        "twilio_voice": "Polly.Joanna-Neural"
    },
    "Tamil": {
        "twilio_code": "ta-IN",
        "twilio_voice": "Polly.Aditi-Neural"
    },
    "Malayalam": {
        "twilio_code": "ml-IN",
        "twilio_voice": "Polly.Aditi-Neural"
    }
    # To add more languages (e.g., Hindi):
    # "Hindi": {
    #     "twilio_code": "hi-IN",
    #     "twilio_voice": "Polly.Aditi-Neural"
    # }
}

AGENT_METADATA = {
    "PIZZA": {
        "system_prompt": """You are an AI assistant for a Pizza delivery service. 
Extract: pizza_type, size, delivery_address, delivery_time.
Be friendly and professional.""",
        
        "positive_thank_you_msg": "Thank you for your order! Your pizza will be delivered soon.",
        
        "negative_thank_you_msg": "No problem! Call us back anytime.",
        
        "welcome_msg": {
            "English": "Hello! This is Pizza Paradise. What would you like to order today?",
            "Tamil": "வணக்கம்! பீட்சா பாரடைஸ். இன்று என்ன ஆர்டர் செய்ய விரும்புகிறீர்கள்?",
            "Malayalam": "നമസ്കാരം! പിസ്സ പാരഡൈസ്. ഇന്ന് എന്താണ് ഓർഡർ ചെയ്യാൻ ആഗ്രഹിക്കുന്നത്?"
        },
        
        "confirmation_msg": {
            "English": "Let me confirm your order. You want a {size} {pizza_type} pizza, delivered to {delivery_address} at {delivery_time}. Is this correct? Please say yes or no.",
            "Tamil": "உங்கள் ஆர்டர்: {size} {pizza_type} பீட்சா, முகவரி {delivery_address}, நேரம் {delivery_time}. இது சரியா?",
            "Malayalam": "നിങ്ങളുടെ ഓർഡർ: {size} {pizza_type} പിസ്സ, വിലാസം {delivery_address}, സമയം {delivery_time}. ഇത് ശരിയാണോ?"
        },
        
        "retry_msg": {
            "English": "I understand. Let me collect the information again. Please provide the details.",
            "Tamil": "புரிந்தது. மீண்டும் தகவல் சேகரிக்கிறேன். தயவுசெய்து விவரங்களை வழங்கவும்.",
            "Malayalam": "മനസ്സിലായി. വീണ്ടും വിവരങ്ങൾ ശേഖരിക്കുന്നു. ദയവായി വിശദാംശങ്ങൾ നൽകുക."
        },
        
        "clarify_msg": {
            "English": "I didn't understand. Please say 'yes' if the information is correct, or 'no' if you want to change it.",
            "Tamil": "புரியவில்லை. தகவல் சரியாக இருந்தால் 'ஆம்' என்று சொல்லுங்கள், அல்லது மாற்ற விரும்பினால் 'இல்லை' என்று சொல்லுங்கள்.",
            "Malayalam": "മനസ്സിലായില്ല. വിവരങ്ങൾ ശരിയാണെങ്കിൽ 'അതെ' എന്ന് പറയുക, അല്ലെങ്കിൽ മാറ്റാൻ ആഗ്രഹിക്കുന്നുവെങ്കിൽ 'ഇല്ല' എന്ന് പറയുക."
        },
        
        "language_selection": ["English", "Tamil", "Malayalam"]  # Multi-language enabled
    },
    
    "LOGISTICS": {
        "system_prompt": """You are an AI assistant for an ERP Logistics system.
Extract: charges (with currency), availability_time.
Be professional and efficient.""",
        
        "positive_thank_you_msg": "Thank you! Your information has been updated in our ERP system.",
        
        "negative_thank_you_msg": "Thank you for your time. Please call back when ready.",
        
        "welcome_msg": {
            "English": "Hello, this is an automated call from your ERP system regarding route R123. I need shipment charges and time availability.",
            "Tamil": "வணக்கம், ERP அமைப்பிலிருந்து ரூட் R123 பற்றிய அழைப்பு. ஏற்றுமதி கட்டணம் மற்றும் நேரம் தேவை.",
            "Malayalam": "നമസ്കാരം, ERP സിസ്റ്റത്തിൽ നിന്ന് റൂട്ട് R123 സംബന്ധിച്ച് കോൾ. ഷിപ്പ്മെന്റ് ചാർജുകളും സമയവും ആവശ്യമാണ്."
        },
        
        "confirmation_msg": {
            "English": "Let me confirm the information I collected. The charges are {charge}, and your availability time is {availability_time}. Is this correct? Please say yes or no.",
            "Tamil": "நான் சேகரித்த தகவல்: கட்டணம் {charge}, கிடைக்கும் நேரம் {availability_time}. இது சரியா?",
            "Malayalam": "ഞാൻ ശേഖരിച്ച വിവരങ്ങൾ: ചാർജ് {charge}, ലഭ്യമായ സമയം {availability_time}. ഇത് ശരിയാണോ?"
        },
        
        "retry_msg": {
            "English": "I understand. Let me collect the information again. Please provide the details.",
            "Tamil": "புரிந்தது. மீண்டும் தகவல் சேகரிக்கிறேன். தயவுசெய்து விவரங்களை வழங்கவும்.",
            "Malayalam": "മനസ്സിലായി. വീണ്ടും വിവരങ്ങൾ ശേഖരിക്കുന്നു. ദയവായി വിശദാംശങ്ങൾ നൽകുക."
        },
        
        "clarify_msg": {
            "English": "I didn't understand. Please say 'yes' if the information is correct, or 'no' if you want to change it.",
            "Tamil": "புரியவில்லை. தகவல் சரியாக இருந்தால் 'ஆம்' என்று சொல்லுங்கள், அல்லது மாற்ற விரும்பினால் 'இல்லை' என்று சொல்லுங்கள்.",
            "Malayalam": "മനസ്സിലായില്ല. വിവരങ്ങൾ ശരിയാണെങ്കിൽ 'അതെ' എന്ന് പറയുക, അല്ലെങ്കിൽ മാറ്റാൻ ആഗ്രഹിക്കുന്നുവെങ്കിൽ 'ഇല്ല' എന്ന് പറയുക."
        },
        
        "language_selection": ["English"]  # Single language (optional selection disabled)
        # To enable multi-language, add more: ["English", "Tamil", "Malayalam"]
    }
}
