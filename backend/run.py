#!/usr/bin/env python
"""
Run the Human-in-the-Loop AI Supervisor application
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app
from app.config import settings
from app.utils.logger import setup_logging, get_logger

# Set up logging
setup_logging()
logger = get_logger(__name__)

def run_server(host: str = None, port: int = None, reload: bool = None):
    """
    Run the FastAPI server
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload
    """
    import uvicorn
    
    # Use command line args or fallback to settings
    host = host or settings.HOST
    port = port or settings.PORT
    reload = reload if reload is not None else settings.DEBUG
    
    logger.info(f"Starting server on {host}:{port} (reload={reload})")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.LOG_LEVEL.lower()
    )

def run_demo():
    """
    Run a demonstration of the system
    """
    from scripts.demo import run_full_demo
    
    logger.info("Running system demonstration...")
    asyncio.run(run_full_demo())

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Human-in-the-Loop AI Supervisor")
    parser.add_argument("command", nargs="?", default="run", 
                        choices=["run", "demo", "test"],
                        help="Command to execute")
    parser.add_argument("--host", type=str, help="Host to bind to")
    parser.add_argument("--port", type=int, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "run":
        reload = None
        if args.reload:
            reload = True
        elif args.no_reload:
            reload = False
        
        run_server(host=args.host, port=args.port, reload=reload)
    
    elif args.command == "demo":
        run_demo()
    
    elif args.command == "test":
        logger.info("Running tests...")
        os.system("pytest tests/")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()