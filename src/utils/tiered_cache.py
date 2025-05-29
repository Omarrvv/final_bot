"""
Tiered Cache implementation for the Egypt Tourism Chatbot.

This module provides a tiered caching system that combines in-memory and Redis caching
to improve response time and reduce database load.
"""
import json
import hashlib
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union, Callable

# Try to import Redis, fall back to LRUCache if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from src.utils.cache import LRUCache

logger = logging.getLogger(__name__)

class TieredCache:
    """
    Tiered cache implementation that combines in-memory and Redis caching.
    
    This class provides a two-level caching system:
    1. Fast in-memory LRU cache for frequently accessed items
    2. Redis cache for distributed caching across multiple instances
    
    If Redis is not available or fails, it falls back to the in-memory cache.
    """
    
    def __init__(self, 
                cache_prefix: str,
                redis_uri: Optional[str] = None, 
                ttl: int = 3600, 
                max_size: int = 1000,
                serialize_fn: Optional[Callable] = None,
                deserialize_fn: Optional[Callable] = None):
        """
        Initialize the tiered cache.
        
        Args:
            cache_prefix: Prefix for cache keys to avoid collisions
            redis_uri: Redis URI for distributed caching
            ttl: Time to live in seconds (default: 1 hour)
            max_size: Maximum size of in-memory cache
            serialize_fn: Function to serialize data before storing in Redis
            deserialize_fn: Function to deserialize data after retrieving from Redis
        """
        self.ttl = ttl
        self.redis_client = None
        self.memory_cache = LRUCache(max_size=max_size, ttl=ttl)
        self.cache_prefix = cache_prefix
        
        # Use custom serialization functions or defaults
        self.serialize_fn = serialize_fn or json.dumps
        self.deserialize_fn = deserialize_fn or json.loads
        
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
                logger.info(f"Tiered cache initialized with Redis: {redis_uri}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis ({redis_uri}): {str(e)}")
                logger.info("Falling back to in-memory cache only")
                self.redis_client = None
        else:
            logger.info("Tiered cache initialized with in-memory cache only")
    
    def _generate_key(self, key_parts: Dict[str, Any]) -> str:
        """
        Generate a cache key from the provided parts.
        
        Args:
            key_parts: Dictionary of key parts to include in the key
            
        Returns:
            str: Cache key
        """
        # Generate a stable JSON representation
        param_str = json.dumps(key_parts, sort_keys=True)
        
        # Hash the parameters to create a compact key
        key_hash = hashlib.md5(param_str.encode()).hexdigest()
        
        # Include the cache prefix
        return f"{self.cache_prefix}:{key_hash}"
    
    def get(self, key_parts: Dict[str, Any]) -> Optional[Any]:
        """
        Get an item from the cache.
        
        Args:
            key_parts: Dictionary of key parts to generate the cache key
            
        Returns:
            The cached item if found, None otherwise
        """
        cache_key = self._generate_key(key_parts)
        
        # Try memory cache first (fastest)
        value = self.memory_cache.get(cache_key)
        if value is not None:
            logger.debug(f"Memory cache hit for {cache_key}")
            return value
        
        # Try Redis if available
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    # Deserialize the data
                    value = self.deserialize_fn(cached_data)
                    
                    # Update memory cache for faster access next time
                    self.memory_cache[cache_key] = value
                    
                    logger.debug(f"Redis cache hit for {cache_key}")
                    return value
            except Exception as e:
                logger.warning(f"Redis cache get error: {str(e)}")
        
        return None
    
    def set(self, key_parts: Dict[str, Any], value: Any) -> bool:
        """
        Set an item in the cache.
        
        Args:
            key_parts: Dictionary of key parts to generate the cache key
            value: Value to cache
            
        Returns:
            bool: Success status
        """
        cache_key = self._generate_key(key_parts)
        
        # Always update memory cache for fast access
        self.memory_cache[cache_key] = value
        
        # Update Redis if available
        if self.redis_client:
            try:
                # Serialize the data
                serialized_data = self.serialize_fn(value)
                
                # Store in Redis with TTL
                self.redis_client.setex(cache_key, self.ttl, serialized_data)
                logger.debug(f"Cached in Redis: {cache_key}")
                return True
            except Exception as e:
                logger.warning(f"Redis cache set error: {str(e)}")
                return False
        
        logger.debug(f"Cached in memory: {cache_key}")
        return True
    
    def invalidate(self, pattern: str) -> bool:
        """
        Invalidate cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match cache keys
            
        Returns:
            bool: Success status
        """
        pattern_with_prefix = f"{self.cache_prefix}:{pattern}*"
        
        # Clear matching keys from Redis
        if self.redis_client:
            try:
                # Find all matching keys
                keys = self.redis_client.keys(pattern_with_prefix)
                
                # Delete matching keys
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} Redis cache entries for pattern: {pattern}")
            except Exception as e:
                logger.warning(f"Redis cache invalidation error: {str(e)}")
        
        # Clear matching keys from memory cache
        keys_to_remove = []
        for key in self.memory_cache.keys():
            if pattern in key:
                keys_to_remove.append(key)
        
        # Remove matching keys
        for key in keys_to_remove:
            self.memory_cache.remove(key)
        
        logger.info(f"Invalidated {len(keys_to_remove)} memory cache entries for pattern: {pattern}")
        
        return True
    
    def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            bool: Success status
        """
        # Clear Redis cache
        if self.redis_client:
            try:
                # Find all cache keys with this prefix
                keys = self.redis_client.keys(f"{self.cache_prefix}:*")
                
                # Delete all matching keys
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Cleared {len(keys)} entries from Redis cache")
            except Exception as e:
                logger.warning(f"Redis cache clear error: {str(e)}")
        
        # Clear memory cache
        self.memory_cache.clear()
        logger.info("Cleared memory cache")
        
        return True
    
    def __contains__(self, key_parts: Dict[str, Any]) -> bool:
        """
        Check if an item is in the cache.
        
        Args:
            key_parts: Dictionary of key parts to generate the cache key
            
        Returns:
            bool: True if the item is in the cache, False otherwise
        """
        return self.get(key_parts) is not None
    
    def __getitem__(self, key_parts: Dict[str, Any]) -> Any:
        """
        Get an item from the cache.
        
        Args:
            key_parts: Dictionary of key parts to generate the cache key
            
        Returns:
            The cached item
            
        Raises:
            KeyError: If the item is not in the cache
        """
        value = self.get(key_parts)
        if value is None:
            raise KeyError(f"Key not found: {key_parts}")
        return value
    
    def __setitem__(self, key_parts: Dict[str, Any], value: Any) -> None:
        """
        Set an item in the cache.
        
        Args:
            key_parts: Dictionary of key parts to generate the cache key
            value: Value to cache
        """
        self.set(key_parts, value)
