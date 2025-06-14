"""
Factory module for the Egypt Tourism Chatbot.
Creates and configures components with dependency injection.
"""
import os
import logging
from src.services.anthropic_service import AnthropicService
from typing import Dict, List, Any, Optional

from src.utils.container import container
from src.utils.exceptions import ConfigurationError
from src.config_unified import settings

logger = logging.getLogger(__name__)

class ComponentFactory:
    """
    Factory for creating components with proper dependencies.
    Simplifies component creation and wiring.
    """

    def __init__(self):
        """Initialize the component factory."""
        self.configs = {}
        self.env_vars = {}
        self._shared_db_manager = None  # Add shared database manager instance

    def initialize(self):
        """Initialize the factory with environment variables and configurations."""
        logger.info("Initializing component factory...")

        # Log key feature flags
        logger.info(f"Feature flags (before initialization): " +
                   f"USE_POSTGRES={settings.feature_flags.use_postgres}")

        self._load_environment_variables()
        self._load_configurations()
        self._register_services()
        logger.info("Component factory initialization complete")

    def _load_environment_variables(self):
        """Load environment variables using settings module."""
        # Use the settings module to get configuration values
        self.env_vars = settings.as_dict()

        # Log settings (excluding sensitive information)
        settings.log_settings(include_secrets=False)

    def _load_configurations(self):
        """Load configuration files."""
        try:
            import json
            from pathlib import Path

            for config_name, config_path in [
                ("models", settings.models_config),
                ("flows", settings.flows_config),
                ("services", settings.services_config)
            ]:
                if not Path(config_path).exists():
                    logger.warning(f"Configuration file not found: {config_path}")
                    self.configs[config_name] = {}
                    continue

                with open(config_path, 'r') as f:
                    self.configs[config_name] = json.load(f)

        except Exception as e:
            logger.error(f"Error loading configurations: {str(e)}")
            raise ConfigurationError(f"Failed to load configurations: {str(e)}")

    def _register_services(self):
        """Register common services in the dependency injection container."""
        logger.info("Registering services...")

        # Log feature flags for component selection
        logger.info(f"Feature flags during registration: " +
                   f"USE_POSTGRES={settings.feature_flags.use_postgres}")

        # Register configurations
        container.register("env_vars", self.env_vars)
        container.register("configs", self.configs)
        container.register("settings", settings)

        # Register cached factory methods (singletons) for main components
        container.register_cached_factory("knowledge_base", self.create_knowledge_base)
        container.register_cached_factory("nlu_engine", self.create_nlu_engine)
        container.register_cached_factory("dialog_manager", self.create_dialog_manager)
        container.register_cached_factory("response_generator", self.create_response_generator)
        container.register_cached_factory("service_hub", self.create_service_hub)
        container.register_cached_factory("session_manager", self.create_session_manager)
        container.register_cached_factory("database_manager", self.create_database_manager)
        
        # CRITICAL FIX: Register missing services that were mentioned in investigation
        container.register_cached_factory("search_service", self.create_search_service)
        container.register_cached_factory("unified_search_service", self.create_unified_search_service)

        # Create AnthropicService with API key from settings
        anthropic_api_key = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else ""
        self.register_component("anthropic_service", AnthropicService({
            "anthropic_api_key": anthropic_api_key
        }))

        # Register Chatbot cached factory (singleton)
        container.register_cached_factory("chatbot", self.create_chatbot)

        logger.info("Service registration complete")
        
        # DEBUG: Verify container state immediately after registration
        debug_info = container.get_cache_info()
        logger.info(f"DEBUG - Container state after registration:")
        logger.info(f"  Registered services: {debug_info['registered_services']}")
        logger.info(f"  Registered factories: {debug_info['registered_factories']}")
        logger.info(f"  Registered singletons: {debug_info['registered_singletons']}")
        
        if not debug_info['registered_factories']:
            logger.error("CRITICAL: No factories were registered! Container registration failed!")
        else:
            logger.info(f"✅ Successfully registered {len(debug_info['registered_factories'])} factories")

    def register_component(self, name, component):
        container.register(name, component)

    def get_session_service(self) -> Any:
        """
        Get the session service instance for authentication middleware.

        This method returns the appropriate session manager for authentication
        and session management throughout the application.

        Returns:
            A session manager instance (RedisSessionManager or MemorySessionManager)
        """
        # Use the same session manager created by create_session_manager
        try:
            # Try to get the session manager from the container
            if container.has("session_manager"):
                logger.info("Using existing session manager from container")
                return container.get("session_manager")

            # If not available, create a new one
            logger.info("Creating new session manager for authentication")
            return self.create_session_manager()

        except Exception as e:
            logger.error(f"Failed to get session service: {str(e)}", exc_info=True)
            # Return a mock service for graceful degradation
            from unittest.mock import MagicMock
            mock_service = MagicMock()
            # Configure the mock to behave as expected
            mock_service.validate_session.return_value = None
            mock_service.get_session.return_value = None
            logger.warning("Using mock session service due to initialization failure")
            return mock_service

    def create_chatbot(self) -> Any:
        """Create the main Chatbot orchestrator component."""
        from src.chatbot import Chatbot

        # Get dependencies from the container
        nlu_engine = container.get("nlu_engine")
        dialog_manager = container.get("dialog_manager")
        knowledge_base = container.get("knowledge_base")
        response_generator = container.get("response_generator")
        service_hub = container.get("service_hub")
        session_manager = container.get("session_manager")
        db_manager = container.get("database_manager")

        # Inject dependencies into Chatbot constructor
        return Chatbot(
            nlu_engine=nlu_engine,
            dialog_manager=dialog_manager,
            knowledge_base=knowledge_base,
            response_generator=response_generator,
            service_hub=service_hub,
            session_manager=session_manager,
            db_manager=db_manager
        )

    def create_database_manager(self) -> Any:
        """Create or return the shared database manager component (SINGLETON PATTERN)."""
        from src.knowledge.database import DatabaseManager

        # Return existing shared instance if available
        if self._shared_db_manager is not None:
            logger.info("🔄 Reusing shared DatabaseManager instance (connection pool sharing)")
            return self._shared_db_manager

        # Create new shared instance only once
        logger.info("📊 Creating shared DatabaseManager with PostgreSQL database (SINGLETON)")
        self._shared_db_manager = DatabaseManager()
        logger.info("✅ Shared DatabaseManager created - all components will reuse this instance")
        return self._shared_db_manager

    def create_knowledge_base(self) -> Any:
        """Create the knowledge base component."""
        from src.knowledge.knowledge_base import KnowledgeBase

        # Always use the new Knowledge Base implementation (default since Phase 5)
        logger.info("Creating Knowledge Base implementation with database connection (new implementation default)")
        # Get DatabaseManager instance from the container
        db_manager = container.get("database_manager")

        # Create and return the KnowledgeBase with the db_manager
        return KnowledgeBase(
            db_manager=db_manager, # Inject the db_manager instance
            vector_db_uri=settings.vector_db_uri,
            content_path=settings.content_path
        )

    def create_nlu_engine(self) -> Any:
        """Create the NLU engine component."""
        from src.nlu.engine import NLUEngine

        knowledge_base = container.get("knowledge_base")
        return NLUEngine(
            models_config=settings.models_config,
            knowledge_base=knowledge_base
        )

    def create_dialog_manager(self) -> Any:
        """Create the dialog manager component."""
        from src.dialog.manager import DialogManager

        knowledge_base = container.get("knowledge_base")
        return DialogManager(
            flows_config=settings.flows_config,
            knowledge_base=knowledge_base
        )

    def create_response_generator(self) -> Any:
        """Create the response generator component."""
        from src.response.generator import ResponseGenerator

        knowledge_base = container.get("knowledge_base")
        return ResponseGenerator(
            templates_path=settings.templates_path,
            knowledge_base=knowledge_base,
            config=self.configs.get("response", {})
        )

    def create_service_hub(self) -> Any:
        """Create the service hub component."""
        from src.integration.service_hub import ServiceHub

        return ServiceHub(
            config_path=settings.services_config
        )

    def create_session_manager(self) -> Any:
        """
        Create the session manager component.

        Returns:
            RedisSessionManager: A Redis-based session manager
            MemorySessionManager: A memory-based session manager (fallback for testing)
        """
        from src.session.redis_manager import RedisSessionManager
        from src.session.memory_manager import MemorySessionManager

        # Handle testing environment
        is_testing = os.getenv("TESTING") == "true"
        if is_testing:
            logger.info("Using memory session manager for testing")
            return MemorySessionManager(session_ttl=settings.session_ttl)

        # For production and development, use Redis
        try:
            # Determine Redis URI
            is_docker = os.path.exists("/.dockerenv")
            if is_docker:
                redis_uri = "redis://redis:6379/0"  # Use Docker service name
                logger.info(f"Using Docker Redis URI: {redis_uri}")
            else:
                redis_uri = settings.redis_url
                logger.info(f"Using local Redis URI: {redis_uri}")

            return RedisSessionManager(
                redis_uri=redis_uri,
                session_ttl=settings.session_ttl
            )

        except Exception as e:
            logger.warning(f"Failed to create Redis session manager: {e}. Falling back to memory-based session manager")
            return MemorySessionManager(session_ttl=settings.session_ttl)

    def create_search_service(self) -> Any:
        """Create the search service component."""
        from src.services.search_service import SearchService
        
        # Get the database manager from container
        db_manager = container.get("database_manager")
        return SearchService(db_manager=db_manager)

    def create_unified_search_service(self) -> Any:
        """Create the unified search service component."""
        from src.services.search_service import UnifiedSearchService
        
        # Get the database manager from container
        db_manager = container.get("database_manager")
        return UnifiedSearchService(db_manager=db_manager)

# Create a global factory instance
component_factory = ComponentFactory()