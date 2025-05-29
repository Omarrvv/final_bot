"""
Knowledge Base Service

This module provides a service for accessing the tourism knowledge base.
It acts as a layer between the API and the database for content retrieval.
"""
import logging
from typing import Any, Dict, List, Optional, Union

from src.utils.logger import get_logger
from src.knowledge.knowledge_base import KnowledgeBase as CoreKnowledgeBase
from src.knowledge.database import DatabaseManager

logger = get_logger(__name__)


class KnowledgeBase:
    """
    Knowledge Base service for accessing tourism information.

    This class provides a service-oriented interface to the core KnowledgeBase implementation.
    It adapts the core implementation's interface to better suit API endpoints and provides
    simplified method signatures.
    """

    def __init__(self, db_manager: DatabaseManager = None):
        """
        Initialize the knowledge base service.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager or DatabaseManager()
        # Use the core KnowledgeBase implementation
        self.core_kb = CoreKnowledgeBase(db_manager=self.db_manager)
        logger.info("KnowledgeBase service initialized as adapter to core KnowledgeBase")

    def get_attraction(self, attraction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an attraction by its ID.

        Args:
            attraction_id: Attraction ID

        Returns:
            Attraction data as a dictionary, or None if not found
        """
        return self.core_kb.get_attraction_by_id(attraction_id)

    def search_attractions(
        self, name: str = None, city_id: str = None, attraction_type: str = None,
        limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for attractions based on filters.

        Args:
            name: Name to search for (partial match)
            city_id: City ID to filter by
            attraction_type: Type of attraction to filter by
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of attractions matching the filters
        """
        # Build filters dictionary
        filters = {}

        if name:
            # Use the name as a text search query if provided
            return self.core_kb.search_attractions(query=name, limit=limit)

        # Otherwise build a structured query
        if city_id:
            filters["city"] = city_id

        if attraction_type:
            filters["type"] = attraction_type

        return self.core_kb.search_attractions(filters=filters, limit=limit)

    def get_city(self, city_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a city by its ID.

        Args:
            city_id: City ID

        Returns:
            City data as a dictionary, or None if not found
        """
        return self.core_kb.get_record_by_id("cities", city_id)

    def search_cities(
        self, name: str = None, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for cities based on filters.

        Args:
            name: Name to search for (partial match)
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of cities matching the filters
        """
        filters = {}

        if name:
            filters["name"] = {"$like": f"%{name}%"}

        return self.core_kb.search_records("cities", filters, limit, offset)

    def get_hotel(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a hotel by its ID.

        Args:
            hotel_id: Hotel ID

        Returns:
            Hotel data as a dictionary, or None if not found
        """
        return self.core_kb.get_hotel_by_id(hotel_id)

    def search_hotels(
        self, name: str = None, city_id: str = None, stars: int = None,
        limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for hotels based on filters.

        Args:
            name: Name to search for (partial match)
            city_id: City ID to filter by
            stars: Minimum star rating
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of hotels matching the filters
        """
        filters = {}

        if name:
            if isinstance(name, str) and len(name) > 0:
                # Use name as a text query
                return self.core_kb.search_hotels(query=name, limit=limit)

        # Otherwise build a structured query
        if city_id:
            filters["city"] = city_id

        if stars is not None:
            filters["stars"] = {"$gte": stars}

        return self.core_kb.search_hotels(query=filters, limit=limit)

    def get_restaurant(self, restaurant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a restaurant by its ID.

        Args:
            restaurant_id: Restaurant ID

        Returns:
            Restaurant data as a dictionary, or None if not found
        """
        return self.core_kb.get_restaurant_by_id(restaurant_id)

    def search_restaurants(
        self, name: str = None, city_id: str = None, cuisine: str = None,
        limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for restaurants based on filters.

        Args:
            name: Name to search for (partial match)
            city_id: City ID to filter by
            cuisine: Cuisine type to filter by
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of restaurants matching the filters
        """
        filters = {}

        if name:
            if isinstance(name, str) and len(name) > 0:
                # Use name as a text query
                return self.core_kb.search_restaurants(query=name, limit=limit)

        # Otherwise build a structured query
        if city_id:
            filters["city"] = city_id

        if cuisine:
            filters["cuisine"] = cuisine

        return self.core_kb.search_restaurants(query=filters, limit=limit)

    def get_practical_info(self, info_id: str) -> Optional[Dict[str, Any]]:
        """
        Get practical information by its ID.

        Args:
            info_id: Practical information ID

        Returns:
            Practical information data as a dictionary, or None if not found
        """
        return self.core_kb.get_practical_info(category=info_id)

    def search_practical_info(
        self, keyword: str = None, category: str = None,
        limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for practical information based on filters.

        Args:
            keyword: Keyword to search for
            category: Category to filter by
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of practical information matching the filters
        """
        filters = {}

        if category:
            filters["category"] = category

        # Direct call to search_records for practical_info table
        # If keyword is provided, we should use enhanced_search or vector_search
        if keyword:
            # Use semantic search if available
            if hasattr(self.core_kb, "semantic_search"):
                return self.core_kb.semantic_search(
                    query=keyword,
                    table="practical_info",
                    limit=limit
                )

        # Otherwise use regular search
        return self.core_kb.search_records("practical_info", filters, limit, offset)

    def log_search(
        self, query: str, results_count: int, filters: Dict[str, Any] = None,
        session_id: str = None, user_id: Union[int, str] = None
    ) -> None:
        """
        Log a search event for analytics.

        Args:
            query: Search query
            results_count: Number of results returned
            filters: Search filters used
            session_id: Session ID
            user_id: User ID (integer or string)
        """
        self.core_kb.log_search(query, results_count, filters, session_id, user_id)

    def log_view(
        self, item_type: str, item_id: str, item_name: str = None,
        session_id: str = None, user_id: Union[int, str] = None
    ) -> None:
        """
        Log a view event for analytics.

        Args:
            item_type: Type of item viewed (attraction, city, hotel, etc.)
            item_id: ID of the item viewed
            item_name: Name of the item viewed
            session_id: Session ID
            user_id: User ID (integer or string)
        """
        self.core_kb.log_view(item_type, item_id, item_name, session_id, user_id)

    # Add additional proxy methods as needed
    def find_nearby_attractions(self, latitude: float, longitude: float,
                          radius_km: float = 5.0, limit: int = 10) -> List[Dict]:
        """Proxy method to find_nearby_attractions in the core implementation"""
        return self.core_kb.find_nearby_attractions(latitude, longitude, radius_km, limit)

    def find_nearby_restaurants(self, latitude: float, longitude: float,
                            radius_km: float = 3.0, limit: int = 10) -> List[Dict]:
        """Proxy method to find_nearby_restaurants in the core implementation"""
        return self.core_kb.find_nearby_restaurants(latitude, longitude, radius_km, limit)

    def find_attractions_near_hotel(self, hotel_id: str, radius_km: float = 3.0, limit: int = 10) -> List[Dict]:
        """Proxy method to find_attractions_near_hotel in the core implementation"""
        return self.core_kb.find_attractions_near_hotel(hotel_id, radius_km, limit)

    def find_restaurants_near_attraction(self, attraction_id: str, radius_km: float = 1.0, limit: int = 5) -> List[Dict]:
        """Proxy method to find_restaurants_near_attraction in the core implementation"""
        return self.core_kb.find_restaurants_near_attraction(attraction_id, radius_km, limit)

    def semantic_search(self, query: str, table: str = "attractions", limit: int = 10) -> List[Dict]:
        """Proxy method to semantic_search in the core implementation"""
        return self.core_kb.semantic_search(query, table, limit)

    def hybrid_search(self, query: str, table: str = "attractions", limit: int = 10) -> List[Dict]:
        """Proxy method to hybrid_search in the core implementation"""
        return self.core_kb.hybrid_search(query, table, limit)