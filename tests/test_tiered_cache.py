"""
Tests for the tiered cache implementation.

This module contains tests for the TieredCache and VectorTieredCache classes.
"""
import json
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from src.utils.tiered_cache import TieredCache
from src.knowledge.vector_tiered_cache import VectorTieredCache

class TestTieredCache:
    """Test suite for the TieredCache class."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        with patch('src.utils.tiered_cache.redis') as mock_redis:
            # Configure the mock
            mock_redis.REDIS_AVAILABLE = True
            mock_redis_client = MagicMock()
            mock_redis.from_url.return_value = mock_redis_client
            yield mock_redis_client
    
    @pytest.fixture
    def tiered_cache(self, mock_redis):
        """Create a TieredCache instance with a mock Redis client."""
        return TieredCache(
            cache_prefix="test_cache",
            redis_uri="redis://localhost:6379/0",
            ttl=3600,
            max_size=100
        )
    
    def test_init_with_redis(self, mock_redis):
        """Test initialization with Redis."""
        cache = TieredCache(
            cache_prefix="test_cache",
            redis_uri="redis://localhost:6379/0",
            ttl=3600,
            max_size=100
        )
        assert cache.redis_client is not None
        assert cache.ttl == 3600
        assert cache.cache_prefix == "test_cache"
    
    def test_init_without_redis(self):
        """Test initialization without Redis."""
        with patch('src.utils.tiered_cache.redis', REDIS_AVAILABLE=False):
            cache = TieredCache(
                cache_prefix="test_cache",
                redis_uri=None,
                ttl=3600,
                max_size=100
            )
            assert cache.redis_client is None
            assert cache.ttl == 3600
            assert cache.cache_prefix == "test_cache"
    
    def test_generate_key(self, tiered_cache):
        """Test key generation."""
        key_parts = {"a": 1, "b": "test", "c": [1, 2, 3]}
        key = tiered_cache._generate_key(key_parts)
        assert key.startswith("test_cache:")
        assert len(key) > len("test_cache:")
    
    def test_get_from_memory_cache(self, tiered_cache):
        """Test getting an item from the memory cache."""
        key_parts = {"a": 1, "b": "test"}
        cache_key = tiered_cache._generate_key(key_parts)
        tiered_cache.memory_cache[cache_key] = "test_value"
        
        result = tiered_cache.get(key_parts)
        assert result == "test_value"
    
    def test_get_from_redis(self, tiered_cache, mock_redis):
        """Test getting an item from Redis."""
        key_parts = {"a": 1, "b": "test"}
        cache_key = tiered_cache._generate_key(key_parts)
        
        # Configure the mock to return a value
        mock_redis.get.return_value = json.dumps("test_value")
        
        # Memory cache miss, Redis hit
        result = tiered_cache.get(key_parts)
        assert result == "test_value"
        mock_redis.get.assert_called_once_with(cache_key)
    
    def test_get_cache_miss(self, tiered_cache, mock_redis):
        """Test cache miss."""
        key_parts = {"a": 1, "b": "test"}
        
        # Configure the mock to return None
        mock_redis.get.return_value = None
        
        # Memory cache miss, Redis miss
        result = tiered_cache.get(key_parts)
        assert result is None
    
    def test_set(self, tiered_cache, mock_redis):
        """Test setting an item in the cache."""
        key_parts = {"a": 1, "b": "test"}
        cache_key = tiered_cache._generate_key(key_parts)
        
        # Set the value
        result = tiered_cache.set(key_parts, "test_value")
        assert result is True
        
        # Check memory cache
        assert tiered_cache.memory_cache[cache_key] == "test_value"
        
        # Check Redis
        mock_redis.setex.assert_called_once_with(
            cache_key, 
            tiered_cache.ttl, 
            json.dumps("test_value")
        )
    
    def test_invalidate(self, tiered_cache, mock_redis):
        """Test invalidating cache entries."""
        # Add some items to the memory cache
        tiered_cache.memory_cache["test_cache:abc"] = "value1"
        tiered_cache.memory_cache["test_cache:def"] = "value2"
        
        # Configure the mock to return some keys
        mock_redis.keys.return_value = ["test_cache:abc", "test_cache:def"]
        
        # Invalidate the cache
        result = tiered_cache.invalidate("a")
        assert result is True
        
        # Check Redis
        mock_redis.keys.assert_called_once_with("test_cache:a*")
        mock_redis.delete.assert_called_once_with("test_cache:abc", "test_cache:def")
    
    def test_clear(self, tiered_cache, mock_redis):
        """Test clearing the cache."""
        # Add some items to the memory cache
        tiered_cache.memory_cache["test_cache:abc"] = "value1"
        tiered_cache.memory_cache["test_cache:def"] = "value2"
        
        # Configure the mock to return some keys
        mock_redis.keys.return_value = ["test_cache:abc", "test_cache:def"]
        
        # Clear the cache
        result = tiered_cache.clear()
        assert result is True
        
        # Check memory cache
        assert len(tiered_cache.memory_cache) == 0
        
        # Check Redis
        mock_redis.keys.assert_called_once_with("test_cache:*")
        mock_redis.delete.assert_called_once_with("test_cache:abc", "test_cache:def")
    
    def test_contains(self, tiered_cache):
        """Test the __contains__ method."""
        key_parts = {"a": 1, "b": "test"}
        cache_key = tiered_cache._generate_key(key_parts)
        tiered_cache.memory_cache[cache_key] = "test_value"
        
        assert key_parts in tiered_cache
    
    def test_getitem(self, tiered_cache):
        """Test the __getitem__ method."""
        key_parts = {"a": 1, "b": "test"}
        cache_key = tiered_cache._generate_key(key_parts)
        tiered_cache.memory_cache[cache_key] = "test_value"
        
        assert tiered_cache[key_parts] == "test_value"
        
        # Test KeyError
        with pytest.raises(KeyError):
            tiered_cache[{"c": 3}]
    
    def test_setitem(self, tiered_cache):
        """Test the __setitem__ method."""
        key_parts = {"a": 1, "b": "test"}
        cache_key = tiered_cache._generate_key(key_parts)
        
        tiered_cache[key_parts] = "test_value"
        assert tiered_cache.memory_cache[cache_key] == "test_value"


class TestVectorTieredCache:
    """Test suite for the VectorTieredCache class."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        with patch('src.utils.tiered_cache.redis') as mock_redis:
            # Configure the mock
            mock_redis.REDIS_AVAILABLE = True
            mock_redis_client = MagicMock()
            mock_redis.from_url.return_value = mock_redis_client
            yield mock_redis_client
    
    @pytest.fixture
    def vector_cache(self, mock_redis):
        """Create a VectorTieredCache instance with a mock Redis client."""
        return VectorTieredCache(
            redis_uri="redis://localhost:6379/0",
            ttl=3600,
            max_size=100
        )
    
    def test_init(self, vector_cache):
        """Test initialization."""
        assert vector_cache.redis_client is not None
        assert vector_cache.ttl == 3600
        assert vector_cache.cache_prefix == "vector_search"
    
    def test_process_embedding_list(self, vector_cache):
        """Test processing a list embedding."""
        embedding = [0.1, 0.2, 0.3]
        result = vector_cache._process_embedding(embedding)
        assert result == embedding
    
    def test_process_embedding_numpy(self, vector_cache):
        """Test processing a numpy array embedding."""
        embedding = np.array([0.1, 0.2, 0.3])
        result = vector_cache._process_embedding(embedding)
        assert isinstance(result, list)
        assert result == [0.1, 0.2, 0.3]
    
    def test_process_embedding_string(self, vector_cache):
        """Test processing a string embedding."""
        embedding = "[0.1, 0.2, 0.3]"
        result = vector_cache._process_embedding(embedding)
        assert isinstance(result, list)
        assert result == [0.1, 0.2, 0.3]
    
    def test_get_embedding_signature(self, vector_cache):
        """Test getting an embedding signature."""
        embedding = [0.1, 0.2, 0.3]
        signature = vector_cache._get_embedding_signature(embedding)
        assert "embedding_sample" in signature
        assert "embedding_len" in signature
        assert "embedding_sum" in signature
        assert signature["embedding_len"] == 3
        assert signature["embedding_sum"] == 0.6
    
    def test_get_vector_search_results(self, vector_cache):
        """Test getting vector search results."""
        # Mock the get method
        vector_cache.get = MagicMock(return_value=["result1", "result2"])
        
        results = vector_cache.get_vector_search_results(
            table_name="attractions",
            embedding=[0.1, 0.2, 0.3],
            filters={"type": "museum"},
            limit=10
        )
        
        assert results == ["result1", "result2"]
        vector_cache.get.assert_called_once()
    
    def test_set_vector_search_results(self, vector_cache):
        """Test setting vector search results."""
        # Mock the set method
        vector_cache.set = MagicMock(return_value=True)
        
        result = vector_cache.set_vector_search_results(
            table_name="attractions",
            embedding=[0.1, 0.2, 0.3],
            results=["result1", "result2"],
            filters={"type": "museum"},
            limit=10
        )
        
        assert result is True
        vector_cache.set.assert_called_once()
    
    def test_invalidate_table(self, vector_cache):
        """Test invalidating a table."""
        # Mock the invalidate method
        vector_cache.invalidate = MagicMock(return_value=True)
        
        result = vector_cache.invalidate_table("attractions")
        
        assert result is True
        vector_cache.invalidate.assert_called_once_with("table:attractions")
    
    def test_invalidate_all_vector_searches(self, vector_cache):
        """Test invalidating all vector searches."""
        # Mock the clear method
        vector_cache.clear = MagicMock(return_value=True)
        
        result = vector_cache.invalidate_all_vector_searches()
        
        assert result is True
        vector_cache.clear.assert_called_once()
