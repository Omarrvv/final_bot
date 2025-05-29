"""
Tests for the query cache implementation.

This module contains tests for the QueryCache class.
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from src.utils.query_cache import QueryCache

class TestQueryCache:
    """Test suite for the QueryCache class."""
    
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
    def query_cache(self, mock_redis):
        """Create a QueryCache instance with a mock Redis client."""
        return QueryCache(
            redis_uri="redis://localhost:6379/0",
            ttl=3600,
            max_size=100
        )
    
    def test_init(self, query_cache):
        """Test initialization."""
        assert query_cache.redis_client is not None
        assert query_cache.ttl == 3600
        assert query_cache.cache_prefix == "query_cache"
    
    def test_get_query_results(self, query_cache):
        """Test getting query results."""
        # Mock the get method
        query_cache.get = MagicMock(return_value=["result1", "result2"])
        
        results = query_cache.get_query_results(
            query_type="search",
            query_params={"name": "test"},
            table_name="attractions"
        )
        
        assert results == ["result1", "result2"]
        query_cache.get.assert_called_once()
    
    def test_set_query_results(self, query_cache):
        """Test setting query results."""
        # Mock the set method
        query_cache.set = MagicMock(return_value=True)
        
        result = query_cache.set_query_results(
            query_type="search",
            query_params={"name": "test"},
            results=["result1", "result2"],
            table_name="attractions"
        )
        
        assert result is True
        query_cache.set.assert_called_once()
    
    def test_invalidate_table(self, query_cache):
        """Test invalidating a table."""
        # Mock the invalidate method
        query_cache.invalidate = MagicMock(return_value=True)
        
        result = query_cache.invalidate_table("attractions")
        
        assert result is True
        query_cache.invalidate.assert_called_once_with("table:attractions")
    
    def test_invalidate_query_type(self, query_cache):
        """Test invalidating a query type."""
        # Mock the invalidate method
        query_cache.invalidate = MagicMock(return_value=True)
        
        result = query_cache.invalidate_query_type("search")
        
        assert result is True
        query_cache.invalidate.assert_called_once_with("query_type:search")
    
    def test_invalidate_all_queries(self, query_cache):
        """Test invalidating all queries."""
        # Mock the clear method
        query_cache.clear = MagicMock(return_value=True)
        
        result = query_cache.invalidate_all_queries()
        
        assert result is True
        query_cache.clear.assert_called_once()
    
    def test_get_search_results(self, query_cache):
        """Test getting search results."""
        # Mock the get_query_results method
        query_cache.get_query_results = MagicMock(return_value=["result1", "result2"])
        
        results = query_cache.get_search_results(
            table_name="attractions",
            query={"name": "test"},
            filters={"type": "museum"},
            limit=10,
            offset=0,
            language="en"
        )
        
        assert results == ["result1", "result2"]
        query_cache.get_query_results.assert_called_once()
    
    def test_set_search_results(self, query_cache):
        """Test setting search results."""
        # Mock the set_query_results method
        query_cache.set_query_results = MagicMock(return_value=True)
        
        result = query_cache.set_search_results(
            table_name="attractions",
            results=["result1", "result2"],
            query={"name": "test"},
            filters={"type": "museum"},
            limit=10,
            offset=0,
            language="en"
        )
        
        assert result is True
        query_cache.set_query_results.assert_called_once()
    
    def test_get_record(self, query_cache):
        """Test getting a record."""
        # Mock the get_query_results method
        query_cache.get_query_results = MagicMock(return_value={"id": "test", "name": "Test"})
        
        result = query_cache.get_record(
            table_name="attractions",
            record_id="test"
        )
        
        assert result == {"id": "test", "name": "Test"}
        query_cache.get_query_results.assert_called_once_with(
            query_type="get",
            query_params={"id": "test"},
            table_name="attractions"
        )
    
    def test_set_record(self, query_cache):
        """Test setting a record."""
        # Mock the set_query_results method
        query_cache.set_query_results = MagicMock(return_value=True)
        
        result = query_cache.set_record(
            table_name="attractions",
            record_id="test",
            record={"id": "test", "name": "Test"}
        )
        
        assert result is True
        query_cache.set_query_results.assert_called_once_with(
            query_type="get",
            query_params={"id": "test"},
            results={"id": "test", "name": "Test"},
            table_name="attractions"
        )
