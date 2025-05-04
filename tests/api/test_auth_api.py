"""
Tests for the Authentication API endpoints.

These tests verify that the authentication API endpoints work correctly
with the new lightweight session-based authentication.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from src.api.auth import router as auth_router
from src.utils.auth import SessionAuth


@pytest.fixture
def mock_session_auth():
    """Create a mock SessionAuth instance."""
    mock_auth = MagicMock(spec=SessionAuth)

    # Configure create_anonymous_session to return a valid result
    mock_auth.create_anonymous_session.return_value = {
        "success": True,
        "session_id": "test-session-123",
        "token": "test-token-123",
        "token_type": "bearer",
        "expires_in": 86400  # 24 hours
    }

    # Configure validate_session to return valid session data
    mock_auth.validate_session.return_value = {
        "session_id": "test-session-123",
        "created_at": "2023-01-01T00:00:00Z",
        "last_accessed": "2023-01-01T01:00:00Z",
        "type": "anonymous"
    }

    # Configure refresh_session to return a valid result
    mock_auth.refresh_session.return_value = {
        "success": True,
        "session_id": "test-session-123",
        "token": "test-token-456",
        "token_type": "bearer",
        "expires_in": 86400  # 24 hours
    }

    # Configure end_session to return True
    mock_auth.end_session.return_value = True

    return mock_auth


@pytest.fixture
def test_client(mock_session_auth):
    """Create a test client with the auth router."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(auth_router)

    # Override the get_session_auth dependency
    app.dependency_overrides = {
        # Import inside the function to avoid circular imports
        __import__("src.utils.dependencies").utils.dependencies.get_session_auth: lambda: mock_session_auth
    }

    return TestClient(app)


def test_create_session(test_client, mock_session_auth):
    """Test creating an anonymous session."""
    # Make request to create a session
    response = test_client.post(
        "/api/v1/auth/session",
        json={"metadata": {"test": "data"}}
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-123"
    assert data["token"] == "test-token-123"
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 86400

    # Verify session cookie was set
    assert "session_token" in response.cookies
    assert response.cookies["session_token"] == "test-token-123"

    # Verify mock was called with correct arguments
    mock_session_auth.create_anonymous_session.assert_called_once()
    call_args = mock_session_auth.create_anonymous_session.call_args[0][0]
    assert "test" in call_args
    assert call_args["test"] == "data"


def test_create_session_with_remember_me(test_client, mock_session_auth):
    """Test creating an anonymous session with remember_me flag."""
    # Make request to create a session with remember_me=True
    response = test_client.post(
        "/api/v1/auth/session",
        json={"metadata": {"test": "data"}, "remember_me": True}
    )

    # Verify response
    assert response.status_code == 200

    # Verify session cookie was set with longer expiry
    assert "session_token" in response.cookies
    assert response.cookies["session_token"] == "test-token-123"

    # Check cookie max-age (should be 30 days)
    cookie_header = response.headers.get("set-cookie")
    assert "Max-Age=2592000" in cookie_header  # 30 days in seconds


def test_validate_session(test_client, mock_session_auth):
    """Test validating a session token."""
    # Make request to validate a session
    response = test_client.post(
        "/api/v1/auth/validate-session",
        headers={"Cookie": "session_token=test-token-123"}
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["session_id"] == "test-session-123"
    assert data["created_at"] == "2023-01-01T00:00:00Z"
    assert data["last_accessed"] == "2023-01-01T01:00:00Z"

    # Verify mock was called with correct arguments
    mock_session_auth.validate_session.assert_called_once_with("test-token-123")


def test_validate_session_no_token(test_client, mock_session_auth):
    """Test validating a session with no token."""
    # Make request to validate a session without a token
    response = test_client.post("/api/v1/auth/validate-session")

    # Verify response
    assert response.status_code == 401
    assert response.json()["detail"] == "No session token provided"

    # Verify mock was not called
    mock_session_auth.validate_session.assert_not_called()


def test_validate_session_invalid_token(test_client, mock_session_auth):
    """Test validating an invalid session token."""
    # Configure mock to return None for invalid token
    mock_session_auth.validate_session.return_value = None

    # Make request to validate a session with invalid token
    response = test_client.post(
        "/api/v1/auth/validate-session",
        headers={"Cookie": "session_token=invalid-token"}
    )

    # Verify response
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid session token"

    # Verify mock was called with correct arguments
    mock_session_auth.validate_session.assert_called_once_with("invalid-token")


def test_refresh_session(test_client, mock_session_auth):
    """Test refreshing a session token."""
    # Make request to refresh a session
    response = test_client.post(
        "/api/v1/auth/refresh-session",
        headers={"Cookie": "session_token=test-token-123"}
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-123"
    assert data["token"] == "test-token-456"  # New token
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 86400

    # Verify session cookie was updated
    assert "session_token" in response.cookies
    assert response.cookies["session_token"] == "test-token-456"

    # Verify mock was called with correct arguments
    mock_session_auth.refresh_session.assert_called_once_with("test-token-123")


def test_end_session(test_client, mock_session_auth):
    """Test ending a session."""
    # Make request to end a session
    response = test_client.post(
        "/api/v1/auth/end-session",
        headers={"Cookie": "session_token=test-token-123"}
    )

    # Verify response
    assert response.status_code == 200
    assert response.json()["message"] == "Session ended successfully"

    # Verify session cookie was cleared - check the Set-Cookie header
    # TestClient doesn't properly handle cookie deletion in the cookies attribute
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "session_token=" in set_cookie_header
    assert "Max-Age=0" in set_cookie_header or "expires=" in set_cookie_header

    # Verify mock was called with correct arguments
    mock_session_auth.end_session.assert_called_once_with("test-token-123")


def test_end_session_no_token(test_client, mock_session_auth):
    """Test ending a session with no token."""
    # Make request to end a session without a token
    response = test_client.post("/api/v1/auth/end-session")

    # Verify response
    assert response.status_code == 200
    assert response.json()["message"] == "Session ended successfully"

    # Verify mock was not called
    mock_session_auth.end_session.assert_not_called()
