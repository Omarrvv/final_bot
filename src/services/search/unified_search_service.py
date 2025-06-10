"""
Unified Search Service for the Egypt Tourism Chatbot.

This service consolidates vector search, text search, and geospatial search operations
from the scattered functionality across DatabaseManager and VectorSearchService,
providing a clean, unified interface while using repositories internally.
"""

import json
import time
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
import numpy as np
from dataclasses import dataclass

from src.utils.logger import get_logger
from src.repositories.repository_factory import RepositoryFactory

logger = get_logger(__name__)


@dataclass
class SearchFilter:
    """Represents search filters for unified search operations."""
    table: str
    text_query: Optional[str] = None
    vector_embedding: Optional[List[float]] = None
    location: Optional[Tuple[float, float]] = None  # (latitude, longitude)
    radius_km: Optional[float] = None
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
    offset: int = 0


@dataclass
class SearchResult:
    """Represents a unified search result."""
    record: Dict[str, Any]
    score: float
    search_type: str  # 'vector', 'text', 'geo', 'hybrid'
    distance_km: Optional[float] = None


class SearchError(Exception):
    """Base exception for search errors."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class UnifiedSearchService:
    """
    Unified search service that consolidates all search functionality.
    
    This service provides a single interface for:
    - Vector similarity search
    - Text search
    - Geospatial search
    - Hybrid search (combination of above)
    
    It uses repositories internally and replaces the scattered search
    functionality from DatabaseManager and VectorSearchService.
    """
    
    # Valid tables for search operations
    VALID_TABLES = {
        'attractions', 'restaurants', 'accommodations', 'cities', 'regions', 'users', 'tourism_faqs'
    }
    
    # Search type weights for hybrid search
    HYBRID_WEIGHTS = {
        'vector': 0.4,
        'text': 0.4,
        'geo': 0.2
    }
    
    def __init__(self, repository_factory: RepositoryFactory):
        """
        Initialize the unified search service.
        
        Args:
            repository_factory: Factory for creating repository instances
        """
        self.repository_factory = repository_factory
        self.search_cache = {}  # Simple in-memory cache for search results
        self.cache_ttl = 300  # 5 minutes cache TTL
        
        logger.info("UnifiedSearchService initialized with repository factory")
    
    def vector_search(self, table: str, embedding: List[float], 
                     filters: Optional[Dict[str, Any]] = None,
                     limit: int = 10) -> List[SearchResult]:
        """
        Perform vector similarity search on a table.
        
        Args:
            table: Table name to search
            embedding: Vector embedding for similarity search
            filters: Additional filters to apply
            limit: Maximum number of results
            
        Returns:
            List of SearchResult objects ordered by similarity
        """
        try:
            self._validate_table(table)
            
            # Get appropriate repository
            repo = self._get_repository(table)
            
            # Perform vector search using repository's database core
            results = repo.db.vector_search(table, embedding, filters, limit)
            
            # Convert to SearchResult objects
            search_results = []
            for result in results:
                score = 1.0 - result.get('distance', 0.5)  # Convert distance to similarity score
                search_results.append(SearchResult(
                    record=result,
                    score=score,
                    search_type='vector'
                ))
            
            logger.info(f"Vector search on {table} returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            raise SearchError(f"Vector search failed: {str(e)}", {
                "table": table,
                "embedding_dim": len(embedding) if embedding else 0,
                "filters": filters
            })
    
    def text_search(self, table: str, query: str,
                   filters: Optional[Dict[str, Any]] = None,
                   limit: int = 10) -> List[SearchResult]:
        """
        Perform text search on a table.
        
        Args:
            table: Table name to search
            query: Text query string
            filters: Additional filters to apply
            limit: Maximum number of results
            
        Returns:
            List of SearchResult objects ordered by text relevance
        """
        try:
            self._validate_table(table)
            
            # Get appropriate repository
            repo = self._get_repository(table)
            
            # Perform text search based on table type
            if table == 'attractions':
                results = repo.search_attractions(query, limit)
            elif table == 'restaurants':
                results = repo.search_restaurants(query, limit)
            elif table == 'accommodations':
                results = repo.search_accommodations(query, limit)
            elif table == 'cities':
                results = repo.search_cities(query, limit)
            elif table == 'regions':
                results = repo.search_regions(query, limit)
            elif table == 'users':
                results = repo.search_users(query, limit)
            elif table == 'tourism_faqs':
                results = repo.search_faqs(query, limit)
            else:
                # Generic search fallback
                results = repo.find(filters={'name': query}, limit=limit)
            
            # Apply additional filters if provided
            if filters:
                filtered_results = []
                for result in results:
                    match = True
                    for key, value in filters.items():
                        if key in result and result[key] != value:
                            match = False
                            break
                    if match:
                        filtered_results.append(result)
                results = filtered_results
            
            # Convert to SearchResult objects
            search_results = []
            for i, result in enumerate(results[:limit]):
                # Calculate text relevance score (simple ranking based on position)
                score = 1.0 - (i / max(len(results), 1))
                search_results.append(SearchResult(
                    record=result,
                    score=score,
                    search_type='text'
                ))
            
            logger.info(f"Text search on {table} for '{query}' returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            raise SearchError(f"Text search failed: {str(e)}", {
                "table": table,
                "query": query,
                "filters": filters
            })
    
    def geo_search(self, table: str, latitude: float, longitude: float,
                  radius_km: float, filters: Optional[Dict[str, Any]] = None,
                  limit: int = 10) -> List[SearchResult]:
        """
        Perform geospatial search on a table.
        
        Args:
            table: Table name to search
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Search radius in kilometers
            filters: Additional filters to apply
            limit: Maximum number of results
            
        Returns:
            List of SearchResult objects ordered by distance
        """
        try:
            self._validate_table(table)
            
            # Get appropriate repository
            repo = self._get_repository(table)
            
            # Perform geospatial search using repository's database core
            results = repo.db.find_nearby(
                table, latitude, longitude, radius_km, limit, filters
            )
            
            # Convert to SearchResult objects
            search_results = []
            for result in results:
                distance_km = result.get('distance_km', 0)
                # Calculate geo relevance score (closer = higher score)
                score = max(0, 1.0 - (distance_km / radius_km))
                
                search_results.append(SearchResult(
                    record=result,
                    score=score,
                    search_type='geo',
                    distance_km=distance_km
                ))
            
            logger.info(f"Geo search on {table} near ({latitude}, {longitude}) "
                       f"returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            raise SearchError(f"Geo search failed: {str(e)}", {
                "table": table,
                "location": (latitude, longitude),
                "radius_km": radius_km,
                "filters": filters
            })
    
    def hybrid_search(self, search_filter: SearchFilter) -> List[SearchResult]:
        """
        Perform hybrid search combining multiple search types.
        
        Args:
            search_filter: SearchFilter object containing search parameters
            
        Returns:
            List of SearchResult objects with combined scores
        """
        try:
            all_results = {}  # Dict to deduplicate and combine scores
            
            # Perform vector search if embedding provided
            if search_filter.vector_embedding:
                vector_results = self.vector_search(
                    search_filter.table,
                    search_filter.vector_embedding,
                    search_filter.filters,
                    search_filter.limit * 2  # Get more results for fusion
                )
                
                for result in vector_results:
                    record_id = result.record.get('id')
                    if record_id:
                        if record_id not in all_results:
                            all_results[record_id] = result
                            all_results[record_id].score = 0
                        all_results[record_id].score += (
                            result.score * self.HYBRID_WEIGHTS['vector']
                        )
            
            # Perform text search if query provided
            if search_filter.text_query:
                text_results = self.text_search(
                    search_filter.table,
                    search_filter.text_query,
                    search_filter.filters,
                    search_filter.limit * 2
                )
                
                for result in text_results:
                    record_id = result.record.get('id')
                    if record_id:
                        if record_id not in all_results:
                            all_results[record_id] = result
                            all_results[record_id].score = 0
                        all_results[record_id].score += (
                            result.score * self.HYBRID_WEIGHTS['text']
                        )
            
            # Perform geo search if location provided
            if search_filter.location and search_filter.radius_km:
                lat, lng = search_filter.location
                geo_results = self.geo_search(
                    search_filter.table, lat, lng,
                    search_filter.radius_km,
                    search_filter.filters,
                    search_filter.limit * 2
                )
                
                for result in geo_results:
                    record_id = result.record.get('id')
                    if record_id:
                        if record_id not in all_results:
                            all_results[record_id] = result
                            all_results[record_id].score = 0
                        all_results[record_id].score += (
                            result.score * self.HYBRID_WEIGHTS['geo']
                        )
                        # Preserve distance information
                        all_results[record_id].distance_km = result.distance_km
            
            # Sort by combined score and update search type
            sorted_results = sorted(
                all_results.values(),
                key=lambda x: x.score,
                reverse=True
            )
            
            # Update search type to hybrid and apply limit
            final_results = []
            for result in sorted_results[:search_filter.limit]:
                result.search_type = 'hybrid'
                final_results.append(result)
            
            logger.info(f"Hybrid search on {search_filter.table} returned {len(final_results)} results")
            return final_results
            
        except Exception as e:
            raise SearchError(f"Hybrid search failed: {str(e)}", {
                "search_filter": search_filter.__dict__
            })
    
    def search_similar_records(self, table: str, reference_record_id: int,
                             search_types: List[str] = None,
                             limit: int = 10) -> List[SearchResult]:
        """
        Find records similar to a reference record.
        
        Args:
            table: Table name to search
            reference_record_id: ID of the reference record
            search_types: Types of similarity to use ['vector', 'geo', 'category']
            limit: Maximum number of results
            
        Returns:
            List of similar SearchResult objects
        """
        try:
            self._validate_table(table)
            search_types = search_types or ['vector', 'geo']
            
            # Get the reference record
            repo = self._get_repository(table)
            reference_record = repo.find_by_id(reference_record_id)
            
            if not reference_record:
                raise SearchError(f"Reference record {reference_record_id} not found")
            
            all_results = {}
            
            # Vector similarity (if embedding exists)
            if 'vector' in search_types and 'embedding' in reference_record:
                try:
                    embedding = reference_record['embedding']
                    if isinstance(embedding, str):
                        embedding = json.loads(embedding)
                    
                    vector_results = self.vector_search(table, embedding, limit=limit*2)
                    
                    for result in vector_results:
                        record_id = result.record.get('id')
                        if record_id != reference_record_id:  # Exclude self
                            all_results[record_id] = result
                            
                except Exception as e:
                    logger.warning(f"Vector similarity failed: {e}")
            
            # Geographic proximity (if location exists)
            if 'geo' in search_types and all(k in reference_record for k in ['latitude', 'longitude']):
                try:
                    geo_results = self.geo_search(
                        table,
                        reference_record['latitude'],
                        reference_record['longitude'],
                        radius_km=50.0,  # 50km radius for similarity
                        limit=limit*2
                    )
                    
                    for result in geo_results:
                        record_id = result.record.get('id')
                        if record_id != reference_record_id:  # Exclude self
                            if record_id not in all_results:
                                all_results[record_id] = result
                            else:
                                # Combine scores
                                all_results[record_id].score = (
                                    all_results[record_id].score + result.score
                                ) / 2
                                
                except Exception as e:
                    logger.warning(f"Geographic similarity failed: {e}")
            
            # Sort by score and return
            sorted_results = sorted(
                all_results.values(),
                key=lambda x: x.score,
                reverse=True
            )[:limit]
            
            logger.info(f"Similar records search for {table}:{reference_record_id} "
                       f"returned {len(sorted_results)} results")
            return sorted_results
            
        except Exception as e:
            raise SearchError(f"Similar records search failed: {str(e)}", {
                "table": table,
                "reference_id": reference_record_id,
                "search_types": search_types
            })
    
    def _get_repository(self, table: str):
        """Get the appropriate repository for a table."""
        if table == 'attractions':
            return self.repository_factory.get_attraction_repository()
        elif table == 'restaurants':
            return self.repository_factory.get_restaurant_repository()
        elif table == 'accommodations':
            return self.repository_factory.get_accommodation_repository()
        elif table == 'cities':
            return self.repository_factory.get_city_repository()
        elif table == 'regions':
            return self.repository_factory.get_region_repository()
        elif table == 'users':
            return self.repository_factory.get_user_repository()
        elif table == 'tourism_faqs':
            return self.repository_factory.get_faq_repository()
        else:
            # Return base repository for generic operations
            return self.repository_factory.get_repository_by_name('base')
    
    def _validate_table(self, table: str):
        """Validate table name against whitelist."""
        if table not in self.VALID_TABLES:
            raise SearchError(f"Invalid table name: {table}", {"valid_tables": list(self.VALID_TABLES)})
    
    def get_search_stats(self) -> Dict[str, Any]:
        """
        Get search service statistics.
        
        Returns:
            Dictionary containing search service statistics
        """
        return {
            "service_type": "unified_search",
            "valid_tables": list(self.VALID_TABLES),
            "supported_search_types": ["vector", "text", "geo", "hybrid"],
            "cache_size": len(self.search_cache),
            "cache_ttl_seconds": self.cache_ttl,
            "hybrid_weights": self.HYBRID_WEIGHTS
        }
    
    def clear_cache(self):
        """Clear the search cache."""
        self.search_cache.clear()
        logger.info("Search cache cleared") 