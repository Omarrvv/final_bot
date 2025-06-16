"""
Authentication utilities for the Egypt Tourism Chatbot.
Provides JWT token generation, validation, and user authentication.
(Adapted for FastAPI)
"""
import os
import bcrypt
import logging
import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Union
import functools

# FastAPI specific imports
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

# Assuming user model might be defined elsewhere, or using dict for now
# from src.models.user import User # Example if you have a User model

logger = logging.getLogger(__name__)

# --- Password Hashing Utilities ---
def hash_password(password: str) -> tuple:
    """
    Hash a password using bcrypt.

    Args:
        password: The password to hash (string)

    Returns:
        tuple: (hashed_password_hex, salt_hex)
    """
    # Always ensure password is bytes
    if not isinstance(password, str):
        raise TypeError("Password must be a string")

    password_bytes = password.encode('utf-8')

    # Generate salt
    salt = bcrypt.gensalt()

    # Hash the password
    hashed_password = bcrypt.hashpw(password_bytes, salt)

    # Return hex strings for database compatibility
    return hashed_password.hex(), salt.hex()

def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against a stored hash.

    Args:
        password: The password to verify (string)
        stored_hash: The stored hash in hex format

    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        # Validate input types
        if not isinstance(password, str):
            raise TypeError("Password must be a string")
        if not isinstance(stored_hash, str):
            raise TypeError("Stored hash must be a string")

        # Convert password to bytes
        password_bytes = password.encode('utf-8')

        # Convert stored hex value back to bytes
        stored_hash_bytes = bytes.fromhex(stored_hash)

        # Use bcrypt to check password
        return bcrypt.checkpw(password_bytes, stored_hash_bytes)
    except TypeError as e:
        logger.error(f"Password verification type error: {str(e)}")
        return False
    except ValueError as e:
        logger.error(f"Password verification value error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

# --- JWT Configuration ---
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    # Use a default secret for development environments ONLY
    logger.warning("JWT_SECRET environment variable not set! Using default secret for development only.")
    JWT_SECRET = "dev-jwt-secret-not-for-production"

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 24 * 60 * 60  # 24 hours

# --- FastAPI OAuth2 Scheme ---
# The tokenUrl should point to your login endpoint (which we haven't created yet)
# Using a placeholder for now.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login") # Placeholder URL

# --- Token Generation/Validation (Framework Agnostic) ---
def generate_token(user_id: Union[int, str], extra_claims: Dict = None) -> str:
    """
    Generate a JWT token for a user.

    Args:
        user_id: The user ID to include in the token (integer or string)
        extra_claims: Additional claims to include in the token

    Returns:
        str: The generated JWT token
    """
    if extra_claims is None:
        extra_claims = {}

    expire = datetime.now(timezone.utc) + timedelta(seconds=JWT_EXPIRATION_SECONDS)
    payload = {
        "sub": str(user_id), # Standard claim for subject (user ID) - convert to string for JWT
        "iat": datetime.now(timezone.utc), # Standard claim for issued at
        "exp": expire, # Standard claim for expiration
    }
    payload.update(extra_claims) # Add custom claims like role, username

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def generate_anonymous_token(session_id: str = None, refresh_nonce: str = None) -> str:
    """
    Generate a JWT token for an anonymous session.

    Args:
        session_id: Optional session ID to include in the token.
                   If not provided, a new UUID will be generated.
        refresh_nonce: Optional nonce to make refreshed tokens unique.

    Returns:
        str: The generated JWT token
    """
    import uuid

    # Generate a session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    # Set expiration time
    expire = datetime.now(timezone.utc) + timedelta(seconds=JWT_EXPIRATION_SECONDS)

    # Create payload with minimal claims
    payload = {
        "sub": f"anon_{session_id}", # Prefix to identify as anonymous
        "session_id": session_id,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "type": "anonymous" # Identify token type
    }

    # Add refresh nonce if provided to make refreshed tokens unique
    if refresh_nonce:
        payload["nonce"] = refresh_nonce

    # Generate token
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def validate_token(token: str) -> Dict:
    """Validate a JWT token and return its payload."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e: # Catch any other decoding errors
        logger.error(f"Unexpected error validating token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- FastAPI Dependency Functions for Authentication ---
async def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    FastAPI dependency function to validate token and return payload.
    Use this in routes requiring authentication.
    """
    return validate_token(token)

async def get_current_active_user(payload: dict = Depends(get_current_user_payload)) -> dict:
    """
    Get the current active user based on token payload.
    Returns the validated user information from the JWT payload.
    """
    # Example: Fetch user from DB (assuming db_manager is available via Depends or context)
    # user_id = payload.get("sub")
    # db_manager = container.get("database_manager") # Assuming container is accessible
    # user = db_manager.get_user_by_id(user_id)
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")
    # return user # Or a Pydantic User model

    # For now, just return the payload as it contains the essential claims
    # Ensure the payload includes necessary info like user_id and role
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload (missing sub)")

    # You might want to wrap the payload in a Pydantic model here for consistency
    return payload

async def get_current_admin_user(current_user: dict = Depends(get_current_active_user)) -> dict:
    """
    FastAPI dependency function to ensure the user is an admin.
    Relies on the 'role' claim being present in the token payload.
    """
    user_role = current_user.get("role")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted: Requires admin privileges"
        )
    return current_user

# --- Lightweight Session Authentication ---
class SessionAuth:
    """
    Lightweight session-based authentication service.
    Handles anonymous sessions and token generation without requiring user accounts.
    """
    def __init__(self, session_manager=None):
        """
        Initialize SessionAuth service.

        Args:
            session_manager: Optional session manager instance
        """
        self._session_manager = session_manager
        logger.info("Lightweight SessionAuth service initialized")

    @property
    def session_manager(self):
        """Lazy load SessionManager."""
        if not self._session_manager:
            try:
                # PHASE 0C FIX: Use dependency injection instead of direct import to avoid layer violation
                # Get session manager from container to maintain architectural boundaries
                from src.core.container import container
                self._session_manager = container.get("session_manager")
                logger.info("Retrieved session manager from container for SessionAuth")
            except Exception as e:
                logger.error(f"Failed to get session manager from container: {e}", exc_info=True)
                # Fallback: create a basic session manager without enhanced features
                logger.warning("Using basic session fallback due to container unavailability")
                self._session_manager = None  # Will trigger basic auth behavior
        return self._session_manager

    def create_anonymous_session(self, metadata: Dict = None) -> Dict:
        """
        Create an anonymous session with optional metadata.

        Args:
            metadata: Optional dictionary of metadata to store with the session

        Returns:
            Dict: Session information including token and session_id
        """
        import uuid

        # Generate a unique session ID
        session_id = str(uuid.uuid4())

        # Initialize session data
        session_data = metadata or {}
        session_data.update({
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_accessed": datetime.now(timezone.utc).isoformat(),
            "type": "anonymous"
        })

        # Create session in session manager if available
        if hasattr(self, 'session_manager') and self.session_manager:
            try:
                self.session_manager.create_session(session_data)
            except Exception as e:
                logger.warning(f"Failed to create session in session manager: {e}")
                # Continue anyway - we'll use the token-based approach

        # Generate anonymous token
        token = generate_anonymous_token(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "token": token,
            "token_type": "bearer",
            "expires_in": JWT_EXPIRATION_SECONDS
        }

    def validate_session(self, token: str) -> Dict:
        """
        Validate a session token.

        Args:
            token: The session token to validate

        Returns:
            Dict: Session data if valid, empty dict if invalid
        """
        try:
            # Validate the token
            payload = validate_token(token)

            # Check if it's an anonymous token
            if payload.get("type") != "anonymous":
                logger.warning(f"Token is not an anonymous token: {payload.get('type')}")
                return {}

            # Get session ID from payload
            session_id = payload.get("session_id")
            if not session_id:
                logger.warning("Token does not contain session_id")
                return {}

            # Get session data from session manager if available
            if hasattr(self, 'session_manager') and self.session_manager:
                try:
                    session_data = self.session_manager.get_session(session_id)
                    if session_data:
                        return session_data
                except Exception as e:
                    logger.warning(f"Failed to get session from session manager: {e}")

            # If session manager not available or session not found,
            # return minimal session data from token
            return {
                "session_id": session_id,
                "type": "anonymous",
                "exp": payload.get("exp")
            }

        except Exception as e:
            logger.error(f"Error validating session token: {e}", exc_info=True)
            return {}

    def refresh_session(self, token: str) -> Dict:
        """
        Refresh a session token.

        Args:
            token: The current session token

        Returns:
            Dict: New session information including token
        """
        try:
            # Validate the current token
            payload = validate_token(token)

            # Check if it's an anonymous token
            if payload.get("type") != "anonymous":
                logger.warning(f"Token is not an anonymous token: {payload.get('type')}")
                return {"success": False, "error": "Invalid token type"}

            # Get session ID from payload
            session_id = payload.get("session_id")
            if not session_id:
                logger.warning("Token does not contain session_id")
                return {"success": False, "error": "Invalid token"}

            # Generate a refresh nonce to ensure the new token is different
            import uuid
            refresh_nonce = str(uuid.uuid4())

            # Generate a new token with the same session ID but different nonce
            new_token = generate_anonymous_token(session_id, refresh_nonce)

            # Update session in session manager if available
            if hasattr(self, 'session_manager') and self.session_manager:
                try:
                    session_data = self.session_manager.get_session(session_id)
                    if session_data:
                        session_data["last_accessed"] = datetime.now(timezone.utc).isoformat()
                        session_data["refresh_count"] = session_data.get("refresh_count", 0) + 1
                        session_data["last_refresh"] = datetime.now(timezone.utc).isoformat()
                        self.session_manager.update_session(session_id, session_data)
                except Exception as e:
                    logger.warning(f"Failed to update session in session manager: {e}")

            return {
                "success": True,
                "session_id": session_id,
                "token": new_token,
                "token_type": "bearer",
                "expires_in": JWT_EXPIRATION_SECONDS
            }

        except Exception as e:
            logger.error(f"Error refreshing session token: {e}", exc_info=True)
            return {"success": False, "error": "Failed to refresh token"}

    def end_session(self, token: str) -> bool:
        """
        End a session.

        Args:
            token: The session token to end

        Returns:
            bool: True if session was ended successfully, False otherwise
        """
        try:
            # Validate the token
            payload = validate_token(token)

            # Get session ID from payload
            session_id = payload.get("session_id")
            if not session_id:
                logger.warning("Token does not contain session_id")
                return False

            # Delete session from session manager if available
            if hasattr(self, 'session_manager') and self.session_manager:
                try:
                    return self.session_manager.delete_session(session_id)
                except Exception as e:
                    logger.warning(f"Failed to delete session from session manager: {e}")

            # If session manager not available, just return success
            return True

        except Exception as e:
            logger.error(f"Error ending session: {e}", exc_info=True)
            return False
