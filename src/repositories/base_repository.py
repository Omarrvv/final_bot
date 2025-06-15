"""
Base Repository Module for the Egypt Tourism Chatbot.

This module provides a base repository class that can be extended by specific repository classes
to handle database operations for different entity types.
"""
import json
from typing import Any, Dict, List, Optional, Tuple, Union

from src.knowledge.core.database_core import DatabaseCore
from src.utils.logger import get_logger

logger = get_logger(__name__)

class BaseRepository:
    """
    Base repository class for database operations.

    This class provides common database operations that can be used by specific repository classes.
    It handles error handling, JSON parsing, and other common operations.
    """

    def __init__(self, db_core: DatabaseCore, table_name: str, jsonb_fields: List[str] = None):
        """
        Initialize the base repository.

        Args:
            db_core: Database core instance with connection pool
            table_name: Name of the table this repository manages
            jsonb_fields: List of JSONB fields in the table
        """
        self.db = db_core
        self.table_name = table_name
        self.jsonb_fields = jsonb_fields or []

    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a record by ID.

        Args:
            record_id: ID of the record to retrieve

        Returns:
            dict: Record data or None if not found
        """
        logger.info(f"Getting {self.table_name} with ID: {record_id}")
        try:
            sql = f"SELECT * FROM {self.table_name} WHERE id = %s"
            result = self.db.execute_query(sql, (record_id,), fetchall=False)

            if result:
                # Parse JSON fields
                for field in self.jsonb_fields:
                    self._parse_json_field(result, field)
                return result
            return None
        except Exception as e:
            return self._handle_error(f"get_{self.table_name}_{record_id}", e)

    def find(self, filters: Dict[str, Any] = None, limit: int = 10,
            offset: int = 0, order_by: str = None) -> List[Dict[str, Any]]:
        """
        Find records matching the given filters.

        Args:
            filters: Dictionary of field-value pairs to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination
            order_by: Field to order by

        Returns:
            list: List of records matching the criteria
        """
        logger.info(f"Finding {self.table_name} with filters: {filters}")
        try:
            # Build the base query
            query = f"SELECT * FROM {self.table_name} WHERE 1=1"
            params = []

            # Apply filters
            if filters:
                for key, value in filters.items():
                    # SECURITY FIX: Validate column names to prevent SQL injection
                    if not key.replace('_', '').replace('-', '').replace('>', '').replace("'", '').isalnum():
                        logger.warning(f"Potentially unsafe column name in filter: {key}")
                        continue
                    query += f" AND {key} = %s"
                    params.append(value)

            # Add ordering
            if order_by:
                # SECURITY FIX: Validate order_by column name
                if not order_by.replace('_', '').replace('-', '').replace('>', '').replace("'", '').isalnum():
                    logger.warning(f"Potentially unsafe order_by column: {order_by}")
                    order_by = "id"  # Default to safe column
                query += f" ORDER BY {order_by}"

            # Add limit and offset
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Execute the query
            results = self.db.execute_query(query, tuple(params))

            # Parse JSON fields
            if results:
                for result in results:
                    for field in self.jsonb_fields:
                        self._parse_json_field(result, field)

            return results or []
        except Exception as e:
            return self._handle_error(f"find_{self.table_name}", e, return_empty_list=True)

    def create(self, data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new record.

        Args:
            data: Dictionary of field-value pairs

        Returns:
            int: ID of the created record or None if creation failed
        """
        logger.info(f"Creating new {self.table_name}")
        try:
            # Process JSONB fields
            processed_data = data.copy()
            for field in self.jsonb_fields:
                if field in processed_data and not isinstance(processed_data[field], str):
                    processed_data[field] = json.dumps(processed_data[field])

            # Extract fields and values with security validation
            safe_fields = []
            values = []
            
            for field in processed_data.keys():
                # SECURITY FIX: Validate field names to prevent SQL injection
                if not field.replace('_', '').replace('-', '').replace('>', '').replace("'", '').isalnum():
                    logger.warning(f"Potentially unsafe field name in create: {field}")
                    continue
                safe_fields.append(field)
                values.append(processed_data[field])
            
            if not safe_fields:
                logger.error("No safe fields found for insertion")
                return None

            # Build the query
            placeholders = ["%s"] * len(safe_fields)
            fields_str = ", ".join(safe_fields)
            placeholders_str = ", ".join(placeholders)
            sql = f"INSERT INTO {self.table_name} ({fields_str}) VALUES ({placeholders_str}) RETURNING id"

            # Execute the query
            result = self.db.execute_query(sql, tuple(values), fetchall=False)

            if result and "id" in result:
                return result["id"]
            return None
        except Exception as e:
            return self._handle_error(f"create_{self.table_name}", e)

    def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """
        Update an existing record.

        Args:
            record_id: ID of the record to update
            data: Dictionary of field-value pairs to update

        Returns:
            bool: True if update was successful, False otherwise
        """
        logger.info(f"Updating {self.table_name} with ID: {record_id}")
        try:
            # Handle empty updates
            if not data:
                return True

            # Process JSONB fields
            processed_data = data.copy()
            for field in self.jsonb_fields:
                if field in processed_data and not isinstance(processed_data[field], str):
                    processed_data[field] = json.dumps(processed_data[field])

            # Build SET clause with security validation
            set_clauses = []
            values = []

            for key, value in processed_data.items():
                # SECURITY FIX: Validate field names to prevent SQL injection
                if not key.replace('_', '').replace('-', '').replace('>', '').replace("'", '').isalnum():
                    logger.warning(f"Potentially unsafe field name in update: {key}")
                    continue
                set_clauses.append(f"{key} = %s")
                values.append(value)

            # Add updated_at timestamp
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")

            # Build and execute update query
            sql = f"""
                UPDATE {self.table_name}
                SET {', '.join(set_clauses)}
                WHERE id = %s
                RETURNING id
            """
            values.append(record_id)

            result = self.db.execute_query(sql, tuple(values), fetchall=False)

            return result is not None
        except Exception as e:
            logger.error(f"Error updating {self.table_name} {record_id}: {str(e)}")
            return False

    def delete(self, record_id: int) -> bool:
        """
        Delete a record.

        Args:
            record_id: ID of the record to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        logger.info(f"Deleting {self.table_name} with ID: {record_id}")
        try:
            sql = f"DELETE FROM {self.table_name} WHERE id = %s RETURNING id"
            result = self.db.execute_query(sql, (record_id,), fetchall=False)
            return result is not None
        except Exception as e:
            logger.error(f"Error deleting {self.table_name} {record_id}: {str(e)}")
            return False

    def search(self, query: str, language: str = "en", limit: int = 10,
              offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search records based on a text query.

        Args:
            query: Text query to search for
            language: Language code (en, ar)
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of records matching the search criteria
        """
        logger.info(f"Searching {self.table_name} for: {query}")
        try:
            # Validate language parameter
            if language not in ["en", "ar"]:
                logger.warning(f"Invalid language '{language}', defaulting to 'en'")
                language = "en"

            # Build the search query based on JSONB fields
            search_conditions = []
            params = []

            query_pattern = f"%{query}%"

            # Add search conditions for JSONB fields
            for field in self.jsonb_fields:
                search_conditions.append(f"{field}->>'en' ILIKE %s")
                search_conditions.append(f"{field}->>'ar' ILIKE %s")
                params.extend([query_pattern, query_pattern])

            # If no JSONB fields, search by ID as fallback
            if not search_conditions:
                search_conditions.append("id::text ILIKE %s")
                params.append(query_pattern)

            # Build the final query
            sql = f"""
                SELECT * FROM {self.table_name}
                WHERE {' OR '.join(search_conditions)}
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])

            # Execute the query
            results = self.db.execute_query(sql, tuple(params))

            # Parse JSON fields
            if results:
                for result in results:
                    for field in self.jsonb_fields:
                        self._parse_json_field(result, field)

            return results or []
        except Exception as e:
            return self._handle_error(f"search_{self.table_name}", e, return_empty_list=True)

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
