"""
Clean DatabaseManager Facade Shell (Phase 5)

This file replaces the 3,924-line god object with a clean 200-line facade
that delegates all operations to the new facade architecture while preserving
100% API compatibility.

Target: 200 lines (95% reduction from original)
"""
import os
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum

from .database_facade import DatabaseManagerFacade
from ..utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class DatabaseType(Enum):
    POSTGRES = "postgres"

class DatabaseManager:
    """
    Clean DatabaseManager facade shell.
    
    This class maintains API compatibility with the legacy DatabaseManager
    while delegating all operations to the new facade architecture.
    
    All 80+ public methods are preserved with identical signatures.
    Implementation details are now handled by DatabaseManagerFacade.
    """
    
    def __init__(self, database_uri: str = None, vector_dimension: int = 1536):
        """Initialize DatabaseManager with facade delegation."""
        logger.info("🧹 Phase 5: Creating clean DatabaseManager facade shell")
        
        # Initialize the facade
        self._facade = DatabaseManagerFacade(database_uri, vector_dimension)
        
        # Store original parameters for compatibility
        self.database_uri = database_uri
        self.vector_dimension = vector_dimension
        
        logger.info(f"✅ Clean DatabaseManager ready (facade: {type(self._facade).__name__})")
    
    # ========================================================================
    # Context Manager Protocol
    # ========================================================================
    
    def __enter__(self):
        """Enter context manager."""
        return self._facade.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        return self._facade.__exit__(exc_type, exc_val, exc_tb)
    
    def close(self):
        """Close database connections."""
        return self._facade.close()
    
    # ========================================================================
    # Connection Management
    # ========================================================================
    
    def connect(self):
        """Connect to database."""
        return self._facade.connect()
    
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._facade.is_connected()
    
    def test_connection(self) -> bool:
        """Test database connection."""
        return self._facade.test_connection()
    
    # ========================================================================
    # Core Query Methods
    # ========================================================================
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute SQL query."""
        return self._facade.execute_query(query, params)
    
    def execute_postgres_query(self, query, params=None, fetchall=True, cursor_factory=None):
        """Execute PostgreSQL query."""
        return self._facade.execute_postgres_query(query, params, fetchall, cursor_factory)
    
    # ========================================================================
    # Entity Retrieval Methods
    # ========================================================================
    
    def get_attraction(self, attraction_id: int):
        """Get attraction by ID."""
        return self._facade.get_attraction(attraction_id)
    
    def get_restaurant(self, restaurant_id: int) -> Optional[Dict[str, Any]]:
        """Get restaurant by ID."""
        return self._facade.get_restaurant(restaurant_id)
    
    def get_city(self, city_id: int) -> Optional[Dict[str, Any]]:
        """Get city by ID.""" 
        return self._facade.get_city(city_id)
    
    def get_accommodation(self, accommodation_id: str) -> Optional[Dict[str, Any]]:
        """Get accommodation by ID."""
        return self._facade.get_accommodation(accommodation_id)
    
    def get_region(self, region_id: str) -> Optional[Dict[str, Any]]:
        """Get region by ID."""
        return self._facade.get_region(region_id)
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        return self._facade.get_user(user_id)
    
    def get_itinerary(self, itinerary_id: int) -> Optional[Dict[str, Any]]:
        """Get itinerary by ID."""
        return self._facade.get_itinerary(itinerary_id)
    
    def get_tourism_faq(self, faq_id: int) -> Optional[Dict[str, Any]]:
        """Get tourism FAQ by ID.""" 
        return self._facade.get_tourism_faq(faq_id)
    
    def get_practical_info(self, info_id: int) -> Optional[Dict[str, Any]]:
        """Get practical info by ID."""
        return self._facade.get_practical_info(info_id)
    
    def get_event_festival(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Get event/festival by ID."""
        return self._facade.get_event_festival(event_id)
    
    def get_tour_package(self, package_id: int) -> Optional[Dict[str, Any]]:
        """Get tour package by ID."""
        return self._facade.get_tour_package(package_id)
    
    # ========================================================================
    # Search Methods
    # ========================================================================
    
    def search_attractions(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None, 
                          limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """Search attractions."""
        return self._facade.search_attractions(query, filters, limit, offset, language)
    
    def search_restaurants(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None, 
                          limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """Search restaurants."""
        return self._facade.search_restaurants(query, filters, limit, offset, language)
    
    def search_accommodations(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None, 
                            limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """Search accommodations."""
        return self._facade.search_accommodations(query, filters, limit, offset, language)
    
    def search_hotels(self, query: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None,
                     limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """Search hotels."""
        return self._facade.search_hotels(query, filters, limit, offset, language)
    
    def search_cities(self, query: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Search cities."""
        return self._facade.search_cities(query, limit, offset)
    
    def search_regions(self, query: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Search regions."""
        return self._facade.search_regions(query, limit, offset)
    
    def search_users(self, query: Optional[Dict[str, Any]] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Search users."""
        return self._facade.search_users(query, limit, offset)
    
    def search_tourism_faqs(self, query: Optional[str] = None, category_id: Optional[str] = None, 
                           limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """Search tourism FAQs."""
        return self._facade.search_tourism_faqs(query, category_id, limit, offset, language)
    
    def search_practical_info(self, query: Optional[str] = None, category_id: Optional[str] = None,
                            limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """Search practical info."""
        return self._facade.search_practical_info(query, category_id, limit, offset, language)
    
    def search_events_festivals(self, query: Optional[str] = None, category_id: Optional[str] = None,
                              destination_id: Optional[str] = None, start_date: Optional[str] = None,
                              end_date: Optional[str] = None, limit: int = 10, offset: int = 0,
                              language: str = "en") -> List[Dict[str, Any]]:
        """Search events and festivals."""
        return self._facade.search_events_festivals(query, category_id, destination_id, start_date, end_date, limit, offset, language)
    
    def search_tour_packages(self, query: Optional[str] = None, category_id: Optional[str] = None,
                           min_duration: Optional[int] = None, max_duration: Optional[int] = None,
                           limit: int = 10, offset: int = 0, language: str = "en") -> List[Dict[str, Any]]:
        """Search tour packages."""
        return self._facade.search_tour_packages(query, category_id, min_duration, max_duration, limit, offset, language)
    
    # ========================================================================
    # Vector Search Methods
    # ========================================================================
    
    def vector_search(self, table_name: str, embedding: list, filters: Optional[dict] = None, 
                     limit: int = 10) -> List[Dict[str, Any]]:
        """Vector search."""
        return self._facade.vector_search(table_name, embedding, filters, limit)
    
    def vector_search_attractions(self, embedding: list, filters: Optional[dict] = None, 
                                limit: int = 10) -> List[Dict[str, Any]]:
        """Vector search attractions."""
        return self._facade.vector_search_attractions(embedding, filters, limit)
    
    def vector_search_restaurants(self, embedding: list, filters: Optional[dict] = None,
                                limit: int = 10) -> List[Dict[str, Any]]:
        """Vector search restaurants."""
        return self._facade.vector_search_restaurants(embedding, filters, limit)
    
    def vector_search_hotels(self, embedding: list, filters: Optional[dict] = None,
                           limit: int = 10) -> List[Dict[str, Any]]:
        """Vector search hotels."""
        return self._facade.vector_search_hotels(embedding, filters, limit)
    
    def vector_search_cities(self, embedding: list, filters: Optional[dict] = None,
                           limit: int = 10) -> List[Dict[str, Any]]:
        """Vector search cities."""
        return self._facade.vector_search_cities(embedding, filters, limit)
    
    def semantic_search(self, query: str, table: str = "attractions", limit: int = 10,
                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Semantic search."""
        return self._facade.semantic_search(query, table, limit, filters)
    
    def hybrid_search(self, table_name: str, query_text: str, embedding: list,
                     filters: Optional[Dict[str, Any]] = None, limit: int = 10,
                     vector_weight: float = 0.7, language: str = 'english') -> List[Dict[str, Any]]:
        """Hybrid search."""
        return self._facade.hybrid_search(table_name, query_text, embedding, filters, limit, vector_weight, language)
    
    # ========================================================================
    # Generic CRUD Methods  
    # ========================================================================
    
    def generic_get(self, table: str, record_id: int, jsonb_fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """Generic get method."""
        return self._facade.generic_get(table, record_id, jsonb_fields)
    
    def generic_search(self, table: str, filters: Dict[str, Any] = None, limit: int = 10, 
                      offset: int = 0, jsonb_fields: List[str] = None, language: str = "en") -> List[Dict[str, Any]]:
        """Generic search method."""
        return self._facade.generic_search(table, filters, limit, offset, jsonb_fields, language)
    
    def generic_create(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """Generic create method."""
        return self._facade.generic_create(table, data)
    
    def generic_update(self, table: str, record_id: int, data: Dict[str, Any]) -> bool:
        """Generic update method."""
        return self._facade.generic_update(table, record_id, data)
    
    def generic_delete(self, table: str, record_id: int) -> bool:
        """Generic delete method."""
        return self._facade.generic_delete(table, record_id)
    
    # ========================================================================
    # Delegate All Other Methods to Facade
    # ========================================================================
    
    def __getattr__(self, name):
        """Delegate any missing methods to the facade."""
        return getattr(self._facade, name) 