"""
Accommodation Repository Module for the Egypt Tourism Chatbot.

This module provides a repository class for handling database operations related to accommodations.
"""
from typing import Any, Dict, List, Optional, Tuple, Union

from src.repositories.base_repository import BaseRepository
from src.knowledge.core.database_core import DatabaseCore
from src.utils.logger import get_logger

logger = get_logger(__name__)

class AccommodationRepository(BaseRepository):
    """
    Repository class for accommodation-related database operations.

    This class extends the BaseRepository class to provide accommodation-specific database operations.
    """

    def __init__(self, db_core: DatabaseCore):
        """
        Initialize the accommodation repository.

        Args:
            db_core: Database core instance with connection pool
        """
        super().__init__(
            db_core=db_core,
            table_name="accommodations",
            jsonb_fields=['name', 'description', 'data']
        )

    def find_by_type(self, type_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find accommodations by type.

        Args:
            type_id: Type ID to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of accommodations matching the type
        """
        logger.info(f"Finding accommodations by type: {type_id}")
        return self.find(filters={"type_id": type_id}, limit=limit, offset=offset)

    def find_by_city(self, city_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find accommodations by city.

        Args:
            city_id: City ID to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of accommodations in the city
        """
        logger.info(f"Finding accommodations by city: {city_id}")
        return self.find(filters={"city_id": city_id}, limit=limit, offset=offset)

    def find_by_region(self, region_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find accommodations by region.

        Args:
            region_id: Region ID to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of accommodations in the region
        """
        logger.info(f"Finding accommodations by region: {region_id}")
        return self.find(filters={"region_id": region_id}, limit=limit, offset=offset)

    def find_by_stars(self, stars: int, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find accommodations by star rating.

        Args:
            stars: Star rating to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of accommodations with the specified star rating
        """
        logger.info(f"Finding accommodations with {stars} stars")
        return self.find(filters={"stars": stars}, limit=limit, offset=offset)

    def find_by_price_range(self, min_price: Optional[float] = None, 
                           max_price: Optional[float] = None,
                           limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find accommodations within a price range.

        Args:
            min_price: Minimum price to filter by
            max_price: Maximum price to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of accommodations within the price range
        """
        logger.info(f"Finding accommodations with price range: {min_price} - {max_price}")
        
        try:
            # Build the base query
            base_query = f"SELECT * FROM {self.table_name} WHERE 1=1"
            params = []

            # Apply price filters
            if min_price is not None:
                base_query += " AND price_min >= %s"
                params.append(min_price)

            if max_price is not None:
                base_query += " AND price_max <= %s"
                params.append(max_price)

            # Add ordering and pagination
            base_query += " ORDER BY price_min ASC LIMIT %s OFFSET %s"
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
            return self._handle_error("find_by_price_range", e, return_empty_list=True)

    def search_accommodations(self, query: Optional[str] = None,
                            type_id: Optional[str] = None,
                            city_id: Optional[str] = None,
                            region_id: Optional[str] = None,
                            stars: Optional[int] = None,
                            min_price: Optional[float] = None,
                            max_price: Optional[float] = None,
                            limit: int = 10,
                            offset: int = 0,
                            language: str = "en") -> List[Dict[str, Any]]:
        """
        Search accommodations based on various criteria.

        Args:
            query: Text query to search for in name and description
            type_id: Type ID to filter by
            city_id: City ID to filter by
            region_id: Region ID to filter by
            stars: Star rating to filter by
            min_price: Minimum price to filter by
            max_price: Maximum price to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination
            language: Language code (en, ar)

        Returns:
            list: List of accommodations matching the criteria
        """
        logger.info(f"Searching accommodations with query={query}, type_id={type_id}, city_id={city_id}")

        try:
            # Validate language parameter
            if language not in ["en", "ar"]:
                logger.warning(f"Invalid language '{language}', defaulting to 'en'")
                language = "en"

            # Build the base query
            base_query = f"SELECT * FROM {self.table_name} WHERE 1=1"
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

            if stars:
                base_query += " AND stars = %s"
                params.append(stars)

            if min_price is not None:
                base_query += " AND price_min >= %s"
                params.append(min_price)

            if max_price is not None:
                base_query += " AND price_max <= %s"
                params.append(max_price)

            # Add ordering and pagination
            base_query += " ORDER BY stars DESC, price_min ASC, name->>%s LIMIT %s OFFSET %s"
            params.extend([language, limit, offset])

            # Execute the query
            results = self.db.execute_query(base_query, tuple(params))

            # Parse JSON fields
            if results:
                for result in results:
                    for field in self.jsonb_fields:
                        self._parse_json_field(result, field)

            return results or []
        except Exception as e:
            return self._handle_error("search_accommodations", e, return_empty_list=True)

    def find_near_location(self, latitude: float, longitude: float,
                         radius_km: float = 10,
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find accommodations near a specific location.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            radius_km: Radius in kilometers
            limit: Maximum number of results to return

        Returns:
            list: List of accommodations near the location
        """
        logger.info(f"Finding accommodations near location: lat={latitude}, lon={longitude}, radius={radius_km}")
        return self.db.find_nearby(
            self.table_name, latitude, longitude, radius_km, limit
        ) 