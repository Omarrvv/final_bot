"""
Factory module for the Egypt Tourism Chatbot.
Creates and configures components with dependency injection.
"""
import os
import logging
from src.services.anthropic_service import AnthropicService
from typing import Dict, Any, Optional

from src.utils.container import container
from src.utils.exceptions import ConfigurationError

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
        self._load_environment_variables()
        self._load_configurations()
        self._register_services()
        
    def _load_environment_variables(self):
        """Load environment variables."""
        self.env_vars = {
            "database_uri": os.getenv("DATABASE_URI", "sqlite:///./data/egypt_chatbot.db"),
            "vector_db_uri": os.getenv("VECTOR_DB_URI", "./data/vector_db"),
            "content_path": os.getenv("CONTENT_PATH", "./data"),
            "session_storage_uri": os.getenv("SESSION_STORAGE_URI", "file://./data/sessions"),
            "models_config": os.getenv("MODELS_CONFIG", "./configs/models.json"),
            "flows_config": os.getenv("FLOWS_CONFIG", "./configs/dialog_flows.json"),
            "services_config": os.getenv("SERVICES_CONFIG", "./configs/services.json"),
            "templates_path": os.getenv("TEMPLATES_PATH", "./configs/response_templates"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),  

            "debug": os.getenv("FLASK_ENV", "production") == "development"
        }
        
    def _load_configurations(self):
        """Load configuration files."""
        try:
            import json
            from pathlib import Path
            
            for config_name, config_path in [
                ("models", self.env_vars["models_config"]),
                ("flows", self.env_vars["flows_config"]),
                ("services", self.env_vars["services_config"])
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
        # Register configurations
        container.register("env_vars", self.env_vars)
        container.register("configs", self.configs)
        
        # Register factory methods for main components
        container.register_factory("knowledge_base", self.create_knowledge_base)
        container.register_factory("nlu_engine", self.create_nlu_engine)
        container.register_factory("dialog_manager", self.create_dialog_manager)
        container.register_factory("response_generator", self.create_response_generator)
        container.register_factory("service_hub", self.create_service_hub)
        container.register_factory("session_manager", self.create_session_manager)
        container.register_factory("database_manager", self.create_database_manager)
        self.register_component("anthropic_service", AnthropicService(self.env_vars))
        # Register Chatbot factory
        container.register_factory("chatbot", self.create_chatbot)

    def register_component(self, name, component):
        container.register(name, component)    

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
            # Remove initialize_components=False if Chatbot constructor doesn't take it
        )

    def create_database_manager(self) -> Any:
        """Create the database manager component."""
        from src.knowledge.database import DatabaseManager
        # Initialize DatabaseManager using the configured URI
        db_manager = DatabaseManager(database_uri=self.env_vars["database_uri"])
        # Optional: Check connection or perform initial setup if needed
        # db_manager.check_connection() 
        return db_manager
        
    def create_knowledge_base(self) -> Any:
        """Create the knowledge base component."""
        from src.knowledge.knowledge_base import KnowledgeBase
        # Get DatabaseManager instance from the container
        db_manager = container.get("database_manager") 
        
        return KnowledgeBase(
            db_manager=db_manager, # Inject the db_manager instance
            # Pass other URIs/paths if still needed by KB (vector_db_uri, content_path)
            vector_db_uri=self.env_vars["vector_db_uri"],
            content_path=self.env_vars["content_path"]
            # No longer need to pass database_uri here, as db_manager handles it
        )
    
    def create_nlu_engine(self) -> Any:
        """Create the NLU engine component."""
        from src.nlu.engine import NLUEngine
        
        knowledge_base = container.get("knowledge_base")
        return NLUEngine(
            models_config=self.env_vars["models_config"],
            knowledge_base=knowledge_base
        )
    
    def create_dialog_manager(self) -> Any:
        """Create the dialog manager component."""
        from src.dialog.manager import DialogManager
        
        knowledge_base = container.get("knowledge_base")
        return DialogManager(
            flows_config=self.env_vars["flows_config"],
            knowledge_base=knowledge_base
        )
    
    def create_response_generator(self) -> Any:
        """Create the response generator component."""
        from src.response.generator import ResponseGenerator
        
        knowledge_base = container.get("knowledge_base")
        return ResponseGenerator(
            templates_path=self.env_vars["templates_path"],
            knowledge_base=knowledge_base,
            config=self.configs.get("response", {})
        )
    
    def create_service_hub(self) -> Any:
        """Create the service hub component."""
        from src.integration.service_hub import ServiceHub
        
        return ServiceHub(
            config_path=self.env_vars["services_config"]
        )
    
    def create_session_manager(self) -> Any:
        """Create the session manager component."""
        from src.utils.session import SessionManager
        
        # Determine storage URI based on testing environment
        is_testing = os.getenv("TESTING") == "true"
        if is_testing:
            # Force file storage during testing, using the path set in test setup
            # Note: Assumes CONTENT_PATH is set correctly in test setup for temp dir
            temp_dir = self.env_vars.get("CONTENT_PATH") # Get temp path from env_vars
            if temp_dir:
                 storage_uri = f"file:///{os.path.join(temp_dir, '..' ,'sessions')}" # Construct path relative to CONTENT_PATH parent
                 logger.info(f"Forcing file session storage for testing: {storage_uri}")
            else:
                 logger.warning("CONTENT_PATH not found in env_vars during testing, defaulting session storage URI.")
                 storage_uri = self.env_vars["session_storage_uri"] 
        else:
            # Use configured/default URI for non-testing environments
            storage_uri = self.env_vars["session_storage_uri"]
            
            # Set USE_REDIS environment variable if session_storage_uri starts with redis://
            if storage_uri and storage_uri.startswith("redis://"):
                os.environ["USE_REDIS"] = "true"
                logger.info("Detected Redis URI in session_storage_uri, setting USE_REDIS=true")
            
        return SessionManager(
            session_ttl=3600,  # 1 hour by default
            storage_uri=storage_uri # Pass the determined URI
        )

# Create a global factory instance
component_factory = ComponentFactory() 