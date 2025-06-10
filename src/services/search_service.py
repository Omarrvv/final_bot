"""
Consolidated Search Service Module

This module provides unified search functionality including:
- Vector similarity search
- Text search and full-text search
- Geospatial search
- Hybrid search (combination of vector + text + geo)
- Cross-table search operations

Consolidates functionality from:
- src/services/search/unified_search_service.py
- src/services/vector_search_service.py
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union
import numpy as np

from src.services.base_service import BaseService

logger = logging.getLogger(__name__)

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
    """Search operation error."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.details = details or {}

class VectorSearchService(BaseService):
    """
    Service for performing vector searches across different tables.

    Responsibilities:
    - Embedding format standardization
    - Vector similarity search
    - Performance monitoring
    """

    # Valid tables for vector search
    VALID_TABLES = {
        'attractions', 'restaurants', 'accommodations', 'cities', 'regions'
    }

    # Default search parameters
    DEFAULT_EF_SEARCH = 100  # Higher values = more accurate but slower
    DEFAULT_LIMIT = 10

    def __init__(self, db_manager=None):
        super().__init__(db_manager)
        self._search_stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'avg_response_time_ms': 0
        }
        
        logger.info("VectorSearchService initialized")

    def _check_vector_extension(self) -> bool:
        """Check if pgvector extension is available."""
        try:
            query = "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');"
            result = self.db_manager.execute_postgres_query(query, fetchall=False)
            return result.get('exists', False) if result else False
        except Exception as e:
            logger.error(f"Error checking vector extension: {e}")
            return False

    def standardize_embedding(self, embedding: Any) -> List[float]:
        """Standardize embedding to consistent format."""
        if embedding is None:
            raise SearchError("Embedding cannot be None")
        
        # Handle different input types
        if isinstance(embedding, str):
            try:
                # Parse string representation
                embedding = eval(embedding)
            except Exception:
                raise SearchError("Invalid embedding string format")
        
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        
        if not isinstance(embedding, list):
            raise SearchError(f"Unsupported embedding type: {type(embedding)}")
        
        # Validate dimensions
        if not embedding or len(embedding) == 0:
            raise SearchError("Embedding cannot be empty")
        
        # Ensure all elements are floats
        try:
            embedding = [float(x) for x in embedding]
        except (ValueError, TypeError) as e:
            raise SearchError(f"Invalid embedding values: {e}")
        
        return embedding

    def search(self, table_name: str, embedding: Any, 
               filters: Optional[Dict[str, Any]] = None,
               limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
        """Perform vector similarity search on a table."""
        start_time = time.time()
        
        try:
            # Validate inputs
            if table_name not in self.VALID_TABLES:
                raise SearchError(f"Invalid table: {table_name}. Valid tables: {self.VALID_TABLES}")
            
            # Standardize embedding
            std_embedding = self.standardize_embedding(embedding)
            
            # Check vector extension availability
            if not self._check_vector_extension():
                logger.warning("pgvector extension not available, falling back to basic search")
                return self._fallback_search(table_name, filters, limit)
            
            # Build query
            base_query = f"""
                SELECT *, 1 - (embedding <=> %s::vector) AS similarity_score
                FROM {table_name}
                WHERE embedding IS NOT NULL
            """
            
            params = [std_embedding]
            
            # Add filters
            if filters:
                for key, value in filters.items():
                    if key in ['city_id', 'region_id', 'type_id']:
                        base_query += f" AND {key} = %s"
                        params.append(value)
            
            # Add ordering and limit
            base_query += " ORDER BY similarity_score DESC LIMIT %s"
            params.append(limit)
            
            # Execute query
            results = self.db_manager.execute_postgres_query(base_query, tuple(params))
            
            # Update stats
            self._search_stats['total_searches'] += 1
            self._search_stats['successful_searches'] += 1
            response_time = (time.time() - start_time) * 1000
            self._update_avg_response_time(response_time)
            
            return results or []
            
        except Exception as e:
            logger.error(f"Vector search failed for table {table_name}: {e}")
            self._search_stats['total_searches'] += 1
            self._search_stats['failed_searches'] += 1
            
            # Return empty results on error
            return []

    def _fallback_search(self, table_name: str, filters: Optional[Dict[str, Any]], 
                        limit: int) -> List[Dict[str, Any]]:
        """Fallback search when vector extension is not available."""
        try:
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = %s")
                    params.append(value)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            query += f" LIMIT %s"
            params.append(limit)
            
            return self.db_manager.execute_postgres_query(query, tuple(params)) or []
            
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return []

    def _update_avg_response_time(self, response_time_ms: float):
        """Update average response time."""
        current_avg = self._search_stats['avg_response_time_ms']
        total_searches = self._search_stats['successful_searches']
        
        if total_searches == 1:
            self._search_stats['avg_response_time_ms'] = response_time_ms
        else:
            # Running average
            self._search_stats['avg_response_time_ms'] = (
                (current_avg * (total_searches - 1) + response_time_ms) / total_searches
            )

class UnifiedSearchService(BaseService):
    """
    Unified search service that consolidates all search functionality.
    
    Responsibilities:
    - Vector similarity search
    - Text search
    - Geospatial search
    - Hybrid search (combination of above)
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
    
    def __init__(self, db_manager=None):
        super().__init__(db_manager)
        self.vector_search = VectorSearchService(db_manager)
        
        logger.info("UnifiedSearchService initialized")

    def vector_search(self, table: str, embedding: List[float], 
                     filters: Optional[Dict[str, Any]] = None,
                     limit: int = 10) -> List[SearchResult]:
        """Perform vector similarity search."""
        try:
            results = self.vector_search.search(table, embedding, filters, limit)
            
            search_results = []
            for result in results:
                search_results.append(SearchResult(
                    record=result,
                    score=result.get('similarity_score', 0.0),
                    search_type='vector'
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def text_search(self, table: str, query: str,
                   filters: Optional[Dict[str, Any]] = None,
                   limit: int = 10) -> List[SearchResult]:
        """Perform text-based search."""
        try:
            self._validate_table(table)
            
            # Build text search query based on table
            if table == 'attractions':
                search_fields = ['name_en', 'name_ar', 'description_en', 'description_ar']
            elif table == 'restaurants':
                search_fields = ['name_en', 'name_ar', 'cuisine', 'description_en']
            elif table == 'accommodations':
                search_fields = ['name_en', 'name_ar', 'type', 'description_en']
            else:
                search_fields = ['name_en', 'name_ar']
            
            # Build ILIKE conditions for text search
            conditions = []
            params = []
            
            for field in search_fields:
                conditions.append(f"{field} ILIKE %s")
                params.append(f"%{query}%")
            
            search_condition = " OR ".join(conditions)
            base_query = f"SELECT * FROM {table} WHERE ({search_condition})"
            
            # Add additional filters
            if filters:
                for key, value in filters.items():
                    base_query += f" AND {key} = %s"
                    params.append(value)
            
            base_query += f" LIMIT %s"
            params.append(limit)
            
            results = self.db_manager.execute_postgres_query(base_query, tuple(params))
            
            search_results = []
            for result in results:
                # Simple text relevance score (could be improved)
                score = self._calculate_text_relevance(result, query, search_fields)
                search_results.append(SearchResult(
                    record=result,
                    score=score,
                    search_type='text'
                ))
            
            # Sort by relevance score
            search_results.sort(key=lambda x: x.score, reverse=True)
            return search_results
            
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return []

    def geo_search(self, table: str, latitude: float, longitude: float,
                  radius_km: float, filters: Optional[Dict[str, Any]] = None,
                  limit: int = 10) -> List[SearchResult]:
        """Perform geospatial search."""
        try:
            self._validate_table(table)
            
            # Use PostGIS if available, otherwise approximate distance
            query = f"""
                SELECT *, 
                CASE 
                    WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN
                        6371 * acos(
                            cos(radians(%s)) * cos(radians(latitude)) * 
                            cos(radians(longitude) - radians(%s)) + 
                            sin(radians(%s)) * sin(radians(latitude))
                        )
                    ELSE NULL
                END as distance_km
                FROM {table}
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """
            
            params = [latitude, longitude, latitude]
            
            # Add distance filter
            query += " HAVING distance_km <= %s"
            params.append(radius_km)
            
            # Add additional filters
            if filters:
                for key, value in filters.items():
                    query += f" AND {key} = %s"
                    params.append(value)
            
            query += " ORDER BY distance_km ASC LIMIT %s"
            params.append(limit)
            
            results = self.db_manager.execute_postgres_query(query, tuple(params))
            
            search_results = []
            for result in results:
                distance = result.get('distance_km', float('inf'))
                # Score based on proximity (closer = higher score)
                score = max(0, 1 - (distance / radius_km))
                
                search_results.append(SearchResult(
                    record=result,
                    score=score,
                    search_type='geo',
                    distance_km=distance
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Geo search failed: {e}")
            return []

    def hybrid_search(self, search_filter: SearchFilter) -> List[SearchResult]:
        """Perform hybrid search combining multiple search types."""
        try:
            all_results = {}  # Use dict to deduplicate by record ID
            
            # Vector search
            if search_filter.vector_embedding:
                vector_results = self.vector_search(
                    search_filter.table, 
                    search_filter.vector_embedding,
                    search_filter.filters,
                    search_filter.limit * 2  # Get more for combining
                )
                
                for result in vector_results:
                    record_id = result.record.get('id')
                    if record_id:
                        weighted_score = result.score * self.HYBRID_WEIGHTS['vector']
                        if record_id in all_results:
                            all_results[record_id].score += weighted_score
                        else:
                            result.score = weighted_score
                            all_results[record_id] = result
            
            # Text search
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
                        weighted_score = result.score * self.HYBRID_WEIGHTS['text']
                        if record_id in all_results:
                            all_results[record_id].score += weighted_score
                        else:
                            result.score = weighted_score
                            all_results[record_id] = result
            
            # Geo search
            if search_filter.location and search_filter.radius_km:
                lat, lon = search_filter.location
                geo_results = self.geo_search(
                    search_filter.table, lat, lon, search_filter.radius_km,
                    search_filter.filters, search_filter.limit * 2
                )
                
                for result in geo_results:
                    record_id = result.record.get('id')
                    if record_id:
                        weighted_score = result.score * self.HYBRID_WEIGHTS['geo']
                        if record_id in all_results:
                            all_results[record_id].score += weighted_score
                            # Preserve distance info
                            all_results[record_id].distance_km = result.distance_km
                        else:
                            result.score = weighted_score
                            all_results[record_id] = result
            
            # Convert to list and sort by combined score
            final_results = list(all_results.values())
            final_results.sort(key=lambda x: x.score, reverse=True)
            
            # Update search type for combined results
            for result in final_results:
                result.search_type = 'hybrid'
            
            return final_results[:search_filter.limit]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    def _validate_table(self, table: str):
        """Validate table name."""
        if table not in self.VALID_TABLES:
            raise SearchError(f"Invalid table: {table}. Valid tables: {self.VALID_TABLES}")

    def _calculate_text_relevance(self, record: Dict[str, Any], query: str, 
                                 search_fields: List[str]) -> float:
        """Calculate text relevance score."""
        query_lower = query.lower()
        max_score = 0.0
        
        for field in search_fields:
            field_value = record.get(field, '')
            if field_value:
                field_lower = str(field_value).lower()
                
                # Exact match gets highest score
                if query_lower == field_lower:
                    return 1.0
                
                # Partial match gets proportional score
                if query_lower in field_lower:
                    score = len(query_lower) / len(field_lower)
                    max_score = max(max_score, score)
        
        return max_score

    def get_search_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        return {
            'vector_search_stats': self.vector_search._search_stats,
            'supported_tables': list(self.VALID_TABLES)
        }

class SearchService:
    """
    Main search service that provides all search functionality.
    
    This is the primary interface for search operations.
    """
    
    def __init__(self, db_manager=None):
        self.unified_search = UnifiedSearchService(db_manager)
        self.db_manager = db_manager
        
        logger.info("SearchService initialized")

    def vector_search(self, table: str, embedding: List[float], **kwargs) -> List[SearchResult]:
        """Perform vector similarity search."""
        return self.unified_search.vector_search(table, embedding, **kwargs)

    def text_search(self, table: str, query: str, **kwargs) -> List[SearchResult]:
        """Perform text search."""
        return self.unified_search.text_search(table, query, **kwargs)

    def geo_search(self, table: str, latitude: float, longitude: float, 
                  radius_km: float, **kwargs) -> List[SearchResult]:
        """Perform geospatial search."""
        return self.unified_search.geo_search(table, latitude, longitude, radius_km, **kwargs)

    def hybrid_search(self, search_filter: SearchFilter) -> List[SearchResult]:
        """Perform hybrid search."""
        return self.unified_search.hybrid_search(search_filter)

    def get_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        return self.unified_search.get_search_stats() 