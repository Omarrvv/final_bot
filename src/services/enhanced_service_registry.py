"""
Enhanced Service Registry for the Egypt Tourism Chatbot.

This module provides a comprehensive dependency injection container that replaces
the basic ServiceRegistry, offering advanced features like lifecycle management,
dependency resolution, and service configuration.
"""

import threading
import time
from typing import Any, Dict, Type, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum

from src.utils.logger import get_logger
from src.knowledge.core.database_core import DatabaseCore
from src.knowledge.core.connection_manager import ConnectionManager
from src.repositories.repository_factory import RepositoryFactory
from src.services.search.unified_search_service import UnifiedSearchService

logger = get_logger(__name__)


class ServiceLifecycle(Enum):
    """Service lifecycle types."""
    SINGLETON = "singleton"
    PROTOTYPE = "prototype"  # New instance each time
    SCOPED = "scoped"       # One instance per scope/request


@dataclass
class ServiceDefinition:
    """Defines how a service should be created and managed."""
    service_class: Type
    lifecycle: ServiceLifecycle
    factory_method: Optional[Callable] = None
    dependencies: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    initialized: bool = False
    instance: Any = None
    created_at: Optional[float] = None


class ServiceRegistrationError(Exception):
    """Exception raised when service registration fails."""
    pass


class ServiceResolutionError(Exception):
    """Exception raised when service resolution fails."""
    pass


class EnhancedServiceRegistry:
    """
    Enhanced service registry with full dependency injection capabilities.
    
    This registry provides:
    - Dependency injection and resolution
    - Service lifecycle management (singleton, prototype, scoped)
    - Circular dependency detection
    - Service configuration and factory methods
    - Thread-safe operations
    - Service health monitoring
    """
    
    def __init__(self, database_manager=None):
        """
        Initialize the enhanced service registry.
        
        Args:
            database_manager: Optional DatabaseManager for backward compatibility
        """
        self._services: Dict[str, ServiceDefinition] = {}
        self._instances: Dict[str, Any] = {}
        self._scoped_instances: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._resolution_stack: List[str] = []
        
        # Core services initialization order matters
        self._database_manager = database_manager
        
        logger.info("EnhancedServiceRegistry initialized")
        
        # Register core services automatically
        self._register_core_services()
    
    def _register_core_services(self):
        """Register core services with proper dependency order."""
        try:
            # 1. Connection Manager (no dependencies)
            self.register(
                'connection_manager',
                ConnectionManager,
                ServiceLifecycle.SINGLETON,
                dependencies=[]
            )
            
            # 2. Database Core (depends on either connection_manager or database_manager)
            if self._database_manager:
                # Use existing database manager for backward compatibility
                self.register_instance('database_manager', self._database_manager)
                self.register(
                    'database_core',
                    DatabaseCore,
                    ServiceLifecycle.SINGLETON,
                    dependencies=['database_manager']
                )
            else:
                # Use new connection manager
                self.register(
                    'database_core',
                    self._create_database_core_with_connection_manager,
                    ServiceLifecycle.SINGLETON,
                    dependencies=['connection_manager'],
                    factory_method=True
                )
            
            # 3. Repository Factory (depends on database_core)
            self.register(
                'repository_factory',
                RepositoryFactory,
                ServiceLifecycle.SINGLETON,
                dependencies=['database_core']
            )
            
            # 4. Unified Search Service (depends on repository_factory)
            self.register(
                'search_service',
                UnifiedSearchService,
                ServiceLifecycle.SINGLETON,
                dependencies=['repository_factory']
            )
            
            # Also register with alternate name for facade compatibility
            self.register(
                'unified_search_service',
                UnifiedSearchService,
                ServiceLifecycle.SINGLETON,
                dependencies=['repository_factory']
            )
            
            logger.info("Core services registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register core services: {str(e)}")
            raise ServiceRegistrationError(f"Core services registration failed: {str(e)}")
    
    def _create_database_core_with_connection_manager(self, connection_manager: ConnectionManager) -> DatabaseCore:
        """Factory method to create DatabaseCore with ConnectionManager."""
        # Initialize connection pool if not already done
        if not connection_manager.is_connected():
            success = connection_manager.initialize_connection_pool()
            if not success:
                raise ServiceResolutionError("Failed to initialize connection pool")
        
        # Create a lightweight database manager wrapper for DatabaseCore
        class ConnectionManagerAdapter:
            def __init__(self, conn_manager):
                self.conn_manager = conn_manager
            
            def execute_postgres_query(self, query, params=None, fetchall=True):
                return self.conn_manager.execute_query(query, params, fetchall)
            
            def _get_pg_connection(self):
                return self.conn_manager.get_connection()
            
            def _return_pg_connection(self, conn):
                return self.conn_manager.return_connection(conn)
            
            def is_connected(self):
                return self.conn_manager.is_connected()
        
        adapter = ConnectionManagerAdapter(connection_manager)
        return DatabaseCore(adapter)
    
    def register(self, name: str, service_class: Type, 
                lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON,
                dependencies: List[str] = None,
                factory_method: Callable = None,
                configuration: Dict[str, Any] = None) -> 'EnhancedServiceRegistry':
        """
        Register a service with the registry.
        
        Args:
            name: Service name
            service_class: Service class or factory method
            lifecycle: Service lifecycle type
            dependencies: List of dependency service names
            factory_method: Optional factory method
            configuration: Service configuration
            
        Returns:
            Self for method chaining
        """
        with self._lock:
            if name in self._services:
                logger.warning(f"Service '{name}' already registered, overwriting")
            
            self._services[name] = ServiceDefinition(
                service_class=service_class,
                lifecycle=lifecycle,
                factory_method=factory_method,
                dependencies=dependencies or [],
                configuration=configuration or {}
            )
            
            logger.debug(f"Registered service '{name}' with lifecycle {lifecycle.value}")
            return self
    
    def register_instance(self, name: str, instance: Any) -> 'EnhancedServiceRegistry':
        """
        Register an existing instance as a singleton service.
        
        Args:
            name: Service name
            instance: Service instance
            
        Returns:
            Self for method chaining
        """
        with self._lock:
            self._services[name] = ServiceDefinition(
                service_class=type(instance),
                lifecycle=ServiceLifecycle.SINGLETON,
                instance=instance,
                initialized=True,
                created_at=time.time()
            )
            self._instances[name] = instance
            
            logger.debug(f"Registered instance '{name}' of type {type(instance).__name__}")
            return self
    
    def register_factory(self, name: str, factory: Callable,
                        lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON,
                        dependencies: List[str] = None) -> 'EnhancedServiceRegistry':
        """
        Register a factory method for creating services.
        
        Args:
            name: Service name
            factory: Factory method
            lifecycle: Service lifecycle type
            dependencies: List of dependency service names
            
        Returns:
            Self for method chaining
        """
        return self.register(
            name=name,
            service_class=factory,
            lifecycle=lifecycle,
            dependencies=dependencies,
            factory_method=factory
        )
    
    def get(self, name: str, scope_id: str = None) -> Any:
        """
        Get a service instance by name.
        
        Args:
            name: Service name
            scope_id: Optional scope ID for scoped services
            
        Returns:
            Service instance
            
        Raises:
            ServiceResolutionError: If service cannot be resolved
        """
        with self._lock:
            if name not in self._services:
                raise ServiceResolutionError(f"Service '{name}' not registered")
            
            definition = self._services[name]
            
            # Check for circular dependencies
            if name in self._resolution_stack:
                cycle = " -> ".join(self._resolution_stack + [name])
                raise ServiceResolutionError(f"Circular dependency detected: {cycle}")
            
            # Handle different lifecycles
            if definition.lifecycle == ServiceLifecycle.SINGLETON:
                return self._get_singleton_instance(name, definition)
            elif definition.lifecycle == ServiceLifecycle.PROTOTYPE:
                return self._create_instance(name, definition)
            elif definition.lifecycle == ServiceLifecycle.SCOPED:
                return self._get_scoped_instance(name, definition, scope_id)
            else:
                raise ServiceResolutionError(f"Unknown lifecycle: {definition.lifecycle}")
    
    def _get_singleton_instance(self, name: str, definition: ServiceDefinition) -> Any:
        """Get or create singleton instance."""
        if definition.initialized and definition.instance:
            return definition.instance
        
        # Create new instance
        instance = self._create_instance(name, definition)
        
        # Cache the instance
        definition.instance = instance
        definition.initialized = True
        definition.created_at = time.time()
        self._instances[name] = instance
        
        return instance
    
    def _get_scoped_instance(self, name: str, definition: ServiceDefinition, scope_id: str) -> Any:
        """Get or create scoped instance."""
        if not scope_id:
            scope_id = "default"
        
        if scope_id not in self._scoped_instances:
            self._scoped_instances[scope_id] = {}
        
        scope_instances = self._scoped_instances[scope_id]
        
        if name in scope_instances:
            return scope_instances[name]
        
        # Create new instance for this scope
        instance = self._create_instance(name, definition)
        scope_instances[name] = instance
        
        return instance
    
    def _create_instance(self, name: str, definition: ServiceDefinition) -> Any:
        """Create a new service instance."""
        self._resolution_stack.append(name)
        
        try:
            # Resolve dependencies first
            dependency_instances = []
            for dep_name in definition.dependencies:
                dep_instance = self.get(dep_name)
                dependency_instances.append(dep_instance)
            
            # Create instance
            if definition.factory_method:
                # Use factory method
                if callable(definition.service_class):
                    instance = definition.service_class(*dependency_instances)
                else:
                    raise ServiceResolutionError(f"Factory method for '{name}' is not callable")
            else:
                # Use constructor
                instance = definition.service_class(*dependency_instances)
            
            logger.debug(f"Created instance of service '{name}'")
            return instance
            
        except Exception as e:
            raise ServiceResolutionError(f"Failed to create service '{name}': {str(e)}")
        finally:
            self._resolution_stack.pop()
    
    def clear_scope(self, scope_id: str):
        """Clear all instances in a scope."""
        with self._lock:
            if scope_id in self._scoped_instances:
                del self._scoped_instances[scope_id]
                logger.debug(f"Cleared scope '{scope_id}'")
    
    def is_registered(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._services
    
    def get_service_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered service."""
        if name not in self._services:
            return None
        
        definition = self._services[name]
        return {
            "name": name,
            "class": definition.service_class.__name__,
            "lifecycle": definition.lifecycle.value,
            "dependencies": definition.dependencies,
            "initialized": definition.initialized,
            "created_at": definition.created_at,
            "configuration": definition.configuration
        }
    
    def get_all_services(self) -> List[str]:
        """Get list of all registered service names."""
        return list(self._services.keys())
    
    def get_service_graph(self) -> Dict[str, List[str]]:
        """Get dependency graph of all services."""
        graph = {}
        for name, definition in self._services.items():
            graph[name] = definition.dependencies
        return graph
    
    def validate_dependencies(self) -> List[str]:
        """
        Validate all service dependencies.
        
        Returns:
            List of validation errors (empty if no errors)
        """
        errors = []
        
        for name, definition in self._services.items():
            for dep_name in definition.dependencies:
                if dep_name not in self._services:
                    errors.append(f"Service '{name}' depends on unregistered service '{dep_name}'")
        
        # Check for circular dependencies
        try:
            for name in self._services:
                self._check_circular_dependencies(name, set())
        except ServiceResolutionError as e:
            errors.append(str(e))
        
        return errors
    
    def _check_circular_dependencies(self, service_name: str, visited: set):
        """Check for circular dependencies recursively."""
        if service_name in visited:
            raise ServiceResolutionError(f"Circular dependency detected involving '{service_name}'")
        
        visited.add(service_name)
        
        if service_name in self._services:
            for dep_name in self._services[service_name].dependencies:
                self._check_circular_dependencies(dep_name, visited.copy())
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all services.
        
        Returns:
            Health status report
        """
        report = {
            "status": "healthy",
            "services": {},
            "total_services": len(self._services),
            "initialized_services": 0,
            "errors": []
        }
        
        for name, definition in self._services.items():
            service_health = {
                "initialized": definition.initialized,
                "lifecycle": definition.lifecycle.value,
                "dependencies_count": len(definition.dependencies)
            }
            
            if definition.initialized and definition.instance:
                report["initialized_services"] += 1
                
                # Check if service has health check method
                if hasattr(definition.instance, 'health_check'):
                    try:
                        service_health["health"] = definition.instance.health_check()
                    except Exception as e:
                        service_health["health_error"] = str(e)
                        report["errors"].append(f"Health check failed for '{name}': {str(e)}")
            
            report["services"][name] = service_health
        
        if report["errors"]:
            report["status"] = "degraded"
        
        return report
    
    def shutdown(self):
        """Shutdown the service registry and clean up resources."""
        with self._lock:
            # Call shutdown methods on services that support it
            for name, instance in self._instances.items():
                if hasattr(instance, 'close') or hasattr(instance, 'shutdown'):
                    try:
                        if hasattr(instance, 'shutdown'):
                            instance.shutdown()
                        elif hasattr(instance, 'close'):
                            instance.close()
                        logger.debug(f"Shut down service '{name}'")
                    except Exception as e:
                        logger.error(f"Error shutting down service '{name}': {str(e)}")
            
            # Clear all instances
            self._services.clear()
            self._instances.clear()
            self._scoped_instances.clear()
            
            logger.info("EnhancedServiceRegistry shut down")
    
    def __enter__(self):
        """Support context manager pattern."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up when exiting context manager."""
        self.shutdown() 