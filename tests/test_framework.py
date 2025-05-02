"""
Test framework for the Egypt Tourism Chatbot.
Provides base classes and utilities for testing components.
"""
import os
import sys
import json
import uuid
import pytest
import unittest
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock, patch
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Keep necessary imports
from src.nlu.engine import NLUEngine
from src.knowledge.knowledge_base import KnowledgeBase
from src.dialog.manager import DialogManager
from src.response.generator import ResponseGenerator
from src.integration.service_hub import ServiceHub
from src.utils.session import SessionManager
from src.chatbot import Chatbot

# --- Import FastAPI TestClient and the app instance ---
from fastapi.testclient import TestClient
# Ensure src.main is importable (PYTHONPATH should be set)
try:
    from src.main import app as fastapi_app
except ImportError as e:
    # Provide a more informative error if the app cannot be imported
    # This often happens if component initialization fails during import
    print(f"ERROR: Could not import FastAPI app from src.main: {e}")
    print("Ensure all components initialize correctly and PYTHONPATH is set.")
    # Optionally raise the error or provide a dummy app for fixture collection
    # raise
    fastapi_app = None # Or a dummy FastAPI() instance
# --- End FastAPI Imports ---


class BaseTestCase(unittest.TestCase):
    """Base test case for all tests."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        
        # Set up environment variables for testing
        os.environ["CONTENT_PATH"] = os.path.join(self.temp_dir, "data")
        # Use PostgreSQL test database instead of SQLite
        os.environ["POSTGRES_URI"] = "postgresql://postgres:postgres@localhost:5432/egypt_chatbot_test"
        os.environ["SESSION_STORAGE_URI"] = f"file:///{os.path.join(self.temp_dir, 'sessions')}"
        os.environ["FLASK_ENV"] = "testing"
        os.environ["TESTING"] = "true"
        
        # Create necessary directories
        os.makedirs(os.path.join(self.temp_dir, "data", "attractions"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "data", "accommodations"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "data", "restaurants"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "configs"), exist_ok=True)
        
        # Create test configurations
        self._create_test_configs()
        
        # Create test data
        self._create_test_data()
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
        
        # Reset environment variables
        for key in ["CONTENT_PATH", "POSTGRES_URI", "SESSION_STORAGE_URI", "FLASK_ENV", "TESTING"]:
            if key in os.environ:
                del os.environ[key]
    
    def _create_test_configs(self):
        """Create test configuration files."""
        # Models config
        models_config = {
            "language_detection": {
                "model_path": "lid.176.bin",
                "confidence_threshold": 0.8
            },
            "nlp_models": {
                "en": "en_core_web_sm",
                "ar": "xx_ent_wiki_sm"
            },
            "transformer_models": {
                "multilingual": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
            },
            "intent_classification": {
                "intents_file": os.path.join(self.temp_dir, "configs", "intents.json")
            }
        }
        
        with open(os.path.join(self.temp_dir, "configs", "models.json"), "w") as f:
            json.dump(models_config, f)
        
        # Intents config
        intents_config = {
            "greeting": {
                "examples": [
                    "hello", "hi", "hey", "good morning", "good afternoon", 
                    "greetings", "السلام عليكم", "مرحبا", "صباح الخير"
                ],
                "responses": ["greeting"]
            },
            "farewell": {
                "examples": [
                    "goodbye", "bye", "see you", "later", "take care",
                    "مع السلامة", "وداعا", "إلى اللقاء"
                ],
                "responses": ["farewell"]
            },
            "attraction_info": {
                "examples": [
                    "tell me about the pyramids", "information about luxor temple",
                    "what is the sphinx", "history of valley of the kings",
                    "opening hours for egyptian museum", "ticket prices for karnak",
                    "معلومات عن الأهرامات", "ما هو أبو الهول", "مواعيد فتح المتحف المصري"
                ],
                "responses": ["attraction_info"],
                "entities": ["attraction", "location"]
            }
        }
        
        with open(os.path.join(self.temp_dir, "configs", "intents.json"), "w") as f:
            json.dump(intents_config, f)
        
        # Dialog flows config
        dialog_flows = {
            "greeting": {
                "initial_response": "greeting",
                "suggestions": ["attractions", "hotels", "restaurants"],
                "next_states": {
                    "*": "information_gathering"
                }
            },
            "information_gathering": {
                "response": "general",
                "next_states": {
                    "attraction_info": "attraction_details",
                    "*": "information_gathering"
                }
            },
            "attraction_details": {
                "requires_entities": ["attraction"],
                "entity_missing_prompts": {
                    "attraction": {
                        "en": "Which attraction would you like to know about?",
                        "ar": "ما هو المعلم السياحي الذي ترغب في معرفة المزيد عنه؟"
                    }
                },
                "response": "attraction_details",
                "next_states": {
                    "*": "information_gathering"
                }
            }
        }
        
        with open(os.path.join(self.temp_dir, "configs", "dialog_flows.json"), "w") as f:
            json.dump(dialog_flows, f)
        
        # Services config
        services_config = {
            "mock_service": {
                "type": "builtin",
                "methods": ["test_method"],
                "config": {
                    "test_param": "test_value"
                }
            }
        }
        
        with open(os.path.join(self.temp_dir, "configs", "services.json"), "w") as f:
            json.dump(services_config, f)
    
    def _create_test_data(self):
        """Create test data files."""
        # Create test attraction
        test_attraction = {
            "id": "test_attraction",
            "name": {
                "en": "Test Attraction",
                "ar": "معلم اختبار"
            },
            "type": "test",
            "location": {
                "city": "Test City",
                "city_ar": "مدينة اختبار",
                "region": "Test Region",
                "region_ar": "منطقة اختبار",
                "coordinates": {
                    "latitude": 0.0,
                    "longitude": 0.0
                }
            },
            "description": {
                "en": "This is a test attraction for unit tests.",
                "ar": "هذا معلم اختبار للاختبارات الوحدوية."
            },
            "practical_info": {
                "opening_hours": "9:00 AM - 5:00 PM",
                "ticket_prices": {
                    "adults": "10 USD",
                    "children": "5 USD"
                }
            },
            "keywords": ["test", "attraction", "اختبار"],
            "updated_at": "2023-01-01T00:00:00Z"
        }
        
        with open(os.path.join(self.temp_dir, "data", "attractions", "test_attraction.json"), "w") as f:
            json.dump(test_attraction, f)


class MockNLUEngine:
    """Mock NLU engine for testing."""
    
    def __init__(self, intent: str = "greeting", confidence: float = 0.9, entities: Dict = None):
        """
        Initialize mock NLU engine.
        
        Args:
            intent (str): Intent to return
            confidence (float): Confidence score
            entities (dict, optional): Entities to return
        """
        self.intent = intent
        self.confidence = confidence
        self.entities = entities or {}
    
    def process(self, text: str, session_id: str, language: str = None, context: Dict = None) -> Dict:
        """
        Process a message.
        
        Args:
            text (str): Message text
            session_id (str): Session ID
            language (str, optional): Language code
            context (dict, optional): Conversation context
            
        Returns:
            dict: NLU result
        """
        return {
            "text": text,
            "processed_text": text.lower(),
            "language": language or "en",
            "intent": self.intent,
            "intent_confidence": self.confidence,
            "entities": self.entities,
            "session_id": session_id
        }


class MockKnowledgeBase:
    """Mock knowledge base for testing."""
    
    def __init__(self, attractions: Dict = None, accommodations: Dict = None, restaurants: Dict = None):
        """
        Initialize mock knowledge base.
        
        Args:
            attractions (dict, optional): Mock attraction data
            accommodations (dict, optional): Mock accommodation data
            restaurants (dict, optional): Mock restaurant data
        """
        self.attractions = attractions or {
            "test_attraction": {
                "id": "test_attraction", 
                "name": {"en": "Test Attraction"}, 
                "type": "test", 
                "location": {"city": "Test City", "region": "Test Region"}
            }
        }
        self.accommodations = accommodations or {}
        self.restaurants = restaurants or {}
    
    def get_attraction_by_id(self, attraction_id: str) -> Optional[Dict]:
        """Get attraction by ID."""
        return self.attractions.get(attraction_id)
    
    def lookup_attraction(self, name: str, language: str, location: str = None) -> Optional[Dict]:
        """Lookup attraction by name."""
        # Simple mock lookup
        for attraction in self.attractions.values():
            if attraction["name"].get(language) == name:
                return attraction
        return None
    
    def search_attractions(self, query: str = "", filters: Dict = None, language: str = "en", limit: int = 10) -> List[Dict]:
        """Search attractions."""
        # Return a list of attractions based on simple matching or filters
        # For simplicity, return all attractions if no query/filters
        if not query and not filters:
            return list(self.attractions.values())[:limit]
        # Implement basic search if needed for tests, otherwise return empty
        return []

    # --- ADD MISSING MOCK METHODS --- 
    def lookup_location(self, name: str, language: str) -> Optional[Dict]:
        """Mock location lookup."""
        # Basic mock - return a simple structure if name matches common cities
        if name.lower() in ["cairo", "luxor", "aswan", "القاهرة", "الأقصر", "أسوان"]:
            return {"name": name, "canonical_name": name, "type": "city"} # Example structure
        return None

    def search_hotels(self, query: str = "", filters: Dict = None, language: str = "en", limit: int = 10) -> List[Dict]:
        """Mock search hotels."""
        # Return empty list for basic testing needs
        return []

    def search_restaurants(self, query: str = "", filters: Dict = None, language: str = "en", limit: int = 10) -> List[Dict]:
        """Mock search restaurants."""
        # Return empty list for basic testing needs
        return []

    # Add other required KB methods as mocks if needed by other tests
    # e.g., get_restaurant_by_id, get_hotel_by_id, etc.
    def get_restaurant_by_id(self, restaurant_id: str) -> Optional[Dict]:
        return self.restaurants.get(restaurant_id)
        
    def get_hotel_by_id(self, hotel_id: str) -> Optional[Dict]:
        return self.accommodations.get(hotel_id)
        
    def get_practical_info(self, item_id: str, item_type: str, language: str = "en") -> Optional[Dict]:
        # Simple mock - needs expansion if tests rely on specific practical info
        if item_type == "attraction" and item_id in self.attractions:
            return self.attractions[item_id].get("practical_info")
        return None


class MockDialogManager:
    """Mock dialog manager for testing."""
    
    def __init__(self, action: Dict = None):
        """
        Initialize mock dialog manager.
        
        Args:
            action (dict, optional): Action to return
        """
        self.action = action or {
            "action_type": "response",
            "response_type": "greeting",
            "dialog_state": "information_gathering",
            "suggestions": ["attractions", "hotels", "restaurants"]
        }
    
    def next_action(self, nlu_result: Dict, context: Dict) -> Dict:
        """Get next dialog action."""
        return self.action


class MockResponseGenerator:
    """Mock response generator for testing."""
    
    def __init__(self, response: Dict = None):
        """
        Initialize mock response generator.
        
        Args:
            response (dict, optional): Response to return
        """
        self.response = response or {
            "text": "This is a test response.",
            "response_type": "greeting",
            "language": "en",
            "suggestions": ["attractions", "hotels", "restaurants"]
        }
    
    def generate_response(self, dialog_action: Dict, nlu_result: Dict, context: Dict) -> Dict:
        """Generate response."""
        return self.response


class MockServiceHub:
    """Mock service hub for testing."""
    
    def __init__(self, service_results: Dict = None):
        """
        Initialize mock service hub.
        
        Args:
            service_results (dict, optional): Service results to return
        """
        self.service_results = service_results or {}
    
    def execute_service(self, service: str, method: str, params: Dict = None) -> Dict:
        """Execute service."""
        key = f"{service}_{method}"
        return self.service_results.get(key, {"result": "mock_result"})
    
    def get_service(self, service: str) -> Optional[Any]:
        """Get service by name."""
        return None


class MockSessionManager:
    """Mock session manager for testing."""
    
    def __init__(self, sessions: Dict = None):
        """
        Initialize mock session manager.
        
        Args:
            sessions (dict, optional): Session data
        """
        self.sessions = sessions or {}
    
    def create_session(self) -> str:
        """Create new session."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "id": session_id,
            "created_at": "2023-01-01T00:00:00Z",
            "context": {
                "dialog_state": "greeting",
                "entities": {},
                "history": []
            }
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    def get_context(self, session_id: str) -> Dict:
        """Get session context."""
        session = self.get_session(session_id)
        if session:
            return session.get("context", {})
        return {}
    
    def set_context(self, session_id: str, context: Dict) -> bool:
        """Set session context."""
        if session_id in self.sessions:
            self.sessions[session_id]["context"] = context
            return True
        return False
    
    def update_context(self, session_id: str, nlu_result: Dict) -> Dict:
        """Update context based on NLU result."""
        context = self.get_context(session_id)
        
        # Update with NLU result
        if "intent" in nlu_result:
            context["last_intent"] = nlu_result["intent"]
        
        if "entities" in nlu_result:
            if "entities" not in context:
                context["entities"] = {}
            
            for entity_type, entity_values in nlu_result["entities"].items():
                context["entities"][entity_type] = entity_values
        
        # Set updated context
        self.set_context(session_id, context)
        
        return context


class ChatbotTestMixin:
    """Mixin for chatbot tests with common utilities."""
    
    def create_test_chatbot(self, **kwargs):
        """
        Create a test chatbot instance with optional mocked components.
        
        Args:
            **kwargs: Component overrides
                - nlu_engine: NLU engine instance
                - knowledge_base: Knowledge base instance
                - dialog_manager: Dialog manager instance
                - response_generator: Response generator instance
                - service_hub: Service hub instance
                - session_manager: Session manager instance
        """
        chatbot = Chatbot()
        
        # Override components with mocks if provided
        for component, instance in kwargs.items():
            if hasattr(chatbot, component):
                setattr(chatbot, component, instance)
        
        return chatbot
    
    def generate_test_message(self, text="Hello", intent="greeting", entities=None):
        """
        Generate a test message.
        
        Args:
            text (str): Message text
            intent (str): Intent
            entities (dict, optional): Entities
            
        Returns:
            tuple: (session_id, result)
        """
        entities = entities or {}
        
        # Create test session
        session_id = str(uuid.uuid4())
        
        # Create mock NLU engine
        nlu_engine = MockNLUEngine(intent=intent, entities=entities)
        
        # Create mock dialog manager
        dialog_manager = MockDialogManager()
        
        # Create mock response generator
        response_generator = MockResponseGenerator()
        
        # Create mock session manager
        session_manager = MockSessionManager(sessions={
            session_id: {
                "id": session_id,
                "created_at": "2023-01-01T00:00:00Z",
                "context": {
                    "dialog_state": "greeting",
                    "entities": {},
                    "history": []
                }
            }
        })
        
        # Create test chatbot
        chatbot = self.create_test_chatbot(
            nlu_engine=nlu_engine,
            dialog_manager=dialog_manager,
            response_generator=response_generator,
            session_manager=session_manager
        )
        
        # Process message
        result = chatbot.process_message(text, session_id)
        
        return session_id, result


# --- Fixture Definition --- 
@pytest.fixture(scope="module") # Use module scope for efficiency
def test_client():
    """Pytest fixture for creating a FastAPI test client."""
    if fastapi_app is None:
        pytest.fail("FastAPI app could not be imported. Check errors above.")
        
    # Create TestClient instance using the imported FastAPI app
    with TestClient(fastapi_app) as client:
        # Yield the client for use in tests
        yield client
# --- End Fixture Definition ---