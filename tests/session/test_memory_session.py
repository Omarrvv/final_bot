"""
Tests for the MemorySessionManager class.

These tests verify that the in-memory session manager correctly handles
session creation, retrieval, updating, and deletion.
"""
import pytest
import time
import uuid
from typing import Dict, List, Any, Optional

from src.session.memory_manager import MemorySessionManager


class TestMemorySessionManager:
    """Tests for the MemorySessionManager class."""
    
    @pytest.fixture
    def session_manager(self):
        """Create a memory session manager for testing."""
        return MemorySessionManager(session_ttl=3600)
    
    def test_create_session_no_user(self, session_manager):
        """Test creating a session without a user ID."""
        # Create session
        session_id = session_manager.create_session()
        
        # Verify session was created
        assert session_id is not None
        assert session_id in session_manager.sessions
        
        # Verify session data
        session = session_manager.sessions[session_id]
        assert session["session_id"] == session_id
        assert session["user_id"] is None
        assert session["messages"] == []
        assert session["message_count"] == 0
        assert "created_at" in session
        assert "last_accessed" in session
        assert "metadata" in session
    
    def test_create_session_with_user(self, session_manager):
        """Test creating a session with a user ID."""
        user_id = "test-user-1"
        
        # Create session
        session_id = session_manager.create_session(user_id=user_id)
        
        # Verify session was created
        assert session_id is not None
        assert session_id in session_manager.sessions
        
        # Verify session data
        session = session_manager.sessions[session_id]
        assert session["session_id"] == session_id
        assert session["user_id"] == user_id
        
        # Verify user index was updated
        assert user_id in session_manager.user_sessions
        assert session_id in session_manager.user_sessions[user_id]
    
    def test_create_session_with_metadata(self, session_manager):
        """Test creating a session with metadata."""
        metadata = {"device": "mobile", "language": "en"}
        
        # Create session
        session_id = session_manager.create_session(metadata=metadata)
        
        # Verify session was created with metadata
        session = session_manager.sessions[session_id]
        assert session["metadata"] == metadata
    
    def test_get_session_exists(self, session_manager):
        """Test retrieving an existing session."""
        # Create session
        session_id = session_manager.create_session()
        original_access_time = session_manager.sessions[session_id]["last_accessed"]
        
        # Wait a moment to ensure timestamp changes
        time.sleep(0.01)
        
        # Get session
        session = session_manager.get_session(session_id)
        
        # Verify session data
        assert session is not None
        assert session["session_id"] == session_id
        
        # Verify last accessed time was updated
        assert session["last_accessed"] > original_access_time
    
    def test_get_session_not_exists(self, session_manager):
        """Test retrieving a non-existent session."""
        # Get non-existent session
        session = session_manager.get_session("non-existent-id")
        
        # Verify session is None
        assert session is None
    
    def test_update_session(self, session_manager):
        """Test updating a session."""
        # Create session
        session_id = session_manager.create_session()
        original_access_time = session_manager.sessions[session_id]["last_accessed"]
        
        # Wait a moment to ensure timestamp changes
        time.sleep(0.01)
        
        # Update session
        updates = {"metadata": {"language": "fr"}, "user_id": "updated-user"}
        result = session_manager.update_session(session_id, updates)
        
        # Verify update was successful
        assert result is True
        
        # Verify session was updated
        session = session_manager.sessions[session_id]
        assert session["metadata"] == {"language": "fr"}
        assert session["user_id"] == "updated-user"
        
        # Verify last accessed time was updated
        assert session["last_accessed"] > original_access_time
    
    def test_update_session_not_exists(self, session_manager):
        """Test updating a non-existent session."""
        # Update non-existent session
        result = session_manager.update_session("non-existent-id", {"metadata": {}})
        
        # Verify update failed
        assert result is False
    
    def test_delete_session_no_user(self, session_manager):
        """Test deleting a session without a user ID."""
        # Create session
        session_id = session_manager.create_session()
        
        # Delete session
        result = session_manager.delete_session(session_id)
        
        # Verify deletion was successful
        assert result is True
        assert session_id not in session_manager.sessions
    
    def test_delete_session_with_user(self, session_manager):
        """Test deleting a session with a user ID."""
        user_id = "test-user-1"
        
        # Create session
        session_id = session_manager.create_session(user_id=user_id)
        
        # Delete session
        result = session_manager.delete_session(session_id)
        
        # Verify deletion was successful
        assert result is True
        assert session_id not in session_manager.sessions
        assert session_id not in session_manager.user_sessions[user_id]
    
    def test_delete_session_not_exists(self, session_manager):
        """Test deleting a non-existent session."""
        # Delete non-existent session
        result = session_manager.delete_session("non-existent-id")
        
        # Verify deletion failed
        assert result is False
    
    def test_add_message_to_session(self, session_manager):
        """Test adding a message to a session."""
        # Create session
        session_id = session_manager.create_session()
        
        # Add message
        message = {"role": "user", "content": "Hello"}
        result = session_manager.add_message_to_session(session_id, message)
        
        # Verify message was added
        assert result is True
        session = session_manager.sessions[session_id]
        assert len(session["messages"]) == 1
        assert session["messages"][0]["role"] == "user"
        assert session["messages"][0]["content"] == "Hello"
        assert "timestamp" in session["messages"][0]
        assert session["message_count"] == 1
    
    def test_add_message_session_not_exists(self, session_manager):
        """Test adding a message to a non-existent session."""
        # Add message to non-existent session
        result = session_manager.add_message_to_session("non-existent-id", {"role": "user", "content": "Hello"})
        
        # Verify operation failed
        assert result is False
    
    def test_get_session_messages(self, session_manager):
        """Test retrieving messages from a session."""
        # Create session
        session_id = session_manager.create_session()
        
        # Add messages
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]
        for message in messages:
            session_manager.add_message_to_session(session_id, message)
        
        # Get messages
        retrieved_messages = session_manager.get_session_messages(session_id)
        
        # Verify messages
        assert len(retrieved_messages) == 3
        for i, message in enumerate(messages):
            assert retrieved_messages[i]["role"] == message["role"]
            assert retrieved_messages[i]["content"] == message["content"]
    
    def test_get_session_messages_not_exists(self, session_manager):
        """Test retrieving messages from a non-existent session."""
        # Get messages from non-existent session
        messages = session_manager.get_session_messages("non-existent-id")
        
        # Verify result is None
        assert messages is None
    
    def test_get_user_sessions(self, session_manager):
        """Test retrieving all sessions for a user."""
        user_id = "test-user-1"
        
        # Create multiple sessions for the user
        session_id1 = session_manager.create_session(user_id=user_id)
        session_id2 = session_manager.create_session(user_id=user_id)
        session_id3 = session_manager.create_session(user_id=user_id)
        
        # Also create a session for another user
        other_session = session_manager.create_session(user_id="other-user")
        
        # Get user sessions
        user_sessions = session_manager.get_user_sessions(user_id)
        
        # Verify sessions
        assert len(user_sessions) == 3
        session_ids = [session["session_id"] for session in user_sessions]
        assert session_id1 in session_ids
        assert session_id2 in session_ids
        assert session_id3 in session_ids
        assert other_session not in session_ids
    
    def test_get_user_sessions_no_sessions(self, session_manager):
        """Test retrieving sessions for a user with no sessions."""
        # Get sessions for user with no sessions
        user_sessions = session_manager.get_user_sessions("non-existent-user")
        
        # Verify result is empty list
        assert user_sessions == []
    
    def test_cleanup_expired_sessions(self, session_manager):
        """Test cleaning up expired sessions."""
        # Create a session and manually set it to be old
        session_id = session_manager.create_session()
        session_manager.sessions[session_id]["last_accessed"] = time.time() - (2 * 24 * 60 * 60)  # 2 days old
        
        # Create another session that's current
        current_session_id = session_manager.create_session()
        
        # Clean up sessions older than 1 day
        deleted_count = session_manager.cleanup_expired_sessions(days_old=1)
        
        # Verify only the old session was deleted
        assert deleted_count == 1
        assert session_id not in session_manager.sessions
        assert current_session_id in session_manager.sessions 