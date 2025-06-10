"""
Batch Operations Service for the Egypt Tourism Chatbot.

This service handles efficient bulk database operations including batch inserts,
updates, and deletes. Extracted from QueryBatch and DatabaseManager bulk methods
as part of Phase 2.5 refactoring.
"""
import logging
import os
import time
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass
from enum import Enum
from psycopg2.extras import execute_values

# Import existing QueryBatch
from src.utils.query_batch import QueryBatch

logger = logging.getLogger(__name__)

class BatchStatus(Enum):
    """Batch operation status enumeration."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class BatchType(Enum):
    """Batch operation type enumeration."""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    UPSERT = "upsert"
    CUSTOM = "custom"

@dataclass
class BatchMetrics:
    """Batch operation metrics."""
    batch_id: str
    batch_type: BatchType
    table_name: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    execution_time_ms: float
    throughput_ops_per_sec: float
    status: BatchStatus
    error_message: Optional[str] = None

class BatchOperationsService:
    """
    Service for managing bulk database operations.
    
    This service provides efficient batch processing capabilities
    for database operations with monitoring and optimization.
    
    Responsibilities:
    - Batch insert, update, delete operations
    - Optimal batch size determination
    - Transaction management for batches
    - Performance monitoring and metrics
    - Error handling and partial success management
    - Batch operation scheduling and queuing
    """
    
    # Optimal batch sizes for different operations
    DEFAULT_BATCH_SIZES = {
        BatchType.INSERT: 1000,
        BatchType.UPDATE: 500,
        BatchType.DELETE: 1000,
        BatchType.UPSERT: 500,
        BatchType.CUSTOM: 100
    }
    
    def __init__(self, db_manager=None, analytics_service=None):
        """
        Initialize the batch operations service.
        
        Args:
            db_manager: Database manager instance
            analytics_service: Analytics service for performance monitoring
        """
        self.db_manager = db_manager
        self.analytics_service = analytics_service
        
        # Feature flags from environment
        self.enabled = os.getenv('USE_NEW_BATCH_SERVICE', 'false').lower() == 'true'
        
        # Batch management
        self._active_batches = {}
        self._batch_metrics = {}
        self._batch_counter = 0
        
        # Performance tracking
        self._total_operations = 0
        self._total_execution_time = 0
        self._operation_history = []
        
        logger.info("Batch operations service initialized")
    
    def create_batch_executor(self, batch_size: int = 100, auto_execute: bool = False) -> QueryBatch:
        """
        Create a batch executor instance.
        
        Args:
            batch_size: Maximum number of operations in a batch
            auto_execute: Whether to automatically execute when batch is full
            
        Returns:
            QueryBatch: Batch executor instance
        """
        try:
            if not self.enabled and self.db_manager:
                # Fallback to legacy method
                return self.db_manager.create_batch_executor(batch_size, auto_execute)
            
            if not self.db_manager:
                logger.error("No database manager available")
                return None
            
            # Create enhanced batch executor
            batch_executor = QueryBatch(self.db_manager, batch_size, auto_execute)
            
            # Wrap with monitoring if analytics service is available
            if self.analytics_service:
                batch_executor = self._wrap_with_monitoring(batch_executor)
            
            return batch_executor
            
        except Exception as e:
            logger.error(f"Error creating batch executor: {str(e)}")
            return None
    
    def bulk_insert(self, table: str, records: List[Dict[str, Any]], 
                   batch_size: Optional[int] = None, on_conflict: str = "DO NOTHING") -> BatchMetrics:
        """
        Perform bulk insert operation.
        
        Args:
            table: Table name
            records: List of records to insert
            batch_size: Optional batch size, defaults to optimal size
            on_conflict: Conflict resolution strategy
            
        Returns:
            BatchMetrics: Batch operation metrics
        """
        batch_id = self._generate_batch_id()
        start_time = time.time()
        
        try:
            if not records:
                return BatchMetrics(
                    batch_id=batch_id,
                    batch_type=BatchType.INSERT,
                    table_name=table,
                    total_operations=0,
                    successful_operations=0,
                    failed_operations=0,
                    execution_time_ms=0,
                    throughput_ops_per_sec=0,
                    status=BatchStatus.COMPLETED
                )
            
            # Determine optimal batch size
            if batch_size is None:
                batch_size = self.optimize_batch_size(BatchType.INSERT.value, len(records))
            
            logger.info(f"Starting bulk insert: {len(records)} records into {table} (batch_size={batch_size})")
            
            successful_operations = 0
            failed_operations = 0
            
            # Process in batches
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                try:
                    result = self._execute_bulk_insert(table, batch, on_conflict)
                    if result:
                        successful_operations += len(batch)
                    else:
                        failed_operations += len(batch)
                        
                except Exception as e:
                    logger.error(f"Error in bulk insert batch {i//batch_size + 1}: {str(e)}")
                    failed_operations += len(batch)
            
            execution_time_ms = (time.time() - start_time) * 1000
            throughput = successful_operations / (execution_time_ms / 1000) if execution_time_ms > 0 else 0
            
            # Determine status
            if failed_operations == 0:
                status = BatchStatus.COMPLETED
            elif successful_operations == 0:
                status = BatchStatus.FAILED
            else:
                status = BatchStatus.PARTIAL
            
            metrics = BatchMetrics(
                batch_id=batch_id,
                batch_type=BatchType.INSERT,
                table_name=table,
                total_operations=len(records),
                successful_operations=successful_operations,
                failed_operations=failed_operations,
                execution_time_ms=execution_time_ms,
                throughput_ops_per_sec=throughput,
                status=status
            )
            
            # Store metrics and update analytics
            self._store_batch_metrics(metrics)
            self._update_performance_stats(metrics)
            
            logger.info(f"Bulk insert completed: {successful_operations}/{len(records)} successful")
            return metrics
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_metrics = BatchMetrics(
                batch_id=batch_id,
                batch_type=BatchType.INSERT,
                table_name=table,
                total_operations=len(records),
                successful_operations=0,
                failed_operations=len(records),
                execution_time_ms=execution_time_ms,
                throughput_ops_per_sec=0,
                status=BatchStatus.FAILED,
                error_message=str(e)
            )
            
            self._store_batch_metrics(error_metrics)
            logger.error(f"Bulk insert failed: {str(e)}")
            return error_metrics
    
    def bulk_update(self, table: str, updates: List[Dict[str, Any]], 
                   id_column: str = "id", batch_size: Optional[int] = None) -> BatchMetrics:
        """
        Perform bulk update operation.
        
        Args:
            table: Table name
            updates: List of update records (must include id_column)
            id_column: Column name for identifying records
            batch_size: Optional batch size, defaults to optimal size
            
        Returns:
            BatchMetrics: Batch operation metrics
        """
        batch_id = self._generate_batch_id()
        start_time = time.time()
        
        try:
            if not updates:
                return BatchMetrics(
                    batch_id=batch_id,
                    batch_type=BatchType.UPDATE,
                    table_name=table,
                    total_operations=0,
                    successful_operations=0,
                    failed_operations=0,
                    execution_time_ms=0,
                    throughput_ops_per_sec=0,
                    status=BatchStatus.COMPLETED
                )
            
            # Validate that all records have the id column
            for update in updates:
                if id_column not in update:
                    raise ValueError(f"Update record missing required column: {id_column}")
            
            # Determine optimal batch size
            if batch_size is None:
                batch_size = self.optimize_batch_size(BatchType.UPDATE.value, len(updates))
            
            logger.info(f"Starting bulk update: {len(updates)} records in {table} (batch_size={batch_size})")
            
            successful_operations = 0
            failed_operations = 0
            
            # Process in batches
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i + batch_size]
                
                try:
                    result = self._execute_bulk_update(table, batch, id_column)
                    if result:
                        successful_operations += len(batch)
                    else:
                        failed_operations += len(batch)
                        
                except Exception as e:
                    logger.error(f"Error in bulk update batch {i//batch_size + 1}: {str(e)}")
                    failed_operations += len(batch)
            
            execution_time_ms = (time.time() - start_time) * 1000
            throughput = successful_operations / (execution_time_ms / 1000) if execution_time_ms > 0 else 0
            
            # Determine status
            if failed_operations == 0:
                status = BatchStatus.COMPLETED
            elif successful_operations == 0:
                status = BatchStatus.FAILED
            else:
                status = BatchStatus.PARTIAL
            
            metrics = BatchMetrics(
                batch_id=batch_id,
                batch_type=BatchType.UPDATE,
                table_name=table,
                total_operations=len(updates),
                successful_operations=successful_operations,
                failed_operations=failed_operations,
                execution_time_ms=execution_time_ms,
                throughput_ops_per_sec=throughput,
                status=status
            )
            
            self._store_batch_metrics(metrics)
            self._update_performance_stats(metrics)
            
            logger.info(f"Bulk update completed: {successful_operations}/{len(updates)} successful")
            return metrics
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_metrics = BatchMetrics(
                batch_id=batch_id,
                batch_type=BatchType.UPDATE,
                table_name=table,
                total_operations=len(updates),
                successful_operations=0,
                failed_operations=len(updates),
                execution_time_ms=execution_time_ms,
                throughput_ops_per_sec=0,
                status=BatchStatus.FAILED,
                error_message=str(e)
            )
            
            self._store_batch_metrics(error_metrics)
            logger.error(f"Bulk update failed: {str(e)}")
            return error_metrics
    
    def bulk_delete(self, table: str, ids: List[Union[str, int]], 
                   id_column: str = "id", batch_size: Optional[int] = None) -> BatchMetrics:
        """
        Perform bulk delete operation.
        
        Args:
            table: Table name
            ids: List of IDs to delete
            id_column: Column name for identifying records
            batch_size: Optional batch size, defaults to optimal size
            
        Returns:
            BatchMetrics: Batch operation metrics
        """
        batch_id = self._generate_batch_id()
        start_time = time.time()
        
        try:
            if not ids:
                return BatchMetrics(
                    batch_id=batch_id,
                    batch_type=BatchType.DELETE,
                    table_name=table,
                    total_operations=0,
                    successful_operations=0,
                    failed_operations=0,
                    execution_time_ms=0,
                    throughput_ops_per_sec=0,
                    status=BatchStatus.COMPLETED
                )
            
            # Determine optimal batch size
            if batch_size is None:
                batch_size = self.optimize_batch_size(BatchType.DELETE.value, len(ids))
            
            logger.info(f"Starting bulk delete: {len(ids)} records from {table} (batch_size={batch_size})")
            
            successful_operations = 0
            failed_operations = 0
            
            # Process in batches
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                
                try:
                    result = self._execute_bulk_delete(table, batch_ids, id_column)
                    if result:
                        successful_operations += len(batch_ids)
                    else:
                        failed_operations += len(batch_ids)
                        
                except Exception as e:
                    logger.error(f"Error in bulk delete batch {i//batch_size + 1}: {str(e)}")
                    failed_operations += len(batch_ids)
            
            execution_time_ms = (time.time() - start_time) * 1000
            throughput = successful_operations / (execution_time_ms / 1000) if execution_time_ms > 0 else 0
            
            # Determine status
            if failed_operations == 0:
                status = BatchStatus.COMPLETED
            elif successful_operations == 0:
                status = BatchStatus.FAILED
            else:
                status = BatchStatus.PARTIAL
            
            metrics = BatchMetrics(
                batch_id=batch_id,
                batch_type=BatchType.DELETE,
                table_name=table,
                total_operations=len(ids),
                successful_operations=successful_operations,
                failed_operations=failed_operations,
                execution_time_ms=execution_time_ms,
                throughput_ops_per_sec=throughput,
                status=status
            )
            
            self._store_batch_metrics(metrics)
            self._update_performance_stats(metrics)
            
            logger.info(f"Bulk delete completed: {successful_operations}/{len(ids)} successful")
            return metrics
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_metrics = BatchMetrics(
                batch_id=batch_id,
                batch_type=BatchType.DELETE,
                table_name=table,
                total_operations=len(ids),
                successful_operations=0,
                failed_operations=len(ids),
                execution_time_ms=execution_time_ms,
                throughput_ops_per_sec=0,
                status=BatchStatus.FAILED,
                error_message=str(e)
            )
            
            self._store_batch_metrics(error_metrics)
            logger.error(f"Bulk delete failed: {str(e)}")
            return error_metrics
    
    def optimize_batch_size(self, operation_type: str, total_records: int) -> int:
        """
        Determine optimal batch size for an operation.
        
        Args:
            operation_type: Type of operation (insert, update, delete)
            total_records: Total number of records to process
            
        Returns:
            int: Optimal batch size
        """
        try:
            # Get default batch size for operation type
            batch_type = BatchType(operation_type.lower())
            default_size = self.DEFAULT_BATCH_SIZES.get(batch_type, 100)
            
            # Adjust based on total records
            if total_records < 100:
                return min(total_records, 50)
            elif total_records < 1000:
                return min(total_records, default_size // 2)
            elif total_records > 10000:
                return min(default_size * 2, 2000)  # Cap at 2000
            else:
                return default_size
            
        except Exception as e:
            logger.warning(f"Error optimizing batch size: {str(e)}")
            return 100  # Safe default
    
    def get_batch_metrics(self, batch_id: Optional[str] = None) -> Union[BatchMetrics, List[BatchMetrics]]:
        """
        Get batch operation metrics.
        
        Args:
            batch_id: Optional specific batch ID, returns all if None
            
        Returns:
            BatchMetrics or List[BatchMetrics]: Batch metrics
        """
        try:
            if batch_id:
                return self._batch_metrics.get(batch_id)
            else:
                return list(self._batch_metrics.values())
                
        except Exception as e:
            logger.error(f"Error getting batch metrics: {str(e)}")
            return [] if batch_id is None else None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get batch operations performance statistics.
        
        Returns:
            Dict[str, Any]: Performance statistics
        """
        try:
            total_batches = len(self._batch_metrics)
            if total_batches == 0:
                return {
                    'total_batches': 0,
                    'total_operations': 0,
                    'avg_throughput_ops_per_sec': 0,
                    'success_rate': 0,
                    'avg_execution_time_ms': 0
                }
            
            successful_batches = sum(1 for m in self._batch_metrics.values() 
                                   if m.status == BatchStatus.COMPLETED)
            total_successful_ops = sum(m.successful_operations for m in self._batch_metrics.values())
            total_failed_ops = sum(m.failed_operations for m in self._batch_metrics.values())
            total_ops = total_successful_ops + total_failed_ops
            
            avg_throughput = sum(m.throughput_ops_per_sec for m in self._batch_metrics.values()) / total_batches
            avg_execution_time = sum(m.execution_time_ms for m in self._batch_metrics.values()) / total_batches
            success_rate = total_successful_ops / total_ops if total_ops > 0 else 0
            
            return {
                'total_batches': total_batches,
                'successful_batches': successful_batches,
                'total_operations': total_ops,
                'successful_operations': total_successful_ops,
                'failed_operations': total_failed_ops,
                'success_rate': success_rate,
                'avg_throughput_ops_per_sec': avg_throughput,
                'avg_execution_time_ms': avg_execution_time,
                'batch_type_distribution': self._get_batch_type_distribution()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance stats: {str(e)}")
            return {}
    
    def _execute_bulk_insert(self, table: str, records: List[Dict[str, Any]], 
                           on_conflict: str = "DO NOTHING") -> bool:
        """Execute bulk insert operation."""
        try:
            if not records:
                return True
            
            conn = self.db_manager._get_pg_connection()
            if not conn:
                return False
            
            try:
                with conn:
                    with conn.cursor() as cursor:
                        # Get field names from first record
                        fields = list(records[0].keys())
                        fields_str = ', '.join(fields)
                        placeholders = ', '.join(['%s'] * len(fields))
                        
                        # Prepare data
                        values = []
                        for record in records:
                            row = [record.get(field) for field in fields]
                            values.append(row)
                        
                        # Execute bulk insert
                        execute_values(
                            cursor,
                            f"INSERT INTO {table} ({fields_str}) VALUES %s ON CONFLICT (id) {on_conflict}",
                            values,
                            template=f"({placeholders})",
                            page_size=len(records)
                        )
                
                return True
                
            finally:
                self.db_manager._return_pg_connection(conn)
                
        except Exception as e:
            logger.error(f"Error executing bulk insert: {str(e)}")
            return False
    
    def _execute_bulk_update(self, table: str, updates: List[Dict[str, Any]], 
                           id_column: str = "id") -> bool:
        """Execute bulk update operation."""
        try:
            if not updates:
                return True
            
            conn = self.db_manager._get_pg_connection()
            if not conn:
                return False
            
            try:
                with conn:
                    with conn.cursor() as cursor:
                        for update in updates:
                            # Build SET clause
                            set_clauses = []
                            values = []
                            
                            for key, value in update.items():
                                if key != id_column:  # Don't update the ID
                                    set_clauses.append(f"{key} = %s")
                                    values.append(value)
                            
                            if set_clauses:
                                # Add updated_at timestamp
                                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                                
                                # Add the ID value
                                values.append(update[id_column])
                                
                                sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {id_column} = %s"
                                cursor.execute(sql, values)
                
                return True
                
            finally:
                self.db_manager._return_pg_connection(conn)
                
        except Exception as e:
            logger.error(f"Error executing bulk update: {str(e)}")
            return False
    
    def _execute_bulk_delete(self, table: str, ids: List[Union[str, int]], 
                           id_column: str = "id") -> bool:
        """Execute bulk delete operation."""
        try:
            if not ids:
                return True
            
            conn = self.db_manager._get_pg_connection()
            if not conn:
                return False
            
            try:
                with conn:
                    with conn.cursor() as cursor:
                        # Create placeholders for the IN clause
                        placeholders = ', '.join(['%s'] * len(ids))
                        sql = f"DELETE FROM {table} WHERE {id_column} IN ({placeholders})"
                        cursor.execute(sql, ids)
                
                return True
                
            finally:
                self.db_manager._return_pg_connection(conn)
                
        except Exception as e:
            logger.error(f"Error executing bulk delete: {str(e)}")
            return False
    
    def _generate_batch_id(self) -> str:
        """Generate unique batch ID."""
        self._batch_counter += 1
        return f"batch_{int(time.time())}_{self._batch_counter}"
    
    def _store_batch_metrics(self, metrics: BatchMetrics) -> None:
        """Store batch metrics for tracking."""
        self._batch_metrics[metrics.batch_id] = metrics
        
        # Keep only last 1000 batches
        if len(self._batch_metrics) > 1000:
            oldest_batch = min(self._batch_metrics.keys())
            del self._batch_metrics[oldest_batch]
    
    def _update_performance_stats(self, metrics: BatchMetrics) -> None:
        """Update performance tracking statistics."""
        self._total_operations += metrics.total_operations
        self._total_execution_time += metrics.execution_time_ms
        
        # Record in analytics service if available
        if self.analytics_service:
            try:
                self.analytics_service.record_query_performance(
                    query=f"BATCH_{metrics.batch_type.value.upper()}",
                    params=(),
                    duration_ms=metrics.execution_time_ms,
                    rows_affected=metrics.successful_operations,
                    table_name=metrics.table_name,
                    query_type="batch"
                )
            except Exception as e:
                logger.warning(f"Error recording batch metrics in analytics: {str(e)}")
    
    def _get_batch_type_distribution(self) -> Dict[str, int]:
        """Get distribution of batch types."""
        distribution = {}
        for metrics in self._batch_metrics.values():
            batch_type = metrics.batch_type.value
            distribution[batch_type] = distribution.get(batch_type, 0) + 1
        return distribution
    
    def _wrap_with_monitoring(self, batch_executor: QueryBatch) -> QueryBatch:
        """Wrap batch executor with monitoring capabilities."""
        # This would enhance the QueryBatch with monitoring
        # For now, return as-is since it's already functional
        return batch_executor 