"""Logging utilities for the project."""

import logging
import sys
from pathlib import Path
from src.utils.config import LOG_DIR, LOG_FORMAT, LOG_LEVEL


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    Set up a logger with both console and file handlers.
    
    Args:
        name: Logger name (typically __name__)
        log_file: Optional log file name. If provided, logs are written to LOG_DIR/log_file
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False

    if logger.handlers:
        return logger
    
    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler (optional)
    if log_file:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_path = LOG_DIR / log_file
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with the given name."""
    return setup_logger(name)
