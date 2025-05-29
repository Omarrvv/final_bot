import os
import sys
import json
import pytest
import logging
from unittest.mock import MagicMock, patch

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.chatbot import Chatbot
from src.knowledge.knowledge_base import KnowledgeBase
from src.nlu.intent import IntentClassifier
from src.utils.llm_config import use_llm_first

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestDatabaseFirst:
    """Test that the chatbot uses the database first before falling back to LLM."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        mock_db = MagicMock()
        mock_db.is_connected.return_value = True
        mock_db.execute_query.return_value = []
        return mock_db

    @pytest.fixture
    def mock_knowledge_base(self, mock_db_manager):
        """Create a mock knowledge base with the mock database manager."""
        kb = MagicMock(spec=KnowledgeBase)
        kb.db_manager = mock_db_manager
        kb._db_available = True

        # Mock the search methods to return test data
        kb.search_practical_info.return_value = [{
            "id": "drinking_water",
            "category_id": "health_safety",
            "title": {"en": "Drinking Water Safety", "ar": "سلامة مياه الشرب"},
            "content": {"en": "It's recommended to drink bottled water in Egypt. Tap water is generally not safe for tourists to drink.", "ar": ""},
            "tags": ["health", "safety", "water"],
            "is_featured": True,
            "source": "database",
            "text": "It's recommended to drink bottled water in Egypt. Tap water is generally not safe for tourists to drink.",
            "response": "It's recommended to drink bottled water in Egypt. Tap water is generally not safe for tourists to drink."
        }]

        kb.search_faqs.return_value = [{
            "id": "language",
            "category_id": "general",
            "question": {"en": "What language is spoken in Egypt?", "ar": ""},
            "answer": {"en": "Arabic is the official language of Egypt. English is widely spoken in tourist areas.", "ar": ""},
            "tags": ["language", "communication"],
            "is_featured": True,
            "source": "database",
            "text": "Arabic is the official language of Egypt. English is widely spoken in tourist areas.",
            "response": "Arabic is the official language of Egypt. English is widely spoken in tourist areas."
        }]

        kb.search_events.return_value = [{
            "id": "cairo_food_festival",
            "category_id": "food",
            "name": {"en": "Cairo Food Festival", "ar": ""},
            "description": {"en": "Annual food festival showcasing Egyptian cuisine and international dishes.", "ar": ""},
            "location_description": {"en": "Cairo Exhibition Center", "ar": ""},
            "is_annual": True,
            "tags": ["food", "festival", "cairo"],
            "is_featured": True,
            "source": "database",
            "text": "Annual food festival showcasing Egyptian cuisine and international dishes.",
            "response": "The Cairo Food Festival is an annual food festival showcasing Egyptian cuisine and international dishes."
        }]

        kb.search_itineraries.return_value = [{
            "id": "adventure_egypt",
            "type_id": "adventure",
            "name": {"en": "Egypt Adventure Tour", "ar": ""},
            "description": {"en": "An exciting 10-day adventure tour covering Egypt's most thrilling experiences.", "ar": ""},
            "duration_days": 10,
            "regions": ["sinai", "western_desert", "red_sea"],
            "tags": ["adventure", "hiking", "diving"],
            "is_featured": True,
            "source": "database",
            "text": "An exciting 10-day adventure tour covering Egypt's most thrilling experiences.",
            "response": "The Egypt Adventure Tour is an exciting 10-day adventure tour covering Egypt's most thrilling experiences."
        }]

        return kb

    @pytest.fixture
    def mock_intent_classifier(self):
        """Create a mock intent classifier."""
        # Use a regular MagicMock instead of a spec-based one
        intent_classifier = MagicMock()

        # Define intent classification responses for different queries
        def classify_side_effect(text, **kwargs):
            text = text.lower()
            if "water" in text or "drink" in text:
                return {"intent": "practical_info", "confidence": 0.9}
            elif "language" in text or "speak" in text:
                return {"intent": "faq_query", "confidence": 0.9}
            elif "food" in text or "festival" in text:
                return {"intent": "event_query", "confidence": 0.9}
            elif "itinerary" in text or "adventure" in text:
                return {"intent": "itinerary_query", "confidence": 0.9}
            else:
                return {"intent": "general_query", "confidence": 0.7}

        # Define process method for NLU
        def process_side_effect(text, session_id=None, language=None, context=None, **kwargs):
            text_lower = text.lower()
            if "water" in text_lower or "drink" in text_lower:
                return {"intent": "practical_info", "confidence": 0.9, "text": text, "entities": {}}
            elif "language" in text_lower or "speak" in text_lower:
                return {"intent": "faq_query", "confidence": 0.9, "text": text, "entities": {}}
            elif "food" in text_lower or "festival" in text_lower:
                return {"intent": "event_query", "confidence": 0.9, "text": text, "entities": {}}
            elif "itinerary" in text_lower or "adventure" in text_lower:
                return {"intent": "itinerary_query", "confidence": 0.9, "text": text, "entities": {}}
            else:
                return {"intent": "general_query", "confidence": 0.7, "text": text, "entities": {}}

        intent_classifier.classify.side_effect = classify_side_effect
        intent_classifier.process.side_effect = process_side_effect
        return intent_classifier

    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service."""
        llm_service = MagicMock()
        llm_service.generate_response.return_value = "This is a response from the LLM."
        return llm_service

    @pytest.fixture
    def chatbot(self, mock_knowledge_base, mock_intent_classifier, mock_llm_service):
        """Create a chatbot instance with mocked components."""
        # Create additional required mock components
        mock_dialog_manager = MagicMock()
        mock_dialog_manager.get_suggestions.return_value = []

        mock_response_generator = MagicMock()
        mock_response_generator.generate_response_by_type.return_value = "This is a mock response"

        mock_service_hub = MagicMock()
        mock_service_hub.get_service.return_value = mock_llm_service

        mock_session_manager = MagicMock()
        mock_session_manager.get_session.return_value = {
            "session_id": "test-session-id",
            "language": "en",
            "state": "greeting",
            "history": []
        }

        mock_db_manager = MagicMock()

        # Create chatbot with all required components
        chatbot = Chatbot(
            knowledge_base=mock_knowledge_base,
            nlu_engine=mock_intent_classifier,
            dialog_manager=mock_dialog_manager,
            response_generator=mock_response_generator,
            service_hub=mock_service_hub,
            session_manager=mock_session_manager,
            db_manager=mock_db_manager
        )

        # Set LLM service
        chatbot.llm_service = mock_llm_service

        # Set USE_LLM_FIRST to False to prioritize database queries
        setattr(chatbot, 'USE_LLM_FIRST', False)

        return chatbot

    @pytest.mark.asyncio
    @patch('src.utils.llm_config.use_llm_first', return_value=False)
    async def test_practical_info_query(self, _, chatbot, mock_knowledge_base):
        """Test that practical info queries use the database first."""
        # Process a query about drinking water
        response = await chatbot.process_message("Is it safe to drink tap water in Egypt?")

        # Verify that the knowledge base was queried
        mock_knowledge_base.search_practical_info.assert_called()

        # Verify that the response contains database content
        assert "source" in response
        assert response["source"] == "database"
        assert "bottled water" in response["text"].lower()

    @pytest.mark.asyncio
    @patch('src.utils.llm_config.use_llm_first', return_value=False)
    async def test_faq_query(self, _, chatbot, mock_knowledge_base):
        """Test that FAQ queries use the database first."""
        # Process a query about language
        response = await chatbot.process_message("What language do they speak in Egypt?")

        # Verify that the knowledge base was queried
        mock_knowledge_base.search_faqs.assert_called()

        # Verify that the response contains database content
        assert "source" in response
        assert response["source"] == "database"
        assert "arabic" in response["text"].lower()

    @pytest.mark.asyncio
    @patch('src.utils.llm_config.use_llm_first', return_value=False)
    async def test_event_query(self, _, chatbot, mock_knowledge_base):
        """Test that event queries use the database first."""
        # Process a query about food festivals
        response = await chatbot.process_message("What food festivals are there in Egypt?")

        # Verify that the knowledge base was queried
        mock_knowledge_base.search_events.assert_called()

        # Verify that the response contains database content
        assert "source" in response
        assert response["source"] == "database"
        assert "cairo food festival" in response["text"].lower()

    @pytest.mark.asyncio
    @patch('src.utils.llm_config.use_llm_first', return_value=False)
    async def test_itinerary_query(self, _, chatbot, mock_knowledge_base):
        """Test that itinerary queries use the database first."""
        # Process a query about adventure itineraries
        response = await chatbot.process_message("Can you suggest an adventure itinerary for Egypt?")

        # Verify that the knowledge base was queried
        mock_knowledge_base.search_itineraries.assert_called()

        # Verify that the response contains database content
        assert "source" in response
        assert response["source"] == "database"
        assert "adventure tour" in response["text"].lower()

    @pytest.mark.asyncio
    @patch('src.utils.llm_config.use_llm_first', return_value=False)
    async def test_llm_fallback(self, _, chatbot, mock_knowledge_base, mock_llm_service):
        """Test that the LLM is used as a fallback when the database has no results."""
        # Make the knowledge base return empty results
        mock_knowledge_base.search_practical_info.return_value = []
        mock_knowledge_base.search_faqs.return_value = []
        mock_knowledge_base.search_events.return_value = []
        mock_knowledge_base.search_itineraries.return_value = []

        # Process a query
        response = await chatbot.process_message("Is it safe to drink tap water in Egypt?")

        # Verify that the LLM was used as a fallback
        mock_llm_service.generate_response.assert_called()

        # Verify that the response contains LLM content
        assert "source" in response
        assert response["source"] in ["anthropic_llm", "anthropic_llm_fallback", "knowledge_base"]
