"""
Minimal LiveKit Voice Agent for testing
This version uses basic LiveKit SDK features only
"""
import asyncio
import logging
from livekit import agents
from livekit.agents import JobContext, WorkerOptions, cli

from app.services.ai_agent import ai_agent
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def entrypoint(ctx: JobContext):
    """Simple entrypoint that just logs the connection"""
    logger.info(f"Voice agent started for job {ctx.job.id}")
    logger.info(f"Room: {ctx.room.name if ctx.room else 'No room'}")
    
    # Keep the job alive for testing
    try:
        # Handle incoming call
        call_id = f"call_{ctx.job.id}"
        customer_id = "test_customer"
        phone_number = "+1234567890"
        
        # Create a call record
        call_record = await ai_agent.handle_incoming_call(
            call_id, customer_id, phone_number
        )
        
        if call_record:
            logger.info(f"Call record created: {call_id}")
            
            # Simulate a conversation
            questions = [
                "What are your hours?",
                "Do you offer student discounts?",
                "Can I book an appointment?"
            ]
            
            for question in questions:
                logger.info(f"Processing question: {question}")
                result = await ai_agent.process_call_question(call_id, question)
                if result:
                    logger.info(f"AI Response: {result['answer'][:100]}...")
                await asyncio.sleep(2)  # Simulate conversation timing
            
            # End the call
            await ai_agent.handle_call_ended(call_id, 60000)  # 1 minute call
            logger.info(f"Call ended: {call_id}")
    
    except Exception as e:
        logger.error(f"Error in voice agent: {e}", exc_info=True)

# Create worker options
worker_options = WorkerOptions(
    entrypoint_fnc=entrypoint,
)

def run_worker():
    """Run the minimal voice agent worker"""
    logger.info("Starting minimal voice agent worker...")
    cli.run_app(worker_options)

if __name__ == "__main__":
    run_worker()