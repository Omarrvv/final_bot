"""
Repository Factory Module for the Egypt Tourism Chatbot.

This module provides a factory class for creating and managing repository instances
with proper dependency injection and lifecycle management.
"""
from typing import Dict, Type, TypeVar, Optional

from src.knowledge.core.database_core import DatabaseCore
from src.repositories.base_repository import BaseRepository
from src.repositories.attraction_repository import AttractionRepository
from src.repositories.restaurant_repository import RestaurantRepository
from src.repositories.accommodation_repository import AccommodationRepository
from src.repositories.city_repository import CityRepository
from src.repositories.region_repository import RegionRepository
from src.repositories.user_repository import UserRepository
from src.repositories.faq_repository import FaqRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T', bound=BaseRepository)

class RepositoryFactory:
    """
    Factory class for creating and managing repository instances.
    
    This factory provides centralized creation and management of repository instances,
    ensuring proper dependency injection and singleton behavior for repositories.
    """
    
    def __init__(self, db_core: DatabaseCore):
        """
        Initialize the repository factory.
        
        Args:
            db_core: Database core instance to inject into repositories
        """
        self.db_core = db_core
        self._repositories: Dict[Type[BaseRepository], BaseRepository] = {}
        
        # Registry of available repository classes
        self._repository_classes = {
            'attraction': AttractionRepository,
            'restaurant': RestaurantRepository,
            'accommodation': AccommodationRepository,
            'city': CityRepository,
            'region': RegionRepository,
            'user': UserRepository,
            'faq': FaqRepository,
        }
        
        logger.info("RepositoryFactory initialized")
    
    def get_repository(self, repository_class: Type[T]) -> T:
        """
        Get a repository instance of the specified class.
        
        Uses singleton pattern - returns the same instance for the same class.
        
        Args:
            repository_class: Repository class to get an instance of
            
        Returns:
            Repository instance
        """
        if repository_class not in self._repositories:
            logger.info(f"Creating new repository instance: {repository_class.__name__}")
            self._repositories[repository_class] = repository_class(self.db_core)
        
        return self._repositories[repository_class]
    
    def get_attraction_repository(self) -> AttractionRepository:
        """Get the attraction repository instance."""
        return self.get_repository(AttractionRepository)
    
    def get_restaurant_repository(self) -> RestaurantRepository:
        """Get the restaurant repository instance."""
        return self.get_repository(RestaurantRepository)
    
    def get_accommodation_repository(self) -> AccommodationRepository:
        """Get the accommodation repository instance."""
        return self.get_repository(AccommodationRepository)
    
    def get_city_repository(self) -> CityRepository:
        """Get the city repository instance."""
        return self.get_repository(CityRepository)
    
    def get_region_repository(self) -> RegionRepository:
        """Get the region repository instance."""
        return self.get_repository(RegionRepository)
    
    def get_user_repository(self) -> UserRepository:
        """Get the user repository instance."""
        return self.get_repository(UserRepository)
    
    def get_faq_repository(self) -> FaqRepository:
        """Get the FAQ repository instance."""
        return self.get_repository(FaqRepository)
    
    def get_repository_by_name(self, name: str) -> BaseRepository:
        """
        Get a repository instance by name.
        
        Args:
            name: Repository name (e.g., 'attraction', 'restaurant', etc.)
            
        Returns:
            Repository instance
            
        Raises:
            ValueError: If repository name is not recognized
        """
        if name not in self._repository_classes:
            available = ', '.join(self._repository_classes.keys())
            raise ValueError(f"Unknown repository name '{name}'. Available: {available}")
        
        repository_class = self._repository_classes[name]
        return self.get_repository(repository_class)
    
    def clear_cache(self):
        """Clear all cached repository instances."""
        logger.info("Clearing repository cache")
        self._repositories.clear()
    
    def get_all_repositories(self) -> Dict[str, BaseRepository]:
        """
        Get all available repository instances.
        
        Returns:
            Dictionary mapping repository names to instances
        """
        repositories = {}
        for name in self._repository_classes:
            repositories[name] = self.get_repository_by_name(name)
        return repositories
    
    @property
    def available_repositories(self) -> list:
        """Get list of available repository names."""
        return list(self._repository_classes.keys())
    
    def is_connected(self) -> bool:
        """Check if the underlying database connection is active."""
        return self.db_core.is_connected() 