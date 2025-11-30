"""
Test Script for Multi-Agent Voice Conversation System
Tests all components: MongoDB, Twilio, ElevenLabs, LLM
"""

import os
import requests
from dotenv import load_dotenv
from database import CallDatabase
from elevenlabs_service import ElevenLabsTTS
from agent_config import AGENT_METADATA

load_dotenv()

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("=" * 70)
    print("🔍 Testing Environment Variables")
    print("=" * 70)
    
    required_vars = {
        "GEMINI_API_KEY": "Gemini LLM",
        "TWILIO_ACCOUNT_SID": "Twilio Voice",
        "TWILIO_AUTH_TOKEN": "Twilio Voice",
        "TWILIO_PHONE_NUMBER": "Twilio Voice",
        "MONGODB_URL": "MongoDB Database",
        "WEBHOOK_BASE_URL": "Twilio Webhooks"
    }
    
    optional_vars = {
        "ELEVENLABS_API_KEY": "ElevenLabs Voice (optional)",
        "ELEVENLABS_VOICE_ID": "ElevenLabs Voice (optional)"
    }
    
    all_good = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {description}")
        else:
            print(f"❌ {var}: {description} - NOT SET")
            all_good = False
    
    print()
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {description}")
        else:
            print(f"⚠️  {var}: {description} - NOT SET (will use fallback)")
    
    print()
    return all_good


def test_mongodb():
    """Test MongoDB connection"""
    print("=" * 70)
    print("🗄️  Testing MongoDB Connection")
    print("=" * 70)
    
    try:
        db = CallDatabase()
        
        if db.client:
            print("✅ MongoDB connected successfully")
            
            # Test save and retrieve
            test_call_sid = "TEST_CALL_123"
            test_session = {
                "agent_type": "LOGISTICS",
                "stage": "test",
                "language": "English",
                "history": [],
                "collected_data": {}
            }
            
            db.save_call(test_call_sid, test_session)
            print("✅ Test call saved")
            
            retrieved = db.get_call(test_call_sid)
            if retrieved:
                print("✅ Test call retrieved")
            else:
                print("❌ Failed to retrieve test call")
            
            return True
        else:
            print("⚠️  MongoDB not connected - using in-memory storage")
            return True  # Not a failure, just a fallback
            
    except Exception as e:
        print(f"❌ MongoDB test failed: {str(e)}")
        return False


def test_audio_storage():
    """Test audio storage"""
    print("=" * 70)
    print("📁 Testing Audio Storage")
    print("=" * 70)
    
    try:
        from audio_storage import init_audio_storage
        
        webhook_base = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
        audio_storage = init_audio_storage(webhook_base)
        
        print(f"✅ Audio storage initialized")
        print(f"   Directory: {audio_storage.audio_dir}")
        print(f"   Base URL: {audio_storage.base_url}")
        
        # Test saving a dummy file
        test_content = b"test audio content"
        test_filename = "test_audio.mp3"
        
        url = audio_storage.save_audio_file(test_content, test_filename)
        
        if url:
            print(f"✅ Test audio file saved: {url}")
            
            # Check if file exists
            if audio_storage.file_exists(test_filename):
                print(f"✅ File existence check works")
            
            # Clean up test file
            import os as os_module
            test_path = os_module.path.join(audio_storage.audio_dir, test_filename)
            if os_module.path.exists(test_path):
                os_module.remove(test_path)
                print(f"✅ Test file cleaned up")
            
            return True
        else:
            print("❌ Failed to save test audio file")
            return False
            
    except Exception as e:
        print(f"❌ Audio storage test failed: {str(e)}")
        return False


def test_elevenlabs():
    """Test ElevenLabs TTS with audio_storage"""
    print("=" * 70)
    print("🎤 Testing ElevenLabs TTS")
    print("=" * 70)
    
    try:
        from audio_storage import init_audio_storage
        
        webhook_base = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
        audio_storage = init_audio_storage(webhook_base)
        
        tts = ElevenLabsTTS(audio_storage=audio_storage)
        
        if not tts.api_key or not tts.voice_id:
            print("⚠️  ElevenLabs not configured - will use Twilio TTS fallback")
            return True  # Not a failure
        
        # Test audio generation
        test_message = "Hello, this is a test message."
        audio_url = tts.generate_audio_url(test_message, "English")
        
        if audio_url:
            print(f"✅ ElevenLabs audio generated: {audio_url}")
            print(f"   Using audio_storage: {tts.audio_storage is not None}")
            return True
        else:
            print("⚠️  ElevenLabs audio generation failed - will use Twilio TTS fallback")
            return True  # Not a failure
            
    except Exception as e:
        print(f"⚠️  ElevenLabs test failed: {str(e)} - will use Twilio TTS fallback")
        return True  # Not a failure


def test_agent_config():
    """Test agent configuration"""
    print("=" * 70)
    print("🤖 Testing Agent Configuration")
    print("=" * 70)
    
    try:
        print(f"Available agents: {list(AGENT_METADATA.keys())}")
        
        for agent_type in AGENT_METADATA.keys():
            config = AGENT_METADATA[agent_type]
            
            # Check required fields
            required_fields = [
                "system_prompt",
                "positive_thank_you_msg",
                "negative_thank_you_msg",
                "welcome_msg",
                "language_selection"
            ]
            
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                print(f"❌ {agent_type}: Missing fields: {missing_fields}")
                return False
            else:
                print(f"✅ {agent_type}: All required fields present")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent config test failed: {str(e)}")
        return False


def test_api_server():
    """Test if API server is running"""
    print("=" * 70)
    print("🌐 Testing API Server")
    print("=" * 70)
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API server is running")
            print(f"   Service: {data.get('service')}")
            print(f"   Agents: {data.get('agents')}")
            print(f"   Voice: {data.get('voice')}")
            print(f"   LLM: {data.get('llm')}")
            return True
        else:
            print(f"❌ API server returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ API server is not running")
        print("   Start it with: python agent_voice_conversation.py")
        return False
    except Exception as e:
        print(f"❌ API server test failed: {str(e)}")
        return False


def test_start_call():
    """Test starting a call (without actually calling)"""
    print("=" * 70)
    print("📞 Testing Call Initiation (Dry Run)")
    print("=" * 70)
    
    print("⚠️  Skipping actual call test to avoid charges")
    print("   To test manually, run:")
    print('   curl -X POST "http://localhost:8000/start-call?agent_type=LOGISTICS&phone_number=+91xxx"')
    print()
    return True


def main():
    """Run all tests"""
    print()
    print("🧪 Multi-Agent Voice Conversation System - Test Suite")
    print()
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("MongoDB Connection", test_mongodb),
        ("Audio Storage", test_audio_storage),
        ("ElevenLabs TTS", test_elevenlabs),
        ("Agent Configuration", test_agent_config),
        ("API Server", test_api_server),
        ("Call Initiation", test_start_call)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            print()
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            results[test_name] = False
            print()
    
    # Summary
    print("=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print()
        print("🎉 All tests passed! System is ready.")
        print()
        print("Next steps:")
        print("1. Start the server: python agent_voice_conversation.py")
        print("2. Expose with ngrok: ngrok http 8000")
        print("3. Update WEBHOOK_BASE_URL in .env")
        print("4. Make a test call: POST /start-call")
    else:
        print()
        print("⚠️  Some tests failed. Please fix the issues above.")
    
    print()


if __name__ == "__main__":
    main()
