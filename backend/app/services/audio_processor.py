"""
Audio processing service for LiveKit SIP calls
"""
import asyncio
import numpy as np
import logging
from typing import Dict, List, Optional, Callable, Any, Tuple
from collections import deque

from app.services.speech_services import speech_services
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AudioProcessor:
    """
    AudioProcessor handles audio processing for LiveKit SIP calls
    """
    
    def __init__(self):
        """Initialize audio processor"""
        self.active_streams: Dict[str, dict] = {}
        self.speech_detection_threshold = 0.3  # Voice activity detection threshold
        self.silence_timeout = 1.5  # seconds of silence to consider speech complete
        self.buffer_size_ms = 100  # milliseconds of audio per buffer
    
    async def process_audio_track(self, call_id: str, audio_track: Any, 
                                 on_transcription: Callable[[str, str], None]) -> bool:
        """
        Process a new audio track from LiveKit
        
        Args:
            call_id: Call identifier
            audio_track: LiveKit audio track
            on_transcription: Callback for transcription results
            
        Returns:
            bool: Success status
        """
        logger.info(f"Processing audio track for call {call_id}")
        
        # Stop existing processing if any
        if call_id in self.active_streams:
            logger.info(f"Replacing existing audio stream for call {call_id}")
            await self.stop_processing(call_id)
        
        try:
            # Store stream information
            self.active_streams[call_id] = {
                "track": audio_track,
                "on_transcription": on_transcription,
                "last_activity": asyncio.get_event_loop().time(),
                "silence_timer": None,
                "audio_buffer": bytearray(),
                "utterances": [],
                "processing": True
            }
            
            # Start processing audio in a background task
            asyncio.create_task(self._process_audio_stream(call_id))
            
            logger.info(f"Audio processing started for call {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up audio processing for call {call_id}: {e}")
            return False
    
    async def _process_audio_stream(self, call_id: str):
        """
        Process audio stream from a call
        
        Args:
            call_id: Call identifier
        """
        stream_data = self.active_streams.get(call_id)
        if not stream_data:
            return
        
        try:
            # In a real implementation, we would get audio frames from the LiveKit track
            # For this demo, we'll simulate audio processing
            
            while stream_data["processing"]:
                # Simulate receiving audio data
                await asyncio.sleep(0.1)  # 100ms chunks
                
                # In a real system, we would get actual audio data from LiveKit
                # For now, we'll simulate audio detection
                has_voice = self._simulate_voice_activity()
                
                if has_voice:
                    # Voice detected, update activity time
                    stream_data["last_activity"] = asyncio.get_event_loop().time()
                    
                    # Cancel silence timer if exists
                    if stream_data["silence_timer"]:
                        stream_data["silence_timer"].cancel()
                        stream_data["silence_timer"] = None
                    
                    # Simulate adding audio to buffer
                    stream_data["audio_buffer"].extend(b'\x00' * 1600)  # 100ms of 16kHz audio
                
                else:
                    # No voice detected
                    if stream_data["audio_buffer"] and not stream_data["silence_timer"]:
                        # Start silence timer
                        stream_data["silence_timer"] = asyncio.create_task(
                            self._handle_silence_timeout(call_id)
                        )
        
        except Exception as e:
            logger.error(f"Error in audio stream processing for call {call_id}: {e}")
        
        finally:
            # Clean up
            if call_id in self.active_streams:
                self.active_streams[call_id]["processing"] = False
    
    async def _handle_silence_timeout(self, call_id: str):
        """
        Handle silence timeout - process accumulated utterance
        
        Args:
            call_id: Call identifier
        """
        try:
            # Wait for silence timeout
            await asyncio.sleep(self.silence_timeout)
            
            stream_data = self.active_streams.get(call_id)
            if not stream_data or not stream_data["audio_buffer"]:
                return
            
            # Process the accumulated utterance
            audio_data = bytes(stream_data["audio_buffer"])
            callback = stream_data["on_transcription"]
            
            # Clear buffer
            stream_data["audio_buffer"] = bytearray()
            stream_data["silence_timer"] = None
            
            # Process the utterance
            await self.process_utterance(call_id, audio_data, callback)
        
        except asyncio.CancelledError:
            # Silence timer was cancelled
            pass
        except Exception as e:
            logger.error(f"Error in silence timeout for call {call_id}: {e}")
    
    def _simulate_voice_activity(self) -> bool:
        """
        Simulate voice activity detection
        In a real implementation, this would analyze audio samples
        
        Returns:
            bool: True if voice is detected
        """
        # Simulate voice activity (60% chance of voice)
        import random
        return random.random() < 0.6
    
    def detect_voice_activity(self, audio_data: bytes) -> bool:
        """
        Detect voice activity in audio data
        
        Args:
            audio_data: Audio data to analyze
            
        Returns:
            bool: True if voice detected
        """
        # In a real implementation, this would use a voice activity detection algorithm
        # For this demo, we'll use a simple energy-based detection
        
        try:
            # Convert buffer to numpy array (assuming 16-bit PCM)
            if len(audio_data) < 2:
                return False
            
            samples = np.frombuffer(audio_data, dtype=np.int16)
            
            # Calculate energy
            if len(samples) == 0:
                return False
            
            energy = np.abs(samples).mean() / 32768.0
            
            # Compare to threshold
            return energy > self.speech_detection_threshold
        
        except Exception as e:
            logger.error(f"Error in voice activity detection: {e}")
            return False
    
    async def process_utterance(self, call_id: str, audio_data: bytes, 
                              on_transcription: Callable[[str, str], None]):
        """
        Process a complete utterance
        
        Args:
            call_id: Call identifier
            audio_data: Complete utterance audio data
            on_transcription: Callback for transcription results
        """
        logger.debug(f"Processing utterance from call {call_id}, {len(audio_data)} bytes")
        
        try:
            # Get the call data
            call_data = self.active_streams.get(call_id)
            if not call_data:
                return
            
            # Store the utterance info
            call_data["utterances"].append({
                "timestamp": asyncio.get_event_loop().time(),
                "audio_length": len(audio_data)
            })
            
            # Transcribe the audio
            text = await speech_services.transcribe(audio_data, {
                "encoding": "LINEAR16",
                "sample_rate": 16000
            })
            
            if text and text.strip():
                logger.info(f"Transcription for call {call_id}: \"{text}\"")
                
                # Call the transcription callback
                if on_transcription:
                    on_transcription(call_id, text)
        
        except Exception as e:
            logger.error(f"Error processing utterance for call {call_id}: {e}")
    
    async def stop_processing(self, call_id: str):
        """
        Stop processing audio for a call
        
        Args:
            call_id: Call identifier
        """
        call_data = self.active_streams.get(call_id)
        if not call_data:
            return
        
        try:
            # Stop processing
            call_data["processing"] = False
            
            # Cancel any pending silence timer
            if call_data["silence_timer"]:
                call_data["silence_timer"].cancel()
            
            # Remove from active streams
            self.active_streams.pop(call_id, None)
            
            logger.info(f"Audio processing stopped for call {call_id}")
        
        except Exception as e:
            logger.error(f"Error stopping audio processing for call {call_id}: {e}")
    
    async def synthesize_response(self, text: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Create audio from text for TTS responses
        
        Args:
            text: Text to synthesize
            options: TTS options
            
        Returns:
            bytes: Audio data
        """
        return await speech_services.synthesize_speech(text, options)

# Create a singleton instance
audio_processor = AudioProcessor()