"""
Logging configuration utilities
"""
import logging
import logging.config
import sys
from typing import Any

from app.config import settings

# Define logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(funcName)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "default",
            "stream": sys.stdout
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "detailed",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "root": {
        "level": settings.LOG_LEVEL,
        "handlers": ["console", "file"] if not settings.DEBUG else ["console"]
    },
    "loggers": {
        "app": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "file"] if not settings.DEBUG else ["console"],
            "propagate": False
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        },
        "livekit": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        }
    }
}

def setup_logging():
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    import os
    from pathlib import Path
    
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Apply logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Set root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    
    # Log startup message
    logger = logging.getLogger("app")
    logger.info(f"Logging initialized with level: {settings.LOG_LEVEL}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Name of the logger (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f"app.{name}")

class LoggerAdapter(logging.LoggerAdapter):
    """
    Custom logger adapter to add extra context
    """
    
    def process(self, msg: str, kwargs: Any) -> tuple:
        """Process log message"""
        extra = self.extra.copy()
        
        # Add any extra context from kwargs
        if "extra" in kwargs:
            extra.update(kwargs.pop("extra"))
        
        # Add extra to kwargs for the logger
        kwargs["extra"] = extra
        
        return msg, kwargs

def get_logger_with_context(name: str, **context) -> LoggerAdapter:
    """
    Get a logger with additional context
    
    Args:
        name: Name of the logger
        **context: Additional context to include in logs
    
    Returns:
        LoggerAdapter instance
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, context)