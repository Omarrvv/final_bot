"""
Integration tests for the Egypt Tourism Chatbot.
"""
import os
import sys
import json
import pytest
import requests
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid

# Import test framework
from tests.test_framework import BaseTestCase, ChatbotTestMixin, test_client

# Import components to test
from src.chatbot import Chatbot
from src.nlu.engine import NLUEngine
from src.knowledge.knowledge_base import KnowledgeBase
from src.dialog.manager import DialogManager
from src.response.generator import ResponseGenerator
from src.integration.service_hub import ServiceHub
from src.utils.session import SessionManager
from src.knowledge.database import DatabaseManager
from src.utils.factory import component_factory
from src.utils.container import container

class TestChatbotIntegration(BaseTestCase, ChatbotTestMixin):
    """Integration tests for the chatbot components."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Initialize components using the factory
        # This ensures all dependencies are wired correctly
        try:
            component_factory.initialize()
            self.chatbot = container.get("chatbot")
        except Exception as e:
            # Fail setup if components don't initialize
            pytest.fail(f"Failed to initialize chatbot components during test setup: {e}")

        # Create DB Manager separately IF needed for direct assertions (usually not)
        # self.db_manager = container.get("database_manager") 
        
        # Use lightweight models config for testing
        # Environment variables are now set by factory/container, remove direct setting here?
        # os.environ["MODELS_CONFIG"] = os.path.join(self.temp_dir, "configs", "models.json")
        # os.environ["FLOWS_CONFIG"] = os.path.join(self.temp_dir, "configs", "dialog_flows.json")
        # os.environ["SERVICES_CONFIG"] = os.path.join(self.temp_dir, "configs", "services.json")
        
        # Patch heavyweight components (Still might be needed if factory doesn't mock them)
        self.patches = []
        
        # Patch spaCy models
        spacy_patch = patch('spacy.load')
        mock_spacy = spacy_patch.start()
        mock_nlp = MagicMock()
        mock_nlp.return_value.ents = []
        mock_spacy.return_value = mock_nlp
        self.patches.append(spacy_patch)
        
        # Patch transformer models
        tokenizer_patch = patch('transformers.AutoTokenizer.from_pretrained')
        model_patch = patch('transformers.AutoModel.from_pretrained')
        mock_tokenizer = tokenizer_patch.start()
        mock_model = model_patch.start()
        mock_tokenizer.return_value = MagicMock()
        mock_model.return_value = MagicMock()
        self.patches.append(tokenizer_patch)
        self.patches.append(model_patch)
        
        # Patch fasttext
        fasttext_patch = patch('fasttext.load_model')
        mock_fasttext = fasttext_patch.start()
        mock_fasttext.return_value = MagicMock()
        mock_fasttext.return_value.predict.return_value = (["__label__en"], [0.99])
        self.patches.append(fasttext_patch)
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop all patches
        for p in self.patches:
            p.stop()
        
        # Clean up environment variables (Maybe not needed if factory handles context?)
        # ...
        
        super().tearDown()
    
    def test_basic_conversation_flow(self):
        """Test a basic conversation flow through all components."""
        # Chatbot instance is now available as self.chatbot from setUp
        # chatbot = Chatbot()
        
        # Start a new session
        session_id = self.chatbot.session_manager.create_session()
        
        # First message - greeting
        greeting_response = self.chatbot.process_message(
            user_message="Hello",
            session_id=session_id,
            language="en"
        )
        
        # Verify greeting response
        self.assertIsNotNone(greeting_response)
        self.assertIn("text", greeting_response)
        self.assertIn("session_id", greeting_response)
        self.assertEqual(greeting_response["session_id"], session_id)
        
        # Get updated context
        context = self.chatbot.session_manager.get_context(session_id)
        
        # Verify context was updated
        self.assertIn("dialog_state", context)
        
        # Second message - attraction query
        attraction_response = self.chatbot.process_message(
            user_message="Tell me about the Egyptian Museum",
            session_id=session_id,
            language="en"
        )
        
        # Verify attraction response
        self.assertIsNotNone(attraction_response)
        self.assertIn("text", attraction_response)
        
        # Get updated context again
        context = self.chatbot.session_manager.get_context(session_id)
        
        # Verify entities were captured
        self.assertIn("entities", context)
    
    def test_multilingual_support(self):
        """Test handling of multiple languages."""
        # Use self.chatbot from setUp
        # chatbot = Chatbot()
        session_id = self.chatbot.session_manager.create_session()
        english_response = self.chatbot.process_message(
            user_message="Hello",
            session_id=session_id,
            language="en"
        )
        arabic_response = self.chatbot.process_message(
            user_message="مرحبا",
            session_id=session_id,
            language="ar"
        )
        
        # Verify both responses worked
        self.assertIsNotNone(english_response)
        self.assertIsNotNone(arabic_response)
        
        # Verify language detection works
        auto_detect_response = self.chatbot.process_message(
            user_message="مرحبا",
            session_id=session_id,
            language=None  # Auto-detect
        )
        
        self.assertIsNotNone(auto_detect_response)
    
    def test_context_preservation(self):
        """Test that context is preserved across turns."""
        # Use self.chatbot from setUp
        # chatbot = Chatbot()
        session_id = self.chatbot.session_manager.create_session()
        self.chatbot.process_message(
            user_message="Tell me about the Egyptian Museum",
            session_id=session_id,
            language="en"
        )
        context = self.chatbot.session_manager.get_context(session_id)
        self.chatbot.process_message(
            user_message="What are the opening hours?",
            session_id=session_id,
            language="en"
        )
        updated_context = self.chatbot.session_manager.get_context(session_id)
        
        # Verify entity is preserved
        self.assertIn("entities", updated_context)
        
        # Check if attraction entity from first message is preserved
        if "attraction" in context.get("entities", {}):
            self.assertIn("attraction", updated_context.get("entities", {}))
    
    def test_service_integration(self):
        """Test integration with external services."""
        # This test might need adjustment as it mocks ServiceHub separately
        # Option 1: Let the factory initialize, then mock the service hub inside self.chatbot
        # Option 2: Use the create_test_chatbot helper (if it uses the factory)
        
        # Let's try getting the chatbot first and mocking its service_hub
        service_hub_mock = MagicMock(spec=ServiceHub)
        
        # Mock the execute_service method
        def mock_execute(*args, **kwargs):
            service = kwargs.get('service') or args[0]
            method = kwargs.get('method') or args[1]
            params = kwargs.get('params') or (args[2] if len(args) > 2 else {})
            if service == "mock_service" and method == "test_method":
                return {"result": "success", "params": params}
            return {"error": "mock service error"}
        
        service_hub_mock.execute_service.side_effect = mock_execute
        
        # Patch the service_hub within the already initialized chatbot instance
        original_service_hub = self.chatbot.service_hub
        self.chatbot.service_hub = service_hub_mock
        
        # Call service directly via _handle_service_calls
        result = self.chatbot._handle_service_calls(
            [{"service": "mock_service", "method": "test_method", "params": {"param1": "test"}}],
            {}
        )
    
        # Verify service call worked
        expected_key = "mock_service.test_method"
        self.assertIn(expected_key, result)
        self.assertEqual(result[expected_key]["result"], "success")
        self.assertEqual(result[expected_key]["params"]["param1"], "test")

        # Restore original service hub (optional, happens on teardown anyway)
        self.chatbot.service_hub = original_service_hub

    def test_error_handling(self):
        """Test error handling in the chatbot."""
        # Use self.chatbot from setUp
        # chatbot = Chatbot()
        
        # Patch NLU engine to raise an error
        original_process = self.chatbot.nlu_engine.process
        self.chatbot.nlu_engine.process = MagicMock(side_effect=Exception("Test error"))
        
        session_id = self.chatbot.session_manager.create_session()
        
        try:
            response = self.chatbot.process_message(
                user_message="Hello",
                session_id=session_id,
                language="en"
            )
            
            # Verify error was handled and a fallback response was generated
            self.assertIsNotNone(response)
            self.assertIn("text", response)
        finally:
            self.chatbot.nlu_engine.process = original_process


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for the FastAPI API endpoints."""
    
    # Remove setup/teardown if not needed for API tests specifically
    # Use the test_client fixture provided by pytest
    
    def test_chat_endpoint(self, test_client):
        """Test the /api/chat endpoint."""
        # Use FastAPI TestClient syntax
        response = test_client.post("/api/chat", json={
            "message": "Hello",
            "session_id": None, 
            "language": "en"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "session_id" in data
        assert data["language"] == "en"

    def test_health_endpoint(self, test_client):
        """Test the /api/health endpoint."""
        response = test_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "FastAPI backend" in data["service"] # Check for FastAPI mention

    def test_session_persistence(self, test_client):
        """Test session persistence across multiple requests."""
        # First request
        response1 = test_client.post("/api/chat", json={
            "message": "Tell me about attractions",
            "language": "en"
        })
        assert response1.status_code == 200
        data1 = response1.json()
        session_id = data1["session_id"]
        assert session_id is not None
        
        # Second request using the same session ID
        response2 = test_client.post("/api/chat", json={
            "message": "Specifically the pyramids",
            "session_id": session_id,
            "language": "en"
        })
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["session_id"] == session_id
        # Add more assertions based on expected context persistence if needed
        
    # Remove CSRF test as CSRF is removed in FastAPI version
    # def test_csrf_token_endpoint(self, test_client):
    #     """Test the /api/csrf-token endpoint."""
    #     response = test_client.get("/api/csrf-token")
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert "csrf_token" in data

    def test_reset_endpoint(self, test_client):
        """Test the /api/reset endpoint."""
        # Optional: Create a session first
        response_chat = test_client.post("/api/chat", json={"message": "test"})
        old_session_id = response_chat.json().get("session_id")
        
        # Reset the session
        response = test_client.post("/api/reset", json={"session_id": old_session_id}) # Pass optional old ID
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "message" in data
        # Ensure a new session ID is returned
        new_session_id = data["session_id"]
        assert new_session_id is not None
        if old_session_id:
             assert new_session_id != old_session_id

    def test_suggestions_endpoint(self, test_client):
        """Test the /api/suggestions endpoint."""
        # Optional: Get a session ID first
        response_chat = test_client.post("/api/chat", json={"message": "hello"})
        session_id = response_chat.json().get("session_id")
        
        # Test suggestions with session ID
        response = test_client.get(f"/api/suggestions?language=en&session_id={session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        # Add assertions about specific suggestions based on state if needed
        
        # Test suggestions without session ID (should give initial suggestions)
        response_no_session = test_client.get("/api/suggestions?language=en")
        assert response_no_session.status_code == 200
        data_no_session = response_no_session.json()
        assert "suggestions" in data_no_session
        assert isinstance(data_no_session["suggestions"], list)
        # Check if initial suggestions are returned

    def test_languages_endpoint(self, test_client):
        """Test the /api/languages endpoint."""
        response = test_client.get("/api/languages")
        assert response.status_code == 200
        data = response.json()
        assert "languages" in data
        assert isinstance(data["languages"], list)
        assert len(data["languages"]) > 0
        assert "code" in data["languages"][0]
        assert "name" in data["languages"][0]
        assert "default" in data

    def test_feedback_endpoint(self, test_client):
        """Test the /api/feedback endpoint."""
        feedback_data = {
            "message_id": str(uuid.uuid4()),
            "rating": 5,
            "comment": "Excellent service!"
        }
        response = test_client.post("/api/feedback", json=feedback_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    # Add tests for analytics endpoints (require auth mocking or setup)
    # Example:
    # def test_analytics_overview_unauthorized(self, test_client):
    #     """Test accessing protected analytics route without token."""
    #     # Note: Endpoint path is /stats/overview, not /api/stats/overview
    #     response = test_client.get("/stats/overview") 
    #     assert response.status_code == 401 # Or 403 depending on exact setup
    #     assert "Not authenticated" in response.text # Or similar FastAPI default
    
    # def test_analytics_overview_authorized(self, test_client):
    #     """Test accessing protected analytics route with a valid token."""
    #     # 1. Generate a valid token (requires user setup or mocking)
    #     #    admin_token = generate_token(user_id="admin_user", extra_claims={"role": "admin"})
    #     # 2. Make request with Authorization header
    #     #    headers = {"Authorization": f"Bearer {admin_token}"}
    #     #    response = test_client.get("/stats/overview", headers=headers)
    #     #    assert response.status_code == 200
    #     #    data = response.json()
    #     #    assert "total_sessions" in data
    #     pass # Placeholder until auth setup for tests is done


if __name__ == "__main__":
    pytest.main()