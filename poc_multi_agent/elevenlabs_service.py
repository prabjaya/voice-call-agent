"""
ElevenLabs TTS Service for natural voice generation
Matches original app/twilio_service.py implementation with audio_storage
"""

import os
import requests
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ElevenLabsTTS:
    def __init__(self, audio_storage=None):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        self.base_url = "https://api.elevenlabs.io/v1"
        self.audio_storage = audio_storage
        
        # Voice configurations for different languages
        self.voice_configs = {
            "English": {
                "voice_id": self.voice_id,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            },
            "Tamil": {
                "voice_id": self.voice_id,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            },
            "Malayalam": {
                "voice_id": self.voice_id,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
        }
    
    def generate_audio_url(self, text: str, language: str = "English") -> Optional[str]:
        """Generate audio and return public URL (matches original implementation)"""
        if not self.api_key or not self.voice_id:
            logger.warning("ElevenLabs not configured, using Twilio TTS")
            return None
        
        try:
            # Generate unique filename based on message content
            message_hash = hashlib.md5(text.encode()).hexdigest()
            filename = f"elevenlabs_{message_hash}_{language.lower()}.mp3"
            
            # Check if file already exists (using audio_storage if available)
            if self.audio_storage and self.audio_storage.file_exists(filename):
                return self.audio_storage.get_file_url(filename)
            
            # Fallback: check file system directly
            file_path = os.path.join("temp_audio", filename)
            if os.path.exists(file_path):
                webhook_base = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
                return f"{webhook_base}/audio/{filename}"
            
            # Get voice config
            voice_config = self.voice_configs.get(language, self.voice_configs["English"])
            
            # Make API request
            url = f"{self.base_url}/text-to-speech/{voice_config['voice_id']}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": voice_config["voice_settings"]
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # Save audio file using audio_storage if available
                if self.audio_storage:
                    public_url = self.audio_storage.save_audio_file(response.content, filename)
                    logger.info(f"Generated ElevenLabs audio: {public_url}")
                    return public_url
                else:
                    # Fallback: save directly to file system
                    os.makedirs("temp_audio", exist_ok=True)
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    webhook_base = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
                    public_url = f"{webhook_base}/audio/{filename}"
                    logger.info(f"Generated ElevenLabs audio: {public_url}")
                    return public_url
            else:
                logger.error(f"ElevenLabs API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating ElevenLabs audio: {str(e)}")
            return None
