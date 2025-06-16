"""
Database service module for knowledge layer.
This module provides database services for the knowledge layer.
"""

from typing import Optional, Dict, Any, List

class DatabaseService:
    """Database service for knowledge layer operations."""
    
    def __init__(self, database_uri: str = None):
        # Lazy import to avoid circular dependencies
        from src.knowledge.database import DatabaseManager
        self.db_manager = DatabaseManager(database_uri)
    
    def get_manager(self):
        """Get the underlying database manager."""
        return self.db_manager
    
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self.db_manager.is_connected()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a database query."""
        return self.db_manager.execute_query(query, params)

# For backward compatibility
def get_database_service(database_uri: str = None) -> DatabaseService:
    """Factory function to create database service."""
    return DatabaseService(database_uri) 