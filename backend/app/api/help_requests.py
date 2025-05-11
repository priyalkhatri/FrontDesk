"""
Help requests API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.help_request import HelpRequest
from app.services.ai_agent import ai_agent
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Pydantic models for request/response
class HelpRequestResponse(BaseModel):
    request_id: str
    question: str
    call_id: str
    customer_id: str
    customer_phone: str
    status: str
    timestamp: int
    answer: Optional[str] = None

class ResolveRequest(BaseModel):
    answer: str

@router.get("/", response_model=List[HelpRequestResponse])
async def list_help_requests(status: str = "pending", limit: int = 50):
    """
    Get help requests filtered by status
    
    Args:
        status: Filter by status (pending, resolved, unresolved)
        limit: Maximum number of results
    
    Returns:
        List of help requests
    """
    try:
        if status not in ["pending", "resolved", "unresolved"]:
            raise HTTPException(status_code=400, detail="Invalid status parameter")
        
        requests = await HelpRequest.get_by_status(status, limit)
        
        # Convert to response models
        return [HelpRequestResponse(**req.to_dict()) for req in requests]
    
    except Exception as e:
        logger.error(f"Error listing help requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{request_id}", response_model=HelpRequestResponse)
async def get_help_request(request_id: str):
    """
    Get a specific help request
    
    Args:
        request_id: Help request ID
    
    Returns:
        Help request details
    """
    try:
        request = await HelpRequest.get_by_id(request_id)
        
        if not request:
            raise HTTPException(status_code=404, detail="Help request not found")
        
        return HelpRequestResponse(**request.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting help request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{request_id}/resolve", response_model=HelpRequestResponse)
async def resolve_help_request(request_id: str, resolve_data: ResolveRequest):
    """
    Resolve a help request with an answer
    
    Args:
        request_id: Help request ID
        resolve_data: Answer data
    
    Returns:
        Updated help request
    """
    try:
        # Resolve the request through the AI agent
        resolved_request = await ai_agent.resolve_help_request(request_id, resolve_data.answer)
        
        if not resolved_request:
            raise HTTPException(status_code=404, detail="Help request not found")
        
        return HelpRequestResponse(**resolved_request.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving help request: {e}")
        raise HTTPException(status_code=500, detail=str(e))