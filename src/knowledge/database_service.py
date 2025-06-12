"""
Database Manager Facade for Phase 3 Transformation.

This facade maintains the exact same API as the original DatabaseManager
while delegating operations to the new Phase 2.5 services. This allows
for gradual migration with zero breaking changes.
"""
import os
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

# Import Phase 2C consolidated services
from src.services.database_operations_service import DatabaseOperationsService
from src.services.analytics_service import MonitoringService  
from src.services.ai_service import EmbeddingService
from src.services.search_service import UnifiedSearchService

# Import legacy components that will remain
# Legacy imports no longer needed - using clean facade architecture
# from src.knowledge.database_god_object_ARCHIVED import DatabaseManager, DatabaseType
from src.knowledge.core.connection_manager import ConnectionManager
from src.repositories.repository_factory import RepositoryFactory

logger = logging.getLogger(__name__)

class DatabaseManagerService:
    """
    Facade for DatabaseManager that delegates to Phase 2.5 services.
    
    This facade provides the exact same API as the original DatabaseManager
    but routes operations to the new service architecture. Feature flags
    control whether to use new services or fallback to legacy methods.
    
    Key Features:
    - Zero breaking changes to existing API
    - Gradual migration with feature flags
    - Performance monitoring and comparison
    - Automatic fallback to legacy implementation
    - Service health monitoring
    """
    
    def __init__(self, database_uri: str = None, vector_dimension: int = 768):
        """
        Initialize the facade with both new services and legacy fallback.
        
        Args:
            database_uri: Database connection URI
            vector_dimension: Vector embedding dimension
        """
        self.database_uri = database_uri
        self.vector_dimension = vector_dimension
        
        # Feature flags from environment
        self.use_facade = os.getenv('USE_DATABASE_FACADE', 'false').lower() == 'true'
        self.enable_logging = os.getenv('ENABLE_FACADE_LOGGING', 'true').lower() == 'true'
        self.enable_fallback = os.getenv('ENABLE_LEGACY_FALLBACK', 'true').lower() == 'true'
        
        # Performance tracking
        self._facade_metrics = {
            'new_service_calls': 0,
            'legacy_fallbacks': 0,
            'total_operations': 0,
            'avg_response_time_ms': 0.0,
            'error_count': 0
        }
        
        # Initialize connection manager directly (no legacy dependency)
        self._connection_manager = ConnectionManager(database_uri)
        self._connection_manager.initialize_connection_pool()
        
        # Create adapter for service compatibility
        self._db_adapter = self._create_db_adapter()
        
        # Initialize repository factory first
        from src.knowledge.core.database_core import DatabaseCore
        db_core = DatabaseCore(self._db_adapter)
        self._repository_factory = RepositoryFactory(db_core)
        
        # Initialize Phase 2.5 services
        self._initialize_services()
        
        # Legacy DB reference removed - using direct service architecture
        
        logger.info(f"DatabaseManagerService initialized (service_enabled={self.use_facade})")
    
    def _create_db_adapter(self):
        """Create an adapter that makes ConnectionManager compatible with service interface."""
        class DatabaseAdapter:
            def __init__(self, connection_manager):
                self.connection_manager = connection_manager
            
            def execute_postgres_query(self, query, params=None, fetchall=True, cursor_factory=None):
                return self.connection_manager.execute_query(query, params, fetchall, cursor_factory)
            
            def _get_pg_connection(self):
                return self.connection_manager.get_connection()
            
            def _return_pg_connection(self, conn):
                return self.connection_manager.return_connection(conn)
            
            def is_connected(self):
                return self.connection_manager.is_connected()
        
        return DatabaseAdapter(self._connection_manager)
    
    def _initialize_services(self) -> None:
        """Initialize all Phase 2.5 services."""
        try:
            # Database Operations Service (combines batch, schema, extension management)
            self._database_service = DatabaseOperationsService(
                db_manager=self._db_adapter,
                analytics_service=None  # Will be set after analytics service is created
            )
            
            # Analytics Monitoring Service
            self._analytics_service = MonitoringService(
                db_manager=self._db_adapter
            )
            
            # Update database service with analytics service
            self._database_service._analytics_service = self._analytics_service
            
            # AI/Embedding Service
            self._embedding_service = EmbeddingService(
                db_manager=self._db_adapter,
                default_dimension=self.vector_dimension
            )
            
            # Unified Search Service
            self._search_service = UnifiedSearchService(
                db_manager=self._db_adapter
            )
            
            self._services_initialized = True
            logger.info("Phase 2.5 services initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Phase 2.5 services: {str(e)}")
            self._services_initialized = False
    
    def _should_use_service(self, service_flag: str) -> bool:
        """Check if a specific service should be used based on feature flags."""
        if not self.use_facade or not self._services_initialized:
            return False
        return os.getenv(service_flag, 'false').lower() == 'true'
    
    def _track_operation(self, operation_name: str, use_new_service: bool, 
                        duration_ms: float, success: bool = True) -> None:
        """Track performance metrics for facade operations."""
        if not self.enable_logging:
            return
            
        self._facade_metrics['total_operations'] += 1
        
        if use_new_service:
            self._facade_metrics['new_service_calls'] += 1
        else:
            self._facade_metrics['legacy_fallbacks'] += 1
        
        if not success:
            self._facade_metrics['error_count'] += 1
        
        # Update average response time
        current_avg = self._facade_metrics['avg_response_time_ms']
        total_ops = self._facade_metrics['total_operations']
        self._facade_metrics['avg_response_time_ms'] = (
            (current_avg * (total_ops - 1) + duration_ms) / total_ops
        )
        
        if self.enable_logging:
            service_type = "NEW_SERVICE" if use_new_service else "LEGACY"
            logger.debug(f"FACADE: {operation_name} [{service_type}] {duration_ms:.2f}ms success={success}")
    
    # ============================================================================
    # CONNECTION AND CONTEXT MANAGER METHODS
    # ============================================================================
    
    def __enter__(self):
        """Support context manager pattern."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connections when exiting context manager."""
        self.close()
    
    def close(self):
        """Close the database connection."""
        if hasattr(self, '_connection_manager'):
            self._connection_manager.close()
    
    def connect(self):
        """Establish database connection."""
        return self._connection_manager.initialize_connection_pool()
    
    def is_connected(self) -> bool:
        """Check if database connection is established."""
        return self._connection_manager.is_connected()
    
    # ============================================================================
    # EXTENSION MANAGEMENT (delegates to ExtensionManagementService)
    # ============================================================================
    
    def _check_postgis_enabled(self) -> bool:
        """Check if PostGIS extension is enabled."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_EXTENSION_MANAGER')
        
        try:
            if use_service:
                result = self._database_service.check_postgis_available()
            else:
                # Use direct query through adapter
                query = "SELECT 1 FROM pg_extension WHERE extname = 'postgis'"
                result_rows = self._db_adapter.execute_postgres_query(query)
                result = bool(result_rows and len(result_rows) > 0)
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('_check_postgis_enabled', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('_check_postgis_enabled', use_service, duration_ms, False)
            logger.error(f"Error checking PostGIS: {str(e)}")
            return False
    
    def _check_vector_enabled(self) -> bool:
        """Check if pgvector extension is enabled."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_EXTENSION_MANAGER')
        
        try:
            if use_service:
                result = self._database_service.check_pgvector_available()
            # Always use service architecture only
            result = self._database_service.check_pgvector_available()
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('_check_vector_enabled', True, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('_check_vector_enabled', True, duration_ms, False)
            logger.error(f"Extension service failed: {str(e)}")
            raise
    
    # ============================================================================
    # SCHEMA MANAGEMENT (delegates to SchemaManagementService)
    # ============================================================================
    
    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_SCHEMA_MANAGER')
        
        try:
            if use_service:
                result = self._database_service.table_exists(table_name)
            # Legacy fallback removed - using service only
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('_table_exists', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('_table_exists', use_service, duration_ms, False)
            
            if self.enable_fallback and use_service:
                logger.warning(f"Schema service failed, falling back to legacy: {str(e)}")
                return self._legacy_db._table_exists(table_name)
            raise
    
    def _postgres_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_SCHEMA_MANAGER')
        
        try:
            if use_service:
                result = self._database_service.column_exists(table_name, column_name)
            # Legacy fallback removed - using service only
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('_postgres_column_exists', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('_postgres_column_exists', use_service, duration_ms, False)
            
            if self.enable_fallback and use_service:
                logger.warning(f"Schema service failed, falling back to legacy: {str(e)}")
                return self._legacy_db._postgres_column_exists(table_name, column_name)
            raise
    
    def _get_table_columns(self, table_name: str) -> List[str]:
        """Get list of columns for a table."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_SCHEMA_MANAGER')
        
        try:
            if use_service:
                result = self._database_service.get_table_columns(table_name)
            # Legacy fallback removed - using service only
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('_get_table_columns', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('_get_table_columns', use_service, duration_ms, False)
            
            if self.enable_fallback and use_service:
                logger.warning(f"Schema service failed, falling back to legacy: {str(e)}")
                return self._legacy_db._get_table_columns(table_name)
            raise
    
    # ============================================================================
    # BATCH OPERATIONS (delegates to BatchOperationsService)
    # ============================================================================
    
    def create_batch_executor(self, batch_size: int = 100, auto_execute: bool = False):
        """Create a batch executor for bulk operations."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_BATCH_SERVICE')
        
        try:
            if use_service:
                result = self._database_service.create_batch_executor(batch_size, auto_execute)
            # Legacy fallback removed - using service only
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('create_batch_executor', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('create_batch_executor', use_service, duration_ms, False)
            
            if self.enable_fallback and use_service:
                logger.warning(f"Batch service failed, falling back to legacy: {str(e)}")
                return self._legacy_db.create_batch_executor(batch_size, auto_execute)
            raise
    
    # ============================================================================
    # EMBEDDING MANAGEMENT (delegates to EmbeddingManagementService)
    # ============================================================================
    
    def store_embedding(self, table: str, record_id: str, embedding: List[float]) -> bool:
        """Store an embedding for a record."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_EMBEDDING_SERVICE')
        
        try:
            if use_service:
                from src.services.ai_service import EmbeddingStatus
                status = self._embedding_service.store_embedding(table, record_id, embedding)
                result = status == EmbeddingStatus.SUCCESS
            # Legacy fallback removed - using service only
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('store_embedding', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('store_embedding', use_service, duration_ms, False)
            
            if self.enable_fallback and use_service:
                logger.warning(f"Embedding service failed, falling back to legacy: {str(e)}")
                return self._legacy_db.store_embedding(table, record_id, embedding)
            raise
    
    def batch_store_embeddings(self, table: str, embeddings: Dict[str, List[float]]) -> bool:
        """Store multiple embeddings in batch."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_EMBEDDING_SERVICE')
        
        try:
            if use_service:
                results = self._embedding_service.batch_store_embeddings(table, embeddings)
                # Check if all operations succeeded
                from src.services.ai_service import EmbeddingStatus
                result = all(status == EmbeddingStatus.SUCCESS for status in results.values())
            # Legacy fallback removed - using service only
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('batch_store_embeddings', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('batch_store_embeddings', use_service, duration_ms, False)
            
            if self.enable_fallback and use_service:
                logger.warning(f"Embedding service failed, falling back to legacy: {str(e)}")
                return self._legacy_db.batch_store_embeddings(table, embeddings)
            raise
    
    def get_embedding(self, table: str, record_id: str) -> Optional[List[float]]:
        """Get an embedding for a record."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_EMBEDDING_SERVICE')
        
        try:
            if use_service:
                result = self._embedding_service.get_embedding(table, record_id)
            # Legacy fallback removed - using service only
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('get_embedding', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('get_embedding', use_service, duration_ms, False)
            
            if self.enable_fallback and use_service:
                logger.warning(f"Embedding service failed, falling back to legacy: {str(e)}")
                return self._legacy_db.get_embedding(table, record_id)
            raise
    
    def find_similar(self, table: str, embedding: List[float], limit: int = 10, 
                    additional_filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Find similar records using vector similarity."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_EMBEDDING_SERVICE')
        
        try:
            if use_service:
                similarity_results = self._embedding_service.find_similar(
                    table, embedding, limit, 0.0, additional_filters, True
                )
                # Convert to legacy format
                result = []
                for sim_result in similarity_results:
                    record = sim_result.record_data.copy()
                    record['similarity_score'] = sim_result.similarity_score
                    record['distance'] = sim_result.distance
                    result.append(record)
            # Legacy fallback removed - using service only
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('find_similar', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('find_similar', use_service, duration_ms, False)
            
            if self.enable_fallback and use_service:
                logger.warning(f"Embedding service failed, falling back to legacy: {str(e)}")
                return self._legacy_db.find_similar(table, embedding, limit, additional_filters)
            raise
    
    # ============================================================================
    # ANALYTICS MONITORING (delegates to AnalyticsMonitoringService)
    # ============================================================================
    
    def analyze_slow_queries(self) -> Dict[str, Any]:
        """Analyze slow queries."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_ANALYTICS_SERVICE')
        
        try:
            if use_service:
                result = self._analytics_service.get_monitoring_report()
            # Legacy fallback removed - using service only
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('analyze_slow_queries', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('analyze_slow_queries', use_service, duration_ms, False)
            
            if self.enable_fallback and use_service:
                logger.warning(f"Analytics service failed, falling back to legacy: {str(e)}")
                return self._legacy_db.analyze_slow_queries()
            raise
    
    def _track_vector_search_performance(self, table_name: str, query_time: float,
                                       result_count: int, dimension: int = None,
                                       query_type: str = "vector", 
                                       additional_info: Optional[Dict[str, Any]] = None):
        """Track vector search performance."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_ANALYTICS_SERVICE')
        
        try:
            if use_service:
                self._analytics_service.record_query_performance(
                    query=f"vector_search_{table_name}",
                    params=(),
                    duration_ms=query_time * 1000,
                    rows_affected=result_count,
                    table_name=table_name,
                    query_type=query_type
                )
            else:
                self._legacy_db._track_vector_search_performance(
                    table_name, query_time, result_count, dimension, query_type, additional_info
                )
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('_track_vector_search_performance', use_service, duration_ms, True)
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('_track_vector_search_performance', use_service, duration_ms, False)
            
            if self.enable_fallback and use_service:
                logger.warning(f"Analytics service failed, falling back to legacy: {str(e)}")
                self._legacy_db._track_vector_search_performance(
                    table_name, query_time, result_count, dimension, query_type, additional_info
                )
    
    # ============================================================================
    # CACHE MANAGEMENT (delegates to CacheManagementService)
    # ============================================================================
    
    @property
    def vector_cache(self):
        """Get vector cache instance."""
        # For now, return None - cache functionality will be added to database service later
        return None
    
    @property
    def query_cache(self):
        """Get query cache instance."""
        # For now, return None - cache functionality will be added to database service later
        return None
    
    # ============================================================================
    # FACADE MONITORING AND REPORTING
    # ============================================================================
    
    def get_facade_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the facade."""
        total_ops = self._facade_metrics['total_operations']
        if total_ops == 0:
            return self._facade_metrics.copy()
        
        metrics = self._facade_metrics.copy()
        metrics.update({
            'new_service_percentage': (metrics['new_service_calls'] / total_ops) * 100,
            'legacy_fallback_percentage': (metrics['legacy_fallbacks'] / total_ops) * 100,
            'error_rate': (metrics['error_count'] / total_ops) * 100,
            'service_status': {
                'extension_manager': self._should_use_service('USE_NEW_EXTENSION_MANAGER'),
                'schema_manager': self._should_use_service('USE_NEW_SCHEMA_MANAGER'),
                'cache_manager': self._should_use_service('USE_NEW_CACHE_MANAGER'),
                'analytics_service': self._should_use_service('USE_NEW_ANALYTICS_SERVICE'),
                'batch_service': self._should_use_service('USE_NEW_BATCH_SERVICE'),
                'embedding_service': self._should_use_service('USE_NEW_EMBEDDING_SERVICE')
            }
        })
        
        return metrics
    
    # ============================================================================
    # GENERIC CRUD METHODS (delegates to UnifiedSearchService and repositories)
    # ============================================================================
    
    def generic_get(self, table: str, record_id: int, jsonb_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get a record by ID from any table."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_UNIFIED_SEARCH')
        
        try:
            if use_service:
                result = self._search_service.get_record_by_id(table, record_id, jsonb_fields)
            else:
                # Direct database query
                if jsonb_fields is None:
                    jsonb_fields = []
                
                query = f"SELECT * FROM {table} WHERE id = %s"
                results = self._connection_manager.execute_query(query, (record_id,), fetchall=True)
                
                if not results:
                    result = None
                else:
                    result = results[0]
                    # Parse JSONB fields
                    for field in jsonb_fields:
                        if field in result and result[field]:
                            import json
                            try:
                                result[field] = json.loads(result[field]) if isinstance(result[field], str) else result[field]
                            except (json.JSONDecodeError, TypeError):
                                pass
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('generic_get', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('generic_get', use_service, duration_ms, False)
            logger.error(f"Error in generic_get for table {table}, ID {record_id}: {str(e)}")
            
            if self.enable_fallback and use_service:
                logger.warning("Search service failed, falling back to direct query")
                return self.generic_get(table, record_id, jsonb_fields)
            raise
    
    def generic_search(self, table: str, filters: Dict[str, Any] = None,
                      limit: int = 10, offset: int = 0,
                      jsonb_fields: List[str] = None,
                      language: str = "en") -> List[Dict[str, Any]]:
        """Search records in any table with filters."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_UNIFIED_SEARCH')
        
        try:
            if use_service:
                result = self._search_service.search_table(
                    table_name=table,
                    filters=filters,
                    limit=limit,
                    offset=offset,
                    jsonb_fields=jsonb_fields,
                    language=language
                )
            else:
                # Direct database query
                if filters is None:
                    filters = {}
                if jsonb_fields is None:
                    jsonb_fields = []
                
                # Build query
                query = f"SELECT * FROM {table}"
                params = []
                
                if filters:
                    where_conditions = []
                    for field, value in filters.items():
                        if value is not None:
                            where_conditions.append(f"{field} = %s")
                            params.append(value)
                    
                    if where_conditions:
                        query += " WHERE " + " AND ".join(where_conditions)
                
                # Add LIMIT and OFFSET clauses
                query += f" LIMIT %s OFFSET %s"
                # Ensure limit and offset are integers to prevent SQL type errors
                try:
                    params.extend([int(limit), int(offset)])
                except (TypeError, ValueError):
                    logger.warning(f"Invalid limit/offset values: {limit}/{offset}, using defaults")
                    params.extend([10, 0])  # Default values
                
                results = self._connection_manager.execute_query(query, tuple(params), fetchall=True)
                
                # Parse JSONB fields
                for result in results:
                    for field in jsonb_fields:
                        if field in result and result[field]:
                            import json
                            try:
                                result[field] = json.loads(result[field]) if isinstance(result[field], str) else result[field]
                            except (json.JSONDecodeError, TypeError):
                                pass
                
                result = results
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('generic_search', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('generic_search', use_service, duration_ms, False)
            logger.error(f"Error in generic_search for table {table}: {str(e)}")
            
            if self.enable_fallback and use_service:
                logger.warning("Search service failed, falling back to direct query")
                return self.generic_search(table, filters, limit, offset, jsonb_fields, language)
            raise
    
    def generic_create(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """Create a new record in any table."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_BATCH_SERVICE')
        
        try:
            if use_service:
                # Use batch service for consistency
                metrics = self._database_service.bulk_insert(table, [data], batch_size=1)
                result = metrics.successful_operations if metrics.successful_operations > 0 else None
            else:
                # Direct database query
                if not data:
                    result = None
                else:
                    fields = list(data.keys())
                    values = list(data.values())
                    placeholders = ", ".join(["%s"] * len(fields))
                    fields_str = ", ".join(fields)
                    
                    query = f"INSERT INTO {table} ({fields_str}) VALUES ({placeholders}) RETURNING id"
                    results = self._connection_manager.execute_query(query, tuple(values), fetchall=True)
                    result = results[0]['id'] if results else None
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('generic_create', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('generic_create', use_service, duration_ms, False)
            logger.error(f"Error in generic_create for table {table}: {str(e)}")
            
            if self.enable_fallback and use_service:
                logger.warning("Batch service failed, falling back to direct query")
                return self.generic_create(table, data)
            raise
    
    def generic_update(self, table: str, record_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing record in any table."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_BATCH_SERVICE')
        
        try:
            if use_service:
                # Prepare update data with ID
                update_data = data.copy()
                update_data['id'] = record_id
                metrics = self._database_service.bulk_update(table, [update_data], id_column='id', batch_size=1)
                result = metrics.successful_operations > 0
            else:
                # Direct database query
                if not data:
                    result = False
                else:
                    set_clauses = []
                    values = []
                    for field, value in data.items():
                        set_clauses.append(f"{field} = %s")
                        values.append(value)
                    
                    values.append(record_id)
                    set_clause = ", ".join(set_clauses)
                    query = f"UPDATE {table} SET {set_clause} WHERE id = %s"
                    
                    self._connection_manager.execute_query(query, tuple(values), fetchall=False)
                    result = True
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('generic_update', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('generic_update', use_service, duration_ms, False)
            logger.error(f"Error in generic_update for table {table}, ID {record_id}: {str(e)}")
            
            if self.enable_fallback and use_service:
                logger.warning("Batch service failed, falling back to direct query")
                return self.generic_update(table, record_id, data)
            raise
    
    def generic_delete(self, table: str, record_id: int) -> bool:
        """Delete a record from any table."""
        start_time = time.time()
        use_service = self._should_use_service('USE_NEW_BATCH_SERVICE')
        
        try:
            if use_service:
                metrics = self._database_service.bulk_delete(table, [record_id], id_column='id', batch_size=1)
                result = metrics.successful_operations > 0
            else:
                # Direct database query
                query = f"DELETE FROM {table} WHERE id = %s"
                self._connection_manager.execute_query(query, (record_id,), fetchall=False)
                result = True
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('generic_delete', use_service, duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('generic_delete', use_service, duration_ms, False)
            logger.error(f"Error in generic_delete for table {table}, ID {record_id}: {str(e)}")
            
            if self.enable_fallback and use_service:
                logger.warning("Batch service failed, falling back to direct query")
                return self.generic_delete(table, record_id)
            raise
    
    # ============================================================================
    # ADDITIONAL COMPATIBILITY METHODS
    # ============================================================================
    
    def test_connection(self) -> bool:
        """Test database connection."""
        return self.is_connected()
    
    def search_attractions(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None, 
                          limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """Search attractions using the facade's generic search method with text query support."""
        search_filters = filters or {}
        if query:
            if isinstance(query, dict):
                if "text" in query:
                    search_filters.update({k: v for k, v in query.items() if k != "text"})
                else:
                    search_filters.update(query)
            else:
                search_filters["text"] = str(query)
        return self.generic_search("attractions", search_filters, limit, offset, ["name", "description"], language)
    
    def search_restaurants(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None, 
                          limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """Search restaurants using the facade's generic search method with text query support."""
        search_filters = filters or {}
        if query:
            if isinstance(query, dict):
                if "text" in query:
                    search_filters.update({k: v for k, v in query.items() if k != "text"})
                else:
                    search_filters.update(query)
            else:
                search_filters["text"] = str(query)
        return self.generic_search("restaurants", search_filters, limit, offset, ["name", "description"], language)
    
    def search_accommodations(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None, 
                            limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """Search accommodations using the facade's generic search method with text query support.""" 
        search_filters = filters or {}
        if query:
            if isinstance(query, dict):
                if "text" in query:
                    search_filters.update({k: v for k, v in query.items() if k != "text"})
                else:
                    search_filters.update(query)
            else:
                search_filters["text"] = str(query)
        return self.generic_search("accommodations", search_filters, limit, offset, ["name", "description"], language)
    
    # ============================================================================
    # MISSING METHODS - ADDED TO FIX DATABASE QUERY FAILURES
    # ============================================================================
    
    def search_practical_info(self, query: Optional[Dict[str, Any]] = None, category_id: Optional[str] = None,
                             limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """Search practical info using generic search method.
        Maintains backward-compatible positional parameters: (query, category_id, limit, offset, language).
        New code builds a filters dict internally based on optional category_id and any query text/fields.
        """
        # Initialise filters dict
        search_filters: Dict[str, Any] = {}
        if category_id:
            search_filters["category_id"] = category_id
        # Process query argument
        if query:
            if isinstance(query, dict):
                if "text" in query:
                    # For text queries, we keep text separate; remaining keys become filters
                    search_filters.update({k: v for k, v in query.items() if k != "text"})
                else:
                    search_filters.update(query)
            else:
                # Treat string query as text search
                search_filters["text"] = str(query)
        return self.generic_search("practical_info", search_filters, limit, offset, ["title", "content"], language)
    
    def search_hotels(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None,
                     limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """Search hotels - alias for search_accommodations to maintain compatibility."""
        return self.search_accommodations(query, filters, limit, offset, language)
    
    def search_faqs(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None,
                   limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """Search FAQs using generic search method."""
        # Handle both query dict with 'text' and direct filters
        search_filters = filters if isinstance(filters, dict) else {}
        if query:
            if isinstance(query, dict):
                if "text" in query:
                    # For text queries, search in question and answer fields
                    search_filters.update({k: v for k, v in query.items() if k != "text"})
                else:
                    search_filters.update(query)
            else:
                # If query is a string, treat as text search
                search_filters["text"] = str(query)
        
        return self.generic_search("tourism_faqs", search_filters, limit, offset, ["question", "answer"], language)
    
    def search_events(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None,
                     limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """Search events using generic search method."""
        # Handle both query dict with 'text' and direct filters
        search_filters = filters if isinstance(filters, dict) else {}
        if query:
            if isinstance(query, dict):
                if "text" in query:
                    # For text queries, search in name and description fields
                    search_filters.update({k: v for k, v in query.items() if k != "text"})
                else:
                    search_filters.update(query)
            else:
                # If query is a string, treat as text search
                search_filters["text"] = str(query)
        
        return self.generic_search("events_festivals", search_filters, limit, offset, ["name", "description"], language)
    
    # ============================================================================
    # DELEGATE ALL OTHER METHODS TO LEGACY DATABASE MANAGER
    # ============================================================================
    
    def __getattr__(self, name):
        """Delegate all missing methods to the database adapter."""
        if hasattr(self._db_adapter, name):
            return getattr(self._db_adapter, name)
        elif hasattr(self._connection_manager, name):
            return getattr(self._connection_manager, name)
        else:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'") 