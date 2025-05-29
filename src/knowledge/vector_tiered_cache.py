"""
Vector Tiered Cache implementation for the Egypt Tourism Chatbot.

This module provides a specialized tiered caching system for vector search operations.
"""
import json
import logging
import numpy as np
from typing import Any, Dict, List, Optional, Union

from src.utils.tiered_cache import TieredCache

logger = logging.getLogger(__name__)

class VectorTieredCache(TieredCache):
    """
    Specialized tiered cache for vector search operations.
    
    This class extends the TieredCache class to provide specialized functionality
    for caching vector search results.
    """
    
    def __init__(self, redis_uri: Optional[str] = None, ttl: int = 3600, max_size: int = 1000):
        """
        Initialize the vector tiered cache.
        
        Args:
            redis_uri: Redis URI for distributed caching
            ttl: Time to live in seconds (default: 1 hour)
            max_size: Maximum size of in-memory cache
        """
        super().__init__(
            cache_prefix="vector_search",
            redis_uri=redis_uri,
            ttl=ttl,
            max_size=max_size
        )
    
    def _process_embedding(self, embedding: Union[List[float], np.ndarray, str]) -> List[float]:
        """
        Process an embedding to ensure it's in a consistent format.
        
        Args:
            embedding: Vector embedding in various formats
            
        Returns:
            List[float]: Processed embedding
        """
        # Parse embedding if it's a string
        if isinstance(embedding, str):
            try:
                embedding = json.loads(embedding)
            except json.JSONDecodeError:
                # If JSON parsing fails, try manual parsing
                embedding_values = embedding.strip('[]').split(',')
                embedding = [float(val) for val in embedding_values]
        
        # Convert numpy array to list if needed
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        
        return embedding
    
    def _get_embedding_signature(self, embedding: Union[List[float], np.ndarray, str]) -> Dict[str, Any]:
        """
        Get a signature for an embedding that can be used in cache keys.
        
        Args:
            embedding: Vector embedding
            
        Returns:
            Dict[str, Any]: Embedding signature
        """
        processed_embedding = self._process_embedding(embedding)
        
        # Only include a few dimensions to avoid excessively long keys
        # This is a tradeoff between collision prevention and key size
        embedding_sample = processed_embedding[:10] if isinstance(processed_embedding, list) else []
        
        return {
            "embedding_sample": embedding_sample,
            "embedding_len": len(processed_embedding) if hasattr(processed_embedding, '__len__') else 0,
            "embedding_sum": sum(processed_embedding) if isinstance(processed_embedding, list) else 0
        }
    
    def get_vector_search_results(self,
                                 table_name: str,
                                 embedding: Union[List[float], np.ndarray, str],
                                 filters: Optional[Dict[str, Any]] = None,
                                 limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached vector search results.
        
        Args:
            table_name: Database table name
            embedding: Vector embedding
            filters: Additional filters
            limit: Maximum number of results
            
        Returns:
            List of results if found in cache, None otherwise
        """
        # Create key parts
        key_parts = {
            "table": table_name,
            "filters": filters or {},
            "limit": limit,
            **self._get_embedding_signature(embedding)
        }
        
        # Get from cache
        return self.get(key_parts)
    
    def set_vector_search_results(self,
                                 table_name: str,
                                 embedding: Union[List[float], np.ndarray, str],
                                 results: List[Dict[str, Any]],
                                 filters: Optional[Dict[str, Any]] = None,
                                 limit: int = 10) -> bool:
        """
        Cache vector search results.
        
        Args:
            table_name: Database table name
            embedding: Vector embedding
            results: Search results to cache
            filters: Additional filters
            limit: Maximum number of results
            
        Returns:
            bool: Success status
        """
        # Create key parts
        key_parts = {
            "table": table_name,
            "filters": filters or {},
            "limit": limit,
            **self._get_embedding_signature(embedding)
        }
        
        # Set in cache
        return self.set(key_parts, results)
    
    def invalidate_table(self, table_name: str) -> bool:
        """
        Invalidate all cached results for a specific table.
        
        Args:
            table_name: Database table name
            
        Returns:
            bool: Success status
        """
        return self.invalidate(f"table:{table_name}")
    
    def invalidate_all_vector_searches(self) -> bool:
        """
        Invalidate all vector search results.
        
        Returns:
            bool: Success status
        """
        return self.clear()
