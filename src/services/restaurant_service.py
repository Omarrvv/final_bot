"""
Restaurant service for database operations.

This module provides a service class for handling database operations related to restaurants.
"""
from typing import Any, Dict, List, Optional, Tuple, Union

from src.services.base_service import BaseService
from src.utils.logger import get_logger

logger = get_logger(__name__)

class RestaurantService(BaseService):
    """
    Service class for restaurant-related database operations.

    This class extends the BaseService class to provide restaurant-specific database operations.
    """

    def __init__(self, db_manager):
        """
        Initialize the restaurant service.

        Args:
            db_manager: Database manager instance with connection pool
        """
        super().__init__(db_manager)
        self.table = "restaurants"
        self.jsonb_fields = ['name', 'description', 'data']

    def get_restaurant(self, restaurant_id: int) -> Optional[Dict[str, Any]]:
        """
        Get restaurant by ID.

        Args:
            restaurant_id: ID of the restaurant to retrieve

        Returns:
            dict: Restaurant data or None if not found
        """
        logger.info(f"Called get_restaurant for ID: {restaurant_id}")
        return self.generic_get(self.table, restaurant_id, self.jsonb_fields)

    def search_restaurants(self, query: Optional[str] = None,
                          cuisine_id: Optional[int] = None,
                          city_id: Optional[int] = None,
                          region_id: Optional[int] = None,
                          price_range: Optional[str] = None,
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
            limit: Maximum number of results to return
            offset: Offset for pagination
            language: Language code (en, ar)

        Returns:
            list: List of restaurants matching the criteria
        """
        logger.info(f"Called search_restaurants with query={query}, cuisine_id={cuisine_id}, city_id={city_id}, region_id={region_id}")

        try:
            # Validate language parameter
            if language not in ["en", "ar"]:
                logger.warning(f"Invalid language '{language}', defaulting to 'en'")
                language = "en"

            # Build the base query
            base_query = "SELECT * FROM restaurants WHERE 1=1"
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
            return self._handle_error("search_restaurants", e, return_empty_list=True)

    def find_restaurants_near_location(self, latitude: float, longitude: float,
                                     radius_km: float = 5,
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
        logger.info(f"Called find_restaurants_near_location with lat={latitude}, lon={longitude}, radius={radius_km}")

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
                    FROM restaurants
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
                    FROM restaurants
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
            return self._handle_error("find_restaurants_near_location", e, return_empty_list=True)

    def find_restaurants_near_attraction(self, attraction_id: int,
                                       radius_km: float = 2,
                                       limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find restaurants near a specific attraction.

        Args:
            attraction_id: ID of the attraction
            radius_km: Radius in kilometers
            limit: Maximum number of results to return

        Returns:
            list: List of restaurants near the attraction
        """
        logger.info(f"Called find_restaurants_near_attraction with attraction_id={attraction_id}, radius={radius_km}")

        try:
            # Get the attraction's location
            attraction_sql = """
                SELECT ST_X(geom) as longitude, ST_Y(geom) as latitude
                FROM attractions
                WHERE id = %s AND geom IS NOT NULL
            """
            attraction = self.db.execute_postgres_query(attraction_sql, (attraction_id,), fetchall=False)

            if not attraction:
                logger.warning(f"Attraction {attraction_id} not found or has no location data")
                return []

            # Use the location to find nearby restaurants
            return self.find_restaurants_near_location(
                attraction["latitude"],
                attraction["longitude"],
                radius_km,
                limit
            )
        except Exception as e:
            return self._handle_error("find_restaurants_near_attraction", e, return_empty_list=True)

    def create_restaurant(self, restaurant_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new restaurant.

        Args:
            restaurant_data: Dictionary containing restaurant data

        Returns:
            int: ID of the created restaurant or None if creation failed
        """
        logger.info("Called create_restaurant")
        return self.generic_create(self.table, restaurant_data)

    def update_restaurant(self, restaurant_id: int, restaurant_data: Dict[str, Any]) -> bool:
        """
        Update an existing restaurant.

        Args:
            restaurant_id: ID of the restaurant to update
            restaurant_data: Dictionary containing updated restaurant data

        Returns:
            bool: True if update was successful, False otherwise
        """
        logger.info(f"Called update_restaurant for ID: {restaurant_id}")
        return self.generic_update(self.table, restaurant_id, restaurant_data)

    def delete_restaurant(self, restaurant_id: int) -> bool:
        """
        Delete a restaurant.

        Args:
            restaurant_id: ID of the restaurant to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        logger.info(f"Called delete_restaurant for ID: {restaurant_id}")
        return self.generic_delete(self.table, restaurant_id)
