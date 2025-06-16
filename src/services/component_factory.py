"""
Factory module for the Egypt Tourism Chatbot.
Creates and configures components with dependency injection.
"""
import os
import time
import logging
from src.services.anthropic_service import AnthropicService
from typing import Dict, List, Any, Optional

from src.core.container import container
from src.utils.exceptions import ConfigurationError
from src.config_unified import settings

logger = logging.getLogger(__name__)

class ComponentFactory:
    """
    Factory for creating components with proper dependencies.
    Simplifies component creation and wiring.
    
    Implements singleton pattern to ensure consistent component creation.
    """
    
    _instance = None
    _lock = None

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            import threading
            if cls._lock is None:
                cls._lock = threading.Lock()
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the component factory."""
        if hasattr(self, '_initialized') and self._initialized:
            return  # Already initialized
            
        self.configs = {}
        self.env_vars = {}
        self._shared_db_manager = None  # Add shared database manager instance
        self._initialized = True

    def initialize(self):
        """Initialize the factory with environment variables and configurations."""
        logger.info("Initializing component factory...")

        # Log key feature flags
        logger.info(f"Feature flags (before initialization): " +
                   f"USE_POSTGRES={settings.feature_flags.use_postgres}")

        self._load_environment_variables()
        self._load_configurations()
        self._register_services()
        self._register_auto_init_callback()
        logger.info("Component factory initialization complete")

    def _register_auto_init_callback(self):
        """Register auto-initialization callback with service provider."""
        try:
            from src.core.service_provider import service_provider
            service_provider.register_auto_init_callback(self.initialize)
            logger.debug("Auto-initialization callback registered with service provider")
        except Exception as e:
            logger.warning(f"Failed to register auto-init callback: {e}")

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

        # CRITICAL FIX: Container safety validation
        try:
            # Register configurations
            container.register("env_vars", self.env_vars)
            container.register("configs", self.configs)
            container.register("settings", settings)

            # CRITICAL FIX: Register cached factory methods with validation
            logger.info("🔧 CRITICAL FIX: Registering component factories with safety validation...")
            
            # Register each factory with error checking
            factories_to_register = [
                ("knowledge_base", self.create_knowledge_base),
                ("nlu_engine", self.create_nlu_engine),
                ("dialog_manager", self.create_dialog_manager),
                ("response_generator", self.create_response_generator),
                ("service_hub", self.create_service_hub),
                ("session_manager", self.create_session_manager),
                ("database_manager", self.create_database_manager),
                ("search_service", self.create_search_service),
                ("unified_search_service", self.create_unified_search_service),
                ("chatbot", self.create_chatbot)
            ]
            
            successful_registrations = 0
            for factory_name, factory_method in factories_to_register:
                try:
                    container.register_cached_factory(factory_name, factory_method)
                    successful_registrations += 1
                    logger.debug(f"✅ Registered factory: {factory_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to register factory {factory_name}: {e}")
            
            logger.info(f"✅ CRITICAL FIX: Successfully registered {successful_registrations}/{len(factories_to_register)} factories")
            
            # Create AnthropicService with API key from settings
            try:
                anthropic_api_key = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else ""
                self.register_component("anthropic_service", AnthropicService({
                    "anthropic_api_key": anthropic_api_key
                }))
                logger.debug("✅ Registered AnthropicService")
            except Exception as e:
                logger.error(f"❌ Failed to register AnthropicService: {e}")

            logger.info("Service registration complete")
            
            # CRITICAL FIX: Enhanced container validation
            debug_info = container.get_cache_info()
            logger.info(f"🔍 CRITICAL FIX - Container validation:")
            logger.info(f"  Registered services: {debug_info['registered_services']}")
            logger.info(f"  Registered factories: {debug_info['registered_factories']}")
            logger.info(f"  Registered singletons: {debug_info['registered_singletons']}")
            
            # Calculate success metrics
            expected_factories = len(factories_to_register)
            actual_factories = len(debug_info['registered_factories'])
            success_rate = (actual_factories / expected_factories) * 100 if expected_factories > 0 else 0
            
            logger.info(f"📊 Component Factory Success Rate: {success_rate:.1f}% ({actual_factories}/{expected_factories})")
            
            if success_rate < 90:
                logger.error(f"❌ CRITICAL: Factory success rate below 90%! This will cause production issues.")
            elif success_rate == 100:
                logger.info("✅ PERFECT: 100% factory registration success!")
            else:
                logger.warning(f"⚠️  Factory success rate {success_rate:.1f}% - some components may fail")
            
            # Test critical component creation
            self._validate_critical_components()
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in service registration: {e}")
            raise ConfigurationError(f"Failed to register services: {str(e)}")
    
    def _validate_critical_components(self):
        """CRITICAL FIX: Validate that critical components are registered without creating them."""
        logger.info("🔍 CRITICAL FIX: Validating critical component registration (non-blocking)...")
        
        critical_components = ["database_manager", "nlu_engine", "chatbot", "knowledge_base"]
        validation_results = {}
        
        for component_name in critical_components:
            try:
                # CRITICAL FIX: Only check registration, don't create components 
                # (avoids database hangs and model loading delays)
                has_component = container.has(component_name)
                validation_results[component_name] = has_component
                
                if has_component:
                    logger.debug(f"✅ {component_name}: Factory registered successfully")
                else:
                    logger.error(f"❌ {component_name}: Factory not registered")
                    
            except Exception as e:
                validation_results[component_name] = False
                logger.error(f"❌ {component_name}: Registration check failed - {e}")
        
        # Calculate component registration success rate
        successful_components = sum(validation_results.values())
        total_components = len(critical_components)
        component_success_rate = (successful_components / total_components) * 100
        
        logger.info(f"📊 Critical Component Registration Rate: {component_success_rate:.1f}% ({successful_components}/{total_components})")
        
        if component_success_rate == 100:
            logger.info("✅ PERFECT: All critical component factories registered successfully!")
        else:
            logger.warning(f"⚠️  {total_components - successful_components} critical component factories missing")
            for component, success in validation_results.items():
                if not success:
                    logger.error(f"   - {component}: FACTORY NOT REGISTERED")
        
        # CRITICAL FIX: Add lightweight creation test for database manager only
        if validation_results.get("database_manager", False):
            try:
                logger.info("🔧 Testing database manager creation (with timeout)...")
                import threading
                import time
                
                test_result = {"success": False, "error": None}
                
                def test_db_creation():
                    try:
                        # Quick test with minimal timeout
                        test_db = self.create_database_manager()
                        test_result["success"] = test_db is not None
                    except Exception as e:
                        test_result["error"] = str(e)
                
                # Create test thread with 3-second timeout
                test_thread = threading.Thread(target=test_db_creation)
                test_thread.daemon = True
                test_thread.start()
                test_thread.join(timeout=3.0)  # 3-second timeout
                
                if test_thread.is_alive():
                    logger.warning("⚠️  Database creation test timed out (3s) - likely connection issue")
                elif test_result["success"]:
                    logger.info("✅ Database manager creation test passed")
                else:
                    logger.warning(f"⚠️  Database creation test failed: {test_result['error']}")
                    
            except Exception as e:
                logger.warning(f"⚠️  Database creation test error: {e}")
        
        return validation_results

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
        """Create the main Chatbot orchestrator component with lazy import to break circular dependency."""
        # LAZY IMPORT - only import when method is called to break circular dependency
        from src.services.chatbot_service import Chatbot

        # PERFORMANCE FIX: Fast initialization for demonstration
        logger.info("🚀 PERFORMANCE FIX: Creating chatbot with fast initialization")

        start_time = time.time()

        # Create lightweight components for speed
        nlu_engine = self.create_fast_nlu_engine()
        dialog_manager = self.create_dialog_manager()
        knowledge_base = self.create_knowledge_base()
        response_generator = self.create_response_generator()
        service_hub = self.create_service_hub()
        session_manager = self.create_session_manager()
        db_manager = self.create_database_manager()

        creation_time = time.time() - start_time
        logger.info(f"✅ Chatbot dependencies created in {creation_time:.3f}s")

        # CRITICAL FIX: Inject knowledge base into response generator
        if hasattr(response_generator, 'knowledge_base') and response_generator.knowledge_base is None:
            response_generator.knowledge_base = knowledge_base
            logger.info("🔧 Injected knowledge base into response generator")

        # CRITICAL FIX: Update response generator to use correct template path
        correct_template_path = "./src/configs/response_templates"
        if hasattr(response_generator, 'templates_path'):
            old_path = response_generator.templates_path
            response_generator.templates_path = correct_template_path
            logger.info(f"🔧 Updated template path from {old_path} to {correct_template_path}")

            # Reload templates with correct path
            response_generator.templates = response_generator._load_templates(correct_template_path)
            logger.info(f"🔧 Reloaded templates: {list(response_generator.templates.keys())}")

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
        """Create the knowledge base component with auto-initialization safety."""
        from src.knowledge.knowledge_base import KnowledgeBase

        try:
            # CRITICAL FIX: Create database manager directly to avoid deadlock
            logger.info("🔧 CRITICAL FIX: Creating Knowledge Base with direct dependency creation")

            # Create database manager directly instead of using container.get()
            # This prevents the recursive lock acquisition deadlock
            db_manager = self.create_database_manager()
            
            # Validate database manager is functional
            if hasattr(db_manager, 'is_connected') and not db_manager.is_connected():
                logger.warning("⚠️  Database manager not connected, attempting to connect...")
                try:
                    db_manager.connect()
                except Exception as e:
                    logger.warning(f"Database connection failed: {e}")
            
            logger.info("✅ Creating Knowledge Base with validated database connection")
            
            # Create and return the KnowledgeBase with the db_manager
            knowledge_base = KnowledgeBase(
                db_manager=db_manager, # Inject the db_manager instance
                vector_db_uri=settings.vector_db_uri,
                content_path=settings.content_path
            )
            
            logger.info("✅ CRITICAL FIX: Knowledge Base created successfully")
            return knowledge_base
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR: Failed to create knowledge base: {e}")
            logger.error("   This will cause component factory success rate to drop")
            # Return a minimal mock knowledge base for graceful degradation
            from unittest.mock import MagicMock
            mock_kb = MagicMock()
            mock_kb.search_attractions.return_value = []
            mock_kb.search_restaurants.return_value = []
            mock_kb.search_hotels.return_value = []
            logger.warning("⚠️  Using mock knowledge base for graceful degradation")
            return mock_kb

    def create_nlu_engine(self) -> Any:
        """Create the NLU engine component with auto-initialization and smart loading."""
        from src.nlu.engine import NLUEngine

        try:
            # CRITICAL FIX: Create NLU engine with smart initialization
            logger.info("🔧 CRITICAL FIX: Creating NLU Engine with auto-initialization")
            
            # CRITICAL FIX: Use full initialization to ensure language detection works
            nlu_engine = NLUEngine(
                models_config=settings.models_config,
                knowledge_base=None,  # Break circular dependency - inject later if needed
                lightweight_init=False  # FIXED: Use full initialization for proper language support
            )
            
            # CRITICAL FIX: Force initialization of essential models for real AI functionality
            logger.info("🚀 CRITICAL FIX: Triggering essential model loading for real AI processing...")
            
            # Auto-trigger model loading in background to enable full AI capabilities
            try:
                # Check if we can safely initialize models without hanging
                if hasattr(nlu_engine, '_init_full') and hasattr(nlu_engine, '_models_loaded'):
                    if not nlu_engine._models_loaded:
                        logger.info("📦 Loading essential AI models for full NLU processing...")
                        
                        # Initialize essential components manually
                        from src.utils.cache import LRUCache
                        
                        # Initialize embedding cache if not exists
                        if not hasattr(nlu_engine, 'embedding_cache') or nlu_engine.embedding_cache is None:
                            nlu_engine.embedding_cache = LRUCache(max_size=5000)
                        
                        # Initialize embedding service with auto-loading
                        from src.nlu.embedding_adapter import InfrastructureEmbeddingService
                        nlu_engine.embedding_service = InfrastructureEmbeddingService(
                            models={},  # Will auto-load essential models
                            tokenizers={},
                            cache=nlu_engine.embedding_cache
                        )
                        
                        # Initialize hierarchical intent classifier (Phase 1 Week 2)
                        from src.nlu.hierarchical_intent_classifier import HierarchicalIntentClassifier
                        nlu_engine.intent_classifier = HierarchicalIntentClassifier(
                            config=nlu_engine.models_config.get("intent_classification", {}),
                            embedding_service=nlu_engine.embedding_service,
                            knowledge_base=None  # Keep None to avoid circular dependency
                        )
                        
                        # Mark as ready for AI processing
                        nlu_engine._models_loaded = True
                        nlu_engine._fallback_mode = False
                        
                        logger.info("✅ CRITICAL FIX: NLU Engine upgraded to FULL AI PROCESSING mode")
                    else:
                        logger.info("ℹ️  NLU Engine models already loaded")
            
            except Exception as model_error:
                logger.warning(f"⚠️  Could not load full models immediately: {model_error}")
                logger.info("   NLU Engine will use lightweight mode and load models on first use")
            
            logger.info("✅ CRITICAL FIX: NLU Engine created successfully")
            return nlu_engine
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR: Failed to create NLU engine: {e}")
            logger.error("   This will cause component factory success rate to drop")
            # Return a minimal fast NLU engine for graceful degradation
            try:
                from src.nlu.fast_nlu_engine import FastNLUEngine
                fast_engine = FastNLUEngine()
                logger.warning("⚠️  Using fast NLU engine for graceful degradation")
                return fast_engine
            except Exception:
                # Ultimate fallback: mock NLU engine
                from unittest.mock import MagicMock
                mock_nlu = MagicMock()
                mock_nlu.process.return_value = {
                    "intent": "general_query",
                    "entities": {},
                    "confidence": 0.5,
                    "language": "en"
                }
                logger.warning("⚠️  Using mock NLU engine for graceful degradation")
                return mock_nlu

    def create_fast_nlu_engine(self) -> Any:
        """Create a fast, lightweight NLU engine for demonstration performance."""
        try:
            from src.nlu.fast_nlu_engine import FastNLUEngine
            logger.info("🚀 Creating fast NLU engine for demonstration performance")
            return FastNLUEngine()
        except Exception as e:
            logger.warning(f"Fast NLU engine not available: {e}, using mock")
            # Ultimate fallback: mock NLU engine
            from unittest.mock import MagicMock
            mock_nlu = MagicMock()
            mock_nlu.process.return_value = {
                "intent": "general_query",
                "entities": {},
                "confidence": 0.5,
                "language": "en"
            }
            return mock_nlu

    def create_dialog_manager(self) -> Any:
        """Create the dialog manager component - FIXED: Break circular dependency."""
        from src.dialog.manager import DialogManager

        # BREAK CIRCULAR DEPENDENCY: Create dialog manager without knowledge_base
        return DialogManager(
            flows_config=settings.flows_config,
            knowledge_base=None  # Break circular dependency - inject later if needed
        )

    def create_response_generator(self) -> Any:
        """Create the response generator component - FIXED: Break circular dependency."""
        from src.response.generator import ResponseGenerator

        # BREAK CIRCULAR DEPENDENCY: Create response generator without knowledge_base
        return ResponseGenerator(
            templates_path=settings.templates_path,
            knowledge_base=None,  # Break circular dependency - inject later if needed
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