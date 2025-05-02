"""
Database Factory

This module provides a factory for creating database managers.
"""
from src.utils.logger import get_logger
from src.knowledge.database import DatabaseManager

logger = get_logger(__name__)


def get_database_manager():
    """
    Factory function to get the database manager.
    
    Returns:
        A PostgreSQL-based DatabaseManager
    """
    logger.info("Creating PostgreSQL database manager")
    return DatabaseManager()