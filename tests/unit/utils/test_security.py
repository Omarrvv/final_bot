import pytest
from unittest.mock import patch, MagicMock
import time
import os
from datetime import datetime, timedelta, timezone

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

# Adjust import paths as necessary
# Assume functions like verify_password, get_password_hash, create_access_token, verify_token exist
from src.utils import security

# --- Test Password Hashing --- #

def test_get_password_hash_and_verify():
    """Test hashing a password and verifying it successfully."""
    if not hasattr(security, 'get_password_hash') or not hasattr(security, 'verify_password'):
        pytest.skip("Skipping password tests: hashing/verification functions not found.")

    password = "sEcReTpAsSwOrD"
    hashed_password = security.get_password_hash(password)

    assert hashed_password != password # Ensure it's actually hashed
    assert isinstance(hashed_password, str)
    # Verify the original password matches the hash
    assert security.verify_password(password, hashed_password) is True

def test_verify_password_incorrect():
    """Test verifying an incorrect password against a hash."""
    if not hasattr(security, 'get_password_hash') or not hasattr(security, 'verify_password'):
        pytest.skip("Skipping password tests: hashing/verification functions not found.")

    password = "sEcReTpAsSwOrD"
    wrong_password = "wrongPassword"
    hashed_password = security.get_password_hash(password)

    assert security.verify_password(wrong_password, hashed_password) is False

def test_verify_password_invalid_hash():
    """Test verifying a password against an invalid/malformed hash."""
    if not hasattr(security, 'verify_password'):
        pytest.skip("Skipping password tests: verification function not found.")

    password = "sEcReTpAsSwOrD"
    invalid_hash = "not_a_real_bcrypt_hash"

    # Depending on the underlying library (e.g., passlib), this might
    # raise an exception or return False. Assuming False for robustness.
    try:
        assert security.verify_password(password, invalid_hash) is False
    except ValueError:
        # Some libraries might raise ValueError for malformed hashes
        pass
    except Exception as e:
        # Catch other potential errors if the library behaves differently
        pytest.fail(f"verify_password raised unexpected exception {type(e).__name__} for invalid hash")


# --- Test JWT Token Creation & Verification --- #

# Fixture to manage JWT secret key for tests
@pytest.fixture(autouse=True)
def manage_jwt_secret():
    """Sets a predictable JWT secret for testing via environment variable patching."""
    test_secret = "test-jwt-secret-key-very-secure"
    original_secret = os.environ.get("JWT_SECRET")
    os.environ["JWT_SECRET"] = test_secret
    # Patch security module directly if it reads the secret differently
    with patch.object(security, 'SECRET_KEY', test_secret, create=True): # create=True if it might not exist
         yield test_secret # Provide the secret if needed, but primarily sets it
    # Teardown: Restore original secret or remove test secret
    if original_secret is None:
        del os.environ["JWT_SECRET"]
    else:
        os.environ["JWT_SECRET"] = original_secret

def test_create_access_token():
    """Test creating a JWT access token."""
    if not hasattr(security, 'create_access_token'):
        pytest.skip("Skipping token tests: create_access_token function not found.")

    user_data = {"sub": "user@example.com", "user_id": "user_123", "role": "admin"}
    expires_delta = timedelta(minutes=15)

    token = security.create_access_token(data=user_data.copy(), expires_delta=expires_delta)

    assert isinstance(token, str)
    assert "." in token # Basic check for JWT structure

def test_verify_token_valid(manage_jwt_secret):
    """Test verifying a valid, non-expired token."""
    if not hasattr(security, 'create_access_token') or not hasattr(security, 'verify_token'):
        pytest.skip("Skipping token tests: create/verify functions not found.")

    test_secret = manage_jwt_secret
    user_data = {"sub": "verifier@test.com", "id": 999}
    token = security.create_access_token(data=user_data.copy(), expires_delta=timedelta(minutes=5))

    payload = security.verify_token(token)

    assert payload is not None
    assert payload["sub"] == user_data["sub"]
    assert payload["id"] == user_data["id"]
    assert "exp" in payload

def test_verify_token_expired(manage_jwt_secret):
    """Test verifying a token that has expired."""
    if not hasattr(security, 'create_access_token') or not hasattr(security, 'verify_token'):
        pytest.skip("Skipping token tests: create/verify functions not found.")

    test_secret = manage_jwt_secret
    user_data = {"sub": "expired@test.com"}
    # Create a token that expired 1 second ago
    token = security.create_access_token(data=user_data.copy(), expires_delta=timedelta(seconds=-1))

    with pytest.raises(ExpiredSignatureError):
        security.verify_token(token)

def test_verify_token_invalid_signature(manage_jwt_secret):
    """Test verifying a token with an invalid signature (wrong secret)."""
    if not hasattr(security, 'create_access_token') or not hasattr(security, 'verify_token'):
        pytest.skip("Skipping token tests: create/verify functions not found.")

    test_secret = manage_jwt_secret
    user_data = {"sub": "signer@test.com"}
    # Encode with the correct secret
    token = security.create_access_token(data=user_data.copy())

    # Attempt to verify using the wrong secret by temporarily changing the patch/env var
    wrong_secret = "this-is-the-wrong-secret"
    original_module_secret = getattr(security, 'SECRET_KEY', None)
    try:
        # Patch the secret within the security module for the verification call
        with patch.object(security, 'SECRET_KEY', wrong_secret):
             with pytest.raises(InvalidTokenError): # Usually raises InvalidSignatureError or subclass
                 security.verify_token(token)
    finally:
        # Ensure the original patch/secret is restored
        if original_module_secret is not None:
             setattr(security, 'SECRET_KEY', original_module_secret)

def test_verify_token_malformed(manage_jwt_secret):
    """Test verifying a malformed token string."""
    if not hasattr(security, 'verify_token'):
        pytest.skip("Skipping token tests: verify_token function not found.")

    malformed_token = "this.is.not.a.valid.jwt"

    with pytest.raises(InvalidTokenError):
        security.verify_token(malformed_token)

# Add tests for specific claims if used (e.g., audience, issuer)
# Add tests for algorithm checking if ALGORITHMS constant is used
# Add tests for potential edge cases in expiry calculation 