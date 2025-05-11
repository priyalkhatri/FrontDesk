"""
API routes aggregator
"""
from fastapi import APIRouter

from app.api.help_requests import router as help_requests_router
from app.api.knowledge import router as knowledge_router
from app.api.calls import router as calls_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(help_requests_router, prefix="/help-requests", tags=["help_requests"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(calls_router, prefix="/calls", tags=["calls"])