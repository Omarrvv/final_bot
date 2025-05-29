"""
Base service class for database operations.

This module provides a base service class that can be extended by specific service classes
to handle database operations for different entity types.
"""
import json
from typing import Any, Dict, List, Optional, Tuple, Union

from src.utils.logger import get_logger

logger = get_logger(__name__)

class BaseService:
    """
    Base service class for database operations.

    This class provides common database operations that can be used by specific service classes.
    It handles error handling, JSON parsing, and other common operations.
    """

    def __init__(self, db_manager):
        """
        Initialize the base service.

        Args:
            db_manager: Database manager instance with connection pool
        """
        self.db = db_manager

    def generic_get(self, table: str, record_id: int, jsonb_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Generic method to get a record by ID.

        Args:
            table: Table name
            record_id: ID of the record to retrieve
            jsonb_fields: List of JSONB fields to parse

        Returns:
            dict: Record data or None if not found
        """
        logger.info(f"Called generic_get for table={table}, id={record_id}")

        # Call the database manager's generic_get method
        return self.db.generic_get(table, record_id, jsonb_fields)

    def generic_search(self, table: str, filters: Dict[str, Any] = None,
                      limit: int = 10, offset: int = 0,
                      jsonb_fields: List[str] = None,
                      language: str = "en") -> List[Dict[str, Any]]:
        """
        Generic method to search records.

        Args:
            table: Table name
            filters: Dictionary of field-value pairs to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination
            jsonb_fields: List of JSONB fields to parse
            language: Language code (en, ar)

        Returns:
            list: List of records matching the criteria
        """
        logger.info(f"Called generic_search for table={table}, filters={filters}")

        # Call the database manager's generic_search method
        return self.db.generic_search(table, filters, limit, offset, jsonb_fields, language)

    def generic_create(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """
        Generic method to create a record.

        Args:
            table: Table name
            data: Dictionary of field-value pairs

        Returns:
            int: ID of the created record or None if creation failed
        """
        logger.info(f"Called generic_create for table={table}")

        # Call the database manager's generic_create method
        return self.db.generic_create(table, data)

    def generic_update(self, table: str, record_id: int, data: Dict[str, Any]) -> bool:
        """
        Generic method to update a record.

        Args:
            table: Table name
            record_id: ID of the record to update
            data: Dictionary of field-value pairs to update

        Returns:
            bool: True if update was successful, False otherwise
        """
        logger.info(f"Called generic_update for table={table}, id={record_id}")

        # Call the database manager's generic_update method
        return self.db.generic_update(table, record_id, data)

    def generic_delete(self, table: str, record_id: int) -> bool:
        """
        Generic method to delete a record.

        Args:
            table: Table name
            record_id: ID of the record to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        logger.info(f"Called generic_delete for table={table}, id={record_id}")

        # Call the database manager's generic_delete method
        return self.db.generic_delete(table, record_id)

    def _validate_table(self, table: str) -> bool:
        """
        Validate that the table name is in the whitelist.

        Args:
            table: Table name to validate

        Returns:
            bool: True if table is valid, False otherwise
        """
        if not hasattr(self.db, 'VALID_TABLES') or table not in self.db.VALID_TABLES:
            logger.error(f"Invalid table name: {table}")
            return False
        return True

    def _parse_json_field(self, record: dict, field_name: str) -> dict:
        """
        Parse a JSON field in a record safely.

        Args:
            record: The record containing the field
            field_name: The name of the field to parse

        Returns:
            The updated record with the parsed field
        """
        if field_name in record and record[field_name]:
            if isinstance(record[field_name], str):
                try:
                    record[field_name] = json.loads(record[field_name])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON data for {field_name}")
        return record

    def _handle_error(self, operation: str, error: Exception, return_empty_list: bool = False):
        """
        Standardized error handling for database operations.

        Args:
            operation: Description of the operation that failed
            error: The exception that was raised
            return_empty_list: Whether to return an empty list (True) or None (False)

        Returns:
            [] if return_empty_list is True, None otherwise
        """
        logger.error(f"Error in {operation}: {str(error)}")
        if hasattr(error, "__traceback__"):
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
        return [] if return_empty_list else None
