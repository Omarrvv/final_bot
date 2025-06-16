"""
Legacy Dependency Injection container - now a facade over UnifiedServiceProvider.
Maintains backward compatibility while using the new unified system.
"""
import logging
from typing import Dict, Any, Optional, Type, Callable
from src.core.service_provider import service_provider

logger = logging.getLogger(__name__)

class Container:
    """Legacy container facade over UnifiedServiceProvider"""

    def register(self, name: str, implementation: Any) -> None:
        """Register service instance or factory"""
        # If implementation is callable (like a lambda), treat it as a factory
        if callable(implementation):
            service_provider.register_singleton(name, implementation)
        else:
            service_provider.register_instance(name, implementation)

    def register_factory(self, name: str, factory: Callable[..., Any]) -> None:
        """Register factory function"""
        service_provider.register_singleton(name, factory)

    def register_cached_factory(self, name: str, factory: Callable[..., Any]) -> None:
        """Register singleton factory"""
        service_provider.register_singleton(name, factory)

    def register_singleton(self, name: str, implementation: Type) -> None:
        """Register singleton implementation"""
        # Convert Type to factory function
        def singleton_factory():
            return implementation()
        service_provider.register_singleton(name, singleton_factory)

    def get(self, name: str, **kwargs) -> Any:
        """Get a registered service with auto-initialization fallback.
        This prevents early calls to container.get() from failing before the
        ComponentFactory has registered its factories.
        """
        # Use service provider's auto-initialization mechanism
        return service_provider.get_with_auto_init(name)

    def has(self, name: str) -> bool:
        """Check if service exists"""
        return service_provider.has(name)

    def clear_cache(self, name: str = None) -> None:
        """Clear cache (for testing)"""
        if name is None:
            service_provider.clear()
        else:
            # Clear individual service by removing it from the provider
            if hasattr(service_provider, '_instances') and name in service_provider._instances:
                del service_provider._instances[name]
                logger.debug(f"Cleared cache for service: {name}")
            else:
                logger.debug(f"Service not found in cache: {name}")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get debug info"""
        return service_provider.get_debug_info()
    
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