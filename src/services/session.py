"""
Session Management Service (DEPRECATED)

This module provides a service for managing user sessions using Redis as a backend.
It handles session creation, validation, and invalidation.

DEPRECATED: This module is deprecated and will be removed in a future version.
Use the unified session management approach with src/session/redis_manager.py instead.
"""
import json
import secrets
import time
from typing import Any, Dict, Optional, Union

from fastapi import Response
from redis.asyncio import Redis
from starlette.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED

from src.config_unified import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SessionService:
    """
    Service for managing user sessions with Redis.

    DEPRECATED: This class is deprecated and will be removed in a future version.
    Use the unified session management approach with RedisSessionManager instead.
    """

    def __init__(self, redis_client: Redis):
        """
        Initialize the session service.

        Args:
            redis_client: Async Redis client instance
        """
        import warnings
        warnings.warn(
            "SessionService is deprecated and will be removed in a future version. "
            "Use the unified session management approach with RedisSessionManager instead.",
            DeprecationWarning,
            stacklevel=2
        )

        self.redis = redis_client
        self.token_length = 32
        self.session_prefix = "session:"
        self.session_ttl = settings.SESSION_TTL_SECONDS
        # Redis URI for delayed connection in lifespan
        self.redis_uri = None

    async def ensure_redis_client(self):
        """
        Ensure that a valid Redis client exists.

        This method is useful for cases where the initial Redis client was a mock
        and needs to be replaced with a real client.

        Returns:
            bool: True if valid Redis client exists
        """
        if self.redis is None and self.redis_uri:
            try:
                from redis.asyncio import Redis
                self.redis = await Redis.from_url(
                    self.redis_uri,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3
                )
                return True
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                return False
        return self.redis is not None

    def _generate_token(self) -> str:
        """
        Generate a secure random token for session identification.

        Returns:
            A random session token
        """
        return secrets.token_hex(self.token_length)

    def _get_session_key(self, token: str) -> str:
        """
        Get the Redis key for a session token.

        Args:
            token: Session token

        Returns:
            Redis key for the session
        """
        return f"{self.session_prefix}{token}"

    async def create_session(
        self,
        user_data: Dict[str, Any],
        response: Optional[Response] = None,
        ttl: Optional[int] = None,
    ) -> str:
        """
        Create a new session for a user.

        Args:
            user_data: User data to store in the session
            response: Optional response object for setting cookie
            ttl: Optional TTL override for the session

        Returns:
            Session token
        """
        # Ensure Redis client exists
        if not await self.ensure_redis_client():
            logger.error("No Redis client available for session creation")
            return None

        # Generate a secure session token
        token = self._generate_token()
        session_key = self._get_session_key(token)

        # Add timestamp to the session data
        session_data = user_data.copy()
        session_data["created_at"] = int(time.time())

        # Store the session data in Redis
        try:
            session_ttl = ttl or self.session_ttl
            await self.redis.setex(
                session_key,
                session_ttl,
                json.dumps(session_data)
            )

            # If a response object is provided, set the session cookie
            if response:
                response.set_cookie(
                    key="session_token",
                    value=token,
                    max_age=session_ttl,
                    httponly=True,
                    secure=settings.COOKIE_SECURE,
                    samesite="lax"
                )

            logger.info(f"Created session for user {user_data.get('user_id')}")
            return token
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return None

    async def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session token and return the associated user data.

        Args:
            token: Session token to validate

        Returns:
            User data associated with the token, or None if invalid
        """
        if not token:
            return None

        # Ensure Redis client exists
        if not await self.ensure_redis_client():
            logger.error("No Redis client available for session validation")
            return None

        session_key = self._get_session_key(token)

        # Get the session data from Redis
        try:
            session_data_str = await self.redis.get(session_key)
            if not session_data_str:
                logger.warning(f"Invalid session token: {token[:10]}...")
                return None

            # Parse the session data
            session_data = json.loads(session_data_str)

            # Update the TTL to extend the session
            await self.redis.expire(session_key, self.session_ttl)

            return session_data
        except Exception as e:
            logger.error(f"Error validating session: {str(e)}")
            return None

    async def invalidate_session(
        self,
        token: str,
        response: Optional[Response] = None
    ) -> bool:
        """
        Invalidate a session token.

        Args:
            token: Session token to invalidate
            response: Optional response object for clearing cookie

        Returns:
            True if the session was invalidated, False otherwise
        """
        if not token:
            return False

        # Ensure Redis client exists
        if not await self.ensure_redis_client():
            logger.error("No Redis client available for session invalidation")
            return False

        session_key = self._get_session_key(token)

        # Delete the session from Redis
        try:
            result = await self.redis.delete(session_key)

            # If a response object is provided, clear the session cookie
            if response:
                response.delete_cookie(
                    key="session_token",
                    httponly=True,
                    secure=settings.COOKIE_SECURE,
                    samesite="lax"
                )

            return result > 0
        except Exception as e:
            logger.error(f"Error invalidating session: {str(e)}")
            return False

    async def get_unauthorized_response(self, detail: str = "Authentication required") -> JSONResponse:
        """
        Get a standardized unauthorized response.

        Args:
            detail: Error detail message

        Returns:
            JSON response with 401 status code
        """
        return JSONResponse(
            status_code=HTTP_401_UNAUTHORIZED,
            content={"detail": detail}
        )