"""
Restaurant Repository Module for the Egypt Tourism Chatbot.

This module provides a repository class for handling database operations related to restaurants.
"""
from typing import Any, Dict, List, Optional, Tuple, Union

from src.repositories.base_repository import BaseRepository
from src.knowledge.core.database_core import DatabaseCore
from src.utils.logger import get_logger

logger = get_logger(__name__)

class RestaurantRepository(BaseRepository):
    """
    Repository class for restaurant-related database operations.

    This class extends the BaseRepository class to provide restaurant-specific database operations.
    """

    def __init__(self, db_core: DatabaseCore):
        """
        Initialize the restaurant repository.

        Args:
            db_core: Database core instance with connection pool
        """
        super().__init__(
            db_core=db_core,
            table_name="restaurants",
            jsonb_fields=['name', 'description', 'data']
        )

    def find_by_cuisine(self, cuisine_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find restaurants by cuisine type.

        Args:
            cuisine_id: Cuisine ID to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of restaurants matching the cuisine type
        """
        logger.info(f"Finding restaurants by cuisine: {cuisine_id}")
        return self.find(filters={"cuisine_id": cuisine_id}, limit=limit, offset=offset)

    def find_by_city(self, city_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find restaurants by city.

        Args:
            city_id: City ID to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of restaurants in the city
        """
        logger.info(f"Finding restaurants by city: {city_id}")
        return self.find(filters={"city_id": city_id}, limit=limit, offset=offset)

    def find_by_region(self, region_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find restaurants by region.

        Args:
            region_id: Region ID to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of restaurants in the region
        """
        logger.info(f"Finding restaurants by region: {region_id}")
        return self.find(filters={"region_id": region_id}, limit=limit, offset=offset)

    def find_by_price_range(self, price_range: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find restaurants by price range.

        Args:
            price_range: Price range to filter by (e.g., '$', '$$', '$$$', '$$$$')
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of restaurants in the price range
        """
        logger.info(f"Finding restaurants by price range: {price_range}")
        return self.find(filters={"price_range": price_range}, limit=limit, offset=offset)

    def find_by_rating(self, min_rating: float, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find restaurants with minimum rating.

        Args:
            min_rating: Minimum rating to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of restaurants with rating >= min_rating
        """
        logger.info(f"Finding restaurants with rating >= {min_rating}")
        try:
            sql = f"""
                SELECT * FROM {self.table_name} 
                WHERE rating >= %s 
                ORDER BY rating DESC 
                LIMIT %s OFFSET %s
            """
            results = self.db.execute_query(sql, (min_rating, limit, offset))

            # Parse JSON fields
            if results:
                for result in results:
                    for field in self.jsonb_fields:
                        self._parse_json_field(result, field)

            return results or []
        except Exception as e:
            return self._handle_error("find_by_rating", e, return_empty_list=True)

    def search_restaurants(self, query: Optional[str] = None,
                          cuisine_id: Optional[str] = None,
                          city_id: Optional[str] = None,
                          region_id: Optional[str] = None,
                          price_range: Optional[str] = None,
                          min_rating: Optional[float] = None,
                          limit: int = 10,
                          offset: int = 0,
                          language: str = "en") -> List[Dict[str, Any]]:
        """
        Search restaurants based on various criteria.

        Args:
            query: Text query to search for in name and description
            cuisine_id: Cuisine ID to filter by
            city_id: City ID to filter by
            region_id: Region ID to filter by
            price_range: Price range to filter by
            min_rating: Minimum rating to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination
            language: Language code (en, ar)

        Returns:
            list: List of restaurants matching the criteria
        """
        logger.info(f"Searching restaurants with query={query}, cuisine_id={cuisine_id}, city_id={city_id}")

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

            if cuisine_id:
                base_query += " AND cuisine_id = %s"
                params.append(cuisine_id)

            if city_id:
                base_query += " AND city_id = %s"
                params.append(city_id)

            if region_id:
                base_query += " AND region_id = %s"
                params.append(region_id)

            if price_range:
                base_query += " AND price_range = %s"
                params.append(price_range)

            if min_rating:
                base_query += " AND rating >= %s"
                params.append(min_rating)

            # Add ordering and pagination
            base_query += " ORDER BY rating DESC, name->>%s LIMIT %s OFFSET %s"
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
            return self._handle_error("search_restaurants", e, return_empty_list=True)

    def find_near_location(self, latitude: float, longitude: float,
                         radius_km: float = 10,
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find restaurants near a specific location.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            radius_km: Radius in kilometers
            limit: Maximum number of results to return

        Returns:
            list: List of restaurants near the location
        """
        logger.info(f"Finding restaurants near location: lat={latitude}, lon={longitude}, radius={radius_km}")
        return self.db.find_nearby(
            self.table_name, latitude, longitude, radius_km, limit
        ) 