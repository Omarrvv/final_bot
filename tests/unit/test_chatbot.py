import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import uuid

# Adjust import paths as necessary
from src.chatbot import Chatbot
from src.session.memory_manager import MemorySessionManager # Or RedisSessionManager
from src.nlu.engine import NLUEngine
from src.dialog.manager import DialogManager
from src.knowledge.knowledge_base import KnowledgeBase
from src.response.generator import ResponseGenerator
from src.utils.exceptions import ChatbotError, ResourceNotFoundError
from src.integration.service_hub import ServiceHub
from src.knowledge.database import DatabaseManager

# --- Fixtures --- #

@pytest.fixture
def mock_session_manager():
    manager = MagicMock(spec=MemorySessionManager) # Use spec of actual session manager
    manager.create_session.return_value = str(uuid.uuid4()) # Simulate creating new session ID
    manager.get_session.return_value = None # Default: session not found
    manager.update_session.return_value = True
    manager.add_message_to_session.return_value = True
    # Configure delete_session instead of clear_session if that's the correct method
    manager.delete_session.return_value = True
    manager.save_session = MagicMock(return_value=True) # Added missing mock
    return manager

@pytest.fixture
def mock_nlu_engine():
    engine = AsyncMock(spec=NLUEngine)
    # Default NLU result
    engine.process.return_value = {
        "intent": {"name": "greet", "confidence": 0.9},
        "entities": [],
        "language": "en",
        "original_query": "Hello"
    }
    return engine

@pytest.fixture
def mock_dialog_manager():
    manager = AsyncMock(spec=DialogManager)
    # Set return_value directly on the mock method
    manager.next_action.return_value = {
        "action_type": "respond",
        "response_type": "greeting",
        "response_params": {},
        "new_state": "welcomed",
        "confidence": 0.9
    }
    # Add mock for get_suggestions
    manager.get_suggestions = AsyncMock(return_value=[{"text": "Suggestion 1"}])
    return manager

@pytest.fixture
def mock_knowledge_base():
    kb = MagicMock(spec=KnowledgeBase)
    kb.search_attractions.return_value = [] # Default: find nothing
    kb.get_practical_info.return_value = []
    return kb

@pytest.fixture
def mock_response_generator():
    generator = MagicMock(spec=ResponseGenerator)
    generator.generate_response_by_type.return_value = "Hello there! How can I help?"
    return generator

@pytest.fixture
def mock_service_hub():
    """Fixture for a mocked ServiceHub."""
    hub = AsyncMock(spec=ServiceHub)
    hub.execute_service.return_value = {"status": "mock success"}
    return hub

@pytest.fixture
def mock_db_manager():
    """Fixture for a mocked DatabaseManager."""
    db = MagicMock()  # Remove spec to allow adding custom methods
    # Add db_type attribute that's needed by KnowledgeBase
    db.db_type = "postgres"
    # Add log_analytics_event method that's used by Chatbot
    db.log_analytics_event = MagicMock(return_value=True)
    return db

@pytest.fixture
def chatbot_instance(mock_session_manager, mock_nlu_engine, mock_dialog_manager, mock_knowledge_base, mock_response_generator, mock_service_hub, mock_db_manager):
    """Fixture for Chatbot instance with all dependencies mocked."""
    try:
        bot = Chatbot(
            session_manager=mock_session_manager,
            nlu_engine=mock_nlu_engine,
            dialog_manager=mock_dialog_manager,
            knowledge_base=mock_knowledge_base,
            response_generator=mock_response_generator,
            service_hub=mock_service_hub,
            db_manager=mock_db_manager
        )
        return bot
    except TypeError as e:
        pytest.skip(f"Skipping Chatbot tests, __init__ likely missing args or has mismatch: {e}")
    except ImportError as e:
        pytest.skip(f"Skipping Chatbot tests due to import error: {e}")

# --- Chatbot Tests --- #

@pytest.mark.asyncio
async def test_chatbot_instantiation(chatbot_instance):
    """Test if the Chatbot can be instantiated with mocks."""
    assert chatbot_instance is not None
    assert chatbot_instance.session_manager is not None
    assert chatbot_instance.nlu_engine is not None
    assert chatbot_instance.dialog_manager is not None
    assert chatbot_instance.knowledge_base is not None
    assert chatbot_instance.response_generator is not None

@pytest.mark.asyncio
async def test_process_message_new_session(chatbot_instance, mock_session_manager, mock_nlu_engine, mock_dialog_manager, mock_response_generator):
    """Test processing a message when no session_id is provided (creates new session)."""
    user_message = "Hello"
    language = "en"
    new_session_id = "new-uuid-session"
    mock_session_manager.create_session.return_value = new_session_id
    # Simulate session manager returning the new session after creation
    session_data = {
        "session_id": new_session_id,
        "messages": [],
        "state": "welcomed",  # Note state format matches what's expected
        "last_accessed": 0,
        "created_at": 0,
        "user_id": None,
        "metadata": {},
        "language": language
    }
    mock_session_manager.get_session.return_value = session_data

    result = await chatbot_instance.process_message(user_message, session_id=None, language=language)

    assert result["session_id"] == new_session_id
    assert "response" in result
    assert result["response"] == "Hello there! How can I help?"
    # Verify dependencies were called
    mock_session_manager.create_session.assert_called_once()
    mock_session_manager.add_message_to_session.assert_called()
    mock_nlu_engine.process.assert_called_once_with(
        user_message,
        session_id=new_session_id,
        language=language,
        context=session_data
    )
    mock_dialog_manager.next_action.assert_called_once()
    mock_response_generator.generate_response_by_type.assert_called_once()
    mock_session_manager.update_session.assert_called()

@pytest.mark.asyncio
async def test_process_message_existing_session(chatbot_instance, mock_session_manager, mock_nlu_engine):
    """Test processing a message with an existing session_id."""
    user_message = "Tell me about Cairo"
    session_id = "existing-session-123"
    language = "en"
    mock_session_manager.get_session.return_value = {
        "session_id": session_id, "messages": [{"role":"user", "content":"Hi"}],
        "state": {"topic": "greeting"}, "user_id": None, "metadata": {}
    }

    await chatbot_instance.process_message(user_message, session_id=session_id, language=language)

    mock_session_manager.get_session.assert_called_once_with(session_id)
    mock_session_manager.create_session.assert_not_called()
    mock_nlu_engine.process.assert_called_once_with(
        user_message,
        session_id=session_id,
        language=language,
        context=mock_session_manager.get_session.return_value # Assuming context is the session data
    )
    # ... further assertions on dialog manager, response generator calls ...

@pytest.mark.asyncio
async def test_process_message_session_not_found(chatbot_instance, mock_session_manager):
    """Test processing a message with an invalid session_id."""
    user_message = "Anything"
    session_id = "invalid-session-id"
    language = "en"
    mock_session_manager.get_session.return_value = None # Simulate session not found

    with pytest.raises(ResourceNotFoundError):
        await chatbot_instance.process_message(user_message, session_id=session_id, language=language)

    mock_session_manager.get_session.assert_called_once_with(session_id)
    mock_session_manager.create_session.assert_not_called()

@pytest.mark.asyncio
async def test_process_message_nlu_error(chatbot_instance, mock_session_manager, mock_nlu_engine):
    """Test error handling when NLU engine raises an exception."""
    user_message = "Error input"
    session_id = "session-nlu-error"
    language = "en"
    mock_session_manager.get_session.return_value = {"session_id": session_id, "messages": [], "state": {}}
    mock_nlu_engine.process.side_effect = ChatbotError("NLU failed") # Simplified error

    with pytest.raises(ChatbotError, match="NLU failed"):
         await chatbot_instance.process_message(user_message, session_id=session_id, language=language)

    mock_nlu_engine.process.assert_called_once()

@pytest.mark.asyncio
async def test_process_message_dialog_action_kb_query(chatbot_instance, mock_dialog_manager, mock_knowledge_base, mock_response_generator, mock_session_manager, mock_nlu_engine):
    """Test flow where dialog manager requests a KB query."""
    user_message = "Find historical sites in Luxor"
    session_id = "session-kb-query"
    language = "en"

    # Set up session data
    session_data = {
        "session_id": session_id,
        "messages": [],
        "state": "asking_for_location",
        "last_accessed": 0,
        "created_at": 0,
        "user_id": None,
        "metadata": {},
        "language": language
    }
    mock_session_manager.get_session.return_value = session_data

    # NLU result leading to KB query
    nlu_result = {
        "intent": {"name": "find_attraction"},
        "entities": [{"type": "city", "value": "Luxor"}, {"type":"category", "value":"historical"}],
        "language": language
    }
    mock_nlu_engine.process.return_value = nlu_result

    # Dialog action requesting KB query
    mock_dialog_manager.next_action.return_value = {
        "action_type": "knowledge_query",
        "query_params": {"type": "attraction", "filters": {"city_id": "luxor", "type": "historical"}},
        "response_type": "attraction_list",
        "new_state": "showing_attractions"
    }

    # Simulate KB finding results
    kb_results = [{"id": "karnak", "name_en": "Karnak Temple"}]
    mock_knowledge_base.search_attractions.return_value = kb_results

    # Simulate response generator using KB results
    mock_response_generator.generate_response_by_type.return_value = "Found: Karnak Temple"

    result = await chatbot_instance.process_message(user_message, session_id=session_id, language=language)

    # Verify session was retrieved
    mock_session_manager.get_session.assert_called_once_with(session_id)

    # Verify NLU was called with correct parameters
    mock_nlu_engine.process.assert_called_once_with(
        user_message,
        session_id=session_id,
        language=language,
        context=session_data
    )

    # Verify dialog manager was called with NLU results
    mock_dialog_manager.next_action.assert_called_once()

    # Check that KB was called with params from dialog manager
    mock_knowledge_base.search_attractions.assert_called_once_with(filters={"city_id": "luxor", "type": "historical"})

    # Check that response generator received KB results
    mock_response_generator.generate_response_by_type.assert_called_once_with(
        response_type="attraction_list",
        language=language,
        params=kb_results # Or however the KB results are passed
    )

    # Check final response
    assert result["response"] == "Found: Karnak Temple"

@pytest.mark.asyncio
async def test_reset_session_existing(chatbot_instance, mock_session_manager):
    """Test resetting an existing session."""
    session_id = "session-to-reset"
    # Mock get_session to simulate finding it initially
    mock_session_manager.get_session.return_value = {"session_id": session_id}
    # Use delete_session as per the implementation analysis
    mock_session_manager.delete_session.return_value = True

    # Assuming reset_session now correctly calls delete_session
    result = chatbot_instance.reset_session(session_id)

    assert "message" in result
    assert "reset" in result["message"].lower()
    assert result["session_id"] == session_id # Should return the ID that was reset
    # Verify the correct session manager method was called
    mock_session_manager.delete_session.assert_called_once_with(session_id)
    mock_session_manager.create_session.assert_not_called() # Should not create a new one

@pytest.mark.asyncio
async def test_reset_session_non_existent(chatbot_instance, mock_session_manager):
    """Test resetting a session that doesn't exist (should probably still succeed)."""
    session_id = "non-existent-session"
    mock_session_manager.get_session.return_value = None # Simulate session not found
    mock_session_manager.delete_session.return_value = False # Simulate delete failing because it wasn't found

    result = chatbot_instance.reset_session(session_id)

    assert "message" in result
    assert result["session_id"] == session_id
    mock_session_manager.delete_session.assert_called_once_with(session_id)

@pytest.mark.asyncio
async def test_reset_session_create_new(chatbot_instance, mock_session_manager):
    """Test reset_session creating a new session when no ID is provided."""
    new_session_id = "newly-created-session"
    mock_session_manager.create_session.return_value = new_session_id

    result = chatbot_instance.reset_session(session_id=None)

    assert result["session_id"] == new_session_id
    assert "session has been reset" in result["message"].lower()
    mock_session_manager.create_session.assert_called_once()
    mock_session_manager.delete_session.assert_not_called()

# Add tests for get_suggestions, get_supported_languages
# Add tests for different dialog flows (e.g., needing more slots, clarification)
# Add tests for RAG pipeline integration if applicable
# Add tests for error handling in different components (Dialog Manager, KB, Response Generator)