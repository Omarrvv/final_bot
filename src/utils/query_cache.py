"""
Query Cache implementation for the Egypt Tourism Chatbot.

This module provides a specialized tiered caching system for database query results.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from src.utils.tiered_cache import TieredCache

logger = logging.getLogger(__name__)

class QueryCache(TieredCache):
    """
    Specialized tiered cache for database query results.
    
    This class extends the TieredCache class to provide specialized functionality
    for caching database query results.
    """
    
    def __init__(self, redis_uri: Optional[str] = None, ttl: int = 3600, max_size: int = 1000):
        """
        Initialize the query cache.
        
        Args:
            redis_uri: Redis URI for distributed caching
            ttl: Time to live in seconds (default: 1 hour)
            max_size: Maximum size of in-memory cache
        """
        super().__init__(
            cache_prefix="query_cache",
            redis_uri=redis_uri,
            ttl=ttl,
            max_size=max_size
        )
    
    def get_query_results(self,
                         query_type: str,
                         query_params: Dict[str, Any],
                         table_name: Optional[str] = None) -> Optional[Any]:
        """
        Get cached query results.
        
        Args:
            query_type: Type of query (e.g., 'search', 'get', 'count')
            query_params: Query parameters
            table_name: Optional table name
            
        Returns:
            Cached results if found, None otherwise
        """
        # Create key parts
        key_parts = {
            "query_type": query_type,
            "params": query_params
        }
        
        if table_name:
            key_parts["table"] = table_name
        
        # Get from cache
        return self.get(key_parts)
    
    def set_query_results(self,
                         query_type: str,
                         query_params: Dict[str, Any],
                         results: Any,
                         table_name: Optional[str] = None) -> bool:
        """
        Cache query results.
        
        Args:
            query_type: Type of query (e.g., 'search', 'get', 'count')
            query_params: Query parameters
            results: Query results to cache
            table_name: Optional table name
            
        Returns:
            bool: Success status
        """
        # Create key parts
        key_parts = {
            "query_type": query_type,
            "params": query_params
        }
        
        if table_name:
            key_parts["table"] = table_name
        
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
    
    def invalidate_query_type(self, query_type: str) -> bool:
        """
        Invalidate all cached results for a specific query type.
        
        Args:
            query_type: Type of query (e.g., 'search', 'get', 'count')
            
        Returns:
            bool: Success status
        """
        return self.invalidate(f"query_type:{query_type}")
    
    def invalidate_all_queries(self) -> bool:
        """
        Invalidate all cached query results.
        
        Returns:
            bool: Success status
        """
        return self.clear()
    
    def get_search_results(self,
                          table_name: str,
                          query: Optional[Dict[str, Any]] = None,
                          filters: Optional[Dict[str, Any]] = None,
                          limit: int = 10,
                          offset: int = 0,
                          language: str = "en") -> Optional[List[Dict[str, Any]]]:
        """
        Get cached search results.
        
        Args:
            table_name: Database table name
            query: Search query
            filters: Additional filters
            limit: Maximum number of results
            offset: Offset for pagination
            language: Language code (en, ar)
            
        Returns:
            List of results if found in cache, None otherwise
        """
        return self.get_query_results(
            query_type="search",
            query_params={
                "query": query,
                "filters": filters,
                "limit": limit,
                "offset": offset,
                "language": language
            },
            table_name=table_name
        )
    
    def set_search_results(self,
                          table_name: str,
                          results: List[Dict[str, Any]],
                          query: Optional[Dict[str, Any]] = None,
                          filters: Optional[Dict[str, Any]] = None,
                          limit: int = 10,
                          offset: int = 0,
                          language: str = "en") -> bool:
        """
        Cache search results.
        
        Args:
            table_name: Database table name
            results: Search results to cache
            query: Search query
            filters: Additional filters
            limit: Maximum number of results
            offset: Offset for pagination
            language: Language code (en, ar)
            
        Returns:
            bool: Success status
        """
        return self.set_query_results(
            query_type="search",
            query_params={
                "query": query,
                "filters": filters,
                "limit": limit,
                "offset": offset,
                "language": language
            },
            results=results,
            table_name=table_name
        )
    
    def get_record(self,
                  table_name: str,
                  record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached record.
        
        Args:
            table_name: Database table name
            record_id: ID of the record
            
        Returns:
            Record if found in cache, None otherwise
        """
        return self.get_query_results(
            query_type="get",
            query_params={"id": record_id},
            table_name=table_name
        )
    
    def set_record(self,
                  table_name: str,
                  record_id: str,
                  record: Dict[str, Any]) -> bool:
        """
        Cache a record.
        
        Args:
            table_name: Database table name
            record_id: ID of the record
            record: Record to cache
            
        Returns:
            bool: Success status
        """
        return self.set_query_results(
            query_type="get",
            query_params={"id": record_id},
            results=record,
            table_name=table_name
        )
