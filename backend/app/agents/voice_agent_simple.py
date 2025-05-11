"""
LiveKit Voice Agent for handling phone calls
Simplified version compatible with current LiveKit Agents SDK
"""
import logging
import asyncio
import json
from typing import Dict, Optional, Any
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli

from app.services.ai_agent import ai_agent
from app.services.speech_services import speech_services
from app.utils.logger import get_logger

logger = get_logger(__name__)

class SalonVoiceAgent:
    """
    Voice Agent for the AI receptionist
    Handles phone conversations using LiveKit Agents framework
    """
    
    def __init__(self):
        """Initialize the voice agent"""
        self.ai_agent = ai_agent
        self.active_calls: Dict[str, Any] = {}
    
    async def entrypoint(self, ctx: JobContext):
        """
        Main entry point for the voice agent
        Called when a new phone call arrives
        """
        try:
            logger.info(f"Voice agent started for job {ctx.job.id}")
            
            # Get the room
            room = ctx.room
            
            # Wait for a participant to join
            @room.on("participant_connected")
            async def on_participant_connected(participant: rtc.RemoteParticipant):
                logger.info(f"Participant connected: {participant.identity}")
                
                # Extract caller information
                metadata = self._parse_participant_metadata(participant)
                call_id = metadata.get("callId", f"call_{ctx.job.id}")
                phone_number = metadata.get("from", "unknown")
                customer_id = phone_number.replace("+", "")
                
                # Create a new call record
                call_record = await self.ai_agent.handle_incoming_call(
                    call_id, customer_id, phone_number
                )
                
                if call_record:
                    self.active_calls[call_id] = {
                        "participant": participant,
                        "call_record": call_record,
                        "room": room
                    }
                    
                    # Start handling the conversation
                    await self._handle_participant(room, participant, call_id)
            
            # Keep the job alive
            await asyncio.sleep(300)  # 5 minutes max call duration
            
        except Exception as e:
            logger.error(f"Error in voice agent: {e}", exc_info=True)
        finally:
            # Clean up
            for call_id in list(self.active_calls.keys()):
                await self._end_call(call_id)
    
    def _parse_participant_metadata(self, participant: rtc.RemoteParticipant) -> Dict[str, Any]:
        """Parse metadata from the participant"""
        try:
            metadata = json.loads(participant.metadata) if participant.metadata else {}
            return metadata
        except Exception as e:
            logger.error(f"Error parsing participant metadata: {e}")
            return {}
    
    async def _handle_participant(self, room: rtc.Room, participant: rtc.RemoteParticipant, call_id: str):
        """Handle a participant in the call"""
        try:
            logger.info(f"Handling participant {participant.identity} for call {call_id}")
            
            # Send initial greeting
            greeting = f"Thank you for calling {self.ai_agent.salon_info['name']}. How can I help you today?"
            await self._send_audio_response(room, greeting)
            
            # Listen for audio tracks
            @participant.on("track_published")
            async def on_track_published(publication: rtc.RemoteTrackPublication):
                if publication.kind == rtc.TrackKind.KIND_AUDIO:
                    logger.info(f"Audio track published: {publication.sid}")
                    track = await publication.track
                    if isinstance(track, rtc.RemoteAudioTrack):
                        await self._handle_audio_track(room, track, call_id)
            
            # Handle participant disconnect
            @participant.on("disconnected")
            async def on_disconnected():
                logger.info(f"Participant {participant.identity} disconnected")
                await self._end_call(call_id)
            
        except Exception as e:
            logger.error(f"Error handling participant: {e}")
    
    async def _handle_audio_track(self, room: rtc.Room, track: rtc.RemoteAudioTrack, call_id: str):
        """Handle incoming audio from the participant"""
        try:
            logger.info(f"Handling audio track for call {call_id}")
            
            # Create an audio stream to receive data
            audio_stream = rtc.AudioStream(track)
            
            # Buffer for collecting audio data
            audio_buffer = bytearray()
            min_audio_length = 16000  # Minimum samples for transcription
            
            async for frame in audio_stream:
                # Collect audio data
                audio_buffer.extend(frame.data)
                
                # Process when we have enough audio
                if len(audio_buffer) >= min_audio_length:
                    # Convert to bytes for transcription
                    audio_data = bytes(audio_buffer)
                    audio_buffer.clear()
                    
                    # Transcribe the audio
                    text = await self._transcribe_audio(audio_data)
                    
                    if text:
                        logger.info(f"User said: {text}")
                        
                        # Process the question
                        result = await self.ai_agent.process_call_question(call_id, text)
                        
                        if result:
                            # Send the response
                            await self._send_audio_response(room, result["answer"])
        
        except Exception as e:
            logger.error(f"Error handling audio track: {e}")
    
    async def _transcribe_audio(self, audio_data: bytes) -> str:
        """Convert speech to text"""
        try:
            text = await speech_services.transcribe(audio_data, {
                "encoding": "LINEAR16",
                "sample_rate": 16000,
                "language": "en-US"
            })
            return text
        except Exception as e:
            logger.error(f"STT error: {e}")
            return ""
    
    async def _send_audio_response(self, room: rtc.Room, text: str):
        """Send audio response to the participant"""
        try:
            # Convert text to speech
            audio_data = await speech_services.synthesize_speech(text, {
                "voice_id": "professional_female",
                "speed": 1.0
            })
            
            if audio_data:
                # Create an audio source and track
                audio_source = rtc.AudioSource(
                    sample_rate=16000,
                    num_channels=1
                )
                
                track = rtc.LocalAudioTrack.create_audio_track(
                    "assistant_voice",
                    audio_source
                )
                
                # Publish the track to the room
                options = rtc.TrackPublishOptions()
                publication = await room.local_participant.publish_track(track, options)
                
                # Send the audio data
                # Note: This is a simplified version. In production, you'd need to
                # properly format and stream the audio data
                logger.info(f"Sending audio response: {text[:50]}...")
                
                # For now, we'll just log that we would send the audio
                # In a real implementation, you'd need to convert the audio data
                # to the proper format and feed it to the audio source
        
        except Exception as e:
            logger.error(f"Error sending audio response: {e}")
    
    async def _end_call(self, call_id: str):
        """End a call and clean up"""
        try:
            if call_id in self.active_calls:
                logger.info(f"Ending call {call_id}")
                
                # Calculate duration (simplified)
                duration_ms = 60000  # 1 minute for now
                
                # Handle call ended
                await self.ai_agent.handle_call_ended(call_id, duration_ms)
                
                # Clean up
                del self.active_calls[call_id]
        
        except Exception as e:
            logger.error(f"Error ending call: {e}")

# Create a global instance
voice_agent = SalonVoiceAgent()

# Worker options for LiveKit
worker_options = WorkerOptions(
    entrypoint_fnc=voice_agent.entrypoint,
)

# Export the worker function for use with LiveKit CLI
def run_worker():
    """Run the voice agent worker using the LiveKit CLI"""
    cli.run_app(worker_options)

# For running the agent as a worker
if __name__ == "__main__":
    run_worker()