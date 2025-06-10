"""
Region Repository Module for the Egypt Tourism Chatbot.

This module provides a repository class for handling database operations related to regions.
"""
from typing import Any, Dict, List, Optional, Tuple, Union

from src.repositories.base_repository import BaseRepository
from src.knowledge.core.database_core import DatabaseCore
from src.utils.logger import get_logger

logger = get_logger(__name__)

class RegionRepository(BaseRepository):
    """
    Repository class for region-related database operations.

    This class extends the BaseRepository class to provide region-specific database operations.
    """

    def __init__(self, db_core: DatabaseCore):
        """
        Initialize the region repository.

        Args:
            db_core: Database core instance with connection pool
        """
        super().__init__(
            db_core=db_core,
            table_name="regions",
            jsonb_fields=['name', 'description', 'data']
        )

    def find_by_country(self, country: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Find regions by country.

        Args:
            country: Country to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            list: List of regions in the country
        """
        logger.info(f"Finding regions by country: {country}")
        return self.find(filters={"country": country}, limit=limit, offset=offset)

    def search_regions(self, query: Optional[str] = None,
                      country: Optional[str] = None,
                      limit: int = 10,
                      offset: int = 0,
                      language: str = "en") -> List[Dict[str, Any]]:
        """
        Search regions based on various criteria.

        Args:
            query: Text query to search for in name and description
            country: Country to filter by
            limit: Maximum number of results to return
            offset: Offset for pagination
            language: Language code (en, ar)

        Returns:
            list: List of regions matching the criteria
        """
        logger.info(f"Searching regions with query={query}, country={country}")

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

            if country:
                base_query += " AND country = %s"
                params.append(country)

            # Add ordering and pagination
            base_query += " ORDER BY name->>%s LIMIT %s OFFSET %s"
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
            return self._handle_error("search_regions", e, return_empty_list=True)

    def find_near_location(self, latitude: float, longitude: float,
                         radius_km: float = 10,
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find regions near a specific location.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            radius_km: Radius in kilometers
            limit: Maximum number of results to return

        Returns:
            list: List of regions near the location
        """
        logger.info(f"Finding regions near location: lat={latitude}, lon={longitude}, radius={radius_km}")
        return self.db.find_nearby(
            self.table_name, latitude, longitude, radius_km, limit
        ) 