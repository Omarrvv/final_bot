"""
Tests for the auth utility functions.

These tests verify that the token generation and validation functions work correctly.
"""
import pytest
import jwt
from datetime import datetime, timedelta, timezone

from src.utils.auth import generate_token, validate_token, JWT_SECRET, JWT_ALGORITHM


# We no longer need the auth_service fixture since we're only testing token functions


def test_generate_token():
    """Test that tokens are generated correctly with proper claims."""
    user_id = "test-user-123"
    extra_claims = {"username": "testuser", "role": "user"}

    token = generate_token(user_id, extra_claims)

    # Decode the token to verify its contents
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    assert payload["sub"] == user_id
    assert payload["username"] == "testuser"
    assert payload["role"] == "user"
    assert "iat" in payload
    assert "exp" in payload

    # Verify expiration is set to future
    exp_time = datetime.fromtimestamp(payload["exp"], timezone.utc)
    now = datetime.now(timezone.utc)
    assert exp_time > now


def test_validate_token():
    """Test that valid tokens are properly validated."""
    user_id = "test-user-123"
    extra_claims = {"username": "testuser", "role": "user"}

    token = generate_token(user_id, extra_claims)
    payload = validate_token(token)

    assert payload["sub"] == user_id
    assert payload["username"] == "testuser"
    assert payload["role"] == "user"


def test_validate_token_expired():
    """Test that expired tokens are rejected."""
    user_id = "test-user-123"

    # Create a token that's already expired
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1)
    }

    expired_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    with pytest.raises(Exception) as excinfo:
        validate_token(expired_token)

    assert "expired" in str(excinfo.value).lower()


def test_validate_token_invalid():
    """Test that tampered tokens are rejected."""
    user_id = "test-user-123"
    token = generate_token(user_id)

    # Tamper with the token
    invalid_token = token + "invalid"

    with pytest.raises(Exception) as excinfo:
        validate_token(invalid_token)

    assert "invalid" in str(excinfo.value).lower()


# We've removed the user registration and login tests since we're now using
# anonymous sessions instead of user authentication