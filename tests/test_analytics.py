"""
Unit tests for the analytics API module (FastAPI version).
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Import FastAPI TestClient and the app instance from test_framework
from tests.test_framework import test_client # Import the fixture directly
from src.main import app # Import the app for dependency overrides

# Import the DatabaseManager for type hinting mocks
from src.knowledge.database import DatabaseManager
# Import the actual auth dependencies we need to override
import src.utils.auth as auth_utils
import src.api.analytics_api as analytics_api_module

# --- Mocking Setup --- 

# Create a mock DatabaseManager instance globally using autospec=True
mock_db_manager = MagicMock(spec=DatabaseManager, autospec=True)
# Explicitly add get_analytics_events method to the mock
mock_db_manager.get_analytics_events = MagicMock(return_value=[])

# Fixture to automatically reset the mock before each test in the class
@pytest.fixture(autouse=True)
def reset_db_mock_before_each_test():
    mock_db_manager.reset_mock()
    # Ensure get_analytics_events is reset but still available
    mock_db_manager.get_analytics_events.reset_mock()
    mock_db_manager.get_analytics_events.return_value = []
    yield 

# Mock user for authentication override
mock_admin_user = {"user_id": "test_admin", "username": "admin", "role": "admin"}
mock_active_user = {"user_id": "test_user", "username": "user", "role": "user"}
def override_get_current_admin_user(): return mock_admin_user
def override_get_current_active_user(): return mock_active_user

# Apply dependency overrides to the FastAPI app for the duration of these tests
app.dependency_overrides[auth_utils.get_current_admin_user] = override_get_current_admin_user
app.dependency_overrides[auth_utils.get_current_active_user] = override_get_current_active_user

# --- Test Class --- 

class TestAnalyticsAPI:

    def test_get_overview_stats(self, test_client):
        """Test getting overview statistics (FastAPI)."""
        # Patch the helper *within* the test
        with patch.object(analytics_api_module, '_get_db_manager', return_value=mock_db_manager):
            mock_db_manager.get_analytics_events.return_value = [] 
            response = test_client.get('/api/stats/overview')
            
        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data
        mock_db_manager.get_analytics_events.assert_called_once()
        
    def test_get_daily_stats(self, test_client):
        """Test getting daily statistics (FastAPI)."""
        with patch.object(analytics_api_module, '_get_db_manager', return_value=mock_db_manager):
            mock_db_manager.get_analytics_events.return_value = []
            response = test_client.get('/api/stats/daily?days=7')
            
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        mock_db_manager.get_analytics_events.assert_called_once()
        
    def test_get_session_stats(self, test_client):
        """Test getting session statistics (FastAPI)."""
        test_session_id = "session123"
        with patch.object(analytics_api_module, '_get_db_manager', return_value=mock_db_manager):
            # Set return value *inside* the patch context if needed for multiple calls
            mock_db_manager.get_analytics_events.return_value = [
                 {"timestamp": datetime.now().isoformat(), "event_type": "user_interaction", "session_id": test_session_id}
            ] 
            response = test_client.get(f'/api/stats/session/{test_session_id}')
        
        # Assert based on observed behavior (500 due to test client handling of 404)
        # assert response.status_code == 500 
        # Correcting assertion back to 200 as the 500 only occurs on empty event list
        assert response.status_code == 200
        data = response.json() # Now we can check data again
        assert data["session_id"] == test_session_id 
        mock_db_manager.get_analytics_events.assert_called_once_with(filters={"session_id": test_session_id}, limit=1000)
        
    def test_get_session_stats_not_found(self, test_client):
        """Test getting session statistics for non-existent session."""
        with patch.object(analytics_api_module, '_get_db_manager', return_value=mock_db_manager):
            mock_db_manager.get_analytics_events.return_value = []
            response = test_client.get('/api/stats/session/nonexistent')
            
        assert response.status_code == 404 # Changed to 404 not found
        mock_db_manager.get_analytics_events.assert_called_once()
        
    def test_get_intent_distribution(self, test_client):
        """Test getting intent distribution (FastAPI)."""
        with patch.object(analytics_api_module, '_get_db_manager', return_value=mock_db_manager):
            mock_db_manager.get_analytics_events.return_value = [
                {"event_type": "user_interaction", "event_data": {"intent": "greeting"}},
                {"event_type": "user_interaction", "event_data": {"intent": "attraction_info"}},
                {"event_type": "user_interaction", "event_data": {"intent": "greeting"}},
            ]
            response = test_client.get('/api/stats/intents')
        
        assert response.status_code == 200
        data = response.json()
        # Updated to expect a dictionary with 'intents' field
        assert "intents" in data
        assert isinstance(data["intents"], list)
        # Correcting assertion based on mock data provided
        assert len(data["intents"]) == 2 
        assert data["intents"][0]["intent"] == "greeting" 
        assert data["intents"][0]["count"] == 2
        mock_db_manager.get_analytics_events.assert_called_once()
        
    def test_get_entity_distribution(self, test_client):
        """Test getting entity distribution (FastAPI)."""
        with patch.object(analytics_api_module, '_get_db_manager', return_value=mock_db_manager):
            mock_db_manager.get_analytics_events.return_value = []
            response = test_client.get('/api/stats/entities') 
        
        assert response.status_code == 200
        data = response.json()
        # Updated to expect a dictionary with 'entities' field
        assert "entities" in data
        assert isinstance(data["entities"], list)
        assert "total_entities" in data
        mock_db_manager.get_analytics_events.assert_called_once()
        
    def test_get_feedback_stats(self, test_client):
        """Test getting feedback statistics (FastAPI)."""
        with patch.object(analytics_api_module, '_get_db_manager', return_value=mock_db_manager):
            mock_db_manager.get_analytics_events.return_value = []
            response = test_client.get('/api/stats/feedback') 
        
        assert response.status_code == 200
        data = response.json()
        assert "total_feedback" in data
        mock_db_manager.get_analytics_events.assert_called_once()
        
    def test_get_message_stats(self, test_client):
        """Test getting message statistics (FastAPI)."""
        with patch.object(analytics_api_module, '_get_db_manager', return_value=mock_db_manager):
            mock_db_manager.get_analytics_events.return_value = []
            response = test_client.get('/api/stats/messages?limit=10&offset=0')
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        mock_db_manager.get_analytics_events.assert_called_once()

# --- Cleanup dependency overrides after tests in this module run --- 
def teardown_module(module):
    """ Remove dependency overrides after tests complete."""
    app.dependency_overrides.pop(auth_utils.get_current_admin_user, None)
    app.dependency_overrides.pop(auth_utils.get_current_active_user, None)