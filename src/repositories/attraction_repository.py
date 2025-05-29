"""
Attraction Repository Module for the Egypt Tourism Chatbot.

This module provides a repository class for handling database operations related to attractions.
"""
from typing import Any, Dict, List, Optional, Tuple, Union

from src.repositories.base_repository import BaseRepository
from src.knowledge.database_core import DatabaseCore
from src.utils.logger import get_logger

logger = get_logger(__name__)

class AttractionRepository(BaseRepository):
    """
    Repository class for attraction-related database operations.

    This class extends the BaseRepository class to provide attraction-specific database operations.
    """

    def __init__(self, db_core: DatabaseCore):
        """
        Initialize the attraction repository.

        Args:
            db_core: Database core instance with connection pool
        """
        super().__init__(
            db_core=db_core,
            table_name="attractions",
            jsonb_fields=['name', 'description', 'data', 'visiting_info',
                         'accessibility_info', 'historical_context']
        )

    def find_by_type(self, type_id: int, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find attractions by type.

        Args:
            type_id: Type ID to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of attractions matching the type
        """
        logger.info(f"Finding attractions by type: {type_id}")
        return self.find(filters={"type_id": type_id}, limit=limit, offset=offset)

    def find_by_city(self, city_id: int, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find attractions by city.

        Args:
            city_id: City ID to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of attractions in the city
        """
        logger.info(f"Finding attractions by city: {city_id}")
        return self.find(filters={"city_id": city_id}, limit=limit, offset=offset)

    def find_by_region(self, region_id: int, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find attractions by region.

        Args:
            region_id: Region ID to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of attractions in the region
        """
        logger.info(f"Finding attractions by region: {region_id}")
        return self.find(filters={"region_id": region_id}, limit=limit, offset=offset)

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
        logger.info(f"Searching attractions with query={query}, type_id={type_id}, city_id={city_id}, region_id={region_id}")

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
            results = self.db.execute_query(base_query, tuple(params))

            # Parse JSON fields
            if results:
                for result in results:
                    for field in self.jsonb_fields:
                        self._parse_json_field(result, field)

            return results or []
        except Exception as e:
            return self._handle_error("search_attractions", e, return_empty_list=True)

    def find_near_location(self, latitude: float, longitude: float,
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
        logger.info(f"Finding attractions near location: lat={latitude}, lon={longitude}, radius={radius_km}")

        try:
            # Check if PostGIS is available
            postgis_check = self.db.execute_query(
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
            results = self.db.execute_query(sql, params)

            # Parse JSON fields
            if results:
                for result in results:
                    for field in self.jsonb_fields:
                        self._parse_json_field(result, field)

            return results or []
        except Exception as e:
            return self._handle_error("find_attractions_near_location", e, return_empty_list=True)
