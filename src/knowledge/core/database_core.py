"""
Database Core Module for the Egypt Tourism Chatbot.

This module provides a clean interface to the existing DatabaseManager,
serving as a bridge during the refactoring process. It exposes only the 
essential database operations needed by repositories while maintaining 
full compatibility with the existing god object.
"""

import json
from typing import Any, Dict, List, Optional, Tuple, Union
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseCore:
    """
    Core database interface that bridges to the existing DatabaseManager.
    
    This class provides a clean, focused interface for basic database operations
    while delegating to the existing DatabaseManager implementation. This allows
    repositories to work without depending on the full god object interface.
    """
    
    def __init__(self, database_manager):
        """
        Initialize the database core with an existing DatabaseManager.
        
        Args:
            database_manager: Existing DatabaseManager instance
        """
        self._db_manager = database_manager
        logger.debug("DatabaseCore initialized with existing DatabaseManager")
    
    def execute_query(self, query: str, params: tuple = (), fetchall: bool = True) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
        """
        Execute a database query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            fetchall: Whether to fetch all results or just one
            
        Returns:
            Query results as list of dicts (fetchall=True) or single dict (fetchall=False)
        """
        try:
            if fetchall:
                return self._db_manager.execute_postgres_query(query, params, fetchall=True)
            else:
                results = self._db_manager.execute_postgres_query(query, params, fetchall=False)
                return results[0] if results else None
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            logger.debug(f"Query: {query}, Params: {params}")
            raise
    
    def get_connection(self):
        """
        Get a database connection from the pool.
        
        Returns:
            Database connection
        """
        return self._db_manager._get_pg_connection()
    
    def return_connection(self, conn):
        """
        Return a database connection to the pool.
        
        Args:
            conn: Database connection to return
        """
        self._db_manager._return_pg_connection(conn)
    
    def parse_json_field(self, record: dict, field_name: str) -> dict:
        """
        Parse a JSON field in a database record.
        
        Args:
            record: Database record dictionary
            field_name: Name of the JSON field to parse
            
        Returns:
            Updated record with parsed JSON field
        """
        return self._db_manager._parse_json_field(record, field_name)
    
    def generic_get(self, table: str, record_id: int, jsonb_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get a record by ID from any table.
        
        Args:
            table: Table name
            record_id: Record ID
            jsonb_fields: List of JSONB fields to parse
            
        Returns:
            Record data or None if not found
        """
        return self._db_manager.generic_get(table, record_id, jsonb_fields)
    
    def generic_search(self, table: str, filters: Dict[str, Any] = None,
                      limit: int = 10, offset: int = 0,
                      jsonb_fields: List[str] = None,
                      language: str = "en") -> List[Dict[str, Any]]:
        """
        Search records in any table with filters.
        
        Args:
            table: Table name
            filters: Dictionary of field-value pairs to filter by
            limit: Maximum number of results
            offset: Offset for pagination
            jsonb_fields: List of JSONB fields to parse
            language: Language code for multilingual fields
            
        Returns:
            List of matching records
        """
        return self._db_manager.generic_search(
            table, filters, limit, offset, jsonb_fields, language
        )
    
    def generic_create(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new record in any table.
        
        Args:
            table: Table name
            data: Dictionary of field-value pairs
            
        Returns:
            ID of created record or None if creation failed
        """
        return self._db_manager.generic_create(table, data)
    
    def generic_update(self, table: str, record_id: int, data: Dict[str, Any]) -> bool:
        """
        Update an existing record in any table.
        
        Args:
            table: Table name
            record_id: ID of record to update
            data: Dictionary of field-value pairs to update
            
        Returns:
            True if update was successful, False otherwise
        """
        return self._db_manager.generic_update(table, record_id, data)
    
    def generic_delete(self, table: str, record_id: int) -> bool:
        """
        Delete a record from any table.
        
        Args:
            table: Table name
            record_id: ID of record to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        return self._db_manager.generic_delete(table, record_id)
    
    def vector_search(self, table_name: str, embedding: list, 
                     filters: Optional[dict] = None, 
                     limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search on a table.
        
        Args:
            table_name: Name of the table to search
            embedding: Vector embedding for similarity search
            filters: Additional filters to apply
            limit: Maximum number of results
            
        Returns:
            List of similar records ordered by similarity
        """
        return self._db_manager.vector_search(table_name, embedding, filters, limit)
    
    def find_nearby(self, table: str, latitude: float, longitude: float,
                   radius_km: float, limit: int = 10,
                   additional_filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Find records near a geographic location.
        
        Args:
            table: Table name
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_km: Search radius in kilometers
            limit: Maximum number of results
            additional_filters: Additional filters to apply
            
        Returns:
            List of nearby records ordered by distance
        """
        return self._db_manager.find_nearby(
            table, latitude, longitude, radius_km, limit, additional_filters
        )
    
    def transaction(self):
        """
        Get a transaction context manager.
        
        Returns:
            Transaction context manager
        """
        return self._db_manager.transaction()
    
    def is_connected(self) -> bool:
        """
        Check if database connection is established.
        
        Returns:
            True if connected, False otherwise
        """
        return self._db_manager.is_connected()
    
    @property
    def db_manager(self):
        """
        Access to the underlying DatabaseManager for advanced operations.
        
        Returns:
            DatabaseManager instance
        """
        return self._db_manager 