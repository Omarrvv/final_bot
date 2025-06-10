"""
KnowledgeBaseFacade - Provides backward compatibility while using new repository architecture.

This facade maintains the same API as the original KnowledgeBase class while
internally using the new repository pattern and services.
"""
import logging
import time
from typing import Any, Dict, List, Optional

from src.knowledge.database_facade import DatabaseManagerFacade
from src.knowledge.core.connection_manager import ConnectionManager
from src.knowledge.core.database_core import DatabaseCore
from src.repositories.repository_factory import RepositoryFactory
from src.services.enhanced_service_registry import EnhancedServiceRegistry
from src.services.search.unified_search_service import UnifiedSearchService

logger = logging.getLogger(__name__)


class KnowledgeBaseFacade:
    """
    Facade implementation that maintains KnowledgeBase API compatibility.
    
    This facade provides the same interface as the original KnowledgeBase
    while internally using the new repository architecture and services.
    """
    
    def __init__(self, db_manager: Any, vector_db_uri: Optional[str] = None, content_path: Optional[str] = None):
        """Initialize KnowledgeBaseFacade with backward compatibility."""
        self.db_manager = db_manager
        self.vector_db_uri = vector_db_uri
        self.content_path = content_path
        
        # Initialize facade-specific metrics
        self._facade_metrics = {
            'total_operations': 0,
            'repository_calls': 0,
            'service_calls': 0,
            'error_count': 0,
            'avg_response_time_ms': 0.0,
            'legacy_fallback_count': 0
        }
        
        # Configuration
        self.enable_logging = True
        self.enable_fallback = True
        
        # Initialize new architecture components
        self._initialize_new_architecture()
        
        logger.info("KnowledgeBaseFacade initialized with repository architecture")
    
    def _initialize_new_architecture(self) -> None:
        """Initialize the new repository and service architecture."""
        try:
            if hasattr(self.db_manager, '_connection_manager'):
                # Use existing connection manager
                connection_manager = self.db_manager._connection_manager
            else:
                # Create database adapter for legacy compatibility
                connection_manager = None
                
                class DatabaseAdapter:
                    def __init__(self, conn_mgr):
                        self.conn_mgr = conn_mgr or self.db_manager
                    
                    def execute_postgres_query(self, query, params=None, fetchall=True, cursor_factory=None):
                        return self.conn_mgr.execute_postgres_query(query, params, fetchall, cursor_factory)
                    
                    def _get_pg_connection(self):
                        return self.conn_mgr._get_pg_connection()
                    
                    def _return_pg_connection(self, conn):
                        return self.conn_mgr._return_pg_connection(conn)
                    
                    def is_connected(self):
                        return self.conn_mgr.is_connected()
                
                connection_manager = DatabaseAdapter(self.db_manager)
            
            # Initialize database core
            self._db_core = DatabaseCore(connection_manager)
            
            # Initialize repository factory
            self._repository_factory = RepositoryFactory(self._db_core)
            
            # Initialize enhanced service registry
            self._service_registry = EnhancedServiceRegistry(self.db_manager)
            
            # Initialize unified search service
            if hasattr(self._service_registry, 'get'):
                self._search_service = self._service_registry.get('unified_search_service')
            else:
                self._search_service = None
            
            logger.info("New architecture components initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize new architecture: {e}. Falling back to legacy mode.")
            self._repository_factory = None
            self._search_service = None
    
    def _track_operation(self, operation_name: str, duration_ms: float, success: bool = True) -> None:
        """Track performance metrics for facade operations."""
        if not self.enable_logging:
            return
            
        self._facade_metrics['total_operations'] += 1
        self._facade_metrics['repository_calls'] += 1
        
        if not success:
            self._facade_metrics['error_count'] += 1
        
        # Update average response time
        current_avg = self._facade_metrics['avg_response_time_ms']
        total_ops = self._facade_metrics['total_operations']
        self._facade_metrics['avg_response_time_ms'] = (
            (current_avg * (total_ops - 1) + duration_ms) / total_ops
        )
        
        if self.enable_logging:
            logger.debug(f"KB_FACADE: {operation_name} [REPOSITORY] {duration_ms:.2f}ms success={success}")
    
    # ============================================================================
    # ATTRACTION METHODS
    # ============================================================================
    
    def get_attraction_by_id(self, attraction_id: int) -> Optional[Dict]:
        """Get attraction by ID."""
        start_time = time.time()
        
        try:
            repo = self._repository_factory.get_attraction_repository()
            result = repo.get_by_id(attraction_id)
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('get_attraction_by_id', duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('get_attraction_by_id', duration_ms, False)
            logger.error(f"Error getting attraction by ID {attraction_id}: {str(e)}")
            raise
    
    def search_attractions(self, query: str = "", filters: Optional[Dict] = None, 
                          language: str = "en", limit: int = 10) -> List[Dict]:
        """Search for attractions using new repository pattern or fallback."""
        start_time = time.time()
        
        try:
            if self._repository_factory:
                # Use new repository architecture
                repo = self._repository_factory.get_attraction_repository()
                if isinstance(query, str) and query:
                    # Text search
                    result = repo.search_attractions(
                        query=query,
                        limit=limit,
                        language=language
                    )
                else:
                    # Filter-based search
                    search_filters = filters or {}
                    result = repo.search_attractions(
                        **search_filters,
                        limit=limit,
                        language=language
                    )
            else:
                # Fallback to legacy database manager
                result = self.db_manager.search_attractions(query, filters, limit, 0, language)
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('search_attractions', duration_ms, True)
            return result or []
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('search_attractions', duration_ms, False)
            logger.error(f"Error searching attractions: {str(e)}")
            
            # Final fallback to db_manager
            if hasattr(self.db_manager, 'search_attractions'):
                return self.db_manager.search_attractions(query, filters, limit, 0, language)
            return []
    
    def lookup_attraction(self, attraction_name: str, language: str = "en") -> Optional[Dict]:
        """Lookup attraction by name."""
        start_time = time.time()
        
        try:
            repo = self._repository_factory.get_attraction_repository()
            results = repo.search(attraction_name, language=language, limit=1)
            result = results[0] if results else None
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('lookup_attraction', duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('lookup_attraction', duration_ms, False)
            logger.error(f"Error looking up attraction {attraction_name}: {str(e)}")
            raise
    
    # ============================================================================
    # RESTAURANT METHODS
    # ============================================================================
    
    def get_restaurant_by_id(self, restaurant_id: str) -> Optional[Dict]:
        """Get restaurant by ID."""
        start_time = time.time()
        
        try:
            repo = self._repository_factory.get_restaurant_repository()
            result = repo.get_by_id(int(restaurant_id))
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('get_restaurant_by_id', duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('get_restaurant_by_id', duration_ms, False)
            logger.error(f"Error getting restaurant by ID {restaurant_id}: {str(e)}")
            raise
    
    def search_restaurants(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search restaurants."""
        start_time = time.time()
        
        try:
            repo = self._repository_factory.get_restaurant_repository()
            
            if query:
                # Extract parameters from legacy query format
                text_query = query.get('query') or query.get('name')
                cuisine_id = query.get('cuisine_id')
                city_id = query.get('city_id')
                region_id = query.get('region_id')
                price_range = query.get('price_range')
                min_rating = query.get('min_rating')
                
                result = repo.search_restaurants(
                    query=text_query, cuisine_id=cuisine_id, city_id=city_id,
                    region_id=region_id, price_range=price_range, min_rating=min_rating,
                    limit=limit, language=language
                )
            else:
                result = repo.find(limit=limit)
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('search_restaurants', duration_ms, True)
            return result or []
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('search_restaurants', duration_ms, False)
            logger.error(f"Error searching restaurants: {str(e)}")
            raise
    
    # ============================================================================
    # ACCOMMODATION/HOTEL METHODS
    # ============================================================================
    
    def get_hotel_by_id(self, hotel_id: str) -> Optional[Dict]:
        """Get hotel by ID."""
        start_time = time.time()
        
        try:
            repo = self._repository_factory.get_accommodation_repository()
            result = repo.get_by_id(int(hotel_id))
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('get_hotel_by_id', duration_ms, True)
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('get_hotel_by_id', duration_ms, False)
            logger.error(f"Error getting hotel by ID {hotel_id}: {str(e)}")
            raise
    
    def search_hotels(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """Search hotels."""
        start_time = time.time()
        
        try:
            repo = self._repository_factory.get_accommodation_repository()
            
            if query:
                # Extract parameters from legacy query format
                text_query = query.get('query') or query.get('name')
                type_id = query.get('type_id')
                city_id = query.get('city_id')
                region_id = query.get('region_id')
                stars = query.get('stars')
                min_price = query.get('min_price')
                max_price = query.get('max_price')
                
                result = repo.search_accommodations(
                    query=text_query, type_id=type_id, city_id=city_id,
                    region_id=region_id, stars=stars, min_price=min_price,
                    max_price=max_price, limit=limit, language=language
                )
            else:
                result = repo.find(limit=limit)
            
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('search_hotels', duration_ms, True)
            return result or []
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('search_hotels', duration_ms, False)
            logger.error(f"Error searching hotels: {str(e)}")
            raise
    
    # ============================================================================
    # LEGACY COMPATIBILITY METHODS
    # ============================================================================
    
    def semantic_search(self, query: str, table: str = "attractions", limit: int = 10) -> List[Dict]:
        """Semantic search using vector similarity."""
        start_time = time.time()
        
        try:
            # Use search service for semantic search if available
            if self._search_service:
                try:
                    # Use unified search service
                    result = self._search_service.text_search(table, query, limit=limit)
                    formatted_result = [r.record for r in result] if result else []
                    duration_ms = (time.time() - start_time) * 1000
                    self._track_operation('semantic_search', duration_ms, True)
                    return formatted_result
                except Exception:
                    # Fallback to database manager
                    pass
            
            # Fallback to database manager semantic search
            if hasattr(self.db_manager, 'semantic_search'):
                result = self.db_manager.semantic_search(query, table, limit)
                duration_ms = (time.time() - start_time) * 1000
                self._track_operation('semantic_search', duration_ms, True)
                return result if result else []
            else:
                # Final fallback to regular search
                result = self.db_manager.search_attractions(query, limit=limit) if table == "attractions" else []
                duration_ms = (time.time() - start_time) * 1000
                self._track_operation('semantic_search', duration_ms, True)
                return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('semantic_search', duration_ms, False)
            logger.error(f"Error in semantic search: {str(e)}")
            return []
    
    def hybrid_search(self, query: str, table: str = "attractions", limit: int = 10) -> List[Dict]:
        """Hybrid search combining text and semantic search."""
        start_time = time.time()
        
        try:
            # Use search service for hybrid search if available
            if self._search_service:
                try:
                    # Use unified search service for text search as hybrid placeholder
                    result = self._search_service.text_search(table, query, limit=limit)
                    formatted_result = [r.record for r in result] if result else []
                    duration_ms = (time.time() - start_time) * 1000
                    self._track_operation('hybrid_search', duration_ms, True)
                    return formatted_result
                except Exception:
                    # Fallback to database manager
                    pass
            
            # Fallback to database manager hybrid search
            if hasattr(self.db_manager, 'hybrid_search'):
                result = self.db_manager.hybrid_search(query, table, limit)
                duration_ms = (time.time() - start_time) * 1000
                self._track_operation('hybrid_search', duration_ms, True)
                return result if result else []
            else:
                # Final fallback to regular search
                result = self.db_manager.search_attractions(query, limit=limit) if table == "attractions" else []
                duration_ms = (time.time() - start_time) * 1000
                self._track_operation('hybrid_search', duration_ms, True)
                return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._track_operation('hybrid_search', duration_ms, False)
            logger.error(f"Error in hybrid search: {str(e)}")
            return []
    
    def log_search(self, query: str, results_count: int, filters: Dict[str, Any] = None,
                  session_id: str = None, user_id: str = None) -> None:
        """Log search operation."""
        try:
            # Delegate to database manager if it has search logging capability
            if hasattr(self.db_manager, 'log_search'):
                self.db_manager.log_search(query, results_count, filters, session_id, user_id)
            elif self.enable_logging:
                logger.info(f"Search logged: query='{query}', results={results_count}, session={session_id}")
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error logging search: {e}")
    
    def log_view(self, item_type: str, item_id: str, item_name: str = None,
                session_id: str = None, user_id: str = None) -> None:
        """Log item view."""
        try:
            # Delegate to database manager if it has view logging capability
            if hasattr(self.db_manager, 'log_view'):
                self.db_manager.log_view(item_type, item_id, item_name, session_id, user_id)
            elif self.enable_logging:
                logger.info(f"View logged: type={item_type}, id={item_id}, name={item_name}, session={session_id}")
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error logging view: {e}")
    
    # ============================================================================
    # FACADE METRICS AND MONITORING
    # ============================================================================
    
    def get_facade_metrics(self) -> Dict[str, Any]:
        """Get facade performance and usage metrics."""
        return {
            'facade_type': 'KnowledgeBaseFacade',
            'architecture': 'Repository Pattern',
            'metrics': self._facade_metrics.copy(),
            'components': {
                'repository_factory': self._repository_factory is not None,
                'search_service': self._search_service is not None,
                'service_registry': self._service_registry is not None
            }
        }
    
    # ============================================================================
    # LEGACY API DELEGATION
    # ============================================================================
    
    def __getattr__(self, name):
        """Delegate unknown attributes to the legacy database manager."""
        if hasattr(self.db_manager, name):
            self._facade_metrics['legacy_fallback_count'] += 1
            if self.enable_logging:
                logger.debug(f"KB_FACADE: Delegating {name} to legacy db_manager")
            return getattr(self.db_manager, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") 