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

from .knowledge_base_facade import KnowledgeBaseFacade

logger = logging.getLogger(__name__)

@lru_cache(maxsize=10)
def _load_json_data(file_path: str) -> Optional[Dict]:
    """Cache JSON file loading (preserved from original)."""
    import json
    from pathlib import Path
    
    try:
        path = Path(file_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
    return None

class KnowledgeBase:
    """
    Clean KnowledgeBase facade shell.
    
    This class maintains API compatibility with the legacy KnowledgeBase
    while delegating all operations to the new facade architecture.
    
    All 35+ public methods are preserved with identical signatures.
    Data formatting and processing logic are now handled by KnowledgeBaseFacade.
    """
    
    def __init__(self, db_manager: Any, vector_db_uri: Optional[str] = None, content_path: Optional[str] = None):
        """Initialize KnowledgeBase with facade delegation."""
        logger.info("🧹 Phase 5: Creating clean KnowledgeBase facade shell")
        
        # Initialize the facade
        self._facade = KnowledgeBaseFacade(db_manager, vector_db_uri, content_path)
        
        # Store original parameters for compatibility
        self.db_manager = db_manager
        self.vector_db_uri = vector_db_uri
        self.content_path = content_path
        
        logger.info(f"✅ Clean KnowledgeBase ready (facade: {type(self._facade).__name__})")
    
    # ========================================================================
    # Core Entity Retrieval Methods
    # ========================================================================
    
    def get_attraction_by_id(self, attraction_id: int) -> Optional[Dict]:
        """Get attraction by ID."""
        return self._facade.get_attraction_by_id(attraction_id)
    
    def get_restaurant_by_id(self, restaurant_id: str) -> Optional[Dict]:
        """Get restaurant by ID."""
        return self._facade.get_restaurant_by_id(restaurant_id)
    
    def get_hotel_by_id(self, hotel_id: str) -> Optional[Dict]:
        """Get hotel by ID."""
        return self._facade.get_hotel_by_id(hotel_id)
    
    def get_record_by_id(self, table_name, record_id):
        """Get any record by table name and ID."""
        return self._facade.get_record_by_id(table_name, record_id)
    
    # ========================================================================
    # Search Methods
    # ========================================================================
    
    def search_attractions(self, query: str = "", filters: Optional[Dict] = None, 
                          language: str = "en", limit: int = 10) -> List[Dict]:
        """Search attractions."""
        return self._facade.search_attractions(query, filters, language, limit)
    
    def search_restaurants(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search restaurants."""
        return self._facade.search_restaurants(query, limit, language)
    
    def search_hotels(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search hotels."""
        return self._facade.search_hotels(query, limit, language)
    
    def search_practical_info(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search practical information."""
        return self._facade.search_practical_info(query, limit, language)
    
    def search_faqs(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search FAQs."""
        return self._facade.search_faqs(query, limit, language)
    
    def search_events(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search events."""
        return self._facade.search_events(query, limit, language)
    
    def search_events_festivals(self, query: Dict = None, category_id: str = None,
                              destination_id: str = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search events and festivals."""
        return self._facade.search_events_festivals(query, category_id, destination_id, limit, language)
    
    def search_itineraries(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search itineraries."""
        return self._facade.search_itineraries(query, limit, language)
    
    def search_tour_packages(self, query: Dict = None, category_id: str = None,
                           min_duration: int = None, max_duration: int = None,
                           limit: int = 10, language: str = "en") -> List[Dict]:
        """Search tour packages."""
        return self._facade.search_tour_packages(query, category_id, min_duration, max_duration, limit, language)
    
    def search_transportation(self, query: Dict = None, origin: str = None, destination: str = None,
                            transportation_type: str = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search transportation options."""
        return self._facade.search_transportation(query, origin, destination, transportation_type, limit, language)
    
    def search_records(self, table_name, filters=None, limit=10, offset=0):
        """Generic record search."""
        return self._facade.search_records(table_name, filters, limit, offset)
    
    # ========================================================================
    # Lookup Methods
    # ========================================================================
    
    def lookup_location(self, location_name: str, language: str = "en") -> Optional[Dict]:
        """Lookup location by name."""
        return self._facade.lookup_location(location_name, language)
    
    def lookup_attraction(self, attraction_name: str, language: str = "en") -> Optional[Dict]:
        """Lookup attraction by name."""
        return self._facade.lookup_attraction(attraction_name, language)
    
    def get_practical_info(self, category: str, language: str = "en") -> Optional[Dict]:
        """Get practical information by category."""
        return self._facade.get_practical_info(category, language)
    
    # ========================================================================
    # Geospatial Search Methods
    # ========================================================================
    
    def find_nearby_attractions(self, latitude: float, longitude: float,
                              radius_km: float = 5.0, limit: int = 10) -> List[Dict]:
        """Find nearby attractions."""
        return self._facade.find_nearby_attractions(latitude, longitude, radius_km, limit)
    
    def find_nearby_restaurants(self, latitude: float, longitude: float,
                               radius_km: float = 3.0, limit: int = 10) -> List[Dict]:
        """Find nearby restaurants."""
        return self._facade.find_nearby_restaurants(latitude, longitude, radius_km, limit)
    
    def find_nearby_accommodations(self, latitude: float, longitude: float,
                                  radius_km: float = 3.0, limit: int = 10) -> List[Dict]:
        """Find nearby accommodations."""
        return self._facade.find_nearby_accommodations(latitude, longitude, radius_km, limit)
    
    # ========================================================================
    # City-based Search Methods
    # ========================================================================
    
    def get_attractions_in_city(self, city_name: str, limit: int = 10, language: str = "en") -> List[Dict]:
        """Get attractions in a city."""
        return self._facade.get_attractions_in_city(city_name, limit, language)
    
    def get_restaurants_in_city(self, city_name: str, limit: int = 10, language: str = "en") -> List[Dict]:
        """Get restaurants in a city."""
        return self._facade.get_restaurants_in_city(city_name, limit, language)
    
    def get_accommodations_in_city(self, city_name: str, limit: int = 10, language: str = "en") -> List[Dict]:
        """Get accommodations in a city."""
        return self._facade.get_accommodations_in_city(city_name, limit, language)
    
    # ========================================================================
    # Cross-Entity Relationship Methods
    # ========================================================================
    
    def find_attractions_near_hotel(self, hotel_id: str, radius_km: float = 3.0, limit: int = 10) -> List[Dict]:
        """Find attractions near a hotel."""
        return self._facade.find_attractions_near_hotel(hotel_id, radius_km, limit)
    
    def find_restaurants_near_attraction(self, attraction_id: str = None, attraction_name: str = None,
                                       city: str = None, radius_km: float = 1.0, limit: int = 5) -> List[Dict]:
        """Find restaurants near an attraction."""
        return self._facade.find_restaurants_near_attraction(attraction_id, attraction_name, city, radius_km, limit)
    
    def find_events_near_attraction(self, attraction_id: str = None, attraction_name: str = None,
                                  city: str = None, limit: int = 5) -> List[Dict]:
        """Find events near an attraction."""
        return self._facade.find_events_near_attraction(attraction_id, attraction_name, city, limit)
    
    def find_attractions_in_itinerary_cities(self, itinerary_id: int = None,
                                          itinerary_name: str = None, limit: int = 10) -> Dict[str, List[Dict]]:
        """Find attractions in itinerary cities."""
        return self._facade.find_attractions_in_itinerary_cities(itinerary_id, itinerary_name, limit)
    
    def find_related_attractions(self, attraction_id: int = None, attraction_name: str = None, limit: int = 5) -> List[Dict]:
        """Find related attractions."""
        return self._facade.find_related_attractions(attraction_id, attraction_name, limit)
    
    def find_hotels_near_attraction(self, attraction_id: str = None, attraction_name: str = None,
                                  city: str = None, radius_km: float = 1.0, limit: int = 5) -> List[Dict]:
        """Find hotels near an attraction."""
        return self._facade.find_hotels_near_attraction(attraction_id, attraction_name, city, radius_km, limit)
    
    # ========================================================================
    # Advanced Search Methods
    # ========================================================================
    
    def semantic_search(self, query: str, table: str = "attractions", limit: int = 10) -> List[Dict]:
        """Semantic search using vector embeddings."""
        return self._facade.semantic_search(query, table, limit)
    
    def hybrid_search(self, query: str, table: str = "attractions", limit: int = 10) -> List[Dict]:
        """Hybrid search combining text and vector search."""
        return self._facade.hybrid_search(query, table, limit)
    
    # ========================================================================
    # Logging and Analytics Methods
    # ========================================================================
    
    def log_search(self, query: str, results_count: int, filters: Dict[str, Any] = None,
                  session_id: str = None, user_id: str = None) -> None:
        """Log search activity."""
        return self._facade.log_search(query, results_count, filters, session_id, user_id)
    
    def log_view(self, item_type: str, item_id: str, item_name: str = None,
                session_id: str = None, user_id: str = None) -> None:
        """Log item view activity."""
        return self._facade.log_view(item_type, item_id, item_name, session_id, user_id)
    
    # ========================================================================
    # Debug and Utility Methods
    # ========================================================================
    
    def debug_entity(self, entity_name: str, entity_type: str = "attraction", language: str = "en") -> Dict:
        """Debug entity information."""
        return self._facade.debug_entity(entity_name, entity_type, language)
    
    # ========================================================================
    # Facade Performance and Metrics
    # ========================================================================
    
    def get_facade_metrics(self) -> Dict[str, Any]:
        """Get facade performance metrics."""
        return self._facade.get_facade_metrics()
    
    # ========================================================================
    # Delegate All Other Methods to Facade
    # ========================================================================
    
    def __getattr__(self, name):
        """Delegate any missing methods to the facade."""
        return getattr(self._facade, name) 