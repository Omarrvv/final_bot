"""
Redis-based session manager for persistent session storage.
Stores sessions in Redis with configurable TTL.
"""

import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

class RedisSessionManager:
    """Session manager that stores sessions in Redis"""

    def __init__(self, redis_uri: str, session_ttl: int = 3600):
        """
        Initialize the Redis session manager

        Args:
            redis_uri (str): Redis connection URI
            session_ttl (int, optional): Session time-to-live in seconds. Defaults to 3600 (1 hour).
        """
        self.session_ttl = session_ttl

        try:
            self.redis = redis.from_url(redis_uri)
            self.redis.ping()  # Check connection
            logger.info(f"Connected to Redis at {redis_uri} with TTL: {session_ttl}s")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Cannot connect to Redis: {e}")

    def create_session(self, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new session

        Args:
            user_id (str, optional): User ID to associate with the session. Defaults to None.
            metadata (Dict[str, Any], optional): Additional metadata. Defaults to None.

        Returns:
            str: Session ID
        """
        session_id = str(uuid.uuid4())
        timestamp = time.time()

        # Create session object
        session = {
            "session_id": session_id,
            "created_at": timestamp,
            "last_accessed": timestamp,
            "user_id": user_id,
            "metadata": metadata or {},
            "messages": [],
            "message_count": 0
        }

        # Store session in Redis
        try:
            self.redis.setex(
                f"session:{session_id}",
                self.session_ttl,
                json.dumps(session)
            )

            # Index session by user_id if provided
            if user_id:
                self.redis.sadd(f"user:{user_id}:sessions", session_id)
                # Set TTL on user's sessions set if it doesn't exist
                if not self.redis.exists(f"user:{user_id}:sessions"):
                    self.redis.expire(f"user:{user_id}:sessions", self.session_ttl * 10)  # Longer TTL for user index

            logger.debug(f"Created Redis session: {session_id} for user: {user_id}")
            return session_id

        except RedisError as e:
            logger.error(f"Error creating session in Redis: {e}")
            raise RuntimeError(f"Failed to create session: {e}")

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data by session ID

        Args:
            session_id (str): Session ID

        Returns:
            Optional[Dict[str, Any]]: Session data or None if not found
        """
        try:
            session_data = self.redis.get(f"session:{session_id}")
            if not session_data:
                return None

            # Parse JSON data
            session = json.loads(session_data)

            # Update last accessed time
            self._update_last_accessed(session_id)

            # Refresh TTL
            self.redis.expire(f"session:{session_id}", self.session_ttl)

            return session

        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error retrieving session from Redis: {e}")
            return None

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session data

        Args:
            session_id (str): Session ID
            updates (Dict[str, Any]): Data to update

        Returns:
            bool: True if successful, False if session not found
        """
        try:
            # Get current session
            session_data = self.redis.get(f"session:{session_id}")
            if not session_data:
                return False

            # Parse JSON data
            session = json.loads(session_data)

            # Update session data
            for key, value in updates.items():
                if key not in ["session_id", "created_at", "messages"]:  # Don't overwrite these
                    session[key] = value

            # Update last accessed time
            session["last_accessed"] = time.time()

            # Store updated session
            self.redis.setex(
                f"session:{session_id}",
                self.session_ttl,
                json.dumps(session)
            )

            return True

        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error updating session in Redis: {e}")
            return False

    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Save complete session data, replacing any existing session

        Args:
            session_id (str): Session ID
            session_data (Dict[str, Any]): Complete session data

        Returns:
            bool: True if successful, False if error
        """
        try:
            # Ensure session_id is consistent
            if "session_id" in session_data and session_data["session_id"] != session_id:
                logger.warning(f"Session ID mismatch: {session_id} vs {session_data['session_id']}")
                session_data["session_id"] = session_id

            # Update last accessed time
            session_data["last_accessed"] = time.time()

            # Store session
            self.redis.setex(
                f"session:{session_id}",
                self.session_ttl,
                json.dumps(session_data)
            )

            # Index by user_id if present
            user_id = session_data.get("user_id")
            if user_id:
                self.redis.sadd(f"user:{user_id}:sessions", session_id)
                # Set TTL on user's sessions set if it doesn't exist
                if not self.redis.exists(f"user:{user_id}:sessions"):
                    self.redis.expire(f"user:{user_id}:sessions", self.session_ttl * 10)

            return True

        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error saving session in Redis: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session

        Args:
            session_id (str): Session ID

        Returns:
            bool: True if deleted, False if session not found
        """
        try:
            # Get session to check user_id
            session_data = self.redis.get(f"session:{session_id}")
            if not session_data:
                return False

            # Parse JSON data
            session = json.loads(session_data)

            # Remove from user index if applicable
            user_id = session.get("user_id")
            if user_id:
                self.redis.srem(f"user:{user_id}:sessions", session_id)

            # Delete session
            self.redis.delete(f"session:{session_id}")
            logger.debug(f"Deleted Redis session: {session_id}")
            return True

        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error deleting session from Redis: {e}")
            return False

    def _update_last_accessed(self, session_id: str) -> None:
        """
        Update the last accessed timestamp for a session

        Args:
            session_id (str): Session ID
        """
        try:
            # Get current session
            session_data = self.redis.get(f"session:{session_id}")
            if not session_data:
                return

            # Parse JSON data
            session = json.loads(session_data)

            # Update last accessed time
            session["last_accessed"] = time.time()

            # Store updated session without modifying TTL
            pipe = self.redis.pipeline()
            pipe.setex(f"session:{session_id}", self.session_ttl, json.dumps(session))
            pipe.execute()

        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error updating last accessed time in Redis: {e}")

    def add_message_to_session(self, session_id: str, message: Dict[str, Any] = None, role: str = None, content: str = None) -> bool:
        """
        Add a message to the session history

        Args:
            session_id (str): Session ID
            message (Dict[str, Any], optional): Message data dictionary
            role (str, optional): Message role ('user' or 'assistant')
            content (str, optional): Message content

        Returns:
            bool: True if successful, False if session not found
        """
        try:
            # Get current session
            session_data = self.redis.get(f"session:{session_id}")
            if not session_data:
                return False

            # Parse JSON data
            session = json.loads(session_data)

            # Prepare the message
            msg = None

            # If message dict is provided, use it
            if message is not None:
                msg = message
                # Add timestamp if not provided
                if "timestamp" not in msg:
                    msg["timestamp"] = datetime.now().isoformat()
            # Otherwise, try to create from role and content
            elif role is not None and content is not None:
                msg = {
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # No valid message data
                logger.error("Either message dict or role+content must be provided")
                return False

            # Add message to session
            if "messages" not in session:
                session["messages"] = []
            session["messages"].append(msg)

            # Update message count
            session["message_count"] = len(session["messages"])

            # Update last accessed time
            session["last_accessed"] = time.time()

            # Store updated session
            self.redis.setex(
                f"session:{session_id}",
                self.session_ttl,
                json.dumps(session)
            )

            return True

        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error adding message to session in Redis: {e}")
            return False

    def get_session_messages(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get all messages for a session

        Args:
            session_id (str): Session ID

        Returns:
            Optional[List[Dict[str, Any]]]: List of messages or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        return session.get("messages", [])

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user

        Args:
            user_id (str): User ID

        Returns:
            List[Dict[str, Any]]: List of session data
        """
        try:
            # Get session IDs for this user
            session_ids = self.redis.smembers(f"user:{user_id}:sessions")
            if not session_ids:
                return []

            sessions = []
            for session_id in session_ids:
                # Convert bytes to string if needed
                if isinstance(session_id, bytes):
                    session_id = session_id.decode('utf-8')

                session = self.get_session(session_id)
                if session:
                    sessions.append(session)
                else:
                    # Clean up reference to non-existent session
                    self.redis.srem(f"user:{user_id}:sessions", session_id)

            return sessions

        except RedisError as e:
            logger.error(f"Error retrieving user sessions from Redis: {e}")
            return []

    def cleanup_expired_sessions(self, days_old: int = 1) -> int:
        """
        Clean up expired sessions (note: Redis handles TTL automatically,
        but this can be used for manual cleanup of very old sessions)

        Args:
            days_old (int, optional): Delete sessions older than this many days. Defaults to 1.

        Returns:
            int: Number of sessions deleted (or -1 if operation failed)
        """
        try:
            # Find all session keys
            session_keys = self.redis.keys("session:*")
            if not session_keys:
                return 0

            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            sessions_deleted = 0

            for key in session_keys:
                # Convert bytes to string if needed
                if isinstance(key, bytes):
                    key = key.decode('utf-8')

                # Extract session_id from key
                session_id = key.split(":", 1)[1]

                # Get session data
                session_data = self.redis.get(key)
                if not session_data:
                    continue

                # Parse JSON data
                try:
                    session = json.loads(session_data)

                    # Check if session is older than cutoff
                    if session.get("last_accessed", 0) < cutoff_time:
                        # Delete session
                        if self.delete_session(session_id):
                            sessions_deleted += 1

                except json.JSONDecodeError:
                    # Invalid JSON, delete the key
                    self.redis.delete(key)
                    sessions_deleted += 1

            logger.info(f"Cleaned up {sessions_deleted} expired Redis sessions")
            return sessions_deleted

        except RedisError as e:
            logger.error(f"Error cleaning up expired sessions in Redis: {e}")
            return -1

    # --- Authentication-related methods ---

    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session token.

        Args:
            token (str): Session token (same as session_id in this implementation)

        Returns:
            Optional[Dict[str, Any]]: Session data if valid, None if invalid
        """
        # In this implementation, the token is the session_id
        return self.get_session(token)

    def set_session_cookie(self, response, session_id: str, max_age: Optional[int] = None) -> None:
        """
        Set a session cookie in the response.

        Args:
            response: The FastAPI Response object
            session_id (str): The session ID to set in the cookie
            max_age (int, optional): Cookie max age in seconds. Defaults to session_ttl.
        """
        from fastapi import Response

        # Use provided max_age or default to session_ttl
        cookie_max_age = max_age or self.session_ttl

        # Import settings to get cookie configuration
        from src.utils.settings import settings

        if isinstance(response, Response):
            response.set_cookie(
                key=settings.session_cookie_name,
                value=session_id,
                httponly=True,
                max_age=cookie_max_age,
                secure=settings.session_cookie_secure,
                samesite="lax"
            )

    def delete_session_cookie(self, response) -> None:
        """
        Delete the session cookie in the response.

        Args:
            response: The FastAPI Response object
        """
        from fastapi import Response
        from src.utils.settings import settings

        if isinstance(response, Response):
            response.delete_cookie(
                key=settings.session_cookie_name,
                httponly=True,
                secure=settings.session_cookie_secure,
                samesite="lax"
            )