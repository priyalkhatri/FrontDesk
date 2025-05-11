"""
Speech-to-Text and Text-to-Speech services with real implementations
Supports: Deepgram (STT), Neuphonic (TTS), ElevenLabs (TTS), AssemblyAI (STT)
"""
import asyncio
import json
import logging
import aiohttp
import websockets
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class STTProvider(Enum):
    DEEPGRAM = "deepgram"
    ASSEMBLYAI = "assemblyai"
    GOOGLE = "google"
    
class TTSProvider(Enum):
    NEUPHONIC = "neuphonic"
    ELEVENLABS = "elevenlabs"
    GOOGLE = "google"

class SpeechServices:
    """
    Speech Services for handling speech recognition and synthesis
    """
    
    def __init__(self):
        """Initialize speech services with real providers"""
        # STT Configuration
        try:
            self.stt_provider = STTProvider(settings.STT_PROVIDER.lower())
        except ValueError:
            logger.warning(f"Invalid STT provider '{settings.STT_PROVIDER}', defaulting to Deepgram")
            self.stt_provider = STTProvider.DEEPGRAM
        self.deepgram_api_key = settings.DEEPGRAM_API_KEY if hasattr(settings, 'DEEPGRAM_API_KEY') else None
        self.assemblyai_api_key = settings.ASSEMBLYAI_API_KEY if hasattr(settings, 'ASSEMBLYAI_API_KEY') else None
        
        # TTS Configuration
        try:
            self.tts_provider = TTSProvider(settings.TTS_PROVIDER.lower())
        except ValueError:
            logger.warning(f"Invalid TTS provider '{settings.TTS_PROVIDER}', defaulting to Neuphonic")
            self.tts_provider = TTSProvider.NEUPHONIC
        self.neuphonic_api_key = settings.NEUPHONIC_API_KEY if hasattr(settings, 'NEUPHONIC_API_KEY') else None
        self.elevenlabs_api_key = settings.ELEVENLABS_API_KEY if hasattr(settings, 'ELEVENLABS_API_KEY') else None
        
        # Voice settings
        self.language = settings.SPEECH_RECOGNITION_LANGUAGE
        self.voice_id = settings.TTS_VOICE_ID if hasattr(settings, 'TTS_VOICE_ID') else None
        
        # Initialize provider clients
        self._init_providers()
    
    def _init_providers(self):
        """Initialize provider-specific configurations"""
        # STT Providers
        if self.stt_provider == STTProvider.DEEPGRAM and self.deepgram_api_key:
            logger.info("Initialized Deepgram for Speech-to-Text")
        elif self.stt_provider == STTProvider.ASSEMBLYAI and self.assemblyai_api_key:
            logger.info("Initialized AssemblyAI for Speech-to-Text")
        else:
            logger.warning(f"No valid API key for {self.stt_provider.value} STT")
        
        # TTS Providers
        if self.tts_provider == TTSProvider.NEUPHONIC and self.neuphonic_api_key:
            logger.info("Initialized Neuphonic for Text-to-Speech")
        elif self.tts_provider == TTSProvider.ELEVENLABS and self.elevenlabs_api_key:
            logger.info("Initialized ElevenLabs for Text-to-Speech")
        else:
            logger.warning(f"No valid API key for {self.tts_provider.value} TTS")
    
    async def transcribe(self, audio_data: bytes, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Transcribe audio data to text using the configured provider
        
        Args:
            audio_data: Raw audio data
            options: Additional options for speech recognition
            
        Returns:
            str: Transcribed text
        """
        try:
            if self.stt_provider == STTProvider.DEEPGRAM:
                return await self._transcribe_deepgram(audio_data, options)
            elif self.stt_provider == STTProvider.ASSEMBLYAI:
                return await self._transcribe_assemblyai(audio_data, options)
            else:
                logger.warning(f"Unsupported STT provider: {self.stt_provider}")
                return ""
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return ""
    
    async def _transcribe_deepgram(self, audio_data: bytes, options: Optional[Dict[str, Any]] = None) -> str:
        """Transcribe using Deepgram API"""
        if not self.deepgram_api_key:
            logger.error("Deepgram API key not configured")
            return ""
        
        url = "https://api.deepgram.com/v1/listen"
        
        headers = {
            "Authorization": f"Token {self.deepgram_api_key}",
            "Content-Type": "audio/wav"
        }
        
        params = {
            "model": options.get("model", "nova-2"),
            "language": options.get("language", self.language),
            "punctuate": "true",
            "diarize": "false",
            "smart_format": "true"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, params=params, data=audio_data) as response:
                if response.status == 200:
                    result = await response.json()
                    # Get the transcript from Deepgram response
                    transcript = result.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
                    return transcript
                else:
                    error_text = await response.text()
                    logger.error(f"Deepgram API error: {response.status} - {error_text}")
                    return ""
    
    async def _transcribe_assemblyai(self, audio_data: bytes, options: Optional[Dict[str, Any]] = None) -> str:
        """Transcribe using AssemblyAI API"""
        if not self.assemblyai_api_key:
            logger.error("AssemblyAI API key not configured")
            return ""
        
        headers = {
            "authorization": self.assemblyai_api_key,
            "content-type": "application/json"
        }
        
        # First, upload the audio file
        upload_url = "https://api.assemblyai.com/v2/upload"
        async with aiohttp.ClientSession() as session:
            async with session.post(upload_url, headers=headers, data=audio_data) as response:
                if response.status != 200:
                    logger.error(f"AssemblyAI upload error: {response.status}")
                    return ""
                upload_result = await response.json()
                audio_url = upload_result["upload_url"]
            
            # Then, request transcription
            transcript_url = "https://api.assemblyai.com/v2/transcript"
            data = {
                "audio_url": audio_url,
                "language_code": options.get("language", self.language),
                "punctuate": True,
                "format_text": True
            }
            
            async with session.post(transcript_url, headers=headers, json=data) as response:
                if response.status != 200:
                    logger.error(f"AssemblyAI transcription error: {response.status}")
                    return ""
                transcript_response = await response.json()
                transcript_id = transcript_response["id"]
            
            # Poll for the result
            polling_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
            while True:
                async with session.get(polling_url, headers=headers) as response:
                    result = await response.json()
                    if result["status"] == "completed":
                        return result["text"]
                    elif result["status"] == "error":
                        logger.error(f"AssemblyAI error: {result.get('error', 'Unknown error')}")
                        return ""
                    
                    await asyncio.sleep(1)
    
    async def synthesize_speech(self, text: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Convert text to speech using the configured provider
        
        Args:
            text: Text to convert to speech
            options: Additional options for text-to-speech
            
        Returns:
            bytes: Audio data
        """
        try:
            if self.tts_provider == TTSProvider.NEUPHONIC:
                return await self._synthesize_neuphonic(text, options)
            elif self.tts_provider == TTSProvider.ELEVENLABS:
                return await self._synthesize_elevenlabs(text, options)
            else:
                logger.warning(f"Unsupported TTS provider: {self.tts_provider}")
                return b""
        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            return b""
    
    async def _synthesize_neuphonic(self, text: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        """Synthesize speech using Neuphonic API"""
        if not self.neuphonic_api_key:
            logger.error("Neuphonic API key not configured")
            return b""
        
        url = "https://api.neuphonic.com/v1/tts"
        
        headers = {
            "Authorization": f"Bearer {self.neuphonic_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "text": text,
            "voice_id": options.get("voice_id", self.voice_id) or "default",
            "language": options.get("language", self.language),
            "output_format": options.get("format", "mp3"),
            "speed": options.get("speed", 1.0),
            "pitch": options.get("pitch", 0)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    audio_content = await response.read()
                    return audio_content
                else:
                    error_text = await response.text()
                    logger.error(f"Neuphonic API error: {response.status} - {error_text}")
                    return b""
    
    async def _synthesize_elevenlabs(self, text: str, options: Optional[Dict[str, Any]] = None) -> bytes:
        """Synthesize speech using ElevenLabs API"""
        if not self.elevenlabs_api_key:
            logger.error("ElevenLabs API key not configured")
            return b""
        
        voice_id = options.get("voice_id", self.voice_id) or "21m00Tcm4TlvDq8ikWAM"  # Default voice
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        
        data = {
            "text": text,
            "model_id": options.get("model_id", "eleven_monolingual_v1"),
            "voice_settings": {
                "stability": options.get("stability", 0.5),
                "similarity_boost": options.get("similarity_boost", 0.5),
                "style": options.get("style", 0.5),
                "use_speaker_boost": options.get("use_speaker_boost", True)
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    audio_content = await response.read()
                    return audio_content
                else:
                    error_text = await response.text()
                    logger.error(f"ElevenLabs API error: {response.status} - {error_text}")
                    return b""
    
    async def streaming_recognize(self, audio_stream, callback: Callable[[Optional[str], Optional[str]], None]):
        """
        Stream audio to a speech recognition service for real-time transcription
        
        Args:
            audio_stream: Stream of audio data
            callback: Callback for transcription results (error, text)
        """
        if self.stt_provider == STTProvider.DEEPGRAM:
            await self._streaming_recognize_deepgram(audio_stream, callback)
        elif self.stt_provider == STTProvider.ASSEMBLYAI:
            await self._streaming_recognize_assemblyai(audio_stream, callback)
        else:
            logger.error(f"Streaming not supported for {self.stt_provider}")
            callback("Provider not supported", None)
    
    async def _streaming_recognize_deepgram(self, audio_stream, callback: Callable[[Optional[str], Optional[str]], None]):
        """Stream audio to Deepgram WebSocket for real-time transcription"""
        if not self.deepgram_api_key:
            logger.error("Deepgram API key not configured")
            callback("API key not configured", None)
            return
        
        # Deepgram WebSocket URL
        url = f"wss://api.deepgram.com/v1/listen?model=nova-2&language={self.language}&punctuate=true&interim_results=true"
        
        headers = {
            "Authorization": f"Token {self.deepgram_api_key}"
        }
        
        try:
            async with websockets.connect(url, extra_headers=headers) as websocket:
                logger.info("Connected to Deepgram WebSocket")
                
                # Start tasks for sending audio and receiving transcriptions
                send_task = asyncio.create_task(self._send_audio_to_deepgram(websocket, audio_stream))
                receive_task = asyncio.create_task(self._receive_from_deepgram(websocket, callback))
                
                # Wait for both tasks
                await asyncio.gather(send_task, receive_task)
                
        except Exception as e:
            logger.error(f"Deepgram WebSocket error: {e}")
            callback(str(e), None)
    
    async def _send_audio_to_deepgram(self, websocket, audio_stream):
        """Send audio data to Deepgram WebSocket"""
        try:
            async for chunk in audio_stream:
                if chunk:
                    await websocket.send(chunk)
            
            # Send close message
            await websocket.send(json.dumps({"type": "CloseStream"}))
            
        except Exception as e:
            logger.error(f"Error sending audio to Deepgram: {e}")
    
    async def _receive_from_deepgram(self, websocket, callback):
        """Receive transcriptions from Deepgram WebSocket"""
        try:
            async for message in websocket:
                result = json.loads(message)
                
                if result.get("type") == "Results":
                    transcript = result.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
                    is_final = result.get("is_final", False)
                    
                    if transcript and is_final:
                        callback(None, transcript)
                
        except Exception as e:
            logger.error(f"Error receiving from Deepgram: {e}")
            callback(str(e), None)
    
    async def _streaming_recognize_assemblyai(self, audio_stream, callback: Callable[[Optional[str], Optional[str]], None]):
        """Stream audio to AssemblyAI for real-time transcription"""
        if not self.assemblyai_api_key:
            logger.error("AssemblyAI API key not configured")
            callback("API key not configured", None)
            return
        
        # AssemblyAI WebSocket URL
        url = "wss://api.assemblyai.com/v2/realtime/ws"
        
        try:
            async with websockets.connect(
                url,
                extra_headers={"Authorization": self.assemblyai_api_key},
                ping_interval=5,
                ping_timeout=20
            ) as websocket:
                logger.info("Connected to AssemblyAI WebSocket")
                
                # Send session begins
                session_begins = {
                    "message_type": "SessionBegins",
                    "timestamp": "now"
                }
                await websocket.send(json.dumps(session_begins))
                
                # Start tasks for sending audio and receiving transcriptions
                send_task = asyncio.create_task(self._send_audio_to_assemblyai(websocket, audio_stream))
                receive_task = asyncio.create_task(self._receive_from_assemblyai(websocket, callback))
                
                # Wait for both tasks
                await asyncio.gather(send_task, receive_task)
                
        except Exception as e:
            logger.error(f"AssemblyAI WebSocket error: {e}")
            callback(str(e), None)
    
    async def _send_audio_to_assemblyai(self, websocket, audio_stream):
        """Send audio data to AssemblyAI WebSocket"""
        try:
            async for chunk in audio_stream:
                if chunk:
                    audio_data = {
                        "message_type": "AudioData",
                        "audio_data": chunk.hex()  # AssemblyAI expects hex-encoded audio
                    }
                    await websocket.send(json.dumps(audio_data))
            
            # Send terminate stream
            terminate_stream = {
                "message_type": "TerminateStream"
            }
            await websocket.send(json.dumps(terminate_stream))
            
        except Exception as e:
            logger.error(f"Error sending audio to AssemblyAI: {e}")
    
    async def _receive_from_assemblyai(self, websocket, callback):
        """Receive transcriptions from AssemblyAI WebSocket"""
        try:
            async for message in websocket:
                result = json.loads(message)
                
                if result.get("message_type") == "FinalTranscript":
                    transcript = result.get("text", "")
                    if transcript:
                        callback(None, transcript)
                
        except Exception as e:
            logger.error(f"Error receiving from AssemblyAI: {e}")
            callback(str(e), None)

# Create a singleton instance
speech_services = SpeechServices()