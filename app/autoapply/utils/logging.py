"""
Logging Module - Handles logging configuration
"""
import sys
from pathlib import Path
from datetime import datetime

from loguru import logger

def setup_logger(name: str = None) -> logger:
    """
    Setup logger with custom configuration.
    
    Args:
        name: Optional name for the logger
        
    Returns:
        Configured logger instance
    """
    # Remove default handler
    logger.remove()
    
    # Setup log directory
    log_dir = Path("storage/logs")
    if name:
        log_dir = log_dir / name
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{timestamp}.log"
    
    # Add handlers
    # Console handler with colors
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    # File handler with detailed format
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="1 day",
        retention="1 week",
        compression="zip"
    )
    
    return logger 