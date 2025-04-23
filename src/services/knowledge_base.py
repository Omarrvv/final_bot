"""
Knowledge Base Service

This module provides a service for accessing the tourism knowledge base.
It acts as a layer between the API and the database for content retrieval.
"""
import json
from typing import Any, Dict, List, Optional
import logging

from src.utils.logger import get_logger
from src.utils.database import DatabaseManager

logger = get_logger(__name__)


class KnowledgeBase:
    """
    Knowledge Base service for accessing tourism information.
    
    This class provides methods for retrieving information about
    attractions, cities, hotels, restaurants, and practical information.
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        """
        Initialize the knowledge base service.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager or DatabaseManager()
        logger.info("KnowledgeBase service initialized")
    
    def get_attraction(self, attraction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an attraction by its ID.
        
        Args:
            attraction_id: Attraction ID
            
        Returns:
            Attraction data as a dictionary, or None if not found
        """
        try:
            attraction = self.db_manager.get_attraction_by_id(attraction_id)
            
            if attraction:
                logger.info(f"Retrieved attraction {attraction_id}")
                return attraction
            
            logger.warning(f"Attraction {attraction_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving attraction {attraction_id}: {str(e)}")
            return None
    
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
        try:
            # Build filters dictionary
            filters = {}
            
            if name:
                filters["name"] = name
            
            if city_id:
                filters["city_id"] = city_id
            
            if attraction_type:
                filters["type"] = attraction_type
            
            attractions = self.db_manager.search_attractions(filters, limit, offset)
            
            logger.info(f"Found {len(attractions)} attractions matching filters")
            return attractions
        except Exception as e:
            logger.error(f"Error searching attractions: {str(e)}")
            return []
    
    def get_city(self, city_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a city by its ID.
        
        Args:
            city_id: City ID
            
        Returns:
            City data as a dictionary, or None if not found
        """
        try:
            city = self.db_manager.get_city_by_id(city_id)
            
            if city:
                logger.info(f"Retrieved city {city_id}")
                return city
            
            logger.warning(f"City {city_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving city {city_id}: {str(e)}")
            return None
    
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
        try:
            # Build filters dictionary
            filters = {}
            
            if name:
                filters["name"] = name
            
            cities = self.db_manager.search_cities(filters, limit, offset)
            
            logger.info(f"Found {len(cities)} cities matching filters")
            return cities
        except Exception as e:
            logger.error(f"Error searching cities: {str(e)}")
            return []
    
    def get_hotel(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a hotel by its ID.
        
        Args:
            hotel_id: Hotel ID
            
        Returns:
            Hotel data as a dictionary, or None if not found
        """
        try:
            hotel = self.db_manager.get_hotel_by_id(hotel_id)
            
            if hotel:
                logger.info(f"Retrieved hotel {hotel_id}")
                return hotel
            
            logger.warning(f"Hotel {hotel_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving hotel {hotel_id}: {str(e)}")
            return None
    
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
        try:
            # Build filters dictionary
            filters = {}
            
            if name:
                filters["name"] = name
            
            if city_id:
                filters["city_id"] = city_id
            
            if stars is not None:
                filters["stars"] = stars
            
            hotels = self.db_manager.search_hotels(filters, limit, offset)
            
            logger.info(f"Found {len(hotels)} hotels matching filters")
            return hotels
        except Exception as e:
            logger.error(f"Error searching hotels: {str(e)}")
            return []
    
    def get_restaurant(self, restaurant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a restaurant by its ID.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            Restaurant data as a dictionary, or None if not found
        """
        try:
            restaurant = self.db_manager.get_restaurant_by_id(restaurant_id)
            
            if restaurant:
                logger.info(f"Retrieved restaurant {restaurant_id}")
                return restaurant
            
            logger.warning(f"Restaurant {restaurant_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving restaurant {restaurant_id}: {str(e)}")
            return None
    
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
        try:
            # Build filters dictionary
            filters = {}
            
            if name:
                filters["name"] = name
            
            if city_id:
                filters["city_id"] = city_id
            
            if cuisine:
                filters["cuisine"] = cuisine
            
            restaurants = self.db_manager.search_restaurants(filters, limit, offset)
            
            logger.info(f"Found {len(restaurants)} restaurants matching filters")
            return restaurants
        except Exception as e:
            logger.error(f"Error searching restaurants: {str(e)}")
            return []
    
    def get_practical_info(self, info_id: str) -> Optional[Dict[str, Any]]:
        """
        Get practical information by its ID.
        
        Args:
            info_id: Practical information ID
            
        Returns:
            Practical information data as a dictionary, or None if not found
        """
        try:
            info = self.db_manager.get_practical_info(info_id)
            
            if info:
                logger.info(f"Retrieved practical info {info_id}")
                return info
            
            logger.warning(f"Practical info {info_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving practical info {info_id}: {str(e)}")
            return None
    
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
        try:
            # Build filters dictionary
            filters = {}
            
            if keyword:
                filters["keyword"] = keyword
            
            if category:
                filters["category"] = category
            
            info_items = self.db_manager.search_practical_info(filters, limit, offset)
            
            logger.info(f"Found {len(info_items)} practical info items matching filters")
            return info_items
        except Exception as e:
            logger.error(f"Error searching practical info: {str(e)}")
            return []
    
    def log_search(
        self, query: str, results_count: int, filters: Dict[str, Any] = None,
        session_id: str = None, user_id: str = None
    ) -> None:
        """
        Log a search event for analytics.
        
        Args:
            query: Search query
            results_count: Number of results returned
            filters: Search filters used
            session_id: Session ID
            user_id: User ID
        """
        try:
            event_data = {
                "query": query,
                "results_count": results_count,
                "filters": filters or {}
            }
            
            self.db_manager.log_analytics_event(
                "search", event_data, session_id, user_id
            )
            
            logger.debug(f"Logged search event: {query}")
        except Exception as e:
            logger.error(f"Error logging search event: {str(e)}")
    
    def log_view(
        self, item_type: str, item_id: str, item_name: str = None,
        session_id: str = None, user_id: str = None
    ) -> None:
        """
        Log a view event for analytics.
        
        Args:
            item_type: Type of item viewed (attraction, city, hotel, etc.)
            item_id: ID of the item viewed
            item_name: Name of the item viewed
            session_id: Session ID
            user_id: User ID
        """
        try:
            event_data = {
                "item_type": item_type,
                "item_id": item_id,
                "item_name": item_name
            }
            
            self.db_manager.log_analytics_event(
                "view", event_data, session_id, user_id
            )
            
            logger.debug(f"Logged view event: {item_type} {item_id}")
        except Exception as e:
            logger.error(f"Error logging view event: {str(e)}") 