"""
Voice-Only LiveKit SIP Integration
Optimized for voice calls without video functionality
"""
import os
import json
import time
import asyncio
import logging
import websockets
from typing import Dict, List, Callable, Any, Optional, Union

# Correct imports from LiveKit API
from livekit.api import (
    LiveKitAPI, 
    AccessToken, 
    VideoGrants,
    CreateSIPTrunkRequest,
    SIPTrunkInfo,
)

from app.config.livekit_config import livekit_config
from app.utils.logger import get_logger

logger = get_logger(__name__)

class LiveKitSipIntegration:
    """
    LiveKit SIP Integration optimized for voice-only calls
    Handles phone call functionality through LiveKit SIP
    """
    
    def __init__(self, on_call_received=None, on_call_ended=None, on_audio_data=None):
        """
        Initialize LiveKit SIP integration for voice calls
        
        Args:
            on_call_received: Callback for new calls
            on_call_ended: Callback for ended calls
            on_audio_data: Callback for audio data
        """
        self.config = livekit_config
        self.on_call_received = on_call_received
        self.on_call_ended = on_call_ended
        self.on_audio_data = on_audio_data
        self.active_calls: Dict[str, dict] = {}
        self.api_client = None
        self.ws_connection = None
        self.ws_task = None
    
    async def initialize(self) -> bool:
        """
        Initialize the voice-only LiveKit SIP integration
        
        Returns:
            bool: True if initialization was successful
        """
        # Skip if SIP is disabled
        if not self.config.sip_enabled:
            logger.info("SIP integration is disabled, skipping initialization")
            return False
        
        # Validate configuration
        if not self.config.validate():
            logger.error("Invalid LiveKit configuration, SIP integration disabled")
            return False
        
        try:
            logger.info("Initializing voice-only LiveKit SIP integration...")
            
            # Clean up URL - remove protocol if present
            url = self.config.livekit_url
            if url.startswith("wss://"):
                url = url[6:]
            elif url.startswith("https://"):
                url = url[8:]
            
            # Initialize LiveKit API client
            self.api_client = LiveKitAPI(
                f"https://{url}",
                self.config.api_key,
                self.config.api_secret
            )
            
            # Create a SIP trunk if needed
            sip_trunk = await self.create_sip_trunk()
            if not sip_trunk:
                logger.error("Failed to create/load SIP trunk")
                return False
            
            # Start WebSocket listener for events
            await self.setup_websocket_listener()
            
            logger.info("Voice-only LiveKit SIP integration initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize LiveKit SIP integration: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def create_sip_trunk(self) -> Optional[dict]:
        """
        Create a SIP trunk in LiveKit optimized for voice calls
        
        Returns:
            dict: SIP trunk configuration
        """
        # Check if we already have a SIP trunk configuration saved
        if self.config.sip_trunk_id:
            logger.info(f"Using existing SIP trunk: {self.config.sip_trunk_id}")
            return {"id": self.config.sip_trunk_id}
        
        logger.info("Creating new voice-optimized SIP trunk in LiveKit")
        
        try:
            # Voice-optimized SIP trunk configuration
            trunk_config = self.config.get_sip_trunk_config()
            
            # For development/testing, use a mock response
            # In production, you would use the LiveKit API directly
            trunk_response = {
                "id": f"st_{int(time.time())}",
                "name": "Voice-Only AI Receptionist",
                "created_at": int(time.time()),
                "updated_at": int(time.time()),
                **trunk_config
            }
            
            # Save the configuration
            self.config.save_sip_trunk_config(trunk_response)
            logger.info(f"Voice-only SIP trunk created with ID: {trunk_response['id']}")
            
            return trunk_response
        
        except Exception as e:
            logger.error(f"Error creating SIP trunk: {e}")
            return None
    
    async def setup_websocket_listener(self):
        """
        Set up WebSocket listener for LiveKit voice events
        """
        logger.info("Setting up WebSocket listener for voice events")
        
        try:
            # For SIP monitoring, we'll use a simpler approach
            # The actual voice handling happens in the voice agent worker
            logger.info("SIP event monitoring will be handled by the voice agent worker")
            
            # Start a task to periodically check for active calls
            self.ws_task = asyncio.create_task(self._monitor_sip_events())
            
        except Exception as e:
            logger.error(f"Error setting up voice WebSocket listener: {e}")
            logger.warning("Using mock WebSocket listener for development")
            self.ws_task = asyncio.create_task(self._mock_websocket_listener())
    
    async def _websocket_listener(self, url):
        """
        WebSocket listener task optimized for voice events
        
        Args:
            url: WebSocket URL with token
        """
        retry_delay = 1  # Start with 1 second retry delay
        max_retry_delay = 60  # Maximum retry delay in seconds
        
        while True:
            try:
                logger.info(f"Connecting to voice WebSocket...")
                
                # Add proper connection options
                async with websockets.connect(
                    url, 
                    ping_interval=20,  # Send ping every 20 seconds
                    ping_timeout=10,   # Wait 10 seconds for pong response
                    close_timeout=5    # Wait 5 seconds for close handshake
                ) as websocket:
                    self.ws_connection = websocket
                    logger.info("WebSocket connected to LiveKit for voice events")
                    
                    # Send a presence message
                    presence_msg = {
                        "type": "presence",
                        "role": "monitor"
                    }
                    await websocket.send(json.dumps(presence_msg))
                    
                    # Reset retry delay on successful connection
                    retry_delay = 1
                    
                    async for message in websocket:
                        try:
                            # Parse and handle the event
                            event = json.loads(message)
                            event_type = event.get('type', 'unknown')
                            logger.debug(f"Received voice event: {event_type}")
                            await self.handle_livekit_event(event)
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON in WebSocket message: {message[:100]}...")
                        except Exception as e:
                            logger.error(f"Error handling WebSocket message: {e}")
            
            except websockets.exceptions.InvalidStatusCode as e:
                logger.error(f"WebSocket connection failed with status code: {e.status_code}")
                if hasattr(e, 'headers'):
                    logger.error(f"Response headers: {e.headers}")
                if hasattr(e, 'body'):
                    logger.error(f"Response body: {e.body[:200]}")
                
                # This is likely an authentication issue
                if e.status_code == 401:
                    logger.error("Authentication failed! Check your API key and secret.")
            
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
            
            # Connection lost, retry with exponential backoff
            logger.info(f"WebSocket disconnected, retrying in {retry_delay} seconds...")
            self.ws_connection = None
            await asyncio.sleep(retry_delay)
            
            # Exponential backoff with max delay
            retry_delay = min(retry_delay * 2, max_retry_delay)
    
    async def _mock_websocket_listener(self):
        """Mock WebSocket listener for development"""
        logger.info("Mock voice WebSocket listener started")
        
        while True:
            try:
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                logger.debug("Mock WebSocket listener heartbeat")
            except asyncio.CancelledError:
                break
    
    async def handle_livekit_event(self, event):
        """
        Handle LiveKit events for voice calls
        
        Args:
            event: LiveKit event data
        """
        if not event or "type" not in event:
            return
        
        event_type = event.get("type")
        
        # Handle participant events (focus on audio tracks)
        if event_type == "participant_joined":
            await self._handle_participant_joined(event)
        
        elif event_type == "participant_left":
            await self._handle_participant_left(event)
        
        elif event_type == "track_published":
            # Only process audio tracks
            track = event.get("track", {})
            if track and track.get("type") == "audio":
                await self._handle_track_published(event)
    
    async def _handle_participant_joined(self, event):
        """Handle participant joined events"""
        participant = event.get("participant", {})
        metadata = participant.get("metadata", "{}")
        
        try:
            metadata_dict = json.loads(metadata) if metadata else {}
            
            # Check if this is a SIP participant (phone call)
            if metadata_dict.get("type") == "sip":
                call_id = metadata_dict.get("callId", f"call_{participant.get('identity')}")
                phone_number = metadata_dict.get("from", "unknown")
                
                logger.info(f"Voice call received: {call_id} from {phone_number}")
                
                # Update call information
                if call_id in self.active_calls:
                    self.active_calls[call_id].update({
                        "participant_id": participant.get("identity"),
                        "phone_number": phone_number,
                        "status": "active"
                    })
                else:
                    self.active_calls[call_id] = {
                        "room_name": event.get("room"),
                        "participant_id": participant.get("identity"),
                        "phone_number": phone_number,
                        "start_time": time.time(),
                        "status": "active"
                    }
                
                # Trigger callback if needed
                if self.on_call_received:
                    customer_id = phone_number.replace("+", "")
                    await self.on_call_received(call_id, customer_id, phone_number)
        
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in participant metadata: {metadata}")
        except Exception as e:
            logger.error(f"Error processing participant joined: {e}")
    
    async def _handle_participant_left(self, event):
        """Handle participant left events (call ended)"""
        participant = event.get("participant", {})
        participant_id = participant.get("identity")
        
        # Find the call associated with this participant
        call_id = None
        call_data = None
        
        for cid, cdata in list(self.active_calls.items()):
            if cdata.get("participant_id") == participant_id:
                call_id = cid
                call_data = cdata
                break
        
        if call_id and call_data:
            logger.info(f"Voice call ended: {call_id}")
            
            # Calculate duration
            duration_ms = int((time.time() - call_data.get("start_time", time.time())) * 1000)
            
            # Update status
            call_data["status"] = "ended"
            call_data["end_time"] = time.time()
            call_data["duration_ms"] = duration_ms
            
            # Trigger callback
            if self.on_call_ended:
                await self.on_call_ended(call_id, duration_ms)
    
    async def _handle_track_published(self, event):
        """Handle audio track published events"""
        track = event.get("track", {})
        
        if track and track.get("type") == "audio":
            logger.debug(f"Audio track published: {track.get('sid')}")
            # For processing audio data, you would implement this
            # based on your specific requirements
    
    async def create_test_call(self, phone_number: str = "+15551234567") -> Optional[str]:
        """
        Create a test voice call for development
        
        Args:
            phone_number: Phone number to simulate
            
        Returns:
            str: Call ID if successful
        """
        try:
            # Create a unique call ID
            call_id = f"voice_call_{int(time.time())}"
            
            # Mock a call for development
            self.active_calls[call_id] = {
                "room_name": "voice-test-room",
                "phone_number": phone_number,
                "start_time": time.time(),
                "status": "active"
            }
            
            # Trigger callback if needed
            if self.on_call_received:
                customer_id = phone_number.replace("+", "")
                await self.on_call_received(call_id, customer_id, phone_number)
            
            logger.info(f"Created test voice call: {call_id}")
            return call_id
            
        except Exception as e:
            logger.error(f"Error creating test voice call: {e}")
            return None
    
    async def end_call(self, call_id: str) -> bool:
        """
        End an active voice call
        
        Args:
            call_id: Call identifier
            
        Returns:
            bool: Success status
        """
        call = self.active_calls.get(call_id)
        if not call:
            logger.error(f"Cannot end call: Call {call_id} not found")
            return False
        
        try:
            # Calculate duration
            duration_ms = int((time.time() - call.get("start_time", time.time())) * 1000)
            
            # Trigger callback
            if self.on_call_ended:
                await self.on_call_ended(call_id, duration_ms)
            
            logger.info(f"Voice call {call_id} ended")
            self.active_calls.pop(call_id, None)
            return True
        
        except Exception as e:
            logger.error(f"Error ending voice call {call_id}: {e}")
            return False
    
    async def cleanup(self):
        """Clean up resources when shutting down"""
        logger.info("Cleaning up voice-only LiveKit SIP integration")
        
        # End all active calls
        for call_id in list(self.active_calls.keys()):
            await self.end_call(call_id)
        
        # Cancel WebSocket task
        if self.ws_task:
            self.ws_task.cancel()
            try:
                await self.ws_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket connection
        if self.ws_connection:
            await self.ws_connection.close()