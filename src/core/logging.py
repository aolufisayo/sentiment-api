# src/core/logging.py
from loguru import logger
import sys
from pathlib import Path
from ..config import settings

def setup_logging():
    """Configure logging for production"""
    
    # Remove default handler
    logger.remove()
    
    # Console logging
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=settings.DEBUG
    )
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # File logging with rotation
    logger.add(
        settings.LOG_FILE,
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        backtrace=True,
        diagnose=True
    )
    
    # Error logging
    logger.add(
        settings.ERROR_LOG_FILE,
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        backtrace=True,
        diagnose=True
    )
    
    # JSON logging (for structured logging)
    logger.add(
        "logs/structured.log",
        rotation="1 day",
        retention="7 days",
        serialize=True,
        level=settings.LOG_LEVEL
    )
    
    logger.info(f"✅ Logging configured (level: {settings.LOG_LEVEL})")
    
    return logger