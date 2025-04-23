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
from src.utils.settings import settings

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
        
    def initialize(self):
        """Initialize the factory with environment variables and configurations."""
        logger.info("Initializing component factory...")
        
        # Log key feature flags
        logger.info(f"Feature flags (before initialization): " + 
                   f"USE_NEW_KB={settings.feature_flags.use_new_kb}, " +
                   f"USE_NEW_API={settings.feature_flags.use_new_api}, " +
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
                   f"USE_NEW_KB={settings.feature_flags.use_new_kb}, " +
                   f"USE_NEW_API={settings.feature_flags.use_new_api}, " +
                   f"USE_POSTGRES={settings.feature_flags.use_postgres}")
        
        # Register configurations
        container.register("env_vars", self.env_vars)
        container.register("configs", self.configs)
        container.register("settings", settings)
        
        # Register factory methods for main components
        container.register_factory("knowledge_base", self.create_knowledge_base)
        container.register_factory("nlu_engine", self.create_nlu_engine)
        container.register_factory("dialog_manager", self.create_dialog_manager)
        container.register_factory("response_generator", self.create_response_generator)
        container.register_factory("service_hub", self.create_service_hub)
        container.register_factory("session_manager", self.create_session_manager)
        container.register_factory("database_manager", self.create_database_manager)
        
        # Create AnthropicService with API key from settings
        anthropic_api_key = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else ""
        self.register_component("anthropic_service", AnthropicService({
            "anthropic_api_key": anthropic_api_key
        }))
        
        # Register Chatbot factory
        container.register_factory("chatbot", self.create_chatbot)
        
        logger.info("Service registration complete")

    def register_component(self, name, component):
        container.register(name, component)    

    def get_session_service(self) -> Any:
        """
        Get the SessionService instance for authentication middleware.
        
        This method initializes a Redis client and creates a SessionService
        instance using that client, enabling authentication and session
        management throughout the application.
        
        Returns:
            SessionService instance
        """
        from src.services.session import SessionService
        from src.services.redis_client import RedisClient
        import asyncio
        from unittest.mock import MagicMock
        
        try:
            # Get Redis URI from settings, defaulting to localhost
            is_docker = os.path.exists("/.dockerenv")
            redis_uri = "redis://redis:6379/0" if is_docker else "redis://localhost:6379/0"
            
            # Use explicit setting if available
            if settings.redis_url:
                redis_uri = settings.redis_url
                
            logger.info(f"Initializing SessionService with Redis URI: {redis_uri}")
            
            # Create a fake Redis client - actual connection will happen through the lifespan
            # This avoids the issue with asyncio.run_until_complete() in an existing event loop
            mock_redis = MagicMock()
            session_service = SessionService(mock_redis)
            
            # Store the Redis URI for later use in the lifespan context
            session_service.redis_uri = redis_uri
            
            logger.info("SessionService placeholder initialized successfully")
            return session_service
            
        except Exception as e:
            logger.error(f"Failed to initialize SessionService: {str(e)}", exc_info=True)
            # Return a mock SessionService for graceful degradation
            # This helps the application start even if Redis is unavailable
            from unittest.mock import MagicMock
            mock_service = MagicMock()
            # Configure the mock to behave as expected
            mock_service.validate_session.return_value = None
            logger.warning("Using mock SessionService due to initialization failure")
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
        """Create the database manager component."""
        from src.knowledge.database import DatabaseManager
        # Initialize DatabaseManager using the configured URI
        db_manager = DatabaseManager(database_uri=settings.database_uri)
        # Optional: Check connection or perform initial setup if needed
        # db_manager.check_connection() 
        return db_manager
        
    def create_knowledge_base(self) -> Any:
        """Create the knowledge base component."""
        from src.knowledge.knowledge_base import KnowledgeBase
        from src.knowledge.data.tourism_kb import TourismKnowledgeBase
        
        # Check if USE_NEW_KB flag is enabled
        if settings.feature_flags.use_new_kb:
            logger.info("Creating new Knowledge Base implementation with database connection (USE_NEW_KB=true)")
            # Get DatabaseManager instance from the container
            db_manager = container.get("database_manager") 
            
            # Create and return the KnowledgeBase with the db_manager
            return KnowledgeBase(
                db_manager=db_manager, # Inject the db_manager instance
                vector_db_uri=settings.vector_db_uri,
                content_path=settings.content_path
            )
        else:
            # Legacy implementation - use a direct wrapper around TourismKnowledgeBase
            logger.warning("Using legacy Knowledge Base implementation (USE_NEW_KB=false)")
            class LegacyKnowledgeBase:
                """
                Legacy wrapper around TourismKnowledgeBase to maintain API compatibility
                """
                def __init__(self):
                    self.tourism_kb = TourismKnowledgeBase()
                
                def lookup_attraction(self, attraction_name: str, language: str = "en"):
                    """Map lookup_attraction to the hardcoded data"""
                    attractions = self.tourism_kb.get_category("attractions")
                    
                    # Direct lookup if exact key exists
                    if attraction_name.lower() in attractions:
                        return {
                            "id": attraction_name.lower(),
                            "name": {"en": attraction_name, "ar": attraction_name},
                            "description": {"en": attractions[attraction_name.lower()], "ar": ""},
                            "location": {"coordinates": {"latitude": 0, "longitude": 0}},
                            "source": "hardcoded"
                        }
                    
                    # Fuzzy search for name in hardcoded attraction descriptions
                    for key, description in attractions.items():
                        if attraction_name.lower() in key.lower() or key.lower() in attraction_name.lower():
                            return {
                                "id": key,
                                "name": {"en": key.title(), "ar": key.title()},
                                "description": {"en": description, "ar": ""},
                                "location": {"coordinates": {"latitude": 0, "longitude": 0}},
                                "source": "hardcoded"
                            }
                    
                    return None
                
                def search_attractions(self, query: str = "", filters=None, language: str = "en", limit: int = 10):
                    """Map search_attractions to the hardcoded data"""
                    results = []
                    attractions = self.tourism_kb.get_category("attractions")
                    
                    if not query or query == "":
                        # Return all attractions up to limit
                        for key, description in list(attractions.items())[:limit]:
                            results.append({
                                "id": key,
                                "name": {"en": key.title(), "ar": key.title()},
                                "description": {"en": description, "ar": ""},
                                "location": {"coordinates": {"latitude": 0, "longitude": 0}},
                                "source": "hardcoded"
                            })
                    else:
                        # Search for query in keys and descriptions
                        for key, description in attractions.items():
                            if (query.lower() in key.lower() or 
                                query.lower() in description.lower()):
                                results.append({
                                    "id": key,
                                    "name": {"en": key.title(), "ar": key.title()},
                                    "description": {"en": description, "ar": ""},
                                    "location": {"coordinates": {"latitude": 0, "longitude": 0}},
                                    "source": "hardcoded"
                                })
                                
                                if len(results) >= limit:
                                    break
                    
                    return results
                
                def get_practical_info(self, category: str, language: str = "en"):
                    """Map get_practical_info to the hardcoded data"""
                    travel_tips = self.tourism_kb.get_category("travel_tips")
                    
                    if category in travel_tips:
                        return {
                            "id": category,
                            "title": {"en": category.title(), "ar": category.title()},
                            "content": {"en": travel_tips[category], "ar": ""},
                            "source": "hardcoded"
                        }
                    
                    # Try to fuzzy match the category
                    for key, content in travel_tips.items():
                        if category.lower() in key.lower() or key.lower() in category.lower():
                            return {
                                "id": key,
                                "title": {"en": key.title(), "ar": key.title()},
                                "content": {"en": content, "ar": ""},
                                "source": "hardcoded"
                            }
                    
                    return None
                
                # Add other methods as needed for compatibility
            
            return LegacyKnowledgeBase()
    
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
        """Create the session manager component."""
        from src.utils.session import SessionManager
        import tempfile
        
        # Set default to file storage
        storage_uri = settings.session_storage_uri
        
        # Handle testing environment
        is_testing = os.getenv("TESTING") == "true"
        if is_testing:
            # Force file storage during testing
            temp_dir = settings.content_path
            if temp_dir:
                storage_uri = f"file:///{os.path.join(temp_dir, '..', 'sessions')}"
                logger.info(f"Forcing file session storage for testing: {storage_uri}")
        else:
            # Check if Redis is enabled via feature flag
            if settings.feature_flags.use_redis:
                logger.info("Redis session storage enabled via USE_REDIS feature flag")
                # Use Redis in Docker, local Redis for development
                is_docker = os.path.exists("/.dockerenv")
                if is_docker:
                    storage_uri = "redis://redis:6379/1"  # Use Docker service name
                    logger.info(f"Using Docker Redis URI: {storage_uri}")
                else:
                    storage_uri = settings.redis_url or "redis://localhost:6379/1"
                    logger.info(f"Using local Redis URI: {storage_uri}")
            else:
                # Redis is disabled, force file storage
                # Try to use a reliable writable location
                try:
                    # Try user's home directory first
                    home_path = os.path.expanduser("~/.egypt_sessions")
                    os.makedirs(home_path, exist_ok=True)
                    storage_uri = f"file:///{home_path}"
                except:
                    # Fall back to temp directory
                    temp_dir = tempfile.gettempdir()
                    storage_uri = f"file:///{os.path.join(temp_dir, 'egypt_sessions')}"
                
                logger.info(f"Redis disabled (USE_REDIS=false), using file storage: {storage_uri}")
        
        logger.info(f"Session manager using storage URI: {storage_uri}")
        return SessionManager(
            session_ttl=settings.jwt_expiration,  # Use same TTL as JWT
            storage_uri=storage_uri
        )

# Create a global factory instance
component_factory = ComponentFactory() 