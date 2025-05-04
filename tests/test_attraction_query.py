"""
Test file for attraction query processing in the chatbot.
This file tests the fix for the indentation error in the attraction query handler.
"""
import os
import sys
import logging
import pytest
import asyncio
from unittest.mock import MagicMock, patch

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.chatbot import Chatbot
from src.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

@pytest.fixture
def mock_chatbot():
    """Fixture for a mocked Chatbot instance."""
    # Create mock components
    mock_knowledge_base = MagicMock()
    mock_nlu_engine = MagicMock()
    mock_dialog_manager = MagicMock()
    mock_response_generator = MagicMock()
    mock_service_hub = MagicMock()
    mock_session_manager = MagicMock()
    mock_db_manager = MagicMock()

    # Create chatbot with mock components
    chatbot = Chatbot(
        knowledge_base=mock_knowledge_base,
        nlu_engine=mock_nlu_engine,
        dialog_manager=mock_dialog_manager,
        response_generator=mock_response_generator,
        service_hub=mock_service_hub,
        session_manager=mock_session_manager,
        db_manager=mock_db_manager
    )

    return chatbot

@pytest.mark.asyncio
async def test_process_attraction_query_with_known_attraction(mock_chatbot):
    """Test processing a query with a known attraction."""
    # Mock the knowledge base lookup_attraction method
    mock_chatbot.knowledge_base.lookup_attraction.return_value = {
        "name": {"en": "Pyramids of Giza"},
        "description": {"en": "The Pyramids of Giza are ancient Egyptian pyramids."},
        "practical_info": {
            "opening_hours": "8:00 AM - 5:00 PM",
            "ticket_prices": "Adult: 200 EGP, Student: 100 EGP"
        }
    }

    # Process a query about pyramids
    response = await mock_chatbot.process_attraction_query("Tell me about the pyramids", "test_session", "en")

    # Verify the response
    assert response is not None
    assert "Pyramids of Giza" in response["text"]
    assert "ancient Egyptian pyramids" in response["text"]
    assert "Opening Hours" in response["text"]
    assert "Ticket Prices" in response["text"]
    assert response["intent"] == "attraction_info"
    assert response["entities"][0]["value"] == "pyramids"

@pytest.mark.asyncio
async def test_process_attraction_query_with_unknown_attraction(mock_chatbot):
    """Test processing a query with an unknown attraction."""
    # Mock the knowledge base lookup_attraction method to return None
    mock_chatbot.knowledge_base.lookup_attraction.return_value = None

    # Override the attraction name detection to use "lighthouse" instead of defaulting to pyramids
    with patch.object(mock_chatbot, '_detect_language', return_value="en"):
        # Process a query about an unknown attraction
        # We need to explicitly set the attraction_name in the method
        with patch.dict(mock_chatbot.__dict__, {"_attraction_name_override": "lighthouse"}):
            # Patch the common_attractions dictionary to include our test attraction
            with patch.dict('src.chatbot.Chatbot.process_attraction_query.__globals__', {
                'common_attractions': {"lighthouse": "lighthouse"}
            }):
                response = await mock_chatbot.process_attraction_query("Tell me about the lighthouse", "test_session", "en")

    # Verify the response
    assert response is not None
    assert response["intent"] == "attraction_not_found"
    assert "lighthouse" in response["text"]

@pytest.mark.asyncio
async def test_process_attraction_query_with_no_specific_attraction(mock_chatbot):
    """Test processing a query with no specific attraction mentioned."""
    # Process a general query about attractions
    response = await mock_chatbot.process_attraction_query("What attractions can I visit?", "test_session", "en")

    # Verify the response
    assert response is not None
    assert "Popular attractions in Egypt include" in response["text"]
    assert "pyramids" in response["text"].lower()
    assert "sphinx" in response["text"].lower()
    assert response["intent"] == "list_attractions"
    assert "suggestions" in response
    assert len(response["suggestions"]) > 0

@pytest.mark.asyncio
async def test_process_attraction_query_with_no_attraction_fallback(mock_chatbot):
    """Test processing a query with no attraction mentioned and no general attraction keywords."""
    # Mock the knowledge base lookup_attraction method
    mock_chatbot.knowledge_base.lookup_attraction.return_value = {
        "name": {"en": "Pyramids of Giza"},
        "description": {"en": "The Pyramids of Giza are ancient Egyptian pyramids."}
    }

    # Process a query with no attraction mentioned
    response = await mock_chatbot.process_attraction_query("Tell me something interesting", "test_session", "en")

    # Verify the response
    assert response is not None
    assert "Pyramids of Giza" in response["text"]
    assert "ancient Egyptian pyramids" in response["text"]
    assert response["intent"] == "attraction_info"
    assert response["entities"][0]["value"] == "pyramids"

@pytest.mark.asyncio
async def test_process_message_with_attraction_keyword(mock_chatbot):
    """Test the process_message method with an attraction keyword."""
    # Create a coroutine mock for process_attraction_query
    async def mock_process_attraction_query(*args, **kwargs):
        return {
            "text": "Information about the Pyramids of Giza",
            "intent": "attraction_info"
        }

    # Create a coroutine mock for get_or_create_session
    async def mock_get_or_create_session(*args, **kwargs):
        return {"language": "en"}

    # Create a mock for _ensure_response_fields
    def mock_ensure_response_fields(*args, **kwargs):
        return {
            "text": "Information about the Pyramids of Giza",
            "intent": "attraction_info",
            "session_id": "test_session",
            "language": "en"
        }

    # Apply the mocks
    with patch.object(mock_chatbot, 'process_attraction_query', mock_process_attraction_query), \
         patch.object(mock_chatbot, 'get_or_create_session', mock_get_or_create_session), \
         patch.object(mock_chatbot, '_ensure_response_fields', mock_ensure_response_fields), \
         patch.object(mock_chatbot, '_save_session', return_value=None):

        # Process a message with an attraction keyword
        response = await mock_chatbot.process_message("Tell me about the pyramids", "test_session", "en")

    # Verify the response
    assert response is not None
    assert response["text"] == "Information about the Pyramids of Giza"
    assert response["intent"] == "attraction_info"

if __name__ == "__main__":
    # Run the tests directly if this file is executed
    asyncio.run(test_process_attraction_query_with_known_attraction(mock_chatbot()))
    asyncio.run(test_process_attraction_query_with_unknown_attraction(mock_chatbot()))
    asyncio.run(test_process_attraction_query_with_no_specific_attraction(mock_chatbot()))
    asyncio.run(test_process_attraction_query_with_no_attraction_fallback(mock_chatbot()))
    asyncio.run(test_process_message_with_attraction_keyword(mock_chatbot()))
    print("All tests passed!")
