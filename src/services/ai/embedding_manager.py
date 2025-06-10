"""
Embedding Management Service for the Egypt Tourism Chatbot.

This service handles vector embeddings storage, retrieval, and similarity search.
Extracted from DatabaseManager vector operations as part of Phase 2.5 refactoring.
"""
import logging
import os
import time
import numpy as np
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class EmbeddingStatus(Enum):
    """Embedding operation status enumeration."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    INVALID_DIMENSION = "invalid_dimension"
    EXTENSION_MISSING = "extension_missing"

class SimilarityMetric(Enum):
    """Similarity metric enumeration."""
    COSINE = "cosine"
    L2 = "l2"
    DOT_PRODUCT = "dot_product"

@dataclass
class EmbeddingInfo:
    """Information about a stored embedding."""
    table: str
    record_id: str
    dimension: int
    created_at: float
    updated_at: float
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class SimilarityResult:
    """Similarity search result."""
    record_id: str
    similarity_score: float
    record_data: Dict[str, Any]
    distance: float
    metadata: Optional[Dict[str, Any]] = None

class EmbeddingManagementService:
    """
    Service for managing vector embeddings and similarity search.
    
    This service provides comprehensive management of vector embeddings
    including storage, retrieval, similarity search, and index optimization.
    
    Responsibilities:
    - Embedding storage and retrieval
    - Batch embedding operations
    - Vector similarity search
    - Index management and optimization
    - Dimension validation
    - Performance monitoring for vector operations
    """
    
    # Valid tables for vector operations
    VALID_TABLES = {'attractions', 'restaurants', 'accommodations', 'cities', 'regions'}
    
    # Standard embedding dimensions
    STANDARD_DIMENSIONS = {
        'openai_ada_002': 1536,
        'openai_text_embedding_3_small': 1536,
        'openai_text_embedding_3_large': 3072,
        'sentence_transformers': 768,
        'custom': None  # Allow custom dimensions
    }
    
    def __init__(self, db_manager=None, extension_manager=None, 
                 default_dimension: int = 1536, similarity_metric: SimilarityMetric = SimilarityMetric.COSINE):
        """
        Initialize the embedding management service.
        
        Args:
            db_manager: Database manager instance
            extension_manager: Extension manager for pgvector capability checking
            default_dimension: Default embedding dimension
            similarity_metric: Default similarity metric for searches
        """
        self.db_manager = db_manager
        self.extension_manager = extension_manager
        self.default_dimension = default_dimension
        self.similarity_metric = similarity_metric
        
        # Feature flags from environment
        self.enabled = os.getenv('USE_NEW_EMBEDDING_SERVICE', 'false').lower() == 'true'
        
        # Performance tracking
        self._embedding_operations = 0
        self._similarity_searches = 0
        self._total_search_time = 0
        self._dimension_stats = {}
        
        # Validate pgvector availability
        self._pgvector_available = self._check_pgvector_availability()
        
        logger.info(f"Embedding management service initialized (pgvector={'available' if self._pgvector_available else 'unavailable'})")
    
    def store_embedding(self, table: str, record_id: str, embedding: Union[List[float], np.ndarray],
                       metadata: Optional[Dict[str, Any]] = None) -> EmbeddingStatus:
        """
        Store a vector embedding for a specific record.
        
        Args:
            table: Table name
            record_id: Record identifier
            embedding: Vector embedding
            metadata: Optional metadata about the embedding
            
        Returns:
            EmbeddingStatus: Operation status
        """
        try:
            if not self.enabled and self.db_manager:
                # Fallback to legacy method
                success = self.db_manager.store_embedding(table, record_id, embedding)
                return EmbeddingStatus.SUCCESS if success else EmbeddingStatus.FAILED
            
            # Validate inputs
            if not self._pgvector_available:
                logger.warning("pgvector extension not available")
                return EmbeddingStatus.EXTENSION_MISSING
            
            if table not in self.VALID_TABLES:
                logger.error(f"Invalid table for embedding storage: {table}")
                return EmbeddingStatus.FAILED
            
            # Process and validate embedding
            processed_embedding = self._process_embedding(embedding)
            if not processed_embedding:
                return EmbeddingStatus.INVALID_DIMENSION
            
            # Validate dimension
            if not self._validate_dimension(processed_embedding):
                logger.error(f"Invalid embedding dimension: {len(processed_embedding)}")
                return EmbeddingStatus.INVALID_DIMENSION
            
            # Store the embedding
            success = self._execute_store_embedding(table, record_id, processed_embedding, metadata)
            
            if success:
                self._embedding_operations += 1
                self._update_dimension_stats(table, len(processed_embedding))
                logger.debug(f"Stored embedding for {table}.{record_id}")
                return EmbeddingStatus.SUCCESS
            else:
                return EmbeddingStatus.FAILED
                
        except Exception as e:
            logger.error(f"Error storing embedding: {str(e)}")
            return EmbeddingStatus.FAILED
    
    def batch_store_embeddings(self, table: str, embeddings: Dict[str, Union[List[float], np.ndarray]],
                             metadata: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, EmbeddingStatus]:
        """
        Store multiple embeddings in batch.
        
        Args:
            table: Table name
            embeddings: Dictionary mapping record IDs to embeddings
            metadata: Optional metadata for each embedding
            
        Returns:
            Dict[str, EmbeddingStatus]: Status for each record
        """
        try:
            if not self.enabled and self.db_manager:
                # Fallback to legacy method
                success = self.db_manager.batch_store_embeddings(table, embeddings)
                return {record_id: EmbeddingStatus.SUCCESS if success else EmbeddingStatus.FAILED 
                       for record_id in embeddings.keys()}
            
            if not self._pgvector_available:
                return {record_id: EmbeddingStatus.EXTENSION_MISSING for record_id in embeddings.keys()}
            
            if not embeddings:
                return {}
            
            results = {}
            start_time = time.time()
            
            # Process and validate all embeddings first
            processed_embeddings = {}
            for record_id, embedding in embeddings.items():
                processed = self._process_embedding(embedding)
                if processed and self._validate_dimension(processed):
                    processed_embeddings[record_id] = processed
                    results[record_id] = EmbeddingStatus.SUCCESS
                else:
                    results[record_id] = EmbeddingStatus.INVALID_DIMENSION
            
            if not processed_embeddings:
                logger.warning("No valid embeddings to store")
                return results
            
            # Execute batch storage
            batch_success = self._execute_batch_store_embeddings(table, processed_embeddings, metadata)
            
            if not batch_success:
                # Mark all as failed if batch operation failed
                for record_id in processed_embeddings.keys():
                    results[record_id] = EmbeddingStatus.FAILED
            else:
                # Update statistics
                self._embedding_operations += len(processed_embeddings)
                for embedding in processed_embeddings.values():
                    self._update_dimension_stats(table, len(embedding))
            
            duration = time.time() - start_time
            logger.info(f"Batch stored {len(processed_embeddings)} embeddings in {duration:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch store embeddings: {str(e)}")
            return {record_id: EmbeddingStatus.FAILED for record_id in embeddings.keys()}
    
    def get_embedding(self, table: str, record_id: str) -> Optional[List[float]]:
        """
        Retrieve an embedding for a specific record.
        
        Args:
            table: Table name
            record_id: Record identifier
            
        Returns:
            Optional[List[float]]: The embedding or None if not found
        """
        try:
            if not self.enabled and self.db_manager:
                # Fallback to legacy method
                return self.db_manager.get_embedding(table, record_id)
            
            if not self._pgvector_available:
                logger.warning("pgvector extension not available")
                return None
            
            if table not in self.VALID_TABLES:
                logger.error(f"Invalid table for embedding retrieval: {table}")
                return None
            
            # Execute retrieval
            embedding = self._execute_get_embedding(table, record_id)
            
            if embedding:
                logger.debug(f"Retrieved embedding for {table}.{record_id}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error retrieving embedding: {str(e)}")
            return None
    
    def find_similar(self, table: str, embedding: Union[List[float], np.ndarray], 
                    limit: int = 10, similarity_threshold: float = 0.0,
                    additional_filters: Optional[Dict[str, Any]] = None,
                    include_distance: bool = True) -> List[SimilarityResult]:
        """
        Find records with similar embeddings.
        
        Args:
            table: Table name
            embedding: Query embedding
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            additional_filters: Additional WHERE clause filters
            include_distance: Whether to include distance calculation
            
        Returns:
            List[SimilarityResult]: Similar records with scores
        """
        try:
            if not self.enabled and self.db_manager:
                # Fallback to legacy method
                legacy_results = self.db_manager.find_similar(table, embedding, limit, additional_filters)
                return self._convert_legacy_results(legacy_results)
            
            if not self._pgvector_available:
                logger.warning("pgvector extension not available")
                return []
            
            if table not in self.VALID_TABLES:
                logger.error(f"Invalid table for similarity search: {table}")
                return []
            
            # Process query embedding
            processed_embedding = self._process_embedding(embedding)
            if not processed_embedding:
                logger.error("Invalid query embedding")
                return []
            
            start_time = time.time()
            
            # Execute similarity search
            results = self._execute_similarity_search(
                table, processed_embedding, limit, similarity_threshold, 
                additional_filters, include_distance
            )
            
            # Update search statistics
            duration = time.time() - start_time
            self._similarity_searches += 1
            self._total_search_time += duration
            
            logger.debug(f"Similarity search found {len(results)} results in {duration:.3f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []
    
    def optimize_vector_indexes(self, table: str, index_type: str = 'ivfflat',
                              rebuild: bool = False) -> bool:
        """
        Optimize vector indexes for a table.
        
        Args:
            table: Table name
            index_type: Type of index ('ivfflat' or 'hnsw')
            rebuild: Whether to rebuild existing indexes
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self._pgvector_available:
                logger.warning("pgvector extension not available")
                return False
            
            if table not in self.VALID_TABLES:
                logger.error(f"Invalid table for index optimization: {table}")
                return False
            
            logger.info(f"Optimizing vector indexes for {table} (type: {index_type})")
            
            # Check if we need to rebuild
            if rebuild:
                self._drop_vector_indexes(table)
            
            # Create optimized index
            success = self._create_vector_index(table, index_type)
            
            if success:
                logger.info(f"Successfully optimized vector indexes for {table}")
            else:
                logger.error(f"Failed to optimize vector indexes for {table}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error optimizing vector indexes: {str(e)}")
            return False
    
    def validate_embedding_dimension(self, embedding: Union[List[float], np.ndarray],
                                   expected_dimension: Optional[int] = None) -> bool:
        """
        Validate embedding dimension.
        
        Args:
            embedding: Embedding to validate
            expected_dimension: Expected dimension, defaults to service default
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            processed = self._process_embedding(embedding)
            if not processed:
                return False
            
            expected = expected_dimension or self.default_dimension
            return len(processed) == expected
            
        except Exception as e:
            logger.error(f"Error validating embedding dimension: {str(e)}")
            return False
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get embedding management statistics.
        
        Returns:
            Dict[str, Any]: Comprehensive statistics
        """
        try:
            avg_search_time = (self._total_search_time / self._similarity_searches 
                             if self._similarity_searches > 0 else 0)
            
            return {
                'service_enabled': self.enabled,
                'pgvector_available': self._pgvector_available,
                'default_dimension': self.default_dimension,
                'similarity_metric': self.similarity_metric.value,
                'total_embedding_operations': self._embedding_operations,
                'total_similarity_searches': self._similarity_searches,
                'avg_search_time_ms': avg_search_time * 1000,
                'dimension_distribution': self._dimension_stats,
                'valid_tables': list(self.VALID_TABLES),
                'supported_dimensions': self.STANDARD_DIMENSIONS
            }
            
        except Exception as e:
            logger.error(f"Error getting embedding stats: {str(e)}")
            return {}
    
    def _check_pgvector_availability(self) -> bool:
        """Check if pgvector extension is available."""
        try:
            if self.extension_manager:
                return self.extension_manager.check_pgvector_available()
            elif self.db_manager:
                return self.db_manager._check_vector_enabled()
            return False
        except Exception as e:
            logger.error(f"Error checking pgvector availability: {str(e)}")
            return False
    
    def _process_embedding(self, embedding: Union[List[float], np.ndarray]) -> Optional[List[float]]:
        """Process embedding to ensure consistent format."""
        try:
            if isinstance(embedding, np.ndarray):
                return embedding.tolist()
            elif isinstance(embedding, list):
                # Validate that all elements are numeric
                return [float(x) for x in embedding]
            elif isinstance(embedding, str):
                # Try to parse JSON string
                import json
                try:
                    parsed = json.loads(embedding)
                    return [float(x) for x in parsed]
                except (json.JSONDecodeError, ValueError):
                    logger.error("Invalid embedding string format")
                    return None
            else:
                logger.error(f"Unsupported embedding type: {type(embedding)}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing embedding: {str(e)}")
            return None
    
    def _validate_dimension(self, embedding: List[float]) -> bool:
        """Validate embedding dimension."""
        if not embedding:
            return False
        
        dimension = len(embedding)
        
        # Allow standard dimensions
        if dimension in self.STANDARD_DIMENSIONS.values():
            return True
        
        # Allow custom dimensions within reasonable range
        if 50 <= dimension <= 4096:
            return True
        
        return False
    
    def _execute_store_embedding(self, table: str, record_id: str, embedding: List[float],
                               metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Execute embedding storage operation."""
        try:
            if not self.db_manager:
                return False
            
            # Check if record exists
            check_sql = f"SELECT 1 FROM {table} WHERE id = %s"
            result = self.db_manager.execute_postgres_query(check_sql, (record_id,))
            
            if not result:
                # Insert new record with embedding
                sql = f"""
                    INSERT INTO {table} (id, embedding, created_at, updated_at)
                    VALUES (%s, %s::vector, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO UPDATE SET 
                        embedding = EXCLUDED.embedding,
                        updated_at = CURRENT_TIMESTAMP
                """
            else:
                # Update existing record
                sql = f"""
                    UPDATE {table}
                    SET embedding = %s::vector, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
            
            if not result:
                params = (record_id, embedding)
            else:
                params = (embedding, record_id)
            
            result = self.db_manager.execute_postgres_query(sql, params)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error executing store embedding: {str(e)}")
            return False
    
    def _execute_batch_store_embeddings(self, table: str, embeddings: Dict[str, List[float]],
                                      metadata: Optional[Dict[str, Dict[str, Any]]] = None) -> bool:
        """Execute batch embedding storage."""
        try:
            if not self.db_manager:
                return False
            
            conn = self.db_manager._get_pg_connection()
            if not conn:
                return False
            
            try:
                with conn:
                    with conn.cursor() as cursor:
                        from psycopg2.extras import execute_values
                        
                        # Prepare data for batch update
                        update_data = [(embedding, record_id) for record_id, embedding in embeddings.items()]
                        
                        # Use execute_values for efficient batch operation
                        execute_values(
                            cursor,
                            f"""
                            INSERT INTO {table} (id, embedding, created_at, updated_at)
                            VALUES %s
                            ON CONFLICT (id) DO UPDATE SET 
                                embedding = EXCLUDED.embedding,
                                updated_at = CURRENT_TIMESTAMP
                            """,
                            [(record_id, embedding, 'CURRENT_TIMESTAMP', 'CURRENT_TIMESTAMP') 
                             for record_id, embedding in embeddings.items()],
                            template="(%s, %s::vector, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                            page_size=100
                        )
                
                return True
                
            finally:
                self.db_manager._return_pg_connection(conn)
                
        except Exception as e:
            logger.error(f"Error executing batch store embeddings: {str(e)}")
            return False
    
    def _execute_get_embedding(self, table: str, record_id: str) -> Optional[List[float]]:
        """Execute embedding retrieval."""
        try:
            sql = f"SELECT embedding FROM {table} WHERE id = %s AND embedding IS NOT NULL"
            result = self.db_manager.execute_postgres_query(sql, (record_id,), fetchall=False)
            
            if result and 'embedding' in result:
                return result['embedding']
            
            return None
            
        except Exception as e:
            logger.error(f"Error executing get embedding: {str(e)}")
            return None
    
    def _execute_similarity_search(self, table: str, embedding: List[float], limit: int,
                                 similarity_threshold: float, additional_filters: Optional[Dict[str, Any]],
                                 include_distance: bool) -> List[SimilarityResult]:
        """Execute similarity search operation."""
        try:
            # Build similarity query based on metric
            if self.similarity_metric == SimilarityMetric.COSINE:
                similarity_expr = "1 - (embedding <=> %s::vector)"
                distance_expr = "embedding <=> %s::vector"
            elif self.similarity_metric == SimilarityMetric.L2:
                similarity_expr = "1 / (1 + (embedding <-> %s::vector))"
                distance_expr = "embedding <-> %s::vector"
            else:  # DOT_PRODUCT
                similarity_expr = "embedding <#> %s::vector"
                distance_expr = "embedding <#> %s::vector"
            
            # Build base query
            select_fields = ["id", f"({similarity_expr}) AS similarity_score"]
            if include_distance:
                select_fields.append(f"({distance_expr}) AS distance")
            
            # Add all other columns (except embedding for performance)
            table_columns = self._get_table_columns(table)
            for col in table_columns:
                if col not in ['id', 'embedding']:
                    select_fields.append(col)
            
            sql = f"""
                SELECT {', '.join(select_fields)}
                FROM {table}
                WHERE embedding IS NOT NULL
            """
            
            params = [embedding, embedding]  # Two references to embedding
            if include_distance:
                params.append(embedding)  # Third reference for distance
            
            # Add additional filters
            if additional_filters:
                for key, value in additional_filters.items():
                    sql += f" AND {key} = %s"
                    params.append(value)
            
            # Add similarity threshold
            if similarity_threshold > 0:
                sql += f" AND ({similarity_expr}) >= %s"
                params.append(similarity_threshold)
                params.insert(-1, embedding)  # Add embedding reference for threshold check
            
            # Order by similarity and limit
            sql += f" ORDER BY ({similarity_expr}) DESC LIMIT %s"
            params.insert(-1, embedding)  # Add embedding reference for ordering
            params.append(limit)
            
            # Execute query
            results = self.db_manager.execute_postgres_query(sql, params)
            
            # Convert to SimilarityResult objects
            similarity_results = []
            for row in results or []:
                record_data = {k: v for k, v in row.items() 
                             if k not in ['similarity_score', 'distance']}
                
                result = SimilarityResult(
                    record_id=row['id'],
                    similarity_score=row['similarity_score'],
                    record_data=record_data,
                    distance=row.get('distance', 0.0) if include_distance else 0.0
                )
                similarity_results.append(result)
            
            return similarity_results
            
        except Exception as e:
            logger.error(f"Error executing similarity search: {str(e)}")
            return []
    
    def _get_table_columns(self, table: str) -> List[str]:
        """Get table columns."""
        try:
            if self.db_manager and hasattr(self.db_manager, '_get_table_columns'):
                return self.db_manager._get_table_columns(table)
            
            # Fallback query
            sql = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """
            result = self.db_manager.execute_postgres_query(sql, (table,))
            return [row['column_name'] for row in result] if result else []
            
        except Exception as e:
            logger.error(f"Error getting table columns: {str(e)}")
            return ['id']  # Safe fallback
    
    def _create_vector_index(self, table: str, index_type: str = 'ivfflat') -> bool:
        """Create vector index for table."""
        try:
            # Check if index already exists
            check_sql = """
                SELECT 1 FROM pg_indexes
                WHERE tablename = %s AND indexdef LIKE '%embedding%'
            """
            result = self.db_manager.execute_postgres_query(check_sql, (table,))
            
            if result:
                logger.info(f"Vector index already exists for {table}")
                return True
            
            # Create index based on type
            if index_type.lower() == 'ivfflat':
                # Determine number of lists based on table size
                count_sql = f"SELECT COUNT(*) as count FROM {table} WHERE embedding IS NOT NULL"
                count_result = self.db_manager.execute_postgres_query(count_sql)
                row_count = count_result[0]['count'] if count_result else 0
                
                lists = max(4, min(1000, int(np.sqrt(row_count) / 2)))
                index_sql = f"""
                    CREATE INDEX CONCURRENTLY idx_ivfflat_{table}_embedding ON {table}
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = {lists})
                """
            else:  # hnsw
                index_sql = f"""
                    CREATE INDEX CONCURRENTLY idx_hnsw_{table}_embedding ON {table}
                    USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                """
            
            # Execute index creation
            self.db_manager.execute_postgres_query(index_sql)
            logger.info(f"Created {index_type} vector index for {table}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating vector index: {str(e)}")
            return False
    
    def _drop_vector_indexes(self, table: str) -> None:
        """Drop existing vector indexes for table."""
        try:
            # Find existing vector indexes
            sql = """
                SELECT indexname FROM pg_indexes
                WHERE tablename = %s AND indexdef LIKE '%embedding%'
            """
            result = self.db_manager.execute_postgres_query(sql, (table,))
            
            for row in result or []:
                index_name = row['indexname']
                drop_sql = f"DROP INDEX CONCURRENTLY IF EXISTS {index_name}"
                self.db_manager.execute_postgres_query(drop_sql)
                logger.info(f"Dropped vector index: {index_name}")
                
        except Exception as e:
            logger.error(f"Error dropping vector indexes: {str(e)}")
    
    def _update_dimension_stats(self, table: str, dimension: int) -> None:
        """Update dimension statistics."""
        if table not in self._dimension_stats:
            self._dimension_stats[table] = {}
        
        if dimension not in self._dimension_stats[table]:
            self._dimension_stats[table][dimension] = 0
        
        self._dimension_stats[table][dimension] += 1
    
    def _convert_legacy_results(self, legacy_results: List[Dict[str, Any]]) -> List[SimilarityResult]:
        """Convert legacy similarity results to new format."""
        results = []
        for row in legacy_results:
            # Extract similarity score (might be in different fields)
            similarity_score = row.get('similarity_score', row.get('score', 1.0))
            distance = row.get('distance', 0.0)
            
            # Remove score fields from record data
            record_data = {k: v for k, v in row.items() 
                         if k not in ['similarity_score', 'score', 'distance']}
            
            result = SimilarityResult(
                record_id=row.get('id', ''),
                similarity_score=similarity_score,
                record_data=record_data,
                distance=distance
            )
            results.append(result)
        
        return results 