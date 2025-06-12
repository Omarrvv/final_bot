"""
Dependency Injection container for the Egypt Tourism Chatbot.
Manages component instantiation and lifecycles.
"""
import logging
from typing import Dict, Any, Optional, Type, Callable

logger = logging.getLogger(__name__)

class Container:
    """
    Dependency Injection container that manages component instances.
    Makes testing and configuration easier by centralizing dependencies.
    """
    
    def __init__(self):
        """Initialize the container."""
        self._services = {}
        self._factories = {}
        self._singletons = {}
        self._factory_cache = {}  # NEW: Cache factory results for singleton behavior
    
    def register(self, name: str, implementation: Any) -> None:
        """
        Register a component implementation.
        
        Args:
            name (str): Name of the component
            implementation (Any): Implementation class or instance
        """
        self._services[name] = implementation
        logger.debug(f"Registered service: {name}")
    
    def register_factory(self, name: str, factory: Callable[..., Any]) -> None:
        """
        Register a factory function to create a component.
        
        Args:
            name (str): Name of the component
            factory (Callable): Factory function that creates the component
        """
        self._factories[name] = factory
        logger.debug(f"Registered factory: {name}")
    
    def register_cached_factory(self, name: str, factory: Callable[..., Any]) -> None:
        """
        Register a factory that caches its results (singleton behavior).
        This ensures the factory is only called once and subsequent calls return the cached instance.
        
        Args:
            name (str): Name of the component
            factory (Callable): Factory function that creates the component
        """
        self._factories[name] = factory
        logger.debug(f"Registered cached factory: {name}")
    
    def register_singleton(self, name: str, implementation: Type) -> None:
        """
        Register a singleton component implementation.
        
        Args:
            name (str): Name of the component
            implementation (Type): Component implementation class
        """
        self._singletons[name] = {
            'implementation': implementation,
            'instance': None
        }
        logger.debug(f"Registered singleton: {name}")
    
    def get(self, name: str, **kwargs) -> Any:
        """
        Get a component instance.
        
        Args:
            name (str): Name of the component
            **kwargs: Additional arguments to pass to the factory
            
        Returns:
            Any: Component instance
            
        Raises:
            KeyError: If the component is not registered
        """
        # Check if service is directly registered
        if name in self._services:
            return self._services[name]
        
        # Check if service has a cached factory result
        if name in self._factories:
            if name not in self._factory_cache:
                logger.info(f"Creating singleton instance via factory: {name}")
                self._factory_cache[name] = self._factories[name](**kwargs)
            else:
                logger.debug(f"Returning cached factory instance: {name}")
            return self._factory_cache[name]
        
        # Check if service is a singleton
        if name in self._singletons:
            if self._singletons[name]['instance'] is None:
                logger.info(f"Creating singleton instance: {name}")
                self._singletons[name]['instance'] = self._singletons[name]['implementation'](**kwargs)
            else:
                logger.debug(f"Returning existing singleton instance: {name}")
            return self._singletons[name]['instance']
        
        raise KeyError(f"Service not registered: {name}")
    
    def has(self, name: str) -> bool:
        """
        Check if a component is registered.
        
        Args:
            name (str): Name of the component
            
        Returns:
            bool: True if the component is registered
        """
        return name in self._services or name in self._factories or name in self._singletons
    
    def clear_cache(self, name: str = None) -> None:
        """
        Clear the factory cache for debugging/testing purposes.
        
        Args:
            name (str, optional): Specific component to clear. If None, clears all cached instances.
        """
        if name:
            if name in self._factory_cache:
                del self._factory_cache[name]
                logger.info(f"Cleared cached instance: {name}")
        else:
            self._factory_cache.clear()
            logger.info("Cleared all cached factory instances")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached instances for debugging.
        
        Returns:
            Dict with cache statistics
        """
        return {
            "cached_factories": list(self._factory_cache.keys()),
            "cache_count": len(self._factory_cache),
            "registered_factories": list(self._factories.keys()),
            "registered_singletons": list(self._singletons.keys()),
            "registered_services": list(self._services.keys())
        }
    
    def get_feature_flag(self, flag_name: str) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name (str): Name of the feature flag (e.g., "new_kb", "new_api")
            
        Returns:
            bool: True if the feature flag is enabled
            
        Raises:
            KeyError: If env_vars are not registered or the flag doesn't exist
        """
        try:
            env_vars = self.get("env_vars")
            flag_key = f"use_{flag_name.lower()}"
            
            if flag_key in env_vars:
                return env_vars[flag_key]
            else:
                logger.warning(f"Feature flag not found: {flag_name}")
                return False
                
        except KeyError:
            logger.error("Environment variables not registered in container")
            return False

# Create a global container instance
container = Container() 