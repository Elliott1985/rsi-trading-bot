"""
Logging utilities for the Autonomous Trading AI
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logger(name: str, level: int = logging.INFO, 
                log_to_file: bool = True, log_to_console: bool = True) -> logging.Logger:
    """
    Set up a logger with console and file handlers
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
    
    Returns:
        Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding multiple handlers
    if logger.hasHandlers():
        return logger
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create log file with timestamp
        log_file = log_dir / f"trading_bot_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get an existing logger or create a new one with default settings"""
    return setup_logger(name)