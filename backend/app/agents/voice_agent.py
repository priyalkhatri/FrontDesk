"""
LiveKit Voice Agent for handling phone calls using the new Agent framework
"""
import os
import json
import logging
import asyncio
from typing import Dict, Optional, Any
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import (
    Agent, 
    AgentSession, 
    JobContext, 
    WorkerOptions, 
    cli,
    llm
)
from livekit.plugins import deepgram, openai, silero, neuphonic, groq

from app.config import settings
from app.services.ai_agent import ai_agent
from app.utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

class SalonReceptionist(Agent):
    """Voice agent for the salon that integrates with the knowledge base"""
    
    def __init__(self) -> None:
        # Create salon-specific instructions
        salon_info = settings.SALON_INFO
        
        instructions = f"""
        You are an AI receptionist for {salon_info['name']}. 
        You have VERY LIMITED knowledge and should ONLY answer these specific questions directly:
        
        1. Basic hours: "Our hours are {salon_info['hours']}"
        2. Location: "We're located at {salon_info['address']}"
        3. General services: "We offer {', '.join(salon_info['services'])}"
        
        FOR ALL OTHER QUESTIONS, including but not limited to:
        - Specific prices
        - Appointments or booking
        - Parking information
        - Discounts or special offers
        - Specific stylist information
        - Service details
        - Cancellations or rescheduling
        - ANY other questions
        
        You MUST respond with: "I need to check with my supervisor. Let me get back to you on that."
        
        IMPORTANT: Do NOT attempt to answer questions you're not specifically programmed for.
        IMPORTANT: Do NOT make up information or provide general assistance.
        IMPORTANT: Keep all responses brief and professional.
        """
        
        super().__init__(instructions=instructions)
        self.ai_agent = ai_agent
        self.call_id: Optional[str] = None
        self.customer_id: Optional[str] = None
        self.customer_phone: Optional[str] = None
        self.last_user_message: Optional[str] = None
    
    def set_call_info(self, call_id: str, customer_id: str, customer_phone: str):
        """Set call information for tracking purposes"""
        self.call_id = call_id
        self.customer_id = customer_id
        self.customer_phone = customer_phone

async def entrypoint(ctx: JobContext):
    """Main entry point for the voice agent"""
    logger.info(f"Voice agent started for room {ctx.room.name}")
    
    # Connect to the room
    await ctx.connect()
    
    # Get participant information
    participant = None
    for p in ctx.room.remote_participants.values():
        participant = p
        break
    
    # Extract metadata
    room_sid = ctx.room.name
    call_id = f"call_{room_sid}"
    customer_phone = "unknown"
    
    if participant:
        try:
            metadata = json.loads(participant.metadata) if participant.metadata else {}
            call_id = metadata.get("callId", call_id)
            customer_phone = metadata.get("from", customer_phone)
        except Exception as e:
            logger.error(f"Error parsing participant metadata: {e}")
    
    customer_id = customer_phone.replace("+", "")
    
    logger.info(f"Starting voice assistant for call {call_id} from {customer_phone}")
    
    # Create call record
    call_record = await ai_agent.handle_incoming_call(
        call_id, customer_id, customer_phone
    )
    
    if not call_record:
        logger.error(f"Failed to create call record for {call_id}")
        return
    
    # Create our AI agent
    agent = SalonReceptionist()
    agent.set_call_info(call_id, customer_id, customer_phone)
    
    # Create agent session with components
    session = AgentSession(
        stt=deepgram.STT(
            model="nova-2-phonecall",  # Optimized for phone calls
            language="en-US"
        ),
        llm=groq.LLM(model="llama3-8b-8192"),
        tts=neuphonic.TTS(
            voice_id="e564ba7e-aa8d-46a2-96a8-8dffedade48f",
            api_key=settings.NEUPHONIC_API_KEY if settings.NEUPHONIC_API_KEY else None
        ),
        vad=silero.VAD.load(),
    )
    
    # Start the session
    await session.start(
        room=ctx.room,
        agent=agent,
    )
    
    # Initial greeting
    greeting = f"Thank you for calling {settings.SALON_INFO['name']}. How can I help you today?"
    await session.say(greeting)
    
    # Async handler for user speech
    async def handle_user_speech(user_speech: llm.ChatMessage):
        """Process user speech asynchronously"""
        user_message = user_speech.content
        agent.last_user_message = user_message
        logger.info(f"User said: {user_message}")
        
        # Let the agent handle the message naturally based on its instructions
        # The agent will respond automatically
    
    # Async handler for agent speech
    async def handle_agent_speech(agent_speech: llm.ChatMessage):
        """Check if the agent needs help and create help request"""
        response = agent_speech.content
        logger.info(f"Agent said: {response}")
        
        # Detect when the agent is saying it needs to check with supervisor
        needs_help_phrases = [
            "check with my supervisor",
            "get back to you on that",
            "let me check with my supervisor",
            "i need to check with my supervisor"
        ]
        
        if any(phrase in response.lower() for phrase in needs_help_phrases):
            await handle_help_request(agent, agent.last_user_message)
    
    # Async handler for help request
    async def handle_help_request(agent_instance: SalonReceptionist, question: str):
        """Create help request when agent doesn't know the answer"""
        if not question or not agent_instance.call_id:
            return
            
        logger.info(f"Creating help request for question: {question}")
        
        try:
            # Process through the full AI agent system to create help request
            result = await agent_instance.ai_agent.process_call_question(
                agent_instance.call_id,
                question
            )
            
            logger.info(f"Help request result: {result}")
            
        except Exception as e:
            logger.error(f"Error creating help request: {e}")
    
    # Async handler for participant disconnection
    async def handle_disconnection(participant):
        """Handle participant disconnection asynchronously"""
        logger.info(f"Participant {participant.identity} disconnected")
        # Handle call ended
        if agent.call_id:
            duration_ms = 60000  # You'd calculate this from actual call duration
            await agent.ai_agent.handle_call_ended(agent.call_id, duration_ms)
            logger.info(f"Call {agent.call_id} ended")
    
    # Synchronous event handlers that spawn async tasks
    @session.on("user_speech_committed")
    def on_user_speech(user_speech: llm.ChatMessage):
        """Handle user speech synchronously and spawn async task"""
        asyncio.create_task(handle_user_speech(user_speech))
    
    @session.on("agent_speech_committed")
    def on_agent_speech(agent_speech: llm.ChatMessage):
        """Handle agent speech synchronously and spawn async task"""
        asyncio.create_task(handle_agent_speech(agent_speech))
    
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant):
        """Handle participant disconnection synchronously and spawn async task"""
        asyncio.create_task(handle_disconnection(participant))
    
    # Keep the agent running
    pass

def run_worker():
    """Run the voice agent worker"""
    logger.info("Starting LiveKit Voice Agent Worker...")
    logger.info(f"LiveKit URL: {settings.LIVEKIT_URL}")
    logger.info(f"Business Name: {settings.SALON_INFO['name']}")
    logger.info(f"STT: Deepgram | LLM: Groq | TTS: Neuphonic")
    
    # Run the agent with CLI
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

if __name__ == "__main__":
    run_worker()