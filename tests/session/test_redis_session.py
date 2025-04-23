"""
Tests for the RedisSessionManager class.

These tests verify that the Redis-based session manager correctly handles
session creation, retrieval, updating, and deletion.
"""
import pytest
import json
import time
from unittest.mock import MagicMock, patch
from redis.exceptions import RedisError

from src.session.redis_manager import RedisSessionManager


class TestRedisSessionManager:
    """Tests for the RedisSessionManager class."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = MagicMock()
        # Configure basic methods
        mock.get.return_value = None
        mock.setex.return_value = True
        mock.delete.return_value = 1
        mock.sadd.return_value = 1
        mock.srem.return_value = 1
        mock.smembers.return_value = set()
        mock.exists.return_value = 0
        mock.pipeline.return_value = mock
        mock.execute.return_value = [True]
        
        return mock
    
    @pytest.fixture
    def session_manager(self, mock_redis):
        """Create a Redis session manager with mocked Redis client."""
        with patch('redis.from_url', return_value=mock_redis):
            manager = RedisSessionManager(redis_uri="redis://localhost:6379/0", session_ttl=3600)
            # Replace the Redis client with our mock
            manager.redis = mock_redis
            
            # Also patch _update_last_accessed to prevent it from calling redis.get again
            def mock_update_last_accessed(session_id):
                pass
            
            manager._update_last_accessed = mock_update_last_accessed
            return manager, mock_redis
    
    def test_init_connection_error(self, mock_redis):
        """Test initialization with connection error."""
        mock_redis.ping.side_effect = RedisError("Connection refused")
        
        with patch('redis.from_url', return_value=mock_redis):
            with pytest.raises(ConnectionError):
                RedisSessionManager(redis_uri="redis://localhost:6379/0")
    
    def test_create_session_no_user(self, session_manager):
        """Test creating a session without a user ID."""
        manager, mock_redis = session_manager
        
        # Create session
        session_id = manager.create_session()
        
        # Verify session was created
        assert session_id is not None
        
        # Verify Redis was called correctly
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        assert call_args[0] == f"session:{session_id}"
        assert call_args[1] == 3600  # TTL
        
        # Parse the stored session data
        session_data = json.loads(call_args[2])
        assert session_data["session_id"] == session_id
        assert session_data["user_id"] is None
        assert session_data["messages"] == []
        assert session_data["message_count"] == 0
        
        # Verify user index was not updated
        mock_redis.sadd.assert_not_called()
    
    def test_create_session_with_user(self, session_manager):
        """Test creating a session with a user ID."""
        manager, mock_redis = session_manager
        user_id = "test-user-1"
        
        # Configure mock to simulate user index doesn't exist
        mock_redis.exists.return_value = 0
        
        # Create session
        session_id = manager.create_session(user_id=user_id)
        
        # Verify session was created
        assert session_id is not None
        
        # Verify Redis was called correctly
        mock_redis.setex.assert_called_once()
        mock_redis.sadd.assert_called_once_with(f"user:{user_id}:sessions", session_id)
        mock_redis.exists.assert_called_once_with(f"user:{user_id}:sessions")
        mock_redis.expire.assert_called_once()  # Set TTL on user's sessions set
    
    def test_create_session_with_metadata(self, session_manager):
        """Test creating a session with metadata."""
        manager, mock_redis = session_manager
        metadata = {"device": "mobile", "language": "en"}
        
        # Create session
        session_id = manager.create_session(metadata=metadata)
        
        # Verify Redis was called correctly
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        
        # Parse the stored session data
        session_data = json.loads(call_args[2])
        assert session_data["metadata"] == metadata
    
    def test_create_session_redis_error(self, session_manager):
        """Test handling of Redis error during session creation."""
        manager, mock_redis = session_manager
        
        # Configure mock to raise exception
        mock_redis.setex.side_effect = RedisError("Connection error")
        
        # Attempt to create session
        with pytest.raises(RuntimeError):
            manager.create_session()
    
    def test_get_session_exists(self, session_manager):
        """Test retrieving an existing session."""
        manager, mock_redis = session_manager
        
        # Configure mock to return a session
        session_data = {
            "session_id": "test-session-id",
            "created_at": time.time(),
            "last_accessed": time.time(),
            "user_id": "test-user-id",
            "metadata": {"language": "en"},
            "messages": [],
            "message_count": 0
        }
        mock_redis.get.return_value = json.dumps(session_data)
        
        # Get session
        session = manager.get_session("test-session-id")
        
        # Verify session data
        assert session is not None
        assert session["session_id"] == "test-session-id"
        assert session["user_id"] == "test-user-id"
        
        # Verify Redis get was called
        mock_redis.get.assert_called_with("session:test-session-id")
        
        # Verify Redis expire was called to refresh TTL
        mock_redis.expire.assert_called_with("session:test-session-id", 3600)
    
    def test_get_session_not_exists(self, session_manager):
        """Test retrieving a non-existent session."""
        manager, mock_redis = session_manager
        
        # Configure mock to return None
        mock_redis.get.return_value = None
        
        # Get non-existent session
        session = manager.get_session("non-existent-id")
        
        # Verify result is None
        assert session is None
        
        # Verify Redis was called correctly
        mock_redis.get.assert_called_once_with("session:non-existent-id")
    
    def test_get_session_json_error(self, session_manager):
        """Test handling of JSON decoding error."""
        manager, mock_redis = session_manager
        
        # Configure mock to return invalid JSON
        mock_redis.get.return_value = "invalid json"
        
        # Get session with invalid JSON
        session = manager.get_session("test-session-id")
        
        # Verify result is None
        assert session is None
    
    def test_update_session(self, session_manager):
        """Test updating a session."""
        manager, mock_redis = session_manager
        
        # Configure mock to return a session
        session_data = {
            "session_id": "test-session-id",
            "created_at": time.time(),
            "last_accessed": time.time(),
            "user_id": "test-user-id",
            "metadata": {"language": "en"},
            "messages": [],
            "message_count": 0
        }
        mock_redis.get.return_value = json.dumps(session_data)
        
        # Update session
        updates = {"metadata": {"language": "fr"}, "user_id": "updated-user"}
        result = manager.update_session("test-session-id", updates)
        
        # Verify update was successful
        assert result is True
        
        # Verify Redis was called correctly
        mock_redis.get.assert_called_with("session:test-session-id")
        mock_redis.setex.assert_called_once()
        
        # Check that the updated data was stored
        call_args = mock_redis.setex.call_args[0]
        updated_session = json.loads(call_args[2])
        assert updated_session["metadata"] == {"language": "fr"}
        assert updated_session["user_id"] == "updated-user"
    
    def test_update_session_not_exists(self, session_manager):
        """Test updating a non-existent session."""
        manager, mock_redis = session_manager
        
        # Configure mock to return None
        mock_redis.get.return_value = None
        
        # Update non-existent session
        result = manager.update_session("non-existent-id", {"metadata": {}})
        
        # Verify update failed
        assert result is False
    
    def test_delete_session_no_user(self, session_manager):
        """Test deleting a session without a user ID."""
        manager, mock_redis = session_manager
        
        # Configure mock to return a session without user ID
        session_data = {
            "session_id": "test-session-id",
            "created_at": time.time(),
            "last_accessed": time.time(),
            "user_id": None,
            "metadata": {},
            "messages": [],
            "message_count": 0
        }
        mock_redis.get.return_value = json.dumps(session_data)
        
        # Delete session
        result = manager.delete_session("test-session-id")
        
        # Verify deletion was successful
        assert result is True
        
        # Verify Redis was called correctly
        mock_redis.get.assert_called_with("session:test-session-id")
        mock_redis.delete.assert_called_once_with("session:test-session-id")
        mock_redis.srem.assert_not_called()
    
    def test_delete_session_with_user(self, session_manager):
        """Test deleting a session with a user ID."""
        manager, mock_redis = session_manager
        
        # Configure mock to return a session with user ID
        session_data = {
            "session_id": "test-session-id",
            "created_at": time.time(),
            "last_accessed": time.time(),
            "user_id": "test-user-id",
            "metadata": {},
            "messages": [],
            "message_count": 0
        }
        mock_redis.get.return_value = json.dumps(session_data)
        
        # Delete session
        result = manager.delete_session("test-session-id")
        
        # Verify deletion was successful
        assert result is True
        
        # Verify Redis was called correctly
        mock_redis.get.assert_called_with("session:test-session-id")
        mock_redis.delete.assert_called_once_with("session:test-session-id")
        mock_redis.srem.assert_called_once_with("user:test-user-id:sessions", "test-session-id")
    
    def test_delete_session_not_exists(self, session_manager):
        """Test deleting a non-existent session."""
        manager, mock_redis = session_manager
        
        # Configure mock to return None
        mock_redis.get.return_value = None
        
        # Delete non-existent session
        result = manager.delete_session("non-existent-id")
        
        # Verify deletion failed
        assert result is False
        
        # Verify Redis was called correctly
        mock_redis.get.assert_called_once_with("session:non-existent-id")
        mock_redis.delete.assert_not_called()
    
    def test_add_message_to_session(self, session_manager):
        """Test adding a message to a session."""
        manager, mock_redis = session_manager
        
        # Configure mock to return a session
        session_data = {
            "session_id": "test-session-id",
            "created_at": time.time(),
            "last_accessed": time.time(),
            "user_id": "test-user-id",
            "metadata": {},
            "messages": [],
            "message_count": 0
        }
        mock_redis.get.return_value = json.dumps(session_data)
        
        # Add message
        message = {"role": "user", "content": "Hello"}
        result = manager.add_message_to_session("test-session-id", message)
        
        # Verify message was added successfully
        assert result is True
        
        # Verify Redis was called correctly
        mock_redis.get.assert_called_with("session:test-session-id")
        mock_redis.setex.assert_called_once()
        
        # Check that the message was added to session data
        call_args = mock_redis.setex.call_args[0]
        updated_session = json.loads(call_args[2])
        assert len(updated_session["messages"]) == 1
        assert updated_session["messages"][0]["role"] == "user"
        assert updated_session["messages"][0]["content"] == "Hello"
        assert "timestamp" in updated_session["messages"][0]
        assert updated_session["message_count"] == 1
    
    def test_add_message_session_not_exists(self, session_manager):
        """Test adding a message to a non-existent session."""
        manager, mock_redis = session_manager
        
        # Configure mock to return None
        mock_redis.get.return_value = None
        
        # Add message to non-existent session
        result = manager.add_message_to_session("non-existent-id", {"role": "user", "content": "Hello"})
        
        # Verify operation failed
        assert result is False 