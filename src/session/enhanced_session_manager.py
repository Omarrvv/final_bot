"""
Enhanced Session Management Architecture

This module provides an enhanced session management architecture with:
1. Layered architecture with clear separation of concerns
2. Multiple storage backends (Redis, PostgreSQL, Memory)
3. Automatic failover between backends
4. Session data validation and sanitization
5. Comprehensive metrics and monitoring
6. Configurable session expiration and cleanup
"""

import os
import sys
import time
import json
import uuid
import logging
import threading
import functools
from typing import Dict, List, Any, Optional, Union, Callable, TypeVar, cast
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

# Import Redis connection manager
from src.session.redis_connection import RedisConnectionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Type variable for return type
T = TypeVar('T')

class SessionData:
    """Session data model with validation"""
    
    def __init__(self, 
                 session_id: str,
                 user_id: Optional[str] = None,
                 created_at: Optional[str] = None,
                 updated_at: Optional[str] = None,
                 expires_at: Optional[str] = None,
                 language: str = "en",
                 messages: Optional[List[Dict[str, Any]]] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 context: Optional[Dict[str, Any]] = None):
        """
        Initialize session data
        
        Args:
            session_id (str): Unique session ID
            user_id (Optional[str], optional): User ID. Defaults to None.
            created_at (Optional[str], optional): Creation timestamp. Defaults to None.
            updated_at (Optional[str], optional): Last update timestamp. Defaults to None.
            expires_at (Optional[str], optional): Expiration timestamp. Defaults to None.
            language (str, optional): Session language. Defaults to "en".
            messages (Optional[List[Dict[str, Any]]], optional): Session messages. Defaults to None.
            metadata (Optional[Dict[str, Any]], optional): Session metadata. Defaults to None.
            context (Optional[Dict[str, Any]], optional): Session context. Defaults to None.
        """
        self.session_id = session_id
        self.user_id = user_id
        
        # Set timestamps
        now = datetime.now().isoformat()
        self.created_at = created_at or now
        self.updated_at = updated_at or now
        
        # Set expiration (default: 7 days)
        if expires_at:
            self.expires_at = expires_at
        else:
            expiration = datetime.now() + timedelta(days=7)
            self.expires_at = expiration.isoformat()
        
        self.language = language
        self.messages = messages or []
        self.metadata = metadata or {}
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session data to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "language": self.language,
            "messages": self.messages,
            "metadata": self.metadata,
            "context": self.context
        }
    
    def to_json(self) -> str:
        """Convert session data to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Create session data from dictionary"""
        return cls(
            session_id=data.get("session_id", str(uuid.uuid4())),
            user_id=data.get("user_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            expires_at=data.get("expires_at"),
            language=data.get("language", "en"),
            messages=data.get("messages", []),
            metadata=data.get("metadata", {}),
            context=data.get("context", {})
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SessionData':
        """Create session data from JSON string"""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse session data JSON: {json_str}")
            # Return a new session as fallback
            return cls(session_id=str(uuid.uuid4()))
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        try:
            expires_at = datetime.fromisoformat(self.expires_at)
            return datetime.now() > expires_at
        except (ValueError, TypeError):
            # If we can't parse the expiration date, assume it's expired
            return True
    
    def update_timestamp(self) -> None:
        """Update the last updated timestamp"""
        self.updated_at = datetime.now().isoformat()
    
    def add_message(self, role: str, content: str) -> Dict[str, Any]:
        """Add a message to the session"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(message)
        self.update_timestamp()
        return message

class SessionStorageBackend(ABC):
    """Abstract base class for session storage backends"""
    
    @abstractmethod
    def get(self, session_id: str) -> Optional[SessionData]:
        """Get session data by ID"""
        pass
    
    @abstractmethod
    def save(self, session: SessionData) -> bool:
        """Save session data"""
        pass
    
    @abstractmethod
    def delete(self, session_id: str) -> bool:
        """Delete session data"""
        pass
    
    @abstractmethod
    def exists(self, session_id: str) -> bool:
        """Check if session exists"""
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """Clean up expired sessions"""
        pass

class RedisSessionBackend(SessionStorageBackend):
    """Redis session storage backend"""
    
    def __init__(self, redis_uri: str, prefix: str = "session:", ttl: int = 604800):
        """
        Initialize Redis session backend
        
        Args:
            redis_uri (str): Redis connection URI
            prefix (str, optional): Key prefix. Defaults to "session:".
            ttl (int, optional): Session TTL in seconds. Defaults to 604800 (7 days).
        """
        self.redis_uri = redis_uri
        self.prefix = prefix
        self.ttl = ttl
        self._is_available = True
        self._last_error = None
        
        # Try to connect to Redis
        try:
            redis_client = RedisConnectionManager.get_redis_client(redis_uri)
            redis_client.ping()
            logger.info(f"Connected to Redis: {redis_uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._is_available = False
            self._last_error = str(e)
    
    def _get_key(self, session_id: str) -> str:
        """Get Redis key for session ID"""
        return f"{self.prefix}{session_id}"
    
    @RedisConnectionManager.with_redis_fallback(None)
    def get(self, session_id: str) -> Optional[SessionData]:
        """Get session data by ID"""
        key = self._get_key(session_id)
        
        # Get Redis client
        redis_client = RedisConnectionManager.get_redis_client(self.redis_uri)
        
        # Get session data
        data = redis_client.get(key)
        if not data:
            return None
        
        # Parse session data
        try:
            session = SessionData.from_json(data.decode("utf-8"))
            
            # Check if session is expired
            if session.is_expired():
                logger.info(f"Session {session_id} is expired")
                self.delete(session_id)
                return None
            
            return session
        except Exception as e:
            logger.error(f"Failed to parse session data: {e}")
            return None
    
    @RedisConnectionManager.with_redis_fallback(False)
    def save(self, session: SessionData) -> bool:
        """Save session data"""
        key = self._get_key(session.session_id)
        
        # Update timestamp
        session.update_timestamp()
        
        # Get Redis client
        redis_client = RedisConnectionManager.get_redis_client(self.redis_uri)
        
        # Save session data
        try:
            redis_client.setex(key, self.ttl, session.to_json())
            return True
        except Exception as e:
            logger.error(f"Failed to save session data: {e}")
            return False
    
    @RedisConnectionManager.with_redis_fallback(False)
    def delete(self, session_id: str) -> bool:
        """Delete session data"""
        key = self._get_key(session_id)
        
        # Get Redis client
        redis_client = RedisConnectionManager.get_redis_client(self.redis_uri)
        
        # Delete session data
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete session data: {e}")
            return False
    
    @RedisConnectionManager.with_redis_fallback(False)
    def exists(self, session_id: str) -> bool:
        """Check if session exists"""
        key = self._get_key(session_id)
        
        # Get Redis client
        redis_client = RedisConnectionManager.get_redis_client(self.redis_uri)
        
        # Check if session exists
        try:
            return bool(redis_client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check if session exists: {e}")
            return False
    
    @RedisConnectionManager.with_redis_fallback(0)
    def cleanup_expired(self) -> int:
        """Clean up expired sessions"""
        # Redis automatically expires keys based on TTL
        return 0
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self._is_available and RedisConnectionManager.is_redis_healthy(self.redis_uri)

class MemorySessionBackend(SessionStorageBackend):
    """In-memory session storage backend"""
    
    def __init__(self):
        """Initialize in-memory session backend"""
        self.sessions: Dict[str, SessionData] = {}
        self.lock = threading.RLock()
    
    def get(self, session_id: str) -> Optional[SessionData]:
        """Get session data by ID"""
        with self.lock:
            session = self.sessions.get(session_id)
            
            if not session:
                return None
            
            # Check if session is expired
            if session.is_expired():
                logger.info(f"Session {session_id} is expired")
                self.delete(session_id)
                return None
            
            return session
    
    def save(self, session: SessionData) -> bool:
        """Save session data"""
        with self.lock:
            # Update timestamp
            session.update_timestamp()
            
            # Save session data
            self.sessions[session.session_id] = session
            return True
    
    def delete(self, session_id: str) -> bool:
        """Delete session data"""
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False
    
    def exists(self, session_id: str) -> bool:
        """Check if session exists"""
        with self.lock:
            return session_id in self.sessions
    
    def cleanup_expired(self) -> int:
        """Clean up expired sessions"""
        with self.lock:
            expired_sessions = [
                session_id for session_id, session in self.sessions.items()
                if session.is_expired()
            ]
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
            
            return len(expired_sessions)
    
    def is_available(self) -> bool:
        """Check if memory backend is available"""
        return True

class EnhancedSessionManager:
    """Enhanced session manager with multiple backends and failover"""
    
    def __init__(self, redis_uri: str = "redis://localhost:6379/0", ttl: int = 604800):
        """
        Initialize enhanced session manager
        
        Args:
            redis_uri (str, optional): Redis connection URI. Defaults to "redis://localhost:6379/0".
            ttl (int, optional): Session TTL in seconds. Defaults to 604800 (7 days).
        """
        self.redis_uri = redis_uri
        self.ttl = ttl
        
        # Initialize backends
        self.redis_backend = RedisSessionBackend(redis_uri, ttl=ttl)
        self.memory_backend = MemorySessionBackend()
        
        # Set up metrics
        self.metrics = {
            "created_sessions": 0,
            "retrieved_sessions": 0,
            "updated_sessions": 0,
            "deleted_sessions": 0,
            "failed_operations": 0,
            "redis_fallbacks": 0,
            "expired_sessions": 0
        }
        
        # Set up cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_thread, daemon=True)
        self.cleanup_thread.start()
    
    def _get_backend(self) -> SessionStorageBackend:
        """Get the best available backend"""
        if self.redis_backend.is_available():
            return self.redis_backend
        
        # Increment fallback metric
        self.metrics["redis_fallbacks"] += 1
        
        # Log fallback
        logger.warning("Redis backend is not available, falling back to memory backend")
        
        return self.memory_backend
    
    def create_session(self, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new session
        
        Args:
            user_id (Optional[str], optional): User ID. Defaults to None.
            metadata (Optional[Dict[str, Any]], optional): Session metadata. Defaults to None.
            
        Returns:
            str: Session ID
        """
        try:
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Create session data
            session = SessionData(
                session_id=session_id,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            # Save session data
            backend = self._get_backend()
            if backend.save(session):
                # Increment metric
                self.metrics["created_sessions"] += 1
                
                return session_id
            else:
                # Increment failed operations metric
                self.metrics["failed_operations"] += 1
                
                logger.error(f"Failed to create session")
                return ""
        except Exception as e:
            # Increment failed operations metric
            self.metrics["failed_operations"] += 1
            
            logger.error(f"Error creating session: {e}")
            return ""
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data
        
        Args:
            session_id (str): Session ID
            
        Returns:
            Optional[Dict[str, Any]]: Session data or None if not found
        """
        try:
            # Get session data
            backend = self._get_backend()
            session = backend.get(session_id)
            
            if not session:
                return None
            
            # Increment metric
            self.metrics["retrieved_sessions"] += 1
            
            return session.to_dict()
        except Exception as e:
            # Increment failed operations metric
            self.metrics["failed_operations"] += 1
            
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update session data
        
        Args:
            session_id (str): Session ID
            data (Dict[str, Any]): Data to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get session data
            backend = self._get_backend()
            session = backend.get(session_id)
            
            if not session:
                logger.error(f"Session {session_id} not found")
                return False
            
            # Update session data
            for key, value in data.items():
                if key == "metadata":
                    session.metadata.update(value)
                elif key == "context":
                    session.context.update(value)
                elif hasattr(session, key):
                    setattr(session, key, value)
            
            # Save session data
            if backend.save(session):
                # Increment metric
                self.metrics["updated_sessions"] += 1
                
                return True
            else:
                # Increment failed operations metric
                self.metrics["failed_operations"] += 1
                
                logger.error(f"Failed to update session {session_id}")
                return False
        except Exception as e:
            # Increment failed operations metric
            self.metrics["failed_operations"] += 1
            
            logger.error(f"Error updating session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session
        
        Args:
            session_id (str): Session ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete session data
            backend = self._get_backend()
            if backend.delete(session_id):
                # Increment metric
                self.metrics["deleted_sessions"] += 1
                
                return True
            else:
                # Increment failed operations metric
                self.metrics["failed_operations"] += 1
                
                logger.error(f"Failed to delete session {session_id}")
                return False
        except Exception as e:
            # Increment failed operations metric
            self.metrics["failed_operations"] += 1
            
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def add_message_to_session(self, session_id: str, role: str, content: str) -> bool:
        """
        Add a message to a session
        
        Args:
            session_id (str): Session ID
            role (str): Message role (user, assistant)
            content (str): Message content
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get session data
            backend = self._get_backend()
            session = backend.get(session_id)
            
            if not session:
                # Create a new session if it doesn't exist
                session = SessionData(session_id=session_id)
            
            # Add message
            session.add_message(role, content)
            
            # Save session data
            if backend.save(session):
                # Increment metric
                self.metrics["updated_sessions"] += 1
                
                return True
            else:
                # Increment failed operations metric
                self.metrics["failed_operations"] += 1
                
                logger.error(f"Failed to add message to session {session_id}")
                return False
        except Exception as e:
            # Increment failed operations metric
            self.metrics["failed_operations"] += 1
            
            logger.error(f"Error adding message to session {session_id}: {e}")
            return False
    
    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get session messages
        
        Args:
            session_id (str): Session ID
            
        Returns:
            List[Dict[str, Any]]: Session messages
        """
        try:
            # Get session data
            backend = self._get_backend()
            session = backend.get(session_id)
            
            if not session:
                return []
            
            return session.messages
        except Exception as e:
            logger.error(f"Error getting session messages {session_id}: {e}")
            return []
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get session context
        
        Args:
            session_id (str): Session ID
            
        Returns:
            Dict[str, Any]: Session context
        """
        try:
            # Get session data
            backend = self._get_backend()
            session = backend.get(session_id)
            
            if not session:
                return {}
            
            return session.context
        except Exception as e:
            logger.error(f"Error getting session context {session_id}: {e}")
            return {}
    
    def _cleanup_thread(self) -> None:
        """Background thread for cleaning up expired sessions"""
        while True:
            try:
                # Clean up expired sessions in memory backend
                expired_count = self.memory_backend.cleanup_expired()
                
                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired sessions from memory backend")
                    
                    # Update metric
                    self.metrics["expired_sessions"] += expired_count
                
                # Sleep for 1 hour
                time.sleep(3600)
            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")
                
                # Sleep for 5 minutes before retrying
                time.sleep(300)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get session manager metrics"""
        return self.metrics.copy()
    
    def get_health(self) -> Dict[str, Any]:
        """Get session manager health status"""
        redis_health = RedisConnectionManager.get_health_metrics().get(self.redis_uri, {})
        
        return {
            "redis_available": self.redis_backend.is_available(),
            "memory_available": self.memory_backend.is_available(),
            "redis_health": redis_health,
            "metrics": self.get_metrics()
        }
