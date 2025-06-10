"""
Consolidated AI Service Module

This module provides unified AI functionality including:
- Embedding management and vector operations
- AI model integrations (Anthropic Claude)
- Vector similarity search
- AI-powered response generation

Consolidates functionality from:
- src/services/ai/embedding_manager.py
- src/services/anthropic_service.py
"""

import logging
import hashlib
import time
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
import numpy as np

from src.services.base_service import BaseService

logger = logging.getLogger(__name__)

# Re-export key classes and enums from embedding manager
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

class EmbeddingService(BaseService):
    """
    Service for managing vector embeddings and similarity search.
    
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
        'sentence_transformers': 384
    }

    def __init__(self, db_manager=None, extension_manager=None, 
                 default_dimension: int = 1536, similarity_metric: SimilarityMetric = SimilarityMetric.COSINE):
        super().__init__(db_manager)
        self.extension_manager = extension_manager
        self.default_dimension = default_dimension
        self.similarity_metric = similarity_metric
        
        # Performance tracking
        self._operation_stats = {
            'stores': 0,
            'retrievals': 0,
            'searches': 0,
            'errors': 0,
            'total_duration_ms': 0.0
        }
        self._stats_lock = threading.RLock()
        
        # Dimension statistics
        self._dimension_stats = {}
        
        # Check pgvector availability
        self._pgvector_available = self._check_pgvector_availability()

    def store_embedding(self, table: str, record_id: str, embedding: Union[List[float], np.ndarray],
                       metadata: Optional[Dict[str, Any]] = None) -> EmbeddingStatus:
        """Store a single embedding for a record."""
        start_time = time.time()
        
        try:
            if table not in self.VALID_TABLES:
                logger.error(f"Invalid table for embedding storage: {table}")
                return EmbeddingStatus.FAILED
            
            processed_embedding = self._process_embedding(embedding)
            if not processed_embedding:
                return EmbeddingStatus.INVALID_DIMENSION
            
            if not self._validate_dimension(processed_embedding):
                return EmbeddingStatus.INVALID_DIMENSION
            
            success = self._execute_store_embedding(table, record_id, processed_embedding, metadata)
            
            duration_ms = (time.time() - start_time) * 1000
            
            with self._stats_lock:
                if success:
                    self._operation_stats['stores'] += 1
                    self._update_dimension_stats(table, len(processed_embedding))
                    result = EmbeddingStatus.SUCCESS
                else:
                    self._operation_stats['errors'] += 1
                    result = EmbeddingStatus.FAILED
                
                self._operation_stats['total_duration_ms'] += duration_ms
            
            return result
            
        except Exception as e:
            logger.error(f"Error storing embedding for {table}.{record_id}: {e}")
            with self._stats_lock:
                self._operation_stats['errors'] += 1
            return EmbeddingStatus.FAILED

    def batch_store_embeddings(self, table: str, embeddings: Dict[str, Union[List[float], np.ndarray]],
                             metadata: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, EmbeddingStatus]:
        """Store multiple embeddings in batch."""
        if table not in self.VALID_TABLES:
            logger.error(f"Invalid table for batch embedding storage: {table}")
            return {record_id: EmbeddingStatus.FAILED for record_id in embeddings.keys()}
        
        results = {}
        processed_embeddings = {}
        
        # Process and validate all embeddings first
        for record_id, embedding in embeddings.items():
            processed = self._process_embedding(embedding)
            if processed and self._validate_dimension(processed):
                processed_embeddings[record_id] = processed
                results[record_id] = EmbeddingStatus.SUCCESS
            else:
                results[record_id] = EmbeddingStatus.INVALID_DIMENSION
        
        if not processed_embeddings:
            return results
        
        # Execute batch storage
        try:
            success = self._execute_batch_store_embeddings(table, processed_embeddings, metadata)
            
            if not success:
                # Mark all as failed if batch operation failed
                for record_id in processed_embeddings.keys():
                    results[record_id] = EmbeddingStatus.FAILED
            
            with self._stats_lock:
                successful_count = sum(1 for status in results.values() if status == EmbeddingStatus.SUCCESS)
                self._operation_stats['stores'] += successful_count
                if successful_count > 0:
                    dimension = len(next(iter(processed_embeddings.values())))
                    self._update_dimension_stats(table, dimension)
        
        except Exception as e:
            logger.error(f"Error in batch store embeddings for {table}: {e}")
            for record_id in processed_embeddings.keys():
                results[record_id] = EmbeddingStatus.FAILED
            
            with self._stats_lock:
                self._operation_stats['errors'] += len(processed_embeddings)
        
        return results

    def get_embedding(self, table: str, record_id: str) -> Optional[List[float]]:
        """Retrieve embedding for a specific record."""
        start_time = time.time()
        
        try:
            if table not in self.VALID_TABLES:
                logger.error(f"Invalid table for embedding retrieval: {table}")
                return None
            
            result = self._execute_get_embedding(table, record_id)
            
            duration_ms = (time.time() - start_time) * 1000
            
            with self._stats_lock:
                if result is not None:
                    self._operation_stats['retrievals'] += 1
                else:
                    self._operation_stats['errors'] += 1
                
                self._operation_stats['total_duration_ms'] += duration_ms
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving embedding for {table}.{record_id}: {e}")
            with self._stats_lock:
                self._operation_stats['errors'] += 1
            return None

    def find_similar(self, table: str, embedding: Union[List[float], np.ndarray], 
                    limit: int = 10, similarity_threshold: float = 0.0,
                    additional_filters: Optional[Dict[str, Any]] = None,
                    include_distance: bool = True) -> List[SimilarityResult]:
        """Find similar records using vector similarity search."""
        start_time = time.time()
        
        try:
            if table not in self.VALID_TABLES:
                logger.error(f"Invalid table for similarity search: {table}")
                return []
            
            processed_embedding = self._process_embedding(embedding)
            if not processed_embedding:
                logger.error("Invalid embedding format for similarity search")
                return []
            
            results = self._execute_similarity_search(
                table, processed_embedding, limit, similarity_threshold, 
                additional_filters, include_distance
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            with self._stats_lock:
                self._operation_stats['searches'] += 1
                self._operation_stats['total_duration_ms'] += duration_ms
            
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search for {table}: {e}")
            with self._stats_lock:
                self._operation_stats['errors'] += 1
            return []

    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding operation statistics."""
        with self._stats_lock:
            stats = self._operation_stats.copy()
            stats['dimension_stats'] = self._dimension_stats.copy()
            stats['pgvector_available'] = self._pgvector_available
            
            # Calculate averages
            if stats['stores'] + stats['retrievals'] + stats['searches'] > 0:
                stats['avg_duration_ms'] = stats['total_duration_ms'] / (
                    stats['stores'] + stats['retrievals'] + stats['searches']
                )
            else:
                stats['avg_duration_ms'] = 0.0
            
            return stats

    def _check_pgvector_availability(self) -> bool:
        """Check if pgvector extension is available."""
        try:
            result = self.db_manager.execute_postgres_query(
                "SELECT 1 FROM pg_extension WHERE extname = 'vector'",
                fetchall=True
            )
            return len(result) > 0
        except Exception as e:
            logger.warning(f"Could not check pgvector availability: {e}")
            return False

    def _process_embedding(self, embedding: Union[List[float], np.ndarray]) -> Optional[List[float]]:
        """Process and validate embedding format."""
        try:
            if isinstance(embedding, np.ndarray):
                if embedding.ndim != 1:
                    logger.error(f"Expected 1D array, got {embedding.ndim}D")
                    return None
                return embedding.tolist()
            elif isinstance(embedding, list):
                # Validate all elements are numeric
                for item in embedding:
                    if not isinstance(item, (int, float)):
                        logger.error(f"Non-numeric value in embedding: {type(item)}")
                        return None
                return embedding
            else:
                logger.error(f"Unsupported embedding type: {type(embedding)}")
                return None
        except Exception as e:
            logger.error(f"Error processing embedding: {e}")
            return None

    def _validate_dimension(self, embedding: List[float]) -> bool:
        """Validate embedding dimensions."""
        dimension = len(embedding)
        
        # Check against expected dimension
        if hasattr(self, 'default_dimension') and self.default_dimension:
            if dimension != self.default_dimension:
                logger.warning(f"Embedding dimension {dimension} doesn't match expected {self.default_dimension}")
                return False
        
        # Check reasonable bounds
        if dimension < 1 or dimension > 10000:
            logger.error(f"Unreasonable embedding dimension: {dimension}")
            return False
        
        return True

    # Implementation methods (simplified versions of the original complex logic)
    def _execute_store_embedding(self, table: str, record_id: str, embedding: List[float],
                               metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Execute the actual embedding storage."""
        try:
            embedding_str = f"[{','.join(map(str, embedding))}]"
            
            if metadata:
                query = f"""
                INSERT INTO {table}_embeddings (record_id, embedding, metadata, created_at, updated_at)
                VALUES (%s, %s, %s, NOW(), NOW())
                ON CONFLICT (record_id) 
                DO UPDATE SET embedding = %s, metadata = %s, updated_at = NOW()
                """
                params = (record_id, embedding_str, metadata, embedding_str, metadata)
            else:
                query = f"""
                INSERT INTO {table}_embeddings (record_id, embedding, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
                ON CONFLICT (record_id) 
                DO UPDATE SET embedding = %s, updated_at = NOW()
                """
                params = (record_id, embedding_str, embedding_str)
            
            self.db_manager.execute_postgres_query(query, params, fetchall=False)
            return True
            
        except Exception as e:
            logger.error(f"Failed to store embedding: {e}")
            return False

    def _execute_get_embedding(self, table: str, record_id: str) -> Optional[List[float]]:
        """Execute embedding retrieval."""
        try:
            query = f"SELECT embedding FROM {table}_embeddings WHERE record_id = %s"
            result = self.db_manager.execute_postgres_query(query, (record_id,), fetchall=True)
            
            if result and len(result) > 0:
                embedding_str = result[0].get('embedding')
                if embedding_str:
                    # Parse the embedding string back to list
                    return eval(embedding_str)  # Simple parsing - could be improved
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve embedding: {e}")
            return None

    def _execute_similarity_search(self, table: str, embedding: List[float], limit: int,
                                 similarity_threshold: float, additional_filters: Optional[Dict[str, Any]],
                                 include_distance: bool) -> List[SimilarityResult]:
        """Execute vector similarity search."""
        try:
            embedding_str = f"[{','.join(map(str, embedding))}]"
            
            # Basic similarity search query (simplified)
            query = f"""
            SELECT r.*, e.embedding <-> %s as distance
            FROM {table} r
            JOIN {table}_embeddings e ON r.id = e.record_id
            WHERE e.embedding <-> %s < %s
            ORDER BY e.embedding <-> %s
            LIMIT %s
            """
            
            params = (embedding_str, embedding_str, 1.0 - similarity_threshold, embedding_str, limit)
            results = self.db_manager.execute_postgres_query(query, params, fetchall=True)
            
            similarity_results = []
            for row in results:
                similarity_score = 1.0 - row.get('distance', 1.0)  # Convert distance to similarity
                similarity_results.append(SimilarityResult(
                    record_id=str(row.get('id')),
                    similarity_score=similarity_score,
                    record_data=row,
                    distance=row.get('distance', 1.0)
                ))
            
            return similarity_results
            
        except Exception as e:
            logger.error(f"Failed to execute similarity search: {e}")
            return []

    def _execute_batch_store_embeddings(self, table: str, embeddings: Dict[str, List[float]],
                                      metadata: Optional[Dict[str, Dict[str, Any]]] = None) -> bool:
        """Execute batch embedding storage."""
        try:
            # Simple batch insert implementation
            for record_id, embedding in embeddings.items():
                record_metadata = metadata.get(record_id) if metadata else None
                if not self._execute_store_embedding(table, record_id, embedding, record_metadata):
                    return False
            return True
        except Exception as e:
            logger.error(f"Failed to batch store embeddings: {e}")
            return False

    def _update_dimension_stats(self, table: str, dimension: int) -> None:
        """Update dimension statistics."""
        if table not in self._dimension_stats:
            self._dimension_stats[table] = {}
        
        if dimension not in self._dimension_stats[table]:
            self._dimension_stats[table][dimension] = 0
        
        self._dimension_stats[table][dimension] += 1


class AnthropicService(BaseService):
    """
    Service for Anthropic Claude AI integration.
    
    Responsibilities:
    - Claude API integration
    - Tourism-specific prompt engineering
    - Fallback response generation
    - AI-powered content enhancement
    """

    def __init__(self, db_manager=None, config: Optional[Dict[str, Any]] = None):
        super().__init__(db_manager)
        self.config = config or {}
        self.api_key = self.config.get('api_key', '')
        self.model = self.config.get('model', 'claude-3-sonnet-20240229')
        self.max_tokens = self.config.get('max_tokens', 150)
        
        # Initialize Anthropic client if API key is available
        self.client = None
        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("Anthropic library not installed")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")

    def generate_response(self, prompt: str, max_tokens: Optional[int] = None, 
                         model: Optional[str] = None) -> Dict[str, Any]:
        """Generate response using Claude."""
        if not self.client:
            return self._get_fallback_response("API not available")
        
        try:
            response = self.client.messages.create(
                model=model or self.model,
                max_tokens=max_tokens or self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                "success": True,
                "content": response.content[0].text if response.content else "",
                "model": model or self.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens if hasattr(response, 'usage') else 0,
                    "output_tokens": response.usage.output_tokens if hasattr(response, 'usage') else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating response with Claude: {e}")
            return self._get_fallback_response(str(e))

    def create_egypt_tourism_prompt(self, user_message: str, language: str = "en", 
                                   context: Optional[Dict[str, Any]] = None) -> str:
        """Create tourism-specific prompt for Claude."""
        
        system_context = """You are an expert Egypt tourism assistant. You have extensive knowledge about:
- Egyptian attractions, monuments, and archaeological sites
- Hotels, restaurants, and accommodations across Egypt
- Transportation, practical travel information
- Egyptian culture, history, and customs
- Weather, best times to visit different regions
- Local customs, etiquette, and cultural sensitivity

Provide helpful, accurate, and culturally sensitive information about Egypt tourism."""

        if language == "ar":
            system_context += "\n\nPlease respond in Arabic."
        
        context_info = ""
        if context:
            active_entities = context.get('active_entities', {})
            if active_entities:
                context_info = f"\nContext: The user is currently interested in {active_entities}"
        
        prompt = f"{system_context}\n\nUser Question: {user_message}{context_info}\n\nResponse:"
        
        return prompt

    def generate_fallback_response(self, query: str, language: str = "en", 
                                 session_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate fallback response when other systems fail."""
        
        prompt = self.create_egypt_tourism_prompt(query, language, session_data)
        
        response = self.generate_response(prompt, max_tokens=200)
        
        if response.get('success'):
            return {
                "type": "text",
                "content": response.get('content', ''),
                "source": "ai_fallback",
                "language": language,
                "suggestions": []
            }
        else:
            return self._get_generic_fallback_response(language)

    def _get_fallback_response(self, error: str) -> Dict[str, Any]:
        """Get fallback response when API fails."""
        return {
            "success": False,
            "content": "",
            "error": error,
            "fallback": True
        }

    def _get_generic_fallback_response(self, language: str) -> Dict[str, Any]:
        """Get generic fallback response."""
        if language == "ar":
            content = "أعتذر، لا أستطيع الإجابة على استفسارك في الوقت الحالي. يرجى المحاولة مرة أخرى لاحقاً."
        else:
            content = "I apologize, but I'm unable to answer your question at the moment. Please try again later."
        
        return {
            "type": "text", 
            "content": content,
            "source": "generic_fallback",
            "language": language,
            "suggestions": []
        }


class AIService:
    """
    Unified AI Service that combines embedding and language model functionality.
    
    This is the main entry point for all AI-related operations.
    """
    
    def __init__(self, db_manager=None, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize sub-services
        self.embedding_service = EmbeddingService(
            db_manager=db_manager,
            default_dimension=self.config.get('embedding_dimension', 1536)
        )
        
        self.anthropic_service = AnthropicService(
            db_manager=db_manager,
            config=self.config.get('anthropic', {})
        )
    
    def store_embedding(self, table: str, record_id: str, embedding: Union[List[float], np.ndarray],
                       metadata: Optional[Dict[str, Any]] = None) -> EmbeddingStatus:
        """Store embedding (delegates to embedding service)."""
        return self.embedding_service.store_embedding(table, record_id, embedding, metadata)
    
    def find_similar(self, table: str, embedding: Union[List[float], np.ndarray], 
                    limit: int = 10, **kwargs) -> List[SimilarityResult]:
        """Find similar records (delegates to embedding service)."""
        return self.embedding_service.find_similar(table, embedding, limit, **kwargs)
    
    def generate_ai_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate AI response (delegates to anthropic service)."""
        return self.anthropic_service.generate_response(prompt, **kwargs)
    
    def generate_fallback_response(self, query: str, language: str = "en", 
                                 session_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate fallback response (delegates to anthropic service)."""
        return self.anthropic_service.generate_fallback_response(query, language, session_data)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get combined AI service statistics."""
        return {
            "embedding_stats": self.embedding_service.get_embedding_stats(),
            "anthropic_available": self.anthropic_service.client is not None
        }