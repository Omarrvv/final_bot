"""
Service registry for managing service instances.

This module provides a registry for managing service instances to avoid
creating multiple instances of the same service.
"""
from typing import Any, Dict, Optional, Type

from src.utils.logger import get_logger

logger = get_logger(__name__)

class ServiceRegistry:
    """
    Registry for managing service instances.
    
    This class provides a registry for managing service instances to avoid
    creating multiple instances of the same service.
    """
    
    def __init__(self, db_manager):
        """
        Initialize the service registry.
        
        Args:
            db_manager: Database manager instance with connection pool
        """
        self.db_manager = db_manager
        self._services = {}
    
    def get_service(self, service_class: Type) -> Any:
        """
        Get a service instance.
        
        If the service instance doesn't exist, it will be created.
        
        Args:
            service_class: Service class to get an instance of
            
        Returns:
            Service instance
        """
        service_name = service_class.__name__
        
        if service_name not in self._services:
            logger.info(f"Creating new service instance: {service_name}")
            self._services[service_name] = service_class(self.db_manager)
        
        return self._services[service_name]
    
    def clear(self):
        """Clear all service instances."""
        self._services = {}
