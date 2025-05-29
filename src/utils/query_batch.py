"""
Query Batch Executor for the Egypt Tourism Chatbot.

This module provides tools for batching and executing database operations efficiently.
"""
import time
import logging
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

class QueryBatch:
    """
    Query batch executor for efficient bulk database operations.
    
    This class provides tools for batching and executing database operations efficiently,
    reducing the number of round trips to the database.
    """
    
    def __init__(self, db_manager, batch_size: int = 100, auto_execute: bool = False):
        """
        Initialize the query batch executor.
        
        Args:
            db_manager: Database manager instance
            batch_size: Maximum number of operations in a batch
            auto_execute: Whether to automatically execute batches when they reach batch_size
        """
        self.db_manager = db_manager
        self.batch_size = batch_size
        self.auto_execute = auto_execute
        self.inserts = {}
        self.updates = {}
        self.deletes = {}
        self.custom_batches = {}
    
    def add_insert(self, table: str, data: Dict[str, Any]) -> None:
        """
        Add an insert operation to the batch.
        
        Args:
            table: Table name
            data: Dictionary of field-value pairs
        """
        if table not in self.inserts:
            self.inserts[table] = []
        
        self.inserts[table].append(data)
        
        if self.auto_execute and len(self.inserts[table]) >= self.batch_size:
            self.execute_inserts(table)
    
    def add_update(self, table: str, record_id: str, data: Dict[str, Any]) -> None:
        """
        Add an update operation to the batch.
        
        Args:
            table: Table name
            record_id: ID of the record to update
            data: Dictionary of field-value pairs to update
        """
        if table not in self.updates:
            self.updates[table] = []
        
        self.updates[table].append((record_id, data))
        
        if self.auto_execute and len(self.updates[table]) >= self.batch_size:
            self.execute_updates(table)
    
    def add_delete(self, table: str, record_id: str) -> None:
        """
        Add a delete operation to the batch.
        
        Args:
            table: Table name
            record_id: ID of the record to delete
        """
        if table not in self.deletes:
            self.deletes[table] = []
        
        self.deletes[table].append(record_id)
        
        if self.auto_execute and len(self.deletes[table]) >= self.batch_size:
            self.execute_deletes(table)
    
    def add_custom(self, batch_name: str, item: Any) -> None:
        """
        Add a custom item to a named batch.
        
        Args:
            batch_name: Name of the batch
            item: Item to add to the batch
        """
        if batch_name not in self.custom_batches:
            self.custom_batches[batch_name] = []
        
        self.custom_batches[batch_name].append(item)
        
        if self.auto_execute and len(self.custom_batches[batch_name]) >= self.batch_size:
            self.execute_custom(batch_name)
    
    def execute_inserts(self, table: str) -> bool:
        """
        Execute all pending insert operations for a table.
        
        Args:
            table: Table name
            
        Returns:
            bool: Success status
        """
        if table not in self.inserts or not self.inserts[table]:
            return True
        
        try:
            # Get a connection
            conn = self.db_manager._get_pg_connection()
            if not conn:
                logger.error("Failed to get database connection")
                return False
            
            try:
                with conn:  # Use transaction
                    with conn.cursor() as cursor:
                        # Get the first item to determine the fields
                        first_item = self.inserts[table][0]
                        fields = list(first_item.keys())
                        
                        # Prepare data for batch insert
                        values = []
                        for item in self.inserts[table]:
                            row = [item.get(field) for field in fields]
                            values.append(row)
                        
                        # Build the query
                        fields_str = ', '.join(fields)
                        placeholders = ', '.join(['%s'] * len(fields))
                        
                        # Use execute_values for efficient batch insert
                        execute_values(
                            cursor,
                            f"INSERT INTO {table} ({fields_str}) VALUES %s ON CONFLICT (id) DO NOTHING",
                            values,
                            template=f"({placeholders})",
                            page_size=self.batch_size
                        )
                
                # Clear the batch
                count = len(self.inserts[table])
                self.inserts[table] = []
                
                logger.info(f"Batch inserted {count} records into {table}")
                return True
            
            finally:
                # Return the connection to the pool
                self.db_manager._return_pg_connection(conn)
        
        except Exception as e:
            logger.error(f"Error executing batch inserts for {table}: {str(e)}")
            return False
    
    def execute_updates(self, table: str) -> bool:
        """
        Execute all pending update operations for a table.
        
        Args:
            table: Table name
            
        Returns:
            bool: Success status
        """
        if table not in self.updates or not self.updates[table]:
            return True
        
        try:
            # Get a connection
            conn = self.db_manager._get_pg_connection()
            if not conn:
                logger.error("Failed to get database connection")
                return False
            
            try:
                with conn:  # Use transaction
                    with conn.cursor() as cursor:
                        # Process each update
                        for record_id, data in self.updates[table]:
                            # Build SET clause
                            set_clauses = []
                            values = []
                            
                            for key, value in data.items():
                                set_clauses.append(f"{key} = %s")
                                values.append(value)
                            
                            # Add updated_at timestamp
                            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                            
                            # Add the ID to the values
                            values.append(record_id)
                            
                            # Build and execute update query
                            sql = f"""
                                UPDATE {table}
                                SET {', '.join(set_clauses)}
                                WHERE id = %s
                            """
                            
                            cursor.execute(sql, tuple(values))
                
                # Clear the batch
                count = len(self.updates[table])
                self.updates[table] = []
                
                logger.info(f"Batch updated {count} records in {table}")
                return True
            
            finally:
                # Return the connection to the pool
                self.db_manager._return_pg_connection(conn)
        
        except Exception as e:
            logger.error(f"Error executing batch updates for {table}: {str(e)}")
            return False
    
    def execute_deletes(self, table: str) -> bool:
        """
        Execute all pending delete operations for a table.
        
        Args:
            table: Table name
            
        Returns:
            bool: Success status
        """
        if table not in self.deletes or not self.deletes[table]:
            return True
        
        try:
            # Get a connection
            conn = self.db_manager._get_pg_connection()
            if not conn:
                logger.error("Failed to get database connection")
                return False
            
            try:
                with conn:  # Use transaction
                    with conn.cursor() as cursor:
                        # Build the query with multiple IDs
                        placeholders = ', '.join(['%s'] * len(self.deletes[table]))
                        sql = f"DELETE FROM {table} WHERE id IN ({placeholders})"
                        
                        # Execute the query
                        cursor.execute(sql, tuple(self.deletes[table]))
                
                # Clear the batch
                count = len(self.deletes[table])
                self.deletes[table] = []
                
                logger.info(f"Batch deleted {count} records from {table}")
                return True
            
            finally:
                # Return the connection to the pool
                self.db_manager._return_pg_connection(conn)
        
        except Exception as e:
            logger.error(f"Error executing batch deletes for {table}: {str(e)}")
            return False
    
    def execute_custom(self, batch_name: str, processor: Optional[Callable[[List[Any]], bool]] = None) -> bool:
        """
        Execute a custom batch with an optional processor function.
        
        Args:
            batch_name: Name of the batch
            processor: Function to process the batch items
            
        Returns:
            bool: Success status
        """
        if batch_name not in self.custom_batches or not self.custom_batches[batch_name]:
            return True
        
        try:
            if processor:
                # Use the provided processor function
                result = processor(self.custom_batches[batch_name])
            else:
                # No processor provided, just clear the batch
                result = True
            
            # Clear the batch
            count = len(self.custom_batches[batch_name])
            self.custom_batches[batch_name] = []
            
            logger.info(f"Processed {count} items in custom batch '{batch_name}'")
            return result
        
        except Exception as e:
            logger.error(f"Error executing custom batch '{batch_name}': {str(e)}")
            return False
    
    def execute_all(self) -> bool:
        """
        Execute all pending operations.
        
        Returns:
            bool: Success status
        """
        success = True
        
        # Execute all inserts
        for table in list(self.inserts.keys()):
            if not self.execute_inserts(table):
                success = False
        
        # Execute all updates
        for table in list(self.updates.keys()):
            if not self.execute_updates(table):
                success = False
        
        # Execute all deletes
        for table in list(self.deletes.keys()):
            if not self.execute_deletes(table):
                success = False
        
        # Execute all custom batches
        for batch_name in list(self.custom_batches.keys()):
            if not self.execute_custom(batch_name):
                success = False
        
        return success
    
    def clear(self) -> None:
        """Clear all pending operations."""
        self.inserts = {}
        self.updates = {}
        self.deletes = {}
        self.custom_batches = {}
    
    def __enter__(self):
        """Support context manager pattern."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Execute all pending operations when exiting context."""
        if exc_type is None:
            # No exception occurred, execute all operations
            self.execute_all()
        else:
            # Exception occurred, clear all operations
            self.clear()
