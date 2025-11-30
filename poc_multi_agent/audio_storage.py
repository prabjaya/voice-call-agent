"""
Audio Storage Service
Handles audio file storage and serving for Twilio (like original app/audio_storage.py)
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AudioStorage:
    """Handle audio file storage and serving for Twilio"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.audio_dir = "temp_audio"
        self.ensure_audio_directory()
    
    def ensure_audio_directory(self):
        """Ensure audio directory exists"""
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
            logger.info(f"Created audio directory: {self.audio_dir}")
    
    def save_audio_file(self, audio_content: bytes, filename: str) -> Optional[str]:
        """Save audio content and return public URL"""
        try:
            file_path = os.path.join(self.audio_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(audio_content)
            
            # Return public URL that Twilio can access
            public_url = f"{self.base_url}/audio/{filename}"
            logger.info(f"Saved audio file: {public_url}")
            
            return public_url
            
        except Exception as e:
            logger.error(f"Error saving audio file: {str(e)}")
            return None
    
    def file_exists(self, filename: str) -> bool:
        """Check if audio file already exists"""
        file_path = os.path.join(self.audio_dir, filename)
        return os.path.exists(file_path)
    
    def get_file_url(self, filename: str) -> str:
        """Get public URL for existing file"""
        return f"{self.base_url}/audio/{filename}"
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old audio files"""
        try:
            import time
            current_time = time.time()
            
            for filename in os.listdir(self.audio_dir):
                file_path = os.path.join(self.audio_dir, filename)
                
                # Skip if not a file
                if not os.path.isfile(file_path):
                    continue
                
                file_age = current_time - os.path.getctime(file_path)
                
                if file_age > (max_age_hours * 3600):  # Convert hours to seconds
                    os.remove(file_path)
                    logger.info(f"Cleaned up old audio file: {filename}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up audio files: {str(e)}")


# Global instance (will be initialized with proper base_url)
audio_storage = None


def init_audio_storage(base_url: str):
    """Initialize global audio storage instance"""
    global audio_storage
    audio_storage = AudioStorage(base_url)
    return audio_storage
