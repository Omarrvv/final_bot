"""
Vector Search Service for the Egypt Tourism Chatbot.

This service provides a unified interface for vector search operations across different tables,
with standardized embedding handling, error management, and performance monitoring.
"""

import json
import time
import logging
import traceback
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np

from psycopg2.extras import RealDictCursor
from src.utils.logger import get_logger

logger = get_logger(__name__)

class VectorSearchError(Exception):
    """Base exception for vector search errors."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class VectorSearchService:
    """
    Service for performing vector searches across different tables.

    This service handles:
    - Embedding format standardization
    - Connection management
    - Error handling and logging
    - Performance monitoring
    """

    # Valid tables for vector search
    VALID_TABLES = {
        'attractions', 'restaurants', 'accommodations', 'cities', 'regions'
    }

    # Default search parameters
    DEFAULT_EF_SEARCH = 100  # Higher values = more accurate but slower
    DEFAULT_LIMIT = 10

    def __init__(self, db_manager):
        """
        Initialize the vector search service.

        Args:
            db_manager: Database manager instance with connection pool
        """
        self.db = db_manager
        self.vector_cache = getattr(db_manager, 'vector_cache', None)

        # Verify pgvector extension is available
        self._check_vector_extension()

    def _check_vector_extension(self) -> bool:
        """Check if pgvector extension is available in the database."""
        try:
            result = self.db.execute_postgres_query(
                "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            )
            if not result:
                logger.warning("pgvector extension not found in database. Vector search may not work correctly.")
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking pgvector extension: {e}")
            return False

    def standardize_embedding(self, embedding: Any) -> List[float]:
        """
        Standardize embedding to a list of floats, handling various input formats.

        Args:
            embedding: Embedding in various formats (list, string, numpy array, etc.)

        Returns:
            List of floats representing the embedding

        Raises:
            VectorSearchError: If embedding cannot be standardized
        """
        try:
            # Handle None
            if embedding is None:
                raise VectorSearchError("Embedding cannot be None")

            # Handle numpy arrays
            if isinstance(embedding, np.ndarray):
                return embedding.tolist()

            # Handle lists
            if isinstance(embedding, list):
                # Verify all elements are numeric
                if all(isinstance(x, (int, float)) for x in embedding):
                    return embedding
                else:
                    # Try to convert all elements to float
                    return [float(x) for x in embedding]

            # Handle strings (JSON arrays, etc.)
            if isinstance(embedding, str):
                try:
                    # Try to parse as JSON
                    parsed = json.loads(embedding)
                    if isinstance(parsed, list):
                        return [float(x) for x in parsed]
                    else:
                        raise VectorSearchError(
                            "Embedding string does not represent a list",
                            {"parsed_type": type(parsed).__name__}
                        )
                except json.JSONDecodeError:
                    # Try to parse as comma-separated values
                    try:
                        values = embedding.strip('[]').split(',')
                        return [float(x) for x in values]
                    except ValueError:
                        raise VectorSearchError(
                            "Could not parse embedding string",
                            {"embedding_str": embedding[:100] + "..." if len(embedding) > 100 else embedding}
                        )

            # Handle other types
            raise VectorSearchError(
                f"Unsupported embedding type: {type(embedding).__name__}",
                {"embedding_type": type(embedding).__name__}
            )

        except VectorSearchError:
            # Re-raise VectorSearchError
            raise
        except Exception as e:
            # Wrap other exceptions
            raise VectorSearchError(
                f"Error standardizing embedding: {str(e)}",
                {"error": str(e), "traceback": traceback.format_exc()}
            )

    def search(
        self,
        table_name: str,
        embedding: Any,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        """
        Perform vector search on the specified table.

        Args:
            table_name: Name of the table to search
            embedding: Vector embedding for similarity search
            filters: Additional filters to apply
            limit: Maximum number of results to return

        Returns:
            List of matching records ordered by similarity

        Raises:
            VectorSearchError: If search fails
        """
        start_time = time.time()

        # Validate table name
        if table_name not in self.VALID_TABLES:
            raise VectorSearchError(f"Invalid table name: {table_name}")

        try:
            # Standardize embedding
            std_embedding = self.standardize_embedding(embedding)

            # Check cache if available
            if self.vector_cache:
                cached_results = self.vector_cache.get(table_name, std_embedding, filters, limit)
                if cached_results is not None:
                    logger.info(f"Cache hit for vector search on {table_name}")
                    return cached_results

            # Get database connection from pool
            conn = self.db._get_pg_connection()
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Set search parameters
                    cursor.execute(f"SET hnsw.ef_search = {self.DEFAULT_EF_SEARCH};")

                    # Build query
                    query = f"""
                        SELECT *, embedding <-> %s::vector AS distance
                        FROM {table_name}
                        WHERE embedding IS NOT NULL
                    """
                    params = [std_embedding]

                    # Add filters
                    if filters:
                        for key, value in filters.items():
                            query += f" AND {key} = %s"
                            params.append(value)

                    # Add order by and limit
                    query += " ORDER BY distance LIMIT %s"
                    params.append(limit)

                    # Execute query
                    logger.debug(f"Executing vector search query: {query}")
                    cursor.execute(query, params)

                    # Fetch results
                    results = cursor.fetchall()

                    # Cache results if cache is available
                    if self.vector_cache and results:
                        # Add category to cache key for selective invalidation
                        category = f"{table_name}:vector"
                        if filters:
                            # Add filter info to category for more granular invalidation
                            filter_keys = sorted(filters.keys())
                            category += f":{','.join(filter_keys)}"

                        self.vector_cache.set(table_name, std_embedding, results, filters, limit)

                    # Log performance
                    duration_ms = (time.time() - start_time) * 1000
                    logger.info(f"Vector search on {table_name} completed in {duration_ms:.2f}ms, returned {len(results)} results")

                    return results or []
            finally:
                self.db._return_pg_connection(conn)

        except VectorSearchError:
            # Re-raise VectorSearchError
            raise
        except Exception as e:
            # Wrap other exceptions
            raise VectorSearchError(
                f"Error in vector search for {table_name}: {str(e)}",
                {
                    "table": table_name,
                    "filters": filters,
                    "limit": limit,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            )

    def search_attractions(
        self,
        embedding: Any,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        """
        Search for attractions by vector similarity.

        Args:
            embedding: Vector embedding for similarity search
            filters: Additional filters (city_id, type_id, etc.)
            limit: Maximum number of results to return

        Returns:
            List of matching attractions ordered by similarity
        """
        # Process attraction-specific filters
        processed_filters = {}
        if filters:
            if 'city' in filters or 'city_id' in filters:
                city_value = filters.get('city_id', filters.get('city'))
                # Ensure city_id is an integer
                if city_value is not None and not isinstance(city_value, int):
                    try:
                        city_value = int(city_value)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid city_id value: {city_value}, skipping filter")
                        city_value = None
                if city_value is not None:
                    processed_filters['city_id'] = city_value

            if 'type' in filters or 'type_id' in filters:
                type_value = filters.get('type_id', filters.get('type'))
                # Ensure type_id is an integer
                if type_value is not None and not isinstance(type_value, int):
                    try:
                        type_value = int(type_value)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid type_id value: {type_value}, skipping filter")
                        type_value = None
                if type_value is not None:
                    processed_filters['type_id'] = type_value

        return self.search('attractions', embedding, processed_filters, limit)

    def search_restaurants(
        self,
        embedding: Any,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        """
        Search for restaurants by vector similarity.

        Args:
            embedding: Vector embedding for similarity search
            filters: Additional filters (city_id, cuisine, etc.)
            limit: Maximum number of results to return

        Returns:
            List of matching restaurants ordered by similarity
        """
        # Process restaurant-specific filters
        processed_filters = {}
        if filters:
            if 'city' in filters or 'city_id' in filters:
                city_value = filters.get('city_id', filters.get('city'))
                # Ensure city_id is an integer
                if city_value is not None and not isinstance(city_value, int):
                    try:
                        city_value = int(city_value)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid city_id value: {city_value}, skipping filter")
                        city_value = None
                if city_value is not None:
                    processed_filters['city_id'] = city_value

            if 'cuisine' in filters or 'cuisine_id' in filters:
                cuisine_value = filters.get('cuisine_id', filters.get('cuisine'))
                # Ensure cuisine_id is an integer
                if cuisine_value is not None and not isinstance(cuisine_value, int):
                    try:
                        cuisine_value = int(cuisine_value)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid cuisine_id value: {cuisine_value}, skipping filter")
                        cuisine_value = None
                if cuisine_value is not None:
                    processed_filters['cuisine_id'] = cuisine_value

        return self.search('restaurants', embedding, processed_filters, limit)

    def search_hotels(
        self,
        embedding: Any,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        """
        Search for hotels/accommodations by vector similarity.

        Args:
            embedding: Vector embedding for similarity search
            filters: Additional filters (city_id, stars, etc.)
            limit: Maximum number of results to return

        Returns:
            List of matching hotels ordered by similarity
        """
        # Process hotel-specific filters
        processed_filters = {}
        if filters:
            if 'city' in filters or 'city_id' in filters:
                city_value = filters.get('city_id', filters.get('city'))
                # Ensure city_id is an integer
                if city_value is not None and not isinstance(city_value, int):
                    try:
                        city_value = int(city_value)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid city_id value: {city_value}, skipping filter")
                        city_value = None
                if city_value is not None:
                    processed_filters['city_id'] = city_value

            if 'stars' in filters:
                processed_filters['stars'] = filters.get('stars')

        return self.search('accommodations', embedding, processed_filters, limit)

    def search_cities(
        self,
        embedding: Any,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        """
        Search for cities by vector similarity.

        Args:
            embedding: Vector embedding for similarity search
            filters: Additional filters (region_id, etc.)
            limit: Maximum number of results to return

        Returns:
            List of matching cities ordered by similarity
        """
        # Process city-specific filters
        processed_filters = {}
        if filters:
            if 'region' in filters or 'region_id' in filters:
                region_value = filters.get('region_id', filters.get('region'))
                # Ensure region_id is an integer
                if region_value is not None and not isinstance(region_value, int):
                    try:
                        region_value = int(region_value)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid region_id value: {region_value}, skipping filter")
                        region_value = None
                if region_value is not None:
                    processed_filters['region_id'] = region_value

        return self.search('cities', embedding, processed_filters, limit)
