"""
Session Management Module for FastAPI (DEPRECATED)

This module provides Redis-backed session management for the FastAPI application.

DEPRECATED: This module is deprecated and will be removed in a future version.
Use the unified session management approach with src/session/redis_manager.py instead.
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

import redis
from fastapi import Request, Response, Depends
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from src.config_unified import settings

# Initialize Redis connection
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password,
    decode_responses=True
)

class SessionManager:
    """
    Session management class that handles creating, retrieving, and managing sessions
    using Redis as the backend storage.

    DEPRECATED: This class is deprecated and will be removed in a future version.
    Use the unified session management approach with RedisSessionManager instead.
    """

    def __init__(self, cookie_name: str = settings.SESSION_COOKIE_NAME,
                 expiry_seconds: int = settings.SESSION_EXPIRY):
        import warnings
        warnings.warn(
            "SessionManager is deprecated and will be removed in a future version. "
            "Use the unified session management approach with RedisSessionManager instead.",
            DeprecationWarning,
            stacklevel=2
        )

        self.cookie_name = cookie_name
        self.expiry_seconds = expiry_seconds
        self.redis = redis_client

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())

    def create_session(self, data: Dict[str, Any] = None) -> str:
        """
        Create a new session with optional initial data.

        Args:
            data: Optional dictionary of data to store in the session

        Returns:
            str: New session ID
        """
        session_id = self._generate_session_id()
        session_data = data or {}
        session_data["created_at"] = datetime.now().isoformat()
        session_data["last_accessed"] = datetime.now().isoformat()

        self.redis.setex(
            f"session:{session_id}",
            self.expiry_seconds,
            json.dumps(session_data)
        )
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data for the given session ID.

        Args:
            session_id: The session ID to retrieve

        Returns:
            Optional[Dict[str, Any]]: Session data if found, None otherwise
        """
        session_data = self.redis.get(f"session:{session_id}")
        if not session_data:
            return None

        data = json.loads(session_data)
        data["last_accessed"] = datetime.now().isoformat()

        # Refresh expiry
        self.redis.setex(
            f"session:{session_id}",
            self.expiry_seconds,
            json.dumps(data)
        )

        return data

    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update session data for the given session ID.

        Args:
            session_id: The session ID to update
            data: New data to merge with existing session data

        Returns:
            bool: True if session was updated, False if session not found
        """
        current_data = self.get_session(session_id)
        if not current_data:
            return False

        # Merge new data with existing data
        current_data.update(data)
        current_data["last_accessed"] = datetime.now().isoformat()

        self.redis.setex(
            f"session:{session_id}",
            self.expiry_seconds,
            json.dumps(current_data)
        )
        return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session by ID.

        Args:
            session_id: The session ID to delete

        Returns:
            bool: True if session was deleted, False if session not found
        """
        if not self.redis.exists(f"session:{session_id}"):
            return False

        self.redis.delete(f"session:{session_id}")
        return True

    def set_session_cookie(self, response: Response, session_id: str) -> None:
        """
        Set a session cookie in the response.

        Args:
            response: The FastAPI Response object
            session_id: The session ID to set in the cookie
        """
        response.set_cookie(
            key=self.cookie_name,
            value=session_id,
            httponly=True,
            max_age=self.expiry_seconds,
            expires=int((datetime.now() + timedelta(seconds=self.expiry_seconds)).timestamp()),
            secure=not settings.DEBUG,  # Secure in production only
            samesite="lax"
        )

    def delete_session_cookie(self, response: Response) -> None:
        """
        Delete the session cookie in the response.

        Args:
            response: The FastAPI Response object
        """
        response.delete_cookie(
            key=self.cookie_name,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax"
        )


# Create singleton instance
session_manager = SessionManager()


class SessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to manage sessions in FastAPI requests.

    This middleware automatically extracts the session ID from cookies,
    loads the session data, and provides it in the request state.

    DEPRECATED: This class is deprecated and will be removed in a future version.
    Use the unified session management approach with RedisSessionManager instead.
    """

    def __init__(self, app):
        import warnings
        warnings.warn(
            "SessionMiddleware is deprecated and will be removed in a future version. "
            "Use the unified session management approach with RedisSessionManager instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """
        Process the request through the middleware.

        Args:
            request: The FastAPI Request object
            call_next: The next handler in the middleware chain
        """
        # Set the session manager in the request state
        request.state.session_manager = session_manager

        # Check for existing session cookie
        session_id = request.cookies.get(session_manager.cookie_name)
        session_data = None

        if session_id:
            # Load session data if session exists
            session_data = session_manager.get_session(session_id)

        # If no session or it's invalid, create a new one
        if not session_data:
            session_id = session_manager.create_session()

        # Store the session information in the request state
        request.state.session_id = session_id
        request.state.session = session_data or {}

        # Process the request
        response = await call_next(request)

        # Set the session cookie in the response
        session_manager.set_session_cookie(response, session_id)

        return response


# Dependency for requiring an authenticated session
async def get_session(request: Request) -> Dict[str, Any]:
    """
    Dependency that retrieves the current session.

    Args:
        request: The FastAPI Request object

    Returns:
        Dict[str, Any]: The current session data

    DEPRECATED: This function is deprecated and will be removed in a future version.
    Use the unified session management approach with RedisSessionManager instead.
    """
    import warnings
    warnings.warn(
        "get_session dependency is deprecated and will be removed in a future version. "
        "Use the unified session management approach with RedisSessionManager instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return request.state.session


# Security scheme for swagger docs
security = HTTPBearer(auto_error=False)