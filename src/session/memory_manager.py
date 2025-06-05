"""
In-memory session manager for local testing and fallback.
Stores sessions in local memory, with no persistence between application restarts.
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import Response

from src.config_unified import settings

logger = logging.getLogger(__name__)

class MemorySessionManager:
    """Session manager that stores sessions in memory"""

    def __init__(self, session_ttl: int = 3600):
        """
        Initialize the memory session manager

        Args:
            session_ttl (int, optional): Session time-to-live in seconds. Defaults to 3600 (1 hour).
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> session data
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> list of session_ids
        self.session_ttl = session_ttl
        logger.info(f"Initialized memory session manager with TTL: {session_ttl}s")

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

        # Store session
        self.sessions[session_id] = session

        # Add to user index if user_id provided
        if user_id:
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            self.user_sessions[user_id].append(session_id)

        logger.debug(f"Created memory session: {session_id} for user: {user_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data by session ID

        Args:
            session_id (str): Session ID

        Returns:
            Optional[Dict[str, Any]]: Session data or None if not found
        """
        session = self.sessions.get(session_id)
        if not session:
            return None

        # Update last accessed time
        self._update_last_accessed(session_id)
        return session

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session data

        Args:
            session_id (str): Session ID
            updates (Dict[str, Any]): Data to update

        Returns:
            bool: True if successful, False if session not found
        """
        if session_id not in self.sessions:
            return False

        # Update session data
        for key, value in updates.items():
            if key not in ["session_id", "created_at", "messages"]:  # Don't overwrite these
                self.sessions[session_id][key] = value

        # Update last accessed time
        self._update_last_accessed(session_id)
        return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session

        Args:
            session_id (str): Session ID

        Returns:
            bool: True if deleted, False if session not found
        """
        if session_id not in self.sessions:
            return False

        # Remove from user index if applicable
        user_id = self.sessions[session_id].get("user_id")
        if user_id and user_id in self.user_sessions:
            if session_id in self.user_sessions[user_id]:
                self.user_sessions[user_id].remove(session_id)

        # Delete session
        del self.sessions[session_id]
        logger.debug(f"Deleted memory session: {session_id}")
        return True

    def _update_last_accessed(self, session_id: str) -> None:
        """
        Update the last accessed timestamp for a session

        Args:
            session_id (str): Session ID
        """
        if session_id in self.sessions:
            self.sessions[session_id]["last_accessed"] = time.time()

    def add_message_to_session(self, session_id: str, message: Dict[str, Any]) -> bool:
        """
        Add a message to the session history

        Args:
            session_id (str): Session ID
            message (Dict[str, Any]): Message data

        Returns:
            bool: True if successful, False if session not found
        """
        if session_id not in self.sessions:
            return False

        # Add timestamp if not provided
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        # Add message to session
        self.sessions[session_id]["messages"].append(message)
        self.sessions[session_id]["message_count"] += 1

        # Update last accessed time
        self._update_last_accessed(session_id)
        return True

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
        if user_id not in self.user_sessions:
            return []

        sessions = []
        for session_id in self.user_sessions[user_id]:
            session = self.get_session(session_id)
            if session:
                sessions.append(session)

        return sessions

    def cleanup_expired_sessions(self, days_old: int = 1) -> int:
        """
        Clean up expired sessions

        Args:
            days_old (int, optional): Delete sessions older than this many days. Defaults to 1.

        Returns:
            int: Number of sessions deleted
        """
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        sessions_to_delete = []

        # Find expired sessions
        for session_id, session in self.sessions.items():
            if session["last_accessed"] < cutoff_time:
                sessions_to_delete.append(session_id)

        # Delete expired sessions
        for session_id in sessions_to_delete:
            self.delete_session(session_id)

        logger.info(f"Cleaned up {len(sessions_to_delete)} expired memory sessions")
        return len(sessions_to_delete)

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
        from src.config_unified import settings

        if isinstance(response, Response):
            response.delete_cookie(
                key=settings.session_cookie_name,
                httponly=True,
                secure=settings.session_cookie_secure,
                samesite="lax"
            )