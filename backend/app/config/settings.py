"""
Application settings and configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application settings
APP_NAME = "Human-in-Loop AI Supervisor"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))

# Database settings
DB_TYPE = os.getenv("DB_TYPE", "dynamodb")
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
DYNAMODB_REGION = os.getenv("DYNAMODB_REGION", "ap-south-1")
DYNAMODB_ACCESS_KEY = os.getenv("DYNAMODB_ACCESS_KEY", "dummy")
DYNAMODB_SECRET_KEY = os.getenv("DYNAMODB_SECRET_KEY", "dummy")

# LiveKit settings
LIVEKIT_ENABLED = os.getenv("LIVEKIT_ENABLED", "False").lower() == "true"
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")

# SIP settings
SIP_ENABLED = os.getenv("SIP_ENABLED", "False").lower() == "true"
SIP_DOMAIN = os.getenv("SIP_DOMAIN", "sip.livekit.io")
DEFAULT_CALLER_ID = os.getenv("DEFAULT_CALLER_ID", "+18005551234")

# Speech settings - STT Providers
STT_PROVIDER = os.getenv("STT_PROVIDER", "deepgram").strip()  # deepgram, assemblyai, google
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")

# Speech settings - TTS Providers
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "neuphonic").strip()  # neuphonic, elevenlabs, google
NEUPHONIC_API_KEY = os.getenv("NEUPHONIC_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
TTS_VOICE_ID = os.getenv("TTS_VOICE_ID", "")  # Voice ID for TTS providers

LLM_API_KEY = os.getenv("GROQ_API_KEY", "")

# Common speech settings
SPEECH_RECOGNITION_LANGUAGE = os.getenv("SPEECH_RECOGNITION_LANGUAGE", "en-US")
SPEECH_MODEL = os.getenv("SPEECH_MODEL", "nova-2")  # For Deepgram
TTS_SPEED = float(os.getenv("TTS_SPEED", "1.0"))
TTS_PITCH = float(os.getenv("TTS_PITCH", "0"))

# Recording settings
RECORD_CALLS = os.getenv("RECORD_CALLS", "False").lower() == "true"
RECORDING_FORMAT = os.getenv("RECORDING_FORMAT", "mp3")
S3_BUCKET = os.getenv("S3_BUCKET", "")

# Room settings
DEFAULT_ROOM = os.getenv("DEFAULT_ROOM", "salon-reception")
AI_IDENTITY = os.getenv("AI_IDENTITY", "ai-receptionist")
AI_NAME = os.getenv("AI_NAME", "AI Receptionist")

# Notification settings
NOTIFICATION_ENABLED = os.getenv("NOTIFICATION_ENABLED", "False").lower() == "true"
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
SUPERVISOR_PHONE_NUMBERS = os.getenv("SUPERVISOR_PHONE_NUMBERS", "").split(",")

# Salon information (default data)
SALON_INFO = {
    "name": "Elegant Touch Salon",
    "address": "123 Main Street, Downtown",
    "hours": "Monday-Friday: 9am-7pm, Saturday: 10am-5pm, Sunday: Closed",
    "services": ["Haircut", "Coloring", "Styling", "Manicure", "Pedicure"],
    "prices": {
        "Haircut": "$45-$65",
        "Coloring": "$85-$150",
        "Styling": "$35-$55",
        "Manicure": "$25",
        "Pedicure": "$35"
    },
    "stylists": ["Emma", "James", "Sophia", "Michael"]
}
BUSINESS_NAME='Elegant Touch Salon'

# Timeout settings
HELP_REQUEST_TIMEOUT_SECONDS = int(os.getenv("HELP_REQUEST_TIMEOUT_SECONDS", "3600"))