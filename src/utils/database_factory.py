"""
Database Factory

This module provides a factory for creating database managers.
"""
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_database_manager():
    """
    Factory function to get the shared database manager (PERFORMANCE OPTIMIZED).
    
    Returns:
        The shared DatabaseManager instance (no new connection pools)
    """
    logger.info("🔄 Returning shared DatabaseManager instance (connection pool reuse)")
    
    # Use the shared database manager from component factory
    from src.utils.factory import component_factory
    return component_factory.create_database_manager()  # Uses singleton pattern