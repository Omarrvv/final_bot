"""
Tests for the SessionAuth class.

These tests verify that the SessionAuth class properly handles anonymous sessions,
token generation, validation, and session management.
"""
import pytest
import jwt
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

from src.utils.auth import (
    SessionAuth, 
    generate_anonymous_token, 
    validate_token, 
    JWT_SECRET, 
    JWT_ALGORITHM
)


@pytest.fixture
def session_auth():
    """Create a SessionAuth service with a mocked session manager."""
    mock_session_manager = MagicMock()
    auth = SessionAuth(session_manager=mock_session_manager)
    return auth, mock_session_manager


def test_generate_anonymous_token():
    """Test that anonymous tokens are generated correctly with proper claims."""
    # Test with provided session ID
    session_id = "test-session-123"
    token = generate_anonymous_token(session_id)

    # Decode the token to verify its contents
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    assert payload["sub"] == f"anon_{session_id}"
    assert payload["session_id"] == session_id
    assert payload["type"] == "anonymous"
    assert "iat" in payload
    assert "exp" in payload

    # Verify expiration is set to future
    exp_time = datetime.fromtimestamp(payload["exp"], timezone.utc)
    now = datetime.now(timezone.utc)
    assert exp_time > now

    # Test with auto-generated session ID
    token2 = generate_anonymous_token()
    payload2 = jwt.decode(token2, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    assert payload2["sub"].startswith("anon_")
    assert payload2["session_id"] is not None
    assert payload2["type"] == "anonymous"


def test_create_anonymous_session(session_auth):
    """Test creating an anonymous session."""
    auth, mock_session_manager = session_auth

    # Configure mock
    mock_session_manager.create_session.return_value = "test-session-123"

    # Test with metadata
    metadata = {"user_agent": "test-browser", "ip": "127.0.0.1"}
    result = auth.create_anonymous_session(metadata)

    # Verify session manager was called
    mock_session_manager.create_session.assert_called_once()
    
    # Check the session data passed to session manager
    session_data = mock_session_manager.create_session.call_args[0][0]
    assert session_data["user_agent"] == "test-browser"
    assert session_data["ip"] == "127.0.0.1"
    assert session_data["type"] == "anonymous"
    assert "created_at" in session_data
    assert "last_accessed" in session_data

    # Check result
    assert result["success"] is True
    assert "session_id" in result
    assert "token" in result
    assert result["token_type"] == "bearer"
    assert result["expires_in"] > 0


def test_validate_session_valid_token(session_auth):
    """Test validating a valid session token."""
    auth, mock_session_manager = session_auth

    # Create a session token
    session_id = "test-session-123"
    token = generate_anonymous_token(session_id)

    # Configure mock to return session data
    mock_session_data = {
        "session_id": session_id,
        "type": "anonymous",
        "user_agent": "test-browser",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    mock_session_manager.get_session.return_value = mock_session_data

    # Validate the token
    result = auth.validate_session(token)

    # Verify session manager was called
    mock_session_manager.get_session.assert_called_once_with(session_id)

    # Check result
    assert result == mock_session_data


def test_validate_session_invalid_token(session_auth):
    """Test validating an invalid session token."""
    auth, mock_session_manager = session_auth

    # Test with invalid token
    result = auth.validate_session("invalid-token")

    # Verify session manager was not called
    mock_session_manager.get_session.assert_not_called()

    # Check result
    assert result == {}


def test_validate_session_expired_token(session_auth):
    """Test validating an expired session token."""
    auth, mock_session_manager = session_auth

    # Create an expired token
    session_id = "test-session-123"
    payload = {
        "sub": f"anon_{session_id}",
        "session_id": session_id,
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        "type": "anonymous"
    }
    expired_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Validate the token
    result = auth.validate_session(expired_token)

    # Verify session manager was not called
    mock_session_manager.get_session.assert_not_called()

    # Check result
    assert result == {}


def test_validate_session_no_session_manager(session_auth):
    """Test validating a token when session manager is not available."""
    auth, mock_session_manager = session_auth

    # Create a session token
    session_id = "test-session-123"
    token = generate_anonymous_token(session_id)

    # Configure mock to return None (session not found)
    mock_session_manager.get_session.return_value = None

    # Validate the token
    result = auth.validate_session(token)

    # Verify session manager was called
    mock_session_manager.get_session.assert_called_once_with(session_id)

    # Check result - should return minimal data from token
    assert result["session_id"] == session_id
    assert result["type"] == "anonymous"
    assert "exp" in result


def test_refresh_session(session_auth):
    """Test refreshing a session token."""
    auth, mock_session_manager = session_auth

    # Create a session token
    session_id = "test-session-123"
    token = generate_anonymous_token(session_id)

    # Configure mock to return session data
    mock_session_data = {
        "session_id": session_id,
        "type": "anonymous",
        "user_agent": "test-browser",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    mock_session_manager.get_session.return_value = mock_session_data

    # Refresh the token
    result = auth.refresh_session(token)

    # Verify session manager was called
    mock_session_manager.get_session.assert_called_once_with(session_id)
    mock_session_manager.update_session.assert_called_once()

    # Check result
    assert result["success"] is True
    assert result["session_id"] == session_id
    assert "token" in result
    assert result["token"] != token  # New token should be different


def test_end_session(session_auth):
    """Test ending a session."""
    auth, mock_session_manager = session_auth

    # Create a session token
    session_id = "test-session-123"
    token = generate_anonymous_token(session_id)

    # Configure mock to return success
    mock_session_manager.delete_session.return_value = True

    # End the session
    result = auth.end_session(token)

    # Verify session manager was called
    mock_session_manager.delete_session.assert_called_once_with(session_id)

    # Check result
    assert result is True


def test_end_session_invalid_token(session_auth):
    """Test ending a session with an invalid token."""
    auth, mock_session_manager = session_auth

    # End the session with invalid token
    result = auth.end_session("invalid-token")

    # Verify session manager was not called
    mock_session_manager.delete_session.assert_not_called()

    # Check result
    assert result is False
