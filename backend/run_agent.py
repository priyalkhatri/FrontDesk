# backend/run_voice_agent.py
#!/usr/bin/env python3
"""
Run the LiveKit Voice Agent
"""
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.agents.voice_agent import run_worker
from app.config import settings
from app.utils.logger import setup_logging, get_logger

# Set up logging
setup_logging()
logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info("Starting Voice Agent Worker...")
    logger.info(f"Using Deepgram STT (nova-3, multi-language)")
    logger.info(f"Using Groq LLM (llama3-8b-8192)")
    logger.info(f"Using Neuphonic TTS")
    
    try:
        run_worker()
    except Exception as e:
        logger.error(f"Worker failed: {e}", exc_info=True)
        sys.exit(1)