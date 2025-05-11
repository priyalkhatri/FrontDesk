"""
AI Agent service with LiveKit SIP integration
"""
import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Union

from app.config import settings
from app.models.help_request import HelpRequest
from app.models.knowledge_base import KnowledgeBase
from app.models.call_record import CallRecord
from app.services.speech_services import speech_services
from app.services.audio_processor import audio_processor
from app.services.notification_service import notification_service
from app.integrations.livekit_sip import LiveKitSipIntegration
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AIAgent:
    """
    AI Agent with LiveKit SIP integration
    Handles phone calls, questions, and integrates with the human-in-the-loop system
    """
    
    def __init__(self):
        """Initialize AI agent"""
        self.salon_info = settings.SALON_INFO
        self.livekit_sip = None
        self._initialized = False  # Add this property
        
        # Initialize LiveKit SIP integration when agent is created
        if settings.LIVEKIT_ENABLED and settings.SIP_ENABLED:
            self.livekit_sip = LiveKitSipIntegration(
                on_call_received=self.handle_incoming_call,
                on_call_ended=self.handle_call_ended,
                on_audio_data=self.handle_audio_data
            )
    @property
    def initialized(self):
        """Check if agent is initialized"""
        return self._initialized


    async def initialize(self) -> bool:
        """
        Initialize the AI agent
        
        Returns:
            bool: True if initialization was successful
        """
        # Initialize LiveKit SIP integration if enabled
        if self.livekit_sip:
            success = await self.livekit_sip.initialize()
            self._initialized = success
            return success
        
        self._initialized = True
        return True
    
    async def handle_incoming_call(self, call_id: str, customer_id: str, phone_number: str) -> Optional[CallRecord]:
        """
        Handle an incoming call from the SIP trunk
        
        Args:
            call_id: Call identifier
            customer_id: Customer identifier
            phone_number: Customer phone number
            
        Returns:
            CallRecord: Call record if successful, None otherwise
        """
        logger.info(f"Handling incoming call {call_id} from {phone_number}")
        
        try:
            # Create a call record
            call = CallRecord(
                call_id=call_id,
                customer_id=customer_id,
                customer_phone=phone_number,
                status="in_progress"
            )
            
            await call.save()
            
            # Send greeting
            greeting = f"Thank you for calling {self.salon_info['name']}. How can I help you today?"
            
            await self.send_response(call_id, greeting)
            
            # Add greeting to transcript
            await call.add_transcript_entry("ai", greeting)
            
            # Set up audio processing for this call
            # In a real implementation, you would get the audio track from LiveKit
            # and pass it to the audio processor
            
            return call
        
        except Exception as e:
            logger.error(f"Error handling incoming call {call_id}: {e}")
            return None
    
    async def handle_call_ended(self, call_id: str, duration_ms: int):
        """
        Handle call ended event
        
        Args:
            call_id: Call identifier
            duration_ms: Call duration in milliseconds
        """
        logger.info(f"Call {call_id} ended, duration: {duration_ms}ms")
        
        try:
            # Update call record
            call = await CallRecord.get_by_id(call_id)
            if call:
                call.status = "completed"
                call.duration = int(duration_ms / 1000)  # Convert to seconds
                await call.save()
        
        except Exception as e:
            logger.error(f"Error handling call ended for {call_id}: {e}")
    
    async def handle_audio_data(self, call_id: str, audio_data: bytes):
        """
        Handle audio data from the call for speech-to-text
        
        Args:
            call_id: Call identifier
            audio_data: Audio data
        """
        logger.debug(f"Received audio data from call {call_id}")
        
        try:
            # Process audio through speech-to-text
            transcribed_text = await speech_services.transcribe(audio_data, {
                "encoding": "LINEAR16",
                "sample_rate": 16000
            })
            
            if transcribed_text:
                logger.info(f"Transcribed text from call {call_id}: \"{transcribed_text}\"")
                
                # Process the question
                await self.process_call_question(call_id, transcribed_text)
        
        except Exception as e:
            logger.error(f"Error handling audio data for call {call_id}: {e}")
    
    async def process_call_question(self, call_id: str, question: str) -> Optional[Dict[str, Any]]:
        """
        Process a question from a phone call
        
        Args:
            call_id: Call identifier
            question: Customer question
            
        Returns:
            dict: Response data with answer and whether it needed help
        """
        try:
            # Get call record
            call = await CallRecord.get_by_id(call_id)
            if not call:
                logger.error(f"Call {call_id} not found")
                return None
            
            # Add customer question to transcript
            await call.add_transcript_entry("customer", question)
            
            # Get answer from knowledge base or salon info
            result = await self.answer_question(question)
            answer, needs_help = result["answer"], result["needs_help"]
            
            # Add AI response to transcript
            await call.add_transcript_entry("ai", answer)
            
            # Send spoken response via LiveKit
            await self.send_response(call_id, answer)
            
            # If we need help, create a help request
            if needs_help:
                await self.create_help_request(question, call_id, call.customer_id, call.customer_phone)
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing call question for {call_id}: {e}")
            return None
    
    async def send_response(self, call_id: str, text: str) -> bool:
        """
        Send a response to a caller
        
        Args:
            call_id: Call identifier
            text: Response text
            
        Returns:
            bool: Success status
        """
        if not self.livekit_sip:
            logger.info(f"SIMULATED RESPONSE TO CALL {call_id}: \"{text}\"")
            return True
        
        logger.info(f"RESPONSE TO CALL {call_id}: \"{text}\"")
        return True

    async def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a question using knowledge base or salon info
        
        Args:
            question: Question to answer
            
        Returns:
            dict: Response with answer and whether it needed help
        """
        # First check knowledge base for learned answers
        knowledge_match = await self.find_similar_question(question)
        if knowledge_match:
            logger.info(f"Found answer in knowledge base for: {question}")
            return {
                "answer": knowledge_match.answer,
                "needs_help": False
            }
        
        # Only answer VERY basic questions
        simple_answer = self.check_simple_questions(question)
        if simple_answer:
            logger.info(f"Answered basic question: {question}")
            return {
                "answer": simple_answer,
                "needs_help": False
            }
        
        # For everything else, escalate immediately
        logger.info(f"Escalating to supervisor: {question}")
        return {
            "answer": "Let me check with my supervisor and get back to you.",
            "needs_help": True
        }
        
    async def find_similar_question(self, question: str) -> Optional[KnowledgeBase]:
        """
        Find a similar question in the knowledge base
        
        Args:
            question: Question to search for
            
        Returns:
            KnowledgeBase: Matching knowledge base entry if found
        """
        # In a real implementation, this would use vector embeddings for better matching
        try:
            knowledge_entries = await KnowledgeBase.get_all()
            question_lower = question.lower()
            
            for entry in knowledge_entries:
                entry_question_lower = entry.question.lower()
                
                # Simple string matching - would be more sophisticated in production
                if (question_lower in entry_question_lower or 
                    entry_question_lower in question_lower):
                    return entry
            
            return None
        
        except Exception as e:
            logger.error(f"Error finding similar question: {e}")
            return None
    
    def check_simple_questions(self, question: str) -> Optional[str]:
        """
        ONLY answer very basic salon information.
        For everything else, escalate to supervisor.
        
        Args:
            question: Question to check
            
        Returns:
            str: Answer if it's a very basic question, None otherwise
        """
        question_lower = question.lower()
        
        # Only answer these specific basic questions:
        
        # 1. Hours - ONLY for basic hour inquiries
        if ("what" in question_lower and "hour" in question_lower) or \
        ("when" in question_lower and ("open" in question_lower or "close" in question_lower)):
            return f"Our hours are {self.salon_info['hours']}"
        
        # 2. Address/Location - ONLY for basic location inquiries
        if ("where" in question_lower and ("located" in question_lower or "location" in question_lower)) or \
        ("what" in question_lower and "address" in question_lower):
            return f"We're located at {self.salon_info['address']}"
        
        # 3. Services - ONLY for general service listing
        if "what services" in question_lower or "services do you offer" in question_lower:
            return f"We offer {', '.join(self.salon_info['services'])}"
        
        # For ALL other questions, including:
        # - Specific prices
        # - Appointments/booking
        # - Parking
        # - Discounts
        # - Stylists
        # - Specific service details
        # - Cancellations/Rescheduling
        # - Anything else
        
        return None  # This will trigger supervisor escalation
    
    async def create_help_request(self, question: str, call_id: str, 
                                 customer_id: str, customer_phone: str) -> Optional[HelpRequest]:
        """
        Create a help request when the AI doesn't know an answer
        
        Args:
            question: Customer question
            call_id: Call identifier
            customer_id: Customer identifier
            customer_phone: Customer phone number
            
        Returns:
            HelpRequest: Help request if created successfully
        """
        try:
            # Create help request
            help_request = HelpRequest(
                question=question,
                call_id=call_id,
                customer_id=customer_id,
                customer_phone=customer_phone,
                status="pending"
            )
            
            await help_request.save()
            
            # Notify supervisor
            await notification_service.notify_supervisor(
                f"New help request: \"{question}\" from customer {customer_phone}"
            )
            
            return help_request
        
        except Exception as e:
            logger.error(f"Error creating help request: {e}")
            return None
    
    async def resolve_help_request(self, request_id: str, answer: str) -> Optional[HelpRequest]:
        """
        Resolve a help request with an answer
        
        Args:
            request_id: Help request identifier
            answer: Answer from supervisor
            
        Returns:
            HelpRequest: Updated help request if successful
        """
        try:
            # Get help request
            help_request = await HelpRequest.get_by_id(request_id)
            if not help_request:
                logger.error(f"Help request {request_id} not found")
                return None
            
            # Update status and answer
            help_request.status = "resolved"
            help_request.answer = answer
            await help_request.save()
            
            # Add to knowledge base
            knowledge_entry = KnowledgeBase(
                question=help_request.question,
                answer=answer,
                source_request_id=request_id
            )
            await knowledge_entry.save()
            
            # Notify customer
            await self.notify_customer(help_request)
            
            return help_request
        
        except Exception as e:
            logger.error(f"Error resolving help request {request_id}: {e}")
            return None
    
    async def notify_customer(self, help_request: HelpRequest) -> bool:
        """
        Notify a customer when we have an answer to their question
        
        Args:
            help_request: Help request with answer
            
        Returns:
            bool: Success status
        """
        if help_request.status != "resolved" or not help_request.answer:
            return False
        
        try:
            message = f"Hello! You asked about \"{help_request.question}\". Here's the answer: {help_request.answer}"
            
            # If there's an active call, send the response directly
            if help_request.call_id and self.livekit_sip:
                call = await CallRecord.get_by_id(help_request.call_id)
                if call and call.status == "in_progress":
                    await self.send_response(help_request.call_id, message)
                    return True
            
            # Otherwise, send an SMS notification
            await notification_service.notify_customer(help_request.customer_phone, message)
            
            # Optionally, make an outbound call to deliver the answer
            # if self.livekit_sip and help_request.customer_phone:
            #     call_id = await self.livekit_sip.make_outbound_call(help_request.customer_phone)
            #     if call_id:
            #         # Wait for the call to be answered, then deliver the message
            #         # In a real implementation, this would be handled via events
            
            return True
        
        except Exception as e:
            logger.error(f"Error notifying customer about request {help_request.request_id}: {e}")
            return False
    
    async def make_outbound_call(self, phone_number: str, message: str) -> Optional[str]:
        """
        Make an outbound call to a customer
        
        Args:
            phone_number: Phone number to call
            message: Message to deliver
            
        Returns:
            str: Call ID if successful, None otherwise
        """
        if not self.livekit_sip:
            logger.info(f"SIMULATED OUTBOUND CALL TO {phone_number}: \"{message}\"")
            return None
        
        try:
            # Make the call
            call_id = await self.livekit_sip.make_outbound_call(phone_number)
            if not call_id:
                return None
            
            # Create a call record
            call = CallRecord(
                call_id=call_id,
                customer_id=phone_number.replace("+", ""),  # Use phone as customer ID for outbound calls
                customer_phone=phone_number,
                status="in_progress",
                direction="outbound"
            )
            
            await call.save()
            
            # The actual message delivery would happen through the LiveKit event system
            # when the call is answered, but we'll store the intent
            call.pending_message = message
            await call.save()
            
            return call_id
        
        except Exception as e:
            logger.error(f"Error making outbound call to {phone_number}: {e}")
            return None
    
    async def cleanup(self):
        """Clean up resources when shutting down"""
        logger.info("Cleaning up AI agent")
        
        # Clean up LiveKit SIP integration
        if self.livekit_sip:
            await self.livekit_sip.cleanup()

# Create singleton instance
ai_agent = AIAgent()