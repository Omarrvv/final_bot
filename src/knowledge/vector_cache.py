# src/knowledge/vector_cache.py
"""
Vector Search Cache Module for the Egypt Tourism Chatbot.
Provides caching for vector search results to improve response time and reduce database load.
"""
import json
import hashlib
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

# Try to import Redis, fall back to LRUCache if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from src.utils.cache import LRUCache

logger = logging.getLogger(__name__)

class VectorSearchCache:
    """
    Cache for vector search results, with support for Redis or in-memory LRU cache.
    """
    
    def __init__(self, redis_uri: Optional[str] = None, ttl: int = 3600, max_size: int = 1000):
        """
        Initialize the vector search cache.
        
        Args:
            redis_uri (str, optional): Redis URI for distributed caching
            ttl (int): Time to live in seconds (default: 1 hour)
            max_size (int): Maximum size of in-memory cache (only used if Redis not available)
        """
        self.ttl = ttl
        self.redis_client = None
        self.local_cache = LRUCache(max_size=max_size, ttl=ttl)
        self.cache_prefix = "vector_search:"
        
        # Initialize Redis if URI provided and Redis is available
        if redis_uri and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    redis_uri,
                    decode_responses=True,
                    socket_timeout=2.0
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"Vector search cache initialized with Redis: {redis_uri}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis ({redis_uri}): {str(e)}")
                logger.info("Falling back to in-memory cache")
                self.redis_client = None
        else:
            logger.info("Vector search cache initialized with in-memory LRU cache")
    
    def _generate_cache_key(self, 
                           table_name: str, 
                           embedding: Union[List[float], np.ndarray],
                           filters: Optional[Dict[str, Any]] = None,
                           limit: int = 10) -> str:
        """
        Generate a cache key for vector search parameters.
        
        Args:
            table_name: Database table name
            embedding: Vector embedding
            filters: Additional filters
            limit: Maximum number of results
            
        Returns:
            str: Cache key
        """
        # Convert numpy array to list if needed
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        
        # Only include a few dimensions to avoid excessively long keys
        # This is a tradeoff between collision prevention and key size
        embedding_sample = embedding[:10]
        
        # Create a dictionary of the parameters for stable serialization
        params = {
            "table": table_name,
            "embedding_sample": embedding_sample,
            "embedding_len": len(embedding),  # Include full length for uniqueness
            "embedding_sum": sum(embedding),  # Include sum for uniqueness
            "filters": filters or {},
            "limit": limit
        }
        
        # Generate a stable JSON representation
        param_str = json.dumps(params, sort_keys=True)
        
        # Hash the parameters to create a compact key
        key_hash = hashlib.md5(param_str.encode()).hexdigest()
        
        return f"{self.cache_prefix}{key_hash}"
    
    def get(self, 
           table_name: str, 
           embedding: Union[List[float], np.ndarray],
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
        cache_key = self._generate_cache_key(table_name, embedding, filters, limit)
        
        # Try Redis first if available
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    results = json.loads(cached_data)
                    logger.debug(f"Redis cache hit for {cache_key}")
                    return results
            except Exception as e:
                logger.warning(f"Redis cache get error: {str(e)}")
                # Fall back to local cache
        
        # Try local cache
        results = self.local_cache.get(cache_key)
        if results:
            logger.debug(f"Local cache hit for {cache_key}")
            return results
        
        return None
    
    def set(self, 
           table_name: str, 
           embedding: Union[List[float], np.ndarray],
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
        cache_key = self._generate_cache_key(table_name, embedding, filters, limit)
        
        # Always update local cache for fast access
        self.local_cache[cache_key] = results
        
        # Update Redis if available
        if self.redis_client:
            try:
                serialized_results = json.dumps(results)
                self.redis_client.setex(cache_key, self.ttl, serialized_results)
                logger.debug(f"Cached in Redis: {cache_key}")
                return True
            except Exception as e:
                logger.warning(f"Redis cache set error: {str(e)}")
                return False
        
        logger.debug(f"Cached in local memory: {cache_key}")
        return True
    
    def invalidate(self, table_name: str) -> bool:
        """
        Invalidate all cached results for a specific table.
        Call this when table data changes.
        
        Args:
            table_name: Database table name
            
        Returns:
            bool: Success status
        """
        # Create a pattern for all keys related to this table
        pattern = f"{self.cache_prefix}*"
        
        # Clear matching keys from Redis
        if self.redis_client:
            try:
                # Find all matching keys
                keys = self.redis_client.keys(pattern)
                
                # Delete matching keys
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} Redis cache entries for table: {table_name}")
            except Exception as e:
                logger.warning(f"Redis cache invalidation error: {str(e)}")
        
        # Clear local cache (more aggressive, clears everything)
        # This is because we can't easily filter by table in the local cache
        self.local_cache.clear()
        logger.info(f"Invalidated local cache for table: {table_name}")
        
        return True
    
    def clear(self) -> bool:
        """
        Clear all cached vector search results.
        
        Returns:
            bool: Success status
        """
        # Clear Redis cache
        if self.redis_client:
            try:
                # Find all vector search cache keys
                keys = self.redis_client.keys(f"{self.cache_prefix}*")
                
                # Delete all matching keys
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Cleared {len(keys)} entries from Redis vector search cache")
            except Exception as e:
                logger.warning(f"Redis cache clear error: {str(e)}")
        
        # Clear local cache
        self.local_cache.clear()
        logger.info("Cleared local vector search cache")
        
        return True