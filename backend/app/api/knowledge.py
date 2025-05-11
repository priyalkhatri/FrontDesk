"""
Knowledge base API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.knowledge_base import KnowledgeBase
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Pydantic models for request/response
class KnowledgeBaseResponse(BaseModel):
    question_id: str
    question: str
    answer: str
    created_at: int
    confidence: float
    source_request_id: Optional[str] = None

class KnowledgeBaseCreate(BaseModel):
    question: str
    answer: str
    confidence: Optional[float] = 1.0
    source_request_id: Optional[str] = None

@router.get("/", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_base(limit: int = 100):
    """
    Get all knowledge base entries
    
    Args:
        limit: Maximum number of results
    
    Returns:
        List of knowledge base entries
    """
    try:
        entries = await KnowledgeBase.get_all(limit)
        
        # Convert to response models
        return [KnowledgeBaseResponse(**entry.to_dict()) for entry in entries]
    
    except Exception as e:
        logger.error(f"Error listing knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[KnowledgeBaseResponse])
async def search_knowledge_base(q: str):
    """
    Search the knowledge base
    
    Args:
        q: Search query
    
    Returns:
        List of matching knowledge base entries
    """
    try:
        if not q:
            raise HTTPException(status_code=400, detail="Search query is required")
        
        entries = await KnowledgeBase.find_similar(q)
        
        # Convert to response models
        return [KnowledgeBaseResponse(**entry.to_dict()) for entry in entries]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base_entry(entry_data: KnowledgeBaseCreate):
    """
    Add a new knowledge base entry
    
    Args:
        entry_data: Knowledge base entry data
    
    Returns:
        Created knowledge base entry
    """
    try:
        # Create new entry
        entry = KnowledgeBase(
            question=entry_data.question,
            answer=entry_data.answer,
            confidence=entry_data.confidence,
            source_request_id=entry_data.source_request_id
        )
        
        await entry.save()
        
        return KnowledgeBaseResponse(**entry.to_dict())
    
    except Exception as e:
        logger.error(f"Error creating knowledge base entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{question_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base_entry(question_id: str):
    """
    Get a specific knowledge base entry
    
    Args:
        question_id: Knowledge base entry ID
    
    Returns:
        Knowledge base entry details
    """
    try:
        entry = await KnowledgeBase.get_by_id(question_id)
        
        if not entry:
            raise HTTPException(status_code=404, detail="Knowledge base entry not found")
        
        return KnowledgeBaseResponse(**entry.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge base entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))