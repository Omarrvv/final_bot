# src/utils/cache.py
"""
Cache implementation for the Egypt Tourism Chatbot.
Provides an LRU (Least Recently Used) cache to improve response time.
"""
import logging
import time
from typing import Dict, Any, Optional, List
from collections import OrderedDict

logger = logging.getLogger(__name__)

class LRUCache:
    """
    Least Recently Used (LRU) cache implementation.
    Automatically evicts least recently used items when the cache reaches its maximum size.
    """
    
    def __init__(self, max_size: int = 1000, ttl: Optional[int] = None):
        """
        Initialize the LRU cache.
        
        Args:
            max_size (int): Maximum number of items to store
            ttl (int, optional): Time to live in seconds
        """
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
        self.cache = OrderedDict()  # {key: (value, timestamp)}
        
        logger.info(f"LRU Cache initialized with max_size={max_size}, ttl={ttl}")
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache and is not expired."""
        if key not in self.cache:
            return False
        
        # Check if item is expired
        if self.ttl is not None:
            _, timestamp = self.cache[key]
            if time.time() - timestamp > self.ttl:
                # Remove expired item
                del self.cache[key]
                return False
        
        # Move item to the end (most recently used)
        self.cache.move_to_end(key)
        return True
    
    def __getitem__(self, key: str) -> Any:
        """Get item from cache if it exists and is not expired."""
        if key not in self:
            raise KeyError(key)
        
        # Return the value (not the timestamp)
        value, _ = self.cache[key]
        return value
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Add item to cache, evicting least recently used item if necessary."""
        # Add or update item
        self.cache[key] = (value, time.time())
        
        # Move to the end (most recently used)
        self.cache.move_to_end(key)
        
        # Evict least recently used item if cache is too large
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)  # Remove from the beginning (least recently used)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get item from cache with a default if not found."""
        try:
            return self[key]
        except KeyError:
            return default
    
    def clear(self) -> None:
        """Clear all items from cache."""
        self.cache.clear()
    
    def remove(self, key: str) -> bool:
        """Remove an item from cache if it exists."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def items(self) -> List[tuple]:
        """Get all non-expired (key, value) pairs."""
        if self.ttl is None:
            # No expiration, return all items
            return [(k, v) for k, (v, _) in self.cache.items()]
        
        current_time = time.time()
        valid_items = []
        expired_keys = []
        
        for key, (value, timestamp) in self.cache.items():
            if current_time - timestamp > self.ttl:
                expired_keys.append(key)
            else:
                valid_items.append((key, value))
        
        # Remove expired items
        for key in expired_keys:
            del self.cache[key]
        
        return valid_items
    
    def keys(self) -> List[str]:
        """Get all non-expired keys."""
        return [k for k, _ in self.items()]
    
    def values(self) -> List[Any]:
        """Get all non-expired values."""
        return [v for _, v in self.items()]
    
    def __len__(self) -> int:
        """Get the number of non-expired items in the cache."""
        if self.ttl is None:
            return len(self.cache)
        
        current_time = time.time()
        valid_count = 0
        expired_keys = []
        
        for key, (_, timestamp) in self.cache.items():
            if current_time - timestamp > self.ttl:
                expired_keys.append(key)
            else:
                valid_count += 1
        
        # Remove expired items
        for key in expired_keys:
            del self.cache[key]
        
        return valid_count

class Cache:
    """Simple in-memory cache with TTL."""
    def __init__(self, ttl_seconds=3600):
        self.cache = {}
        self.ttl = ttl_seconds
    
    @staticmethod
    def create_lru_cache(max_size: int = 1000, ttl: Optional[int] = None) -> LRUCache:
        """Create an LRU cache."""
        return LRUCache(max_size=max_size, ttl=ttl)