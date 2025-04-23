"""
Database Factory

This module provides a factory for creating database managers based on the
configured database type in the environment.
"""
import os
from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from src.utils.postgres_database import PostgresqlDatabaseManager

logger = get_logger(__name__)


def get_database_manager():
    """
    Factory function to get the appropriate database manager based on configuration.
    
    Returns:
        Either a SQLite DatabaseManager or a PostgreSQL PostgresqlDatabaseManager
        based on the USE_POSTGRES environment variable.
    """
    use_postgres = os.environ.get("USE_POSTGRES", "false").lower() == "true"
    
    if use_postgres:
        logger.info("Using PostgreSQL database manager")
        return PostgresqlDatabaseManager()
    else:
        logger.info("Using SQLite database manager")
        return DatabaseManager() 