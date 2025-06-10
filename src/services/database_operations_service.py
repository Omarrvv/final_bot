"""
Consolidated Database Operations Service Module

This module provides unified database operations including:
- Batch processing and bulk operations
- Schema management and table operations
- Extension management (PostGIS, pgvector)
- Database optimization and monitoring
- Connection management

Consolidates functionality from:
- src/services/database/batch_processor.py
- src/services/database/schema_manager.py
- src/services/database/extension_manager.py
"""

import logging
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor

from src.services.base_service import BaseService

logger = logging.getLogger(__name__)

# Batch Processing Classes
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

# Extension Management Classes
class ExtensionStatus(Enum):
    """Extension status enumeration."""
    AVAILABLE = "available"
    MISSING = "missing"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class ExtensionInfo:
    """Information about a database extension."""
    name: str
    status: ExtensionStatus
    version: Optional[str] = None
    requires_superuser: bool = False
    error_message: Optional[str] = None

class DatabaseOperationsService(BaseService):
    """
    Unified database service combining all database operations.
    
    Responsibilities:
    - Batch processing operations
    - Schema management
    - Extension management
    - Database optimization
    """
    
    # Optimal batch sizes for different operations
    DEFAULT_BATCH_SIZES = {
        BatchType.INSERT: 1000,
        BatchType.UPDATE: 500,
        BatchType.DELETE: 1000,
        BatchType.UPSERT: 750
    }
    
    # Known extensions and their requirements
    KNOWN_EXTENSIONS = {
        'postgis': {
            'requires_superuser': True,
            'provides': ['spatial_queries', 'geography_types', 'geometric_functions'],
            'version_check': "SELECT PostGIS_Version();"
        },
        'pgvector': {
            'requires_superuser': True,
            'provides': ['vector_similarity', 'embedding_storage', 'vector_indexes'],
            'version_check': "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
        }
    }
    
    def __init__(self, db_manager=None, analytics_service=None):
        super().__init__(db_manager)
        self.analytics_service = analytics_service
        self._batch_metrics: Dict[str, BatchMetrics] = {}
        self._extension_cache: Dict[str, ExtensionInfo] = {}
        self._last_check_time = 0
        
        logger.info("DatabaseOperationsService initialized")

    # Batch Processing Methods
    def bulk_insert(self, table: str, records: List[Dict[str, Any]], 
                   batch_size: Optional[int] = None, on_conflict: str = "DO NOTHING") -> BatchMetrics:
        """Perform bulk insert operation."""
        batch_id = self._generate_batch_id()
        start_time = time.time()
        
        if not records:
            return BatchMetrics(
                batch_id=batch_id, batch_type=BatchType.INSERT, table_name=table,
                total_operations=0, successful_operations=0, failed_operations=0,
                execution_time_ms=0, throughput_ops_per_sec=0, status=BatchStatus.COMPLETED
            )
        
        if batch_size is None:
            batch_size = self.DEFAULT_BATCH_SIZES[BatchType.INSERT]
        
        total_operations = len(records)
        successful_operations = 0
        failed_operations = 0
        
        try:
            # Get column names from first record
            columns = list(records[0].keys())
            column_names = ', '.join(columns)
            
            query = f"""
                INSERT INTO {table} ({column_names})
                VALUES %s
                {on_conflict}
            """
            
            # Process in batches
            for i in range(0, total_operations, batch_size):
                batch_records = records[i:i + batch_size]
                values = [tuple(record[col] for col in columns) for record in batch_records]
                
                try:
                    conn = self.db_manager.get_connection()
                    try:
                        with conn.cursor() as cursor:
                            execute_values(cursor, query, values, template=None, page_size=batch_size)
                            conn.commit()
                            successful_operations += len(batch_records)
                    finally:
                        self.db_manager.return_connection(conn)
                except Exception as e:
                    failed_operations += len(batch_records)
                    logger.error(f"Batch insert failed for batch {i//batch_size + 1}: {e}")
            
            execution_time_ms = (time.time() - start_time) * 1000
            throughput = successful_operations / (execution_time_ms / 1000) if execution_time_ms > 0 else 0
            
            metrics = BatchMetrics(
                batch_id=batch_id, batch_type=BatchType.INSERT, table_name=table,
                total_operations=total_operations, successful_operations=successful_operations,
                failed_operations=failed_operations, execution_time_ms=execution_time_ms,
                throughput_ops_per_sec=throughput,
                status=BatchStatus.COMPLETED if failed_operations == 0 else BatchStatus.PARTIAL
            )
            
            self._store_batch_metrics(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            execution_time_ms = (time.time() - start_time) * 1000
            
            metrics = BatchMetrics(
                batch_id=batch_id, batch_type=BatchType.INSERT, table_name=table,
                total_operations=total_operations, successful_operations=successful_operations,
                failed_operations=total_operations - successful_operations,
                execution_time_ms=execution_time_ms, throughput_ops_per_sec=0,
                status=BatchStatus.FAILED, error_message=str(e)
            )
            
            self._store_batch_metrics(metrics)
            return metrics

    # Extension Management Methods
    def check_postgis_available(self) -> bool:
        """Check if PostGIS extension is available."""
        try:
            extension_info = self.get_extension_info('postgis')
            return extension_info.status == ExtensionStatus.AVAILABLE
        except Exception as e:
            logger.error(f"Error checking PostGIS availability: {e}")
            return False

    def check_pgvector_available(self) -> bool:
        """Check if pgvector extension is available."""
        try:
            extension_info = self.get_extension_info('pgvector')
            return extension_info.status == ExtensionStatus.AVAILABLE
        except Exception as e:
            logger.error(f"Error checking pgvector availability: {e}")
            return False

    def get_extension_info(self, extension_name: str) -> ExtensionInfo:
        """Get detailed information about an extension."""
        current_time = time.time()
        
        # Use cached result if recent (within 5 minutes)
        if (extension_name in self._extension_cache and 
            current_time - self._last_check_time < 300):
            return self._extension_cache[extension_name]
        
        try:
            # Check if extension is installed
            query = """
                SELECT extname, extversion, extrelocatable
                FROM pg_extension 
                WHERE extname = %s
            """
            
            result = self.db_manager.execute_postgres_query(query, (extension_name,), fetchall=False)
            
            if result:
                # Extension is installed
                extension_info = ExtensionInfo(
                    name=extension_name,
                    status=ExtensionStatus.AVAILABLE,
                    version=result.get('extversion'),
                    requires_superuser=self.KNOWN_EXTENSIONS.get(extension_name, {}).get('requires_superuser', False)
                )
            else:
                # Extension not installed
                extension_info = ExtensionInfo(
                    name=extension_name,
                    status=ExtensionStatus.MISSING,
                    requires_superuser=True,
                    error_message=f"Extension {extension_name} not installed"
                )
            
            self._extension_cache[extension_name] = extension_info
            self._last_check_time = current_time
            
            return extension_info
            
        except Exception as e:
            logger.error(f"Error getting extension info for {extension_name}: {e}")
            return ExtensionInfo(
                name=extension_name,
                status=ExtensionStatus.ERROR,
                error_message=str(e)
            )

    # Schema Management Methods
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        try:
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """
            result = self.db_manager.execute_postgres_query(query, (table_name,), fetchall=False)
            return result.get('exists', False) if result else False
        except Exception as e:
            logger.error(f"Error checking table existence for {table_name}: {e}")
            return False

    def column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table."""
        try:
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s 
                    AND column_name = %s
                )
            """
            result = self.db_manager.execute_postgres_query(
                query, (table_name, column_name), fetchall=False
            )
            return result.get('exists', False) if result else False
        except Exception as e:
            logger.error(f"Error checking column existence for {table_name}.{column_name}: {e}")
            return False

    def get_table_columns(self, table_name: str) -> List[str]:
        """Get list of columns for a table."""
        try:
            query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = %s 
                ORDER BY ordinal_position
            """
            results = self.db_manager.execute_postgres_query(query, (table_name,))
            return [row['column_name'] for row in results] if results else []
        except Exception as e:
            logger.error(f"Error getting columns for table {table_name}: {e}")
            return []

    # Utility Methods
    def _generate_batch_id(self) -> str:
        """Generate unique batch ID."""
        return f"batch_{uuid.uuid4().hex[:8]}"

    def _store_batch_metrics(self, metrics: BatchMetrics) -> None:
        """Store batch metrics for later retrieval."""
        self._batch_metrics[metrics.batch_id] = metrics

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all database services."""
        return {
            'database_connected': self.db_manager.is_connected() if self.db_manager else False,
            'postgis_available': self.check_postgis_available(),
            'pgvector_available': self.check_pgvector_available(),
            'batch_metrics_count': len(self._batch_metrics),
            'extensions_cached': len(self._extension_cache)
        }

    def get_batch_metrics(self, batch_id: Optional[str] = None) -> Union[BatchMetrics, List[BatchMetrics]]:
        """Get batch metrics."""
        if batch_id:
            return self._batch_metrics.get(batch_id)
        return list(self._batch_metrics.values()) 