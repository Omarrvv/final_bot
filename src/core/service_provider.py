"""
Unified Service Provider - Single dependency injection system.
Replaces all 5 competing DI systems with one clean approach.
"""
import logging
from typing import Dict, Any, Callable, Optional, Type
from threading import Lock

logger = logging.getLogger(__name__)

class UnifiedServiceProvider:
    """
    Single dependency injection system replacing all 5 competing systems.
    Provides singleton management, factory registration, and dependency resolution.
    """

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._lock = Lock()

    def register_singleton(self, name: str, factory: Callable) -> None:
        """Register a singleton service factory"""
        with self._lock:
            self._factories[name] = factory
            logger.debug(f"Registered singleton factory: {name}")

    def register_instance(self, name: str, instance: Any) -> None:
        """Register a service instance directly"""
        with self._lock:
            self._services[name] = instance
            logger.debug(f"Registered service instance: {name}")

    def get(self, name: str) -> Any:
        """Get service instance (creates singleton if needed)"""
        # Check if already instantiated singleton
        if name in self._singletons:
            return self._singletons[name]

        # Check if direct instance
        if name in self._services:
            return self._services[name]

        # Create singleton from factory
        if name in self._factories:
            with self._lock:
                # Double-check pattern for thread safety
                if name not in self._singletons:
                    logger.info(f"Creating singleton: {name}")
                    self._singletons[name] = self._factories[name]()
                return self._singletons[name]

        raise ValueError(f"Service not registered: {name}")

    def get_with_auto_init(self, name: str) -> Any:
        """
        Get service with auto-initialization fallback.

        If service is not found, attempts to trigger auto-initialization
        of the component factory to register core services.
        """
        try:
            return self.get(name)
        except ValueError:
            # Service not found - try auto-initialization
            self._trigger_auto_initialization()
            # Retry once after initialization
            return self.get(name)

    def _trigger_auto_initialization(self) -> None:
        """
        Trigger auto-initialization of component factory.

        This method provides a callback mechanism for auto-initialization
        without creating import violations. The actual initialization
        logic should be registered by the services layer.
        """
        if hasattr(self, '_auto_init_callback') and self._auto_init_callback:
            try:
                logger.debug("Triggering auto-initialization callback")
                self._auto_init_callback()
            except Exception as exc:
                logger.error(f"Auto-initialization failed: {exc}", exc_info=True)
        else:
            logger.debug("No auto-initialization callback registered")

    def register_auto_init_callback(self, callback: Callable) -> None:
        """Register auto-initialization callback from services layer"""
        self._auto_init_callback = callback
        logger.debug("Auto-initialization callback registered")

    def has(self, name: str) -> bool:
        """Check if service is registered"""
        return name in self._services or name in self._factories or name in self._singletons

    def clear(self) -> None:
        """Clear all services (for testing)"""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._singletons.clear()

    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about registered services"""
        return {
            "registered_services": list(self._services.keys()),
            "registered_factories": list(self._factories.keys()),
            "registered_singletons": [],  # Legacy compatibility - singletons are in factories
            "instantiated_singletons": list(self._singletons.keys()),
            "cached_factories": list(self._singletons.keys()),  # Legacy compatibility
            "cache_count": len(self._singletons),
            "total_services": len(self._services) + len(self._factories)
        }

# Global service provider instance
service_provider = UnifiedServiceProvider() 