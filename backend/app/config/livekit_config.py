"""
LiveKit and SIP configuration
"""
import os
import json
from pathlib import Path
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class LiveKitConfig:
    """LiveKit SIP configuration"""
    
    def __init__(self):
        """Initialize LiveKit configuration"""
        # Core LiveKit credentials
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
        self.livekit_url = settings.LIVEKIT_URL
        
        # SIP settings
        self.sip_enabled = settings.SIP_ENABLED
        self.sip_domain = settings.SIP_DOMAIN
        self.default_caller_id = settings.DEFAULT_CALLER_ID
        
        # Room settings
        self.default_room = settings.DEFAULT_ROOM
        self.ai_identity = settings.AI_IDENTITY
        self.ai_name = settings.AI_NAME
        
        # Audio settings
        self.dtmf_enabled = True  # Enable DTMF tones
        self.audio_bandwidth = "medium"  # low, medium, high
        self.audio_encoding = "OPUS"  # OPUS, PCMU, PCMA
        
        # Paths
        self.config_dir = Path(__file__).parent.parent.parent / "data"
        self.config_dir.mkdir(exist_ok=True)
        self.sip_trunk_config_path = self.config_dir / "sip_trunk_config.json"
        
        # SIP trunk ID (loaded from config file if available)
        self.sip_trunk_id = None
        self._load_sip_trunk_config()
    
    def _load_sip_trunk_config(self):
        """Load SIP trunk configuration from file if available"""
        if self.sip_trunk_config_path.exists():
            try:
                with open(self.sip_trunk_config_path, "r") as f:
                    config = json.load(f)
                    self.sip_trunk_id = config.get("id")
                    logger.info(f"Loaded SIP trunk config with ID: {self.sip_trunk_id}")
            except Exception as e:
                logger.error(f"Error loading SIP trunk config: {e}")
    
    def save_sip_trunk_config(self, config):
        """Save SIP trunk configuration to file"""
        try:
            with open(self.sip_trunk_config_path, "w") as f:
                json.dump(config, f, indent=2)
            self.sip_trunk_id = config.get("id")
            logger.info(f"Saved SIP trunk config with ID: {self.sip_trunk_id}")
        except Exception as e:
            logger.error(f"Error saving SIP trunk config: {e}")
    
    def validate(self):
        """Validate the configuration"""
        if not self.sip_enabled:
            logger.info("SIP integration is disabled")
            return True
        
        # Check required fields
        if not self.api_key or not self.api_secret or not self.livekit_url:
            logger.error("Missing required LiveKit credentials!")
            logger.error("Make sure LIVEKIT_API_KEY, LIVEKIT_API_SECRET, and LIVEKIT_URL are set in your .env file")
            return False
        
        # Validate URL format (no protocol or trailing slashes)
        if not self.livekit_url or "://" in self.livekit_url or self.livekit_url.endswith("/"):
            logger.error("Invalid LiveKit URL format!")
            logger.error("The URL should not include protocol (https://) or trailing slash")
            return False
        
        return True
    
    def get_sip_trunk_config(self):
        """Get SIP trunk configuration parameters with Voice Agent support"""
        return {
            "name": "AI Receptionist SIP Trunk",
            "audioEncoding": self.audio_encoding,
            "defaultBandwidth": self.audio_bandwidth,
            "enableDTMF": self.dtmf_enabled,
            "inbound": {
                "enabled": True,
                "rooms": [{
                    "name": self.default_room,
                    "participantIdentity": self.ai_identity,
                    "participantName": self.ai_name,
                    "participantMetadata": json.dumps({
                        "role": "agent",
                        "type": "ai_receptionist"
                    })
                }],
                "dispatch": {
                    "rule": "agent",  # Route to agent instead of specific room
                    "agent_id": "ai-receptionist"
                }
            },
            "outbound": {
                "enabled": True,
                "fromName": "Elegant Touch Salon",
                "sipDomain": self.sip_domain
            },
            "agent": {
                "enabled": True,
                "agent_id": "ai-receptionist",
                "metadata": json.dumps({
                    "type": "ai_receptionist",
                    "business": "Elegant Touch Salon"
                })
            }
        }
    
    def get_recording_config(self):
        """Get recording configuration"""
        if not settings.RECORD_CALLS:
            return None
        
        return {
            "enabled": True,
            "format": settings.RECORDING_FORMAT,
            "s3Bucket": settings.S3_BUCKET if settings.S3_BUCKET else None,
            "s3KeyPrefix": "call-recordings/"
        }

# Create a singleton instance
livekit_config = LiveKitConfig()