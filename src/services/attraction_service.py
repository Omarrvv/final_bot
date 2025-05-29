"""
Attraction service for database operations.

This module provides a service class for handling database operations related to attractions.
"""
from typing import Any, Dict, List, Optional, Tuple, Union

from src.services.base_service import BaseService
from src.utils.logger import get_logger

logger = get_logger(__name__)

class AttractionService(BaseService):
    """
    Service class for attraction-related database operations.

    This class extends the BaseService class to provide attraction-specific database operations.
    """

    def __init__(self, db_manager):
        """
        Initialize the attraction service.

        Args:
            db_manager: Database manager instance with connection pool
        """
        super().__init__(db_manager)
        self.table = "attractions"
        self.jsonb_fields = ['name', 'description', 'data', 'visiting_info',
                            'accessibility_info', 'historical_context']

    def get_attraction(self, attraction_id: int) -> Optional[Dict[str, Any]]:
        """
        Get attraction by ID.

        Args:
            attraction_id: ID of the attraction to retrieve

        Returns:
            dict: Attraction data or None if not found
        """
        logger.info(f"Called get_attraction for ID: {attraction_id}")
        return self.generic_get(self.table, attraction_id, self.jsonb_fields)

    def search_attractions(self, query: Optional[str] = None,
                          type_id: Optional[int] = None,
                          city_id: Optional[int] = None,
                          region_id: Optional[int] = None,
                          limit: int = 10,
                          offset: int = 0,
                          language: str = "en") -> List[Dict[str, Any]]:
        """
        Search attractions based on various criteria.

        Args:
            query: Text query to search for in name and description
            type_id: Type ID to filter by
            city_id: City ID to filter by
            region_id: Region ID to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination
            language: Language code (en, ar)

        Returns:
            list: List of attractions matching the criteria
        """
        logger.info(f"Called search_attractions with query={query}, type_id={type_id}, city_id={city_id}, region_id={region_id}")

        try:
            # Validate language parameter
            if language not in ["en", "ar"]:
                logger.warning(f"Invalid language '{language}', defaulting to 'en'")
                language = "en"

            # Build the base query
            base_query = "SELECT * FROM attractions WHERE 1=1"
            params = []

            # Apply filters
            if query:
                base_query += f" AND (name->>'{language}' ILIKE %s OR description->>'{language}' ILIKE %s)"
                query_pattern = f"%{query}%"
                params.extend([query_pattern, query_pattern])

            if type_id:
                base_query += " AND type_id = %s"
                params.append(type_id)

            if city_id:
                base_query += " AND city_id = %s"
                params.append(city_id)

            if region_id:
                base_query += " AND region_id = %s"
                params.append(region_id)

            # Add limit and offset
            base_query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            # Execute the query
            results = self.db.execute_postgres_query(base_query, tuple(params))

            # Parse JSON fields
            if results:
                for result in results:
                    for field in self.jsonb_fields:
                        self._parse_json_field(result, field)

            return results or []
        except Exception as e:
            return self._handle_error("search_attractions", e, return_empty_list=True)

    def find_attractions_near_location(self, latitude: float, longitude: float,
                                     radius_km: float = 10,
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find attractions near a specific location.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            radius_km: Radius in kilometers
            limit: Maximum number of results to return

        Returns:
            list: List of attractions near the location
        """
        logger.info(f"Called find_attractions_near_location with lat={latitude}, lon={longitude}, radius={radius_km}")

        try:
            # Check if PostGIS is available
            postgis_check = self.db.execute_postgres_query(
                "SELECT 1 FROM pg_extension WHERE extname = 'postgis'"
            )

            if not postgis_check:
                logger.warning("PostGIS extension not found, falling back to simple distance calculation")
                # Fallback to simple distance calculation using ST_X(geom) and ST_Y(geom)
                sql = """
                    SELECT *,
                    (6371 * acos(cos(radians(%s)) * cos(radians(ST_Y(geom))) * cos(radians(ST_X(geom)) - radians(%s)) + sin(radians(%s)) * sin(radians(ST_Y(geom))))) AS distance
                    FROM attractions
                    WHERE geom IS NOT NULL
                    HAVING distance < %s
                    ORDER BY distance
                    LIMIT %s
                """
                params = (latitude, longitude, latitude, radius_km, limit)
            else:
                # Use PostGIS for more accurate distance calculation
                sql = """
                    SELECT *,
                    ST_Distance(
                        geom::geography,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                    ) / 1000 AS distance
                    FROM attractions
                    WHERE geom IS NOT NULL
                    AND ST_DWithin(
                        geom::geography,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                        %s * 1000
                    )
                    ORDER BY distance
                    LIMIT %s
                """
                params = (longitude, latitude, longitude, latitude, radius_km, limit)

            # Execute the query
            results = self.db.execute_postgres_query(sql, params)

            # Parse JSON fields
            if results:
                for result in results:
                    for field in self.jsonb_fields:
                        self._parse_json_field(result, field)

            return results or []
        except Exception as e:
            return self._handle_error("find_attractions_near_location", e, return_empty_list=True)

    def create_attraction(self, attraction_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new attraction.

        Args:
            attraction_data: Dictionary containing attraction data

        Returns:
            int: ID of the created attraction or None if creation failed
        """
        logger.info("Called create_attraction")
        return self.generic_create(self.table, attraction_data)

    def update_attraction(self, attraction_id: int, attraction_data: Dict[str, Any]) -> bool:
        """
        Update an existing attraction.

        Args:
            attraction_id: ID of the attraction to update
            attraction_data: Dictionary containing updated attraction data

        Returns:
            bool: True if update was successful, False otherwise
        """
        logger.info(f"Called update_attraction for ID: {attraction_id}")
        return self.generic_update(self.table, attraction_id, attraction_data)

    def delete_attraction(self, attraction_id: int) -> bool:
        """
        Delete an attraction.

        Args:
            attraction_id: ID of the attraction to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        logger.info(f"Called delete_attraction for ID: {attraction_id}")
        return self.generic_delete(self.table, attraction_id)
