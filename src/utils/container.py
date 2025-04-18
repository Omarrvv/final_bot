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
        
        # Check if service has a factory
        if name in self._factories:
            return self._factories[name](**kwargs)
        
        # Check if service is a singleton
        if name in self._singletons:
            if self._singletons[name]['instance'] is None:
                self._singletons[name]['instance'] = self._singletons[name]['implementation'](**kwargs)
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

# Create a global container instance
container = Container() 