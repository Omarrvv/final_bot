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
        'attractions', 'restaurants', 'accommodations', 'cities', 'regions', 'events_festivals', 'itineraries'
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
            # SECURITY FIX: Use parameterized queries to prevent SQL injection
            if table_name not in self.VALID_TABLES:
                logger.error(f"Invalid table name: {table_name}")
                return []
            
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    # SECURITY: Validate column names to prevent injection
                    if not key.replace('_', '').isalnum():
                        logger.warning(f"Potentially unsafe column name: {key}")
                        continue
                    conditions.append(f"{key} = %s")
                    params.append(value)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            query += " LIMIT %s"
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
        'attractions', 'restaurants', 'accommodations', 'cities', 'regions', 'users', 'tourism_faqs', 'practical_info',
        'transportation_types', 'transportation_routes', 'transportation_stations', 'events_festivals', 'itineraries'
    }
    
    # Search type weights for hybrid search
    HYBRID_WEIGHTS = {
        'vector': 0.4,
        'text': 0.4,
        'geo': 0.2
    }
    
    # Standardized keyword-to-table routing configuration
    STANDARDIZED_SEARCH_ROUTING = {
        # Practical Information
        "tipping": {"table": "practical_info", "type_id": "tipping_customs"},
        "currency": {"table": "practical_info", "type_id": "currency"},
        "safety": {"table": "practical_info", "type_id": "safety"},
        "water": {"table": "practical_info", "type_id": "drinking_water"},
        "electricity": {"table": "practical_info", "type_id": "electricity_plugs"},

        # Transportation - NOW PROPERLY MAPPED
        "airport": {"table": "transportation_routes", "filters": {"text": "airport"}},
        "taxi": {"table": "transportation_types", "filters": {"text": "taxi"}},
        "bus": {"table": "transportation_types", "filters": {"text": "bus"}},
        "train": {"table": "transportation_types", "filters": {"text": "train"}},
        "transfer": {"table": "transportation_routes", "filters": {"text": "transfer"}},
        "transport": {"table": "transportation_types", "filters": {"text": "transport"}},
        "transportation": {"table": "transportation_types", "filters": {"text": "transportation"}},

        # Attractions
        "pyramid": {"table": "attractions", "filters": {"text": "pyramid"}},
        "museum": {"table": "attractions", "filters": {"text": "museum"}},
        "temple": {"table": "attractions", "filters": {"text": "temple"}},

        # Accommodations
        "hotel": {"table": "accommodations", "filters": {"text": "hotel"}},
        "resort": {"table": "accommodations", "filters": {"text": "resort"}},

        # Restaurants
        "restaurant": {"table": "restaurants", "filters": {"text": "restaurant"}},
        "food": {"table": "restaurants", "filters": {"text": "food"}},

        # FAQs
        "faq": {"table": "tourism_faqs", "filters": {"text": "general"}}
    }
    
    def __init__(self, db_manager=None):
        """
        Initialize the unified search service.
        
        Args:
            db_manager: Database manager instance (optional but recommended)
        """
        if db_manager is not None:
            super().__init__(db_manager)
            self.db_manager = db_manager
        else:
            # For backwards compatibility, allow None but warn
            logger.warning("UnifiedSearchService created without db_manager - database functionality limited")
            self.db_manager = None
        
        self._search_stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'avg_response_time_ms': 0
        }
        
        self.vector_search = VectorSearchService(db_manager)
        
        logger.info("UnifiedSearchService initialized")

    def get_search_config(self, keyword: str) -> Dict[str, Any]:
        """Get standardized search configuration for keyword."""
        return self.STANDARDIZED_SEARCH_ROUTING.get(keyword.lower(), {
            "table": "tourism_faqs",
            "filters": {"text": keyword}
        })

    def keyword_search(self, keyword: str, language: str = "en", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform keyword search across all relevant tables.
        Returns a list of results from all matching tables.
        """
        # CRITICAL FIX: Check for None db_manager
        if self.db_manager is None:
            logger.error("Cannot perform keyword_search: db_manager is None")
            return []
        
        config = self.get_search_config(keyword.lower())
        all_results = []

        for table_name in config['tables']:
            try:
                table_results = self.search_table(
                    table_name=table_name,
                    filters={'keyword': keyword},
                    limit=limit,
                    jsonb_fields=config.get('jsonb_fields', ['name_en', 'description_en']),
                    language=language
                )
                
                # Add metadata for source tracking
                for result in table_results:
                    result['_source_table'] = table_name
                
                all_results.extend(table_results)
                
            except Exception as e:
                logger.error(f"Search failed for table {table_name}: {str(e)}")
                continue

        return all_results[:limit]

    def search_table(self, table_name: str, filters: Optional[Dict[str, Any]] = None,
                    limit: int = 10, offset: int = 0,
                    jsonb_fields: Optional[List[str]] = None,
                    language: str = "en") -> List[Dict[str, Any]]:
        """
        Main search method that DatabaseManagerService expects.
        Routes to appropriate search method based on filters.
        """
        try:
            self._validate_table(table_name)
            
            if not filters:
                filters = {}
            
            # Check if this is a text search (has 'text' key)
            if 'text' in filters:
                text_query = filters.pop('text')  # Remove 'text' from filters
                search_results = self.text_search(table_name, text_query, filters, limit)
                
                # Convert SearchResult objects to dict format
                results = []
                for search_result in search_results:
                    record = search_result.record.copy()
                    record['_search_score'] = search_result.score
                    results.append(record)
                
                # Apply offset manually since text_search doesn't support it
                return results[offset:offset + limit] if offset > 0 else results[:limit]
            
            # For non-text searches, fall back to direct database query
            else:
                return self._direct_database_search(table_name, filters, limit, offset, jsonb_fields)
                
        except Exception as e:
            logger.error(f"Error in search_table for {table_name}: {e}")
            return []
    
    def _direct_database_search(self, table_name: str, filters: Dict[str, Any],
                               limit: int, offset: int, jsonb_fields: Optional[List[str]]) -> List[Dict[str, Any]]:
        """Direct database search for non-text queries."""
        try:
            # SECURITY FIX: Validate table name to prevent SQL injection
            if table_name not in self.VALID_TABLES:
                logger.error(f"Invalid table name: {table_name}")
                return []
            
            # Build query
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if filters:
                where_conditions = []
                for field, value in filters.items():
                    # SECURITY: Validate column names to prevent injection
                    if not field.replace('_', '').replace('-', '').replace('>', '').replace("'", '').isalnum():
                        logger.warning(f"Potentially unsafe column name: {field}")
                        continue
                        
                    if value is not None:
                        where_conditions.append(f"{field} = %s")
                        params.append(value)
                
                if where_conditions:
                    query += " WHERE " + " AND ".join(where_conditions)
            
            # Add LIMIT and OFFSET
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            # Execute query using the database manager
            results = self.db_manager.execute_postgres_query(query, tuple(params))
            
            # Parse JSONB fields if specified
            if jsonb_fields:
                for result in results:
                    for field in jsonb_fields:
                        if field in result and result[field]:
                            import json
                            try:
                                if isinstance(result[field], str):
                                    result[field] = json.loads(result[field])
                            except (json.JSONDecodeError, TypeError):
                                pass
            
            return results
            
        except Exception as e:
            logger.error(f"Direct database search failed for {table_name}: {e}")
            return []

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
            elif table == 'practical_info':
                search_fields = ['title->>\'en\'', 'title->>\'ar\'', 'content->>\'en\'', 'content->>\'ar\'', 'tags']
            elif table == 'transportation_types':
                search_fields = ['name->>\'en\'', 'name->>\'ar\'', 'description->>\'en\'', 'description->>\'ar\'', 'type']
            elif table == 'transportation_routes':
                search_fields = ['name->>\'en\'', 'name->>\'ar\'', 'description->>\'en\'', 'description->>\'ar\'', 'transportation_type']
            elif table == 'transportation_stations':
                search_fields = ['name->>\'en\'', 'name->>\'ar\'', 'description->>\'en\'', 'description->>\'ar\'', 'station_type', 'address->>\'en\'', 'address->>\'ar\'']
            elif table == 'events_festivals':
                search_fields = ['name->>\'en\'', 'name->>\'ar\'', 'description->>\'en\'', 'description->>\'ar\'', 'location_description->>\'en\'', 'highlights->>\'en\'']
            elif table == 'itineraries':
                search_fields = ['name->>\'en\'', 'name->>\'ar\'', 'description->>\'en\'', 'description->>\'ar\'', 'highlights->>\'en\'', 'practical_tips->>\'en\'']
            else:
                search_fields = ['name_en', 'name_ar']
            
            # Build ILIKE conditions for text search
            conditions = []
            params = []
            
            for field in search_fields:
                if field in ['tags', 'types']:
                    # Special handling for array fields
                    conditions.append(f"EXISTS (SELECT 1 FROM unnest({field}) AS tag WHERE tag ILIKE %s)")
                else:
                    conditions.append(f"{field} ILIKE %s")
                params.append(f"%{query}%")
            
            search_condition = " OR ".join(conditions)
            base_query = f"SELECT * FROM {table} WHERE ({search_condition})"
            
            # Add additional filters
            if filters:
                for key, value in filters.items():
                    # SECURITY: Validate column names to prevent injection
                    if not key.replace('_', '').replace('-', '').replace('>', '').replace("'", '').isalnum():
                        logger.warning(f"Potentially unsafe column name in filter: {key}")
                        continue
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
                    # SECURITY: Validate column names to prevent injection
                    if not key.replace('_', '').replace('-', '').replace('>', '').replace("'", '').isalnum():
                        logger.warning(f"Potentially unsafe column name in geo filter: {key}")
                        continue
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