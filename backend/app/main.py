"""
Main FastAPI application entry point
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.api.routes import api_router
from app.services.ai_agent import ai_agent
from app.models.help_request import HelpRequest
from app.models.knowledge_base import KnowledgeBase
from app.models.call_record import CallRecord
from app.utils.logger import setup_logging, get_logger

# Set up logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    description="Human-in-the-Loop AI Supervisor with LiveKit SIP integration",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Mount static files directory if it exists
static_dir = Path(__file__).parent / "web" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Serve the frontend
@app.get("/")
async def serve_frontend():
    """Serve the frontend application"""
    template_file = Path(__file__).parent / "web" / "templates" / "index.html"
    if template_file.exists():
        return FileResponse(str(template_file))
    else:
        return {"message": "Frontend not found. This is the API endpoint."}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "livekit": {
            "enabled": settings.LIVEKIT_ENABLED,
            "sip_enabled": settings.SIP_ENABLED,
            "status": "connected" if ai_agent.livekit_sip else "disconnected"
        },
        "services": {
            "speech_to_text": settings.STT_PROVIDER,
            "text_to_speech": settings.TTS_PROVIDER,
            "notifications": settings.NOTIFICATION_ENABLED
        }
    }

# Background task for checking help request timeouts
async def check_help_request_timeouts():
    """Background task to check for timed out help requests"""
    while True:
        try:
            timed_out_count = await HelpRequest.check_timeouts()
            if timed_out_count > 0:
                logger.info(f"Marked {timed_out_count} help requests as timed out")
        except Exception as e:
            logger.error(f"Error checking help request timeouts: {e}")
        
        # Check every minute
        await asyncio.sleep(60)


# Application startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting up application...")
    
    try:
        # Create data directory if it doesn't exist
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Initialize database tables
        logger.info("Initializing database tables...")
        await HelpRequest.init_table()
        await KnowledgeBase.init_table()
        await CallRecord.init_table()
        
        # Initialize AI agent and LiveKit SIP integration
        logger.info("Initializing AI agent...")
        initialized = await ai_agent.initialize()
        
        if initialized:
            logger.info("AI agent initialized successfully")
            
            # Start the voice agent service
            from app.services.agent_service import agent_service
            
            if await agent_service.start():
                logger.info("Voice Agent service started successfully")
            else:
                logger.warning("Voice Agent service failed to start")
        else:
            logger.warning("AI agent initialization failed or LiveKit SIP is disabled")
        
        # Start background tasks
        asyncio.create_task(check_help_request_timeouts())
        
        logger.info("Application startup complete")
    
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # In production, you might want to exit the application if initialization fails
        # raise e

# Application shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    logger.info("Shutting down application...")
    
    try:
        # Stop the voice agent service
        from app.services.agent_service import agent_service
        agent_service.stop()
        
        # Clean up AI agent resources
        await ai_agent.cleanup()
        
        logger.info("Application shutdown complete")
    
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors"""
    return HTTPException(status_code=400, detail=str(exc))

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return HTTPException(status_code=404, detail="Resource not found")

@app.exception_handler(500)
async def server_error_handler(request, exc):
    """Handle server errors"""
    logger.error(f"Server error: {exc}")
    return HTTPException(status_code=500, detail="Internal server error")

# Development mode - run with uvicorn
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )