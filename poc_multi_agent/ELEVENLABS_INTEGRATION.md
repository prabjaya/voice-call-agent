# ElevenLabs Integration - Like Original Code

This document explains how ElevenLabs is integrated in `agent_voice_conversation.py` to match the original `app/main.py` implementation.

## 🎯 Key Changes

### 1. Added `audio_storage.py` Module

**Purpose**: Handle audio file storage and serving for Twilio (matches `app/audio_storage.py`)

```python
class AudioStorage:
    """Handle audio file storage and serving for Twilio"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.audio_dir = "temp_audio"
        self.ensure_audio_directory()
    
    def save_audio_file(self, audio_content: bytes, filename: str) -> Optional[str]:
        """Save audio content and return public URL"""
        # Saves to temp_audio/ directory
        # Returns public URL: {base_url}/audio/{filename}
    
    def file_exists(self, filename: str) -> bool:
        """Check if audio file already exists"""
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old audio files"""
```

### 2. Updated `elevenlabs_service.py`

**Changes**:
- Added `audio_storage` parameter to `__init__`
- Uses `audio_storage.save_audio_file()` instead of direct file writing
- Checks `audio_storage.file_exists()` before generating new audio
- Matches original `app/twilio_service.py` implementation

**Before**:
```python
class ElevenLabsTTS:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    
    def generate_audio_url(self, text: str, language: str):
        # ... generate audio ...
        
        # Save directly to file system
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        return f"{webhook_base}/audio/{filename}"
```

**After** (matches original):
```python
class ElevenLabsTTS:
    def __init__(self, audio_storage=None):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        self.audio_storage = audio_storage  # NEW!
    
    def generate_audio_url(self, text: str, language: str):
        # Check if file exists using audio_storage
        if self.audio_storage and self.audio_storage.file_exists(filename):
            return self.audio_storage.get_file_url(filename)
        
        # ... generate audio ...
        
        # Save using audio_storage (like original)
        if self.audio_storage:
            public_url = self.audio_storage.save_audio_file(response.content, filename)
            return public_url
```

### 3. Updated `agent_voice_conversation.py`

**Changes**:
- Import `init_audio_storage` from `audio_storage`
- Initialize audio storage with `WEBHOOK_BASE_URL`
- Pass `audio_storage` to `ElevenLabsTTS`
- Added startup/shutdown events for cleanup

**Before**:
```python
from elevenlabs_service import ElevenLabsTTS

elevenlabs_tts = ElevenLabsTTS()
db = CallDatabase()
```

**After** (matches original):
```python
from elevenlabs_service import ElevenLabsTTS
from audio_storage import init_audio_storage

# Initialize audio storage (like original code)
audio_storage = init_audio_storage(WEBHOOK_BASE_URL)

# Initialize ElevenLabs with audio_storage (like original code)
elevenlabs_tts = ElevenLabsTTS(audio_storage=audio_storage)

# Initialize database
db = CallDatabase()

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Multi-Agent Voice Conversation System")
    logger.info(f"MongoDB connection: {'Connected' if db.client else 'Using memory fallback'}")
    logger.info(f"Audio storage: {audio_storage.audio_dir}")
    logger.info(f"ElevenLabs: {'Configured' if elevenlabs_tts.api_key else 'Not configured'}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown"""
    # Save calls to database
    # Close database connection
    # Cleanup old audio files
    audio_storage.cleanup_old_files(max_age_hours=24)
```

## 🔄 Data Flow

### Original Code (`app/main.py`)

```
ElevenLabs API
    ↓
Generate Audio (bytes)
    ↓
audio_storage.save_audio_file()
    ↓
Save to temp_audio/elevenlabs_xxx.mp3
    ↓
Return public URL: {WEBHOOK_BASE_URL}/audio/elevenlabs_xxx.mp3
    ↓
Twilio plays audio from URL
```

### New Code (`agent_voice_conversation.py`)

```
ElevenLabs API
    ↓
Generate Audio (bytes)
    ↓
audio_storage.save_audio_file()  ← SAME!
    ↓
Save to temp_audio/elevenlabs_xxx.mp3
    ↓
Return public URL: {WEBHOOK_BASE_URL}/audio/elevenlabs_xxx.mp3
    ↓
Twilio plays audio from URL
```

**Result**: Identical implementation! ✅

## 📁 File Structure

```
poc_multi_agent/
├── agent_voice_conversation.py  ← Uses audio_storage
├── elevenlabs_service.py        ← Uses audio_storage
├── audio_storage.py             ← NEW! (matches app/audio_storage.py)
├── database.py
├── agent_config.py
└── temp_audio/                  ← Audio files stored here
    ├── elevenlabs_abc123_english.mp3
    ├── elevenlabs_def456_tamil.mp3
    └── elevenlabs_ghi789_malayalam.mp3
```

## 🎨 Benefits

### 1. Consistent with Original Code
- Same architecture as `app/main.py`
- Same audio storage pattern
- Same file naming convention

### 2. Better Organization
- Separation of concerns (audio storage vs voice generation)
- Easier to test
- Easier to maintain

### 3. Automatic Cleanup
- Old audio files cleaned up on shutdown
- Configurable max age (default: 24 hours)
- Prevents disk space issues

### 4. Caching
- Checks if audio file exists before generating
- Reuses existing files for same message
- Reduces API calls to ElevenLabs
- Faster response times

## 🧪 Testing

### Test Audio Storage

```bash
python test_voice_system.py
```

Expected output:
```
📁 Testing Audio Storage
✅ Audio storage initialized
   Directory: temp_audio
   Base URL: http://localhost:8000
✅ Test audio file saved: http://localhost:8000/audio/test_audio.mp3
✅ File existence check works
✅ Test file cleaned up
```

### Test ElevenLabs with Audio Storage

```bash
python test_voice_system.py
```

Expected output:
```
🎤 Testing ElevenLabs TTS
✅ ElevenLabs audio generated: http://localhost:8000/audio/elevenlabs_xxx.mp3
   Using audio_storage: True
```

## 🔧 Configuration

No changes needed! Uses same `.env` configuration:

```env
ELEVENLABS_API_KEY=your_api_key
ELEVENLABS_VOICE_ID=your_voice_id
WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok.io
```

## 📊 Comparison

| Feature | Before | After (Like Original) |
|---------|--------|----------------------|
| Audio Storage | Direct file writing | audio_storage module |
| File Caching | Manual check | audio_storage.file_exists() |
| Cleanup | Manual | Automatic on shutdown |
| URL Generation | Manual string concat | audio_storage.get_file_url() |
| Organization | Mixed concerns | Separated concerns |
| Testing | Harder | Easier |

## 🚀 Usage

### In Your Code

```python
from audio_storage import init_audio_storage
from elevenlabs_service import ElevenLabsTTS

# Initialize audio storage
audio_storage = init_audio_storage(WEBHOOK_BASE_URL)

# Initialize ElevenLabs with audio_storage
elevenlabs_tts = ElevenLabsTTS(audio_storage=audio_storage)

# Generate audio
audio_url = elevenlabs_tts.generate_audio_url("Hello world", "English")

# Audio is automatically:
# 1. Cached (reused if same message)
# 2. Saved to temp_audio/
# 3. Served via /audio/{filename} endpoint
# 4. Cleaned up after 24 hours
```

### Cleanup Old Files

```python
# Manual cleanup (optional)
audio_storage.cleanup_old_files(max_age_hours=12)

# Automatic cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    audio_storage.cleanup_old_files(max_age_hours=24)
```

## 🎯 Key Differences from Original

### Similarities ✅
- Same `AudioStorage` class structure
- Same `save_audio_file()` method
- Same `cleanup_old_files()` method
- Same file naming convention
- Same URL generation pattern

### Differences 🔄
- **Location**: `poc_multi_agent/audio_storage.py` vs `app/audio_storage.py`
- **Initialization**: Uses `init_audio_storage()` function for global instance
- **Integration**: Directly in `agent_voice_conversation.py` vs separate `twilio_service.py`

### Why These Differences?
- **Simpler structure**: Single file vs multiple service files
- **Easier to understand**: All voice logic in one place
- **Same functionality**: Identical behavior and API

## ✅ Verification

### Check Audio Storage Works

```bash
# Start server
python agent_voice_conversation.py

# Make a call
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"

# Check temp_audio directory
ls -la temp_audio/

# Should see files like:
# elevenlabs_abc123_english.mp3
# elevenlabs_def456_tamil.mp3
```

### Check Caching Works

```bash
# Make same call twice
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"
curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"

# Check logs - should see:
# "File already exists, using cached version"
```

### Check Cleanup Works

```bash
# Create old test file
touch temp_audio/old_file.mp3

# Wait 25 hours (or modify file timestamp)
# Then restart server

# File should be deleted automatically
```

## 🎉 Summary

The ElevenLabs integration now **exactly matches** the original `app/main.py` implementation:

✅ Uses `audio_storage` module  
✅ Saves files via `audio_storage.save_audio_file()`  
✅ Checks cache via `audio_storage.file_exists()`  
✅ Automatic cleanup on shutdown  
✅ Same file naming convention  
✅ Same URL generation pattern  
✅ Same error handling  
✅ Same fallback to Twilio TTS  

**Result**: Production-ready ElevenLabs integration with proper audio storage management! 🚀

---

**Ready to use?** Just run `python agent_voice_conversation.py` and make a call!
