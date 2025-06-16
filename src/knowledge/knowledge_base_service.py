"""
Knowledge base service module.
This module provides knowledge base services for the knowledge layer.
"""

from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    """Knowledge base service for knowledge layer operations."""
    
    def __init__(self, db_manager, vector_db_uri: Optional[str] = None, content_path: Optional[str] = None):
        """Initialize with direct database manager to avoid circular imports."""
        self.db_manager = db_manager
        self.vector_db_uri = vector_db_uri
        self.content_path = content_path
        logger.info("KnowledgeBaseService initialized without circular dependencies")
    
    def get_knowledge_base(self):
        """Get the underlying knowledge base - returns self to avoid circular dependency."""
        return self
    
    def search_attractions(self, query: str = "", filters: Optional[Dict] = None, 
                          language: str = "en", limit: int = 10) -> List[Dict]:
        """Search attractions using database manager directly."""
        try:
            return self.db_manager.search_attractions(query, filters, limit, 0, language) or []
        except Exception as e:
            logger.error(f"Error searching attractions: {e}")
            return []
    
    def search_restaurants(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search restaurants using database manager directly."""
        try:
            return self.db_manager.search_restaurants(query, None, limit, 0, language) or []
        except Exception as e:
            logger.error(f"Error searching restaurants: {e}")
            return []
    
    def search_hotels(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search hotels using database manager directly."""
        try:
            return self.db_manager.search_hotels(query, None, limit, 0, language) or []
        except Exception as e:
            logger.error(f"Error searching hotels: {e}")
            return []
    
    # ========================================================================
    # Additional methods required by KnowledgeBase facade
    # ========================================================================
    
    def get_attraction_by_id(self, attraction_id: int) -> Optional[Dict]:
        """Get attraction by ID."""
        try:
            return self.db_manager.get_attraction(attraction_id)
        except Exception as e:
            logger.error(f"Error getting attraction {attraction_id}: {e}")
            return None
    
    def get_restaurant_by_id(self, restaurant_id: str) -> Optional[Dict]:
        """Get restaurant by ID."""
        try:
            return self.db_manager.get_restaurant(restaurant_id)
        except Exception as e:
            logger.error(f"Error getting restaurant {restaurant_id}: {e}")
            return None
    
    def get_hotel_by_id(self, hotel_id: str) -> Optional[Dict]:
        """Get hotel by ID."""
        try:
            return self.db_manager.get_accommodation(hotel_id)
        except Exception as e:
            logger.error(f"Error getting hotel {hotel_id}: {e}")
            return None
    
    def get_record_by_id(self, table_name: str, record_id: Any) -> Optional[Dict]:
        """Get record by table and ID."""
        try:
            return self.db_manager.generic_get(table_name, record_id)
        except Exception as e:
            logger.error(f"Error getting {table_name} record {record_id}: {e}")
            return None
    
    def search_practical_info(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search practical info."""
        try:
            query_str = query.get('text', '') if isinstance(query, dict) else str(query or '')
            return self.db_manager.search_practical_info(query_str, None, limit, 0, language) or []
        except Exception as e:
            logger.error(f"Error searching practical info: {e}")
            return []
    
    def search_faqs(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search FAQs."""
        try:
            query_str = query.get('text', '') if isinstance(query, dict) else str(query or '')
            return self.db_manager.search_tourism_faqs(query_str, None, limit, 0, language) or []
        except Exception as e:
            logger.error(f"Error searching FAQs: {e}")
            return []
    
    def search_events(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search events."""
        try:
            query_str = query.get('text', '') if isinstance(query, dict) else str(query or '')
            return self.db_manager.search_events_festivals(query_str, None, None, None, None, limit, 0, language) or []
        except Exception as e:
            logger.error(f"Error searching events: {e}")
            return []
    
    def search_events_festivals(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search events and festivals."""
        try:
            query_str = query.get('text', '') if isinstance(query, dict) else str(query or '')
            category_id = query.get('category_id') if isinstance(query, dict) else None
            destination_id = query.get('destination_id') if isinstance(query, dict) else None
            return self.db_manager.search_events_festivals(query_str, category_id, destination_id, None, None, limit, 0, language) or []
        except Exception as e:
            logger.error(f"Error searching events festivals: {e}")
            return []
    
    def search_itineraries(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search itineraries."""
        try:
            # Return empty list as itineraries might not be implemented
            return []
        except Exception as e:
            logger.error(f"Error searching itineraries: {e}")
            return []
    
    def search_tour_packages(self, query: Dict = None, category_id: str = None, min_duration: int = None, max_duration: int = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search tour packages."""
        try:
            query_str = query.get('text', '') if isinstance(query, dict) else str(query or '')
            return self.db_manager.search_tour_packages(query_str, category_id, min_duration, max_duration, limit, 0, language) or []
        except Exception as e:
            logger.error(f"Error searching tour packages: {e}")
            return []
    
    def search_transportation(self, query: Dict = None, origin: str = None, destination: str = None, transportation_type: str = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search transportation."""
        try:
            # Return empty list as transportation search might not be fully implemented
            return []
        except Exception as e:
            logger.error(f"Error searching transportation: {e}")
            return []
    
    def search_records(self, table_name: str, filters: Dict = None, limit: int = 10, offset: int = 0) -> List[Dict]:
        """Generic record search."""
        try:
            return self.db_manager.generic_search(table_name, filters, limit, offset) or []
        except Exception as e:
            logger.error(f"Error searching {table_name}: {e}")
            return []
    
    def lookup_location(self, location_name: str, language: str = "en") -> Optional[Dict]:
        """Lookup location."""
        try:
            cities = self.db_manager.search_cities({'name': location_name}, limit=1)
            return cities[0] if cities else None
        except Exception as e:
            logger.error(f"Error looking up location {location_name}: {e}")
            return None
    
    def lookup_attraction(self, attraction_name: str, language: str = "en") -> Optional[Dict]:
        """Lookup attraction."""
        try:
            attractions = self.db_manager.search_attractions(attraction_name, None, 1, 0, language)
            return attractions[0] if attractions else None
        except Exception as e:
            logger.error(f"Error looking up attraction {attraction_name}: {e}")
            return None
    
    def get_practical_info(self, category: str, language: str = "en") -> Optional[Dict]:
        """Get practical info by category."""
        try:
            info = self.db_manager.search_practical_info(category, category, 1, 0, language)
            return info[0] if info else None
        except Exception as e:
            logger.error(f"Error getting practical info {category}: {e}")
            return None
    
    # Geospatial and relationship methods (stub implementations)
    def find_nearby_attractions(self, latitude: float, longitude: float, radius_km: float = 5.0, limit: int = 10) -> List[Dict]:
        """Find nearby attractions."""
        return []
    
    def find_nearby_restaurants(self, latitude: float, longitude: float, radius_km: float = 3.0, limit: int = 10) -> List[Dict]:
        """Find nearby restaurants."""
        return []
    
    def find_nearby_accommodations(self, latitude: float, longitude: float, radius_km: float = 3.0, limit: int = 10) -> List[Dict]:
        """Find nearby accommodations."""
        return []
    
    def get_attractions_in_city(self, city_name: str, limit: int = 10, language: str = "en") -> List[Dict]:
        """Get attractions in city."""
        return []
    
    def get_restaurants_in_city(self, city_name: str, limit: int = 10, language: str = "en") -> List[Dict]:
        """Get restaurants in city."""
        return []
    
    def get_accommodations_in_city(self, city_name: str, limit: int = 10, language: str = "en") -> List[Dict]:
        """Get accommodations in city."""
        return []
    
    def find_attractions_near_hotel(self, hotel_id: str, radius_km: float = 3.0, limit: int = 10) -> List[Dict]:
        """Find attractions near hotel."""
        return []
    
    def find_restaurants_near_attraction(self, attraction_id: str = None, attraction_name: str = None, city: str = None, radius_km: float = 1.0, limit: int = 5) -> List[Dict]:
        """Find restaurants near attraction."""
        return []
    
    def find_events_near_attraction(self, attraction_id: str = None, attraction_name: str = None, city: str = None, limit: int = 5) -> List[Dict]:
        """Find events near attraction."""
        return []
    
    def find_attractions_in_itinerary_cities(self, itinerary_id: int = None, itinerary_name: str = None, limit: int = 10) -> Dict[str, List[Dict]]:
        """Find attractions in itinerary cities."""
        return {}
    
    def find_related_attractions(self, attraction_id: int = None, attraction_name: str = None, limit: int = 5) -> List[Dict]:
        """Find related attractions."""
        return []
    
    def find_hotels_near_attraction(self, attraction_id: str = None, attraction_name: str = None, city: str = None, radius_km: float = 1.0, limit: int = 5) -> List[Dict]:
        """Find hotels near attraction."""
        return []
    
    def semantic_search(self, query: str, table: str = "attractions", limit: int = 10) -> List[Dict]:
        """Semantic search."""
        try:
            return self.db_manager.semantic_search(query, table, limit) or []
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def hybrid_search(self, query: str, table: str = "attractions", limit: int = 10) -> List[Dict]:
        """Hybrid search."""
        try:
            # Use semantic search as fallback
            return self.semantic_search(query, table, limit)
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
    
    def log_search(self, query: str, results_count: int, filters: Dict[str, Any] = None, session_id: str = None, user_id: str = None) -> None:
        """Log search operation."""
        logger.info(f"Search logged: query='{query}', results={results_count}, session={session_id}")
    
    def log_view(self, item_type: str, item_id: str, item_name: str = None, session_id: str = None, user_id: str = None) -> None:
        """Log view operation."""
        logger.info(f"View logged: {item_type}={item_id}, session={session_id}")
    
    def debug_entity(self, entity_name: str, entity_type: str = "attraction", language: str = "en") -> Dict:
        """Debug entity lookup."""
        return {"entity_name": entity_name, "entity_type": entity_type, "debug": True}
    
    def get_facade_metrics(self) -> Dict[str, Any]:
        """Get facade metrics."""
        return {"service": "KnowledgeBaseService", "status": "active", "circular_dependency": "resolved"}

# For backward compatibility
def get_knowledge_base_service(db_manager, vector_db_uri: Optional[str] = None, content_path: Optional[str] = None) -> KnowledgeBaseService:
    """Factory function to create knowledge base service."""
    return KnowledgeBaseService(db_manager, vector_db_uri, content_path) 