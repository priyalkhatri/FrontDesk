"""
AI Voice Agent Service for LiveKit integration
Wrapper service for managing the voice agent
"""
import os
import sys
import asyncio
import logging
from typing import Optional
from pathlib import Path

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class VoiceAgentService:
    """
    Voice Agent Service wrapper
    Manages the LiveKit Voice Agent lifecycle
    """
    
    def __init__(self):
        """Initialize the voice agent service"""
        self.running = False
    
    async def start(self) -> bool:
        """
        Start the voice agent worker
        
        Returns:
            bool: True if started successfully
        """
        if not settings.LIVEKIT_ENABLED or not settings.SIP_ENABLED:
            logger.info("Voice agent service not started: LiveKit or SIP not enabled")
            return False
        
        if self.running:
            logger.warning("Voice agent service is already running")
            return True
        
        try:
            logger.info("Voice agent service ready (run worker separately)")
            self.running = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to start voice agent service: {e}")
            return False
    
    def stop(self):
        """Stop the voice agent worker"""
        if not self.running:
            return
        
        logger.info("Stopping voice agent service...")
        self.running = False

# Global instance
agent_service = VoiceAgentService()

# Import the actual worker runner
def run_worker():
    """Run the voice agent worker"""
    from app.services.voice_agent import run_worker as run_voice_worker
    run_voice_worker()

if __name__ == "__main__":
    run_worker()