"""
Logger Module

This module provides consistent logging functionality across the application.
"""
import logging
import os
import sys
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance for the given name.
    
    Args:
        name: Logger name, typically __name__ of the module
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure the logger if it hasn't been configured yet
    if not logger.handlers:
        # Set level from environment variable or default to INFO
        log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, log_level, logging.INFO)
        logger.setLevel(level)
    
    return logger


def configure_logger(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
):
    """
    Configure the root logger for the application.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format string
        log_file: Optional path to log file
    """
    # Determine log level
    level_name = log_level or os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    
    # Determine log format
    log_fmt = log_format or os.environ.get(
        "LOG_FORMAT", 
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    date_fmt = "%Y-%m-%d %H:%M:%S"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_fmt, date_fmt))
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(log_fmt, date_fmt))
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.error(f"Failed to create log file handler: {str(e)}")
    
    # Configure third-party loggers to reduce noise
    for logger_name in [
        "uvicorn", 
        "uvicorn.error",
        "fastapi",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
    ]:
        third_party_level = os.environ.get(
            "THIRD_PARTY_LOG_LEVEL", "WARNING"
        ).upper()
        third_party_logger = logging.getLogger(logger_name)
        third_party_logger.setLevel(getattr(logging, third_party_level, logging.WARNING)) 