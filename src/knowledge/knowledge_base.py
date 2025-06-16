"""
Clean KnowledgeBase Facade Shell (Phase 5)

This file replaces the 4,028-line god object with a clean 400-line facade
that delegates all operations to the new facade architecture while preserving
100% API compatibility.

Target: 400 lines (90% reduction from original)
"""
import logging
from typing import Dict, List, Any, Optional
from functools import lru_cache

# Import the service layer
from .knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger(__name__)

@lru_cache(maxsize=10)
def _load_json_data(file_path: str) -> Optional[Dict]:
    """
    Load and cache JSON data from file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Dict containing loaded data or None if error
    """
    try:
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
    return None

class KnowledgeBase:
    """
    Legacy wrapper - use KnowledgeBaseService directly for new code.
    
    This shell maintains API compatibility while delegating to the service layer.
    
    **DEPRECATED**: This wrapper will be removed in future versions.
    Use KnowledgeBaseService from src.services.knowledge_base_service instead.
    
    All 35+ public methods are preserved with identical signatures for compatibility.
    """
    
    def __init__(self, db_manager: Any, vector_db_uri: Optional[str] = None, content_path: Optional[str] = None):
        """Initialize KnowledgeBase with service delegation."""
        logger.info("🧹 Phase 5: Creating clean KnowledgeBase wrapper shell")
        
        # Initialize the service layer
        self._service = KnowledgeBaseService(db_manager, vector_db_uri, content_path)
        
        # Store original parameters for compatibility
        self.db_manager = db_manager
        self.vector_db_uri = vector_db_uri
        self.content_path = content_path
        
        logger.info(f"✅ Clean KnowledgeBase ready (service: {type(self._service).__name__})")
    
    # ========================================================================
    # Core Entity Retrieval Methods
    # ========================================================================
    
    def get_attraction_by_id(self, attraction_id: int) -> Optional[Dict]:
        """Get attraction by ID."""
        return self._service.get_attraction_by_id(attraction_id)
    
    def get_restaurant_by_id(self, restaurant_id: str) -> Optional[Dict]:
        """Get restaurant by ID."""
        return self._service.get_restaurant_by_id(restaurant_id)
    
    def get_hotel_by_id(self, hotel_id: str) -> Optional[Dict]:
        """Get hotel by ID."""
        return self._service.get_hotel_by_id(hotel_id)
    
    def get_record_by_id(self, table_name, record_id):
        """Get any record by table name and ID."""
        return self._service.get_record_by_id(table_name, record_id)
    
    # ========================================================================
    # Search Methods
    # ========================================================================
    
    def search_attractions(self, query: str = "", filters: Optional[Dict] = None, 
                          language: str = "en", limit: int = 10) -> List[Dict]:
        """Search attractions."""
        return self._service.search_attractions(query, filters, language, limit)
    
    def search_restaurants(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search restaurants."""
        return self._service.search_restaurants(query, limit, language)
    
    def search_hotels(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search hotels."""
        return self._service.search_hotels(query, limit, language)
    
    def search_practical_info(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search practical information."""
        return self._service.search_practical_info(query, limit, language)
    
    def search_faqs(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search FAQs."""
        return self._service.search_faqs(query, limit, language)
    
    def search_events(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search events."""
        return self._service.search_events(query=query, limit=limit, language=language)
    
    def search_events_festivals(self, query: Dict = None, category_id: str = None,
                              destination_id: str = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search events and festivals."""
        # Convert Dict query to string for database layer compatibility
        # and merge additional parameters into the query
        final_query = {}
        
        if query and isinstance(query, dict):
            final_query.update(query)
        elif isinstance(query, str):
            final_query['text'] = query
            
        # Add category and destination filters if provided
        if category_id:
            final_query['category_id'] = category_id
        if destination_id:
            final_query['destination_id'] = destination_id
            
        return self._service.search_events_festivals(final_query, limit, language)
    
    def search_itineraries(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search itineraries."""
        return self._service.search_itineraries(query, limit, language)
    
    def search_tour_packages(self, query: Dict = None, category_id: str = None,
                           min_duration: int = None, max_duration: int = None,
                           limit: int = 10, language: str = "en") -> List[Dict]:
        """Search tour packages."""
        return self._service.search_tour_packages(query, category_id, min_duration, max_duration, limit, language)
    
    def search_transportation(self, query: Dict = None, origin: str = None, destination: str = None,
                            transportation_type: str = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search transportation options."""
        return self._service.search_transportation(query, origin, destination, transportation_type, limit, language)
    
    def search_records(self, table_name, filters=None, limit=10, offset=0):
        """Generic record search."""
        return self._service.search_records(table_name, filters, limit, offset)
    
    # ========================================================================
    # Lookup Methods
    # ========================================================================
    
    def lookup_location(self, location_name: str, language: str = "en") -> Optional[Dict]:
        """Lookup location by name."""
        return self._service.lookup_location(location_name, language)
    
    def lookup_attraction(self, attraction_name: str, language: str = "en") -> Optional[Dict]:
        """Lookup attraction by name."""
        return self._service.lookup_attraction(attraction_name, language)
    
    def get_practical_info(self, category: str, language: str = "en") -> Optional[Dict]:
        """Get practical information by category."""
        return self._service.get_practical_info(category, language)
    
    # ========================================================================
    # Geospatial Search Methods
    # ========================================================================
    
    def find_nearby_attractions(self, latitude: float, longitude: float,
                              radius_km: float = 5.0, limit: int = 10) -> List[Dict]:
        """Find nearby attractions."""
        return self._service.find_nearby_attractions(latitude, longitude, radius_km, limit)
    
    def find_nearby_restaurants(self, latitude: float, longitude: float,
                               radius_km: float = 3.0, limit: int = 10) -> List[Dict]:
        """Find nearby restaurants."""
        return self._service.find_nearby_restaurants(latitude, longitude, radius_km, limit)
    
    def find_nearby_accommodations(self, latitude: float, longitude: float,
                                  radius_km: float = 3.0, limit: int = 10) -> List[Dict]:
        """Find nearby accommodations."""
        return self._service.find_nearby_accommodations(latitude, longitude, radius_km, limit)
    
    # ========================================================================
    # City-based Search Methods
    # ========================================================================
    
    def get_attractions_in_city(self, city_name: str, limit: int = 10, language: str = "en") -> List[Dict]:
        """Get attractions in a city."""
        return self._service.get_attractions_in_city(city_name, limit, language)
    
    def get_restaurants_in_city(self, city_name: str, limit: int = 10, language: str = "en") -> List[Dict]:
        """Get restaurants in a city."""
        return self._service.get_restaurants_in_city(city_name, limit, language)
    
    def get_accommodations_in_city(self, city_name: str, limit: int = 10, language: str = "en") -> List[Dict]:
        """Get accommodations in a city."""
        return self._service.get_accommodations_in_city(city_name, limit, language)
    
    # ========================================================================
    # Cross-Entity Relationship Methods
    # ========================================================================
    
    def find_attractions_near_hotel(self, hotel_id: str, radius_km: float = 3.0, limit: int = 10) -> List[Dict]:
        """Find attractions near a hotel."""
        return self._service.find_attractions_near_hotel(hotel_id, radius_km, limit)
    
    def find_restaurants_near_attraction(self, attraction_id: str = None, attraction_name: str = None,
                                       city: str = None, radius_km: float = 1.0, limit: int = 5) -> List[Dict]:
        """Find restaurants near an attraction."""
        return self._service.find_restaurants_near_attraction(attraction_id, attraction_name, city, radius_km, limit)
    
    def find_events_near_attraction(self, attraction_id: str = None, attraction_name: str = None,
                                  city: str = None, limit: int = 5) -> List[Dict]:
        """Find events near an attraction."""
        return self._service.find_events_near_attraction(attraction_id, attraction_name, city, limit)
    
    def find_attractions_in_itinerary_cities(self, itinerary_id: int = None,
                                          itinerary_name: str = None, limit: int = 10) -> Dict[str, List[Dict]]:
        """Find attractions in itinerary cities."""
        return self._service.find_attractions_in_itinerary_cities(itinerary_id, itinerary_name, limit)
    
    def find_related_attractions(self, attraction_id: int = None, attraction_name: str = None, limit: int = 5) -> List[Dict]:
        """Find related attractions."""
        return self._service.find_related_attractions(attraction_id, attraction_name, limit)
    
    def find_hotels_near_attraction(self, attraction_id: str = None, attraction_name: str = None,
                                  city: str = None, radius_km: float = 1.0, limit: int = 5) -> List[Dict]:
        """Find hotels near an attraction."""
        return self._service.find_hotels_near_attraction(attraction_id, attraction_name, city, radius_km, limit)
    
    # ========================================================================
    # Advanced Search Methods
    # ========================================================================
    
    def semantic_search(self, query: str, table: str = "attractions", limit: int = 10) -> List[Dict]:
        """Semantic search using vector embeddings."""
        return self._service.semantic_search(query, table, limit)
    
    def hybrid_search(self, query: str, table: str = "attractions", limit: int = 10) -> List[Dict]:
        """Hybrid search combining text and vector search."""
        return self._service.hybrid_search(query, table, limit)
    
    # ========================================================================
    # Logging and Analytics Methods
    # ========================================================================
    
    def log_search(self, query: str, results_count: int, filters: Dict[str, Any] = None,
                  session_id: str = None, user_id: str = None) -> None:
        """Log search operation."""
        return self._service.log_search(query, results_count, filters, session_id, user_id)
    
    def log_view(self, item_type: str, item_id: str, item_name: str = None,
                session_id: str = None, user_id: str = None) -> None:
        """Log item view."""
        return self._service.log_view(item_type, item_id, item_name, session_id, user_id)
    
    # ========================================================================
    # Debug and Metrics Methods
    # ========================================================================
    
    def debug_entity(self, entity_name: str, entity_type: str = "attraction", language: str = "en") -> Dict:
        """Debug entity lookup."""
        return self._service.debug_entity(entity_name, entity_type, language)
    
    def get_facade_metrics(self) -> Dict[str, Any]:
        """Get service metrics (renamed for compatibility)."""
        return self._service.get_facade_metrics()
    
    # ========================================================================
    # Delegation Pattern - Forward unknown attributes to service
    # ========================================================================
    
    def __getattr__(self, name):
        """Delegate unknown attributes to the service layer."""
        return getattr(self._service, name) 