"""
Calls API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.call_record import CallRecord
from app.services.ai_agent import ai_agent
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter( tags=["calls"])

# Pydantic models for request/response
class CallResponse(BaseModel):
    call_id: str
    customer_id: str
    customer_phone: str
    timestamp: int
    status: str
    duration: Optional[int] = None
    direction: Optional[str] = "inbound"
    transcript: Optional[List[dict]] = None

class StartCallRequest(BaseModel):
    customer_id: str
    customer_phone: str

class ProcessQuestionRequest(BaseModel):
    question: str

class ProcessQuestionResponse(BaseModel):
    answer: str
    needs_help: bool

# IMPORTANT: Place specific routes BEFORE generic routes
@router.get("/test")
async def create_test_call():
    """Create a test call to verify system is working"""
    try:
        # Check if AI agent is initialized
        if not ai_agent or not ai_agent.initialized:
            return {
                "success": False,
                "error": "AI agent not initialized",
                "details": {
                    "ai_agent_exists": bool(ai_agent),
                    "initialized": ai_agent.initialized if ai_agent else False
                }
            }
        
        # Check if LiveKit SIP is available
        if not ai_agent.livekit_sip:
            return {
                "success": False,
                "error": "LiveKit SIP not initialized",
                "details": {
                    "livekit_sip_exists": bool(ai_agent.livekit_sip)
                }
            }
        
        # Create test call
        logger.info("Creating test call...")
        call_id = await ai_agent.livekit_sip.create_test_call()
        
        if call_id:
            logger.info(f"Test call created successfully: {call_id}")
            return {
                "success": True,
                "call_id": call_id,
                "message": "Test call created successfully"
            }
        else:
            logger.warning("Test call creation returned no call_id")
            return {
                "success": False,
                "error": "Failed to create test call - no call_id returned",
                "call_id": None
            }
            
    except Exception as e:
        logger.error(f"Error creating test call: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "call_id": None
        }

@router.post("/", response_model=CallResponse, status_code=201)
async def start_call(call_data: StartCallRequest):
    """
    Start a new call (for testing)
    
    Args:
        call_data: Call data
    
    Returns:
        Created call record
    """
    try:
        # Create a mock call ID for testing
        import uuid
        call_id = f"call_{uuid.uuid4()}"
        
        # In a real system, this would be triggered by LiveKit
        # For testing, we'll simulate it
        call = await ai_agent.handle_incoming_call(
            call_id, 
            call_data.customer_id, 
            call_data.customer_phone
        )
        
        if not call:
            raise HTTPException(status_code=500, detail="Failed to create call")
        
        return CallResponse(**call.to_dict())
    
    except Exception as e:
        logger.error(f"Error starting call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{call_id}/question", response_model=ProcessQuestionResponse)
async def process_question(call_id: str, question_data: ProcessQuestionRequest):
    """
    Process a customer question during a call
    
    Args:
        call_id: Call ID
        question_data: Question data
    
    Returns:
        AI response
    """
    try:
        result = await ai_agent.process_call_question(call_id, question_data.question)
        
        if not result:
            raise HTTPException(status_code=404, detail="Call not found")
        
        return ProcessQuestionResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{call_id}/end", response_model=CallResponse)
async def end_call(call_id: str):
    """
    End an active call
    
    Args:
        call_id: Call ID
    
    Returns:
        Updated call record
    """
    try:
        # Calculate duration (for testing purposes)
        import time
        call = await CallRecord.get_by_id(call_id)
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Simulate call ending
        duration_ms = int((time.time() - call.timestamp) * 1000)
        await ai_agent.handle_call_ended(call_id, duration_ms)
        
        # Get updated call record
        updated_call = await CallRecord.get_by_id(call_id)
        
        return CallResponse(**updated_call.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customer/{customer_id}", response_model=List[CallResponse])
async def get_customer_calls(customer_id: str, limit: int = 20):
    """
    Get all calls for a specific customer
    
    Args:
        customer_id: Customer ID
        limit: Maximum number of results
    
    Returns:
        List of calls
    """
    try:
        calls = await CallRecord.get_by_customer(customer_id, limit)
        
        # Convert to response models
        return [CallResponse(**call.to_dict()) for call in calls]
    
    except Exception as e:
        logger.error(f"Error getting customer calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# This generic route MUST come AFTER specific routes like /test
@router.get("/{call_id}", response_model=CallResponse)
async def get_call(call_id: str):
    """
    Get details for a specific call
    
    Args:
        call_id: Call ID
    
    Returns:
        Call details
    """
    try:
        call = await CallRecord.get_by_id(call_id)
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        return CallResponse(**call.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting call: {e}")
        raise HTTPException(status_code=500, detail=str(e))