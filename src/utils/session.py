# src/utils/session.py
"""
Session management module for the Egypt Tourism Chatbot.
Manages user session state and conversation context.
"""
import json
import logging
import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import threading
import time
import redis

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Session manager that handles user sessions and conversation context.
    Maintains session state across multiple interactions.
    """
    
    def __init__(self, session_ttl: int = 3600, storage_uri: Optional[str] = None):
        """
        Initialize the session manager.
        
        Args:
            session_ttl (int): Session time-to-live in seconds
            storage_uri (str, optional): URI for the session storage backend
        """
        self.session_ttl = session_ttl
        self.storage_uri = storage_uri
        
        # Initialize session storage
        self.sessions = {}
        
        # Session lock for thread safety
        self.session_lock = threading.Lock()
        
        # Initialize session storage backend if URI provided
        self.storage_backend = None
        if storage_uri:
            self._initialize_storage_backend()
        
        # Start session cleanup thread ONLY if not using Redis
        if not isinstance(self.storage_backend, redis.Redis):
            self.cleanup_thread = threading.Thread(target=self._cleanup_expired_sessions, daemon=True)
            self.cleanup_thread.start()
        
        logger.info("Session manager initialized successfully")
    
    def _initialize_storage_backend(self):
        """Initialize the session storage backend based on URI."""
        # Parse storage URI to determine backend type
        # Format: [type]://[host]:[port]/[path]
        # Example: redis://localhost:6379/0
        # Example: file:///path/to/sessions
        
        try:
            if self.storage_uri.startswith("redis://"):
                self._initialize_redis_backend()
            elif self.storage_uri.startswith("file://"):
                self._initialize_file_backend()
            else:
                logger.warning(f"Unsupported storage URI: {self.storage_uri}")
                logger.info("Using in-memory session storage")
        except Exception as e:
            logger.error(f"Failed to initialize storage backend: {str(e)}")
            logger.info("Using in-memory session storage")
    
    def _initialize_redis_backend(self):
        """Initialize Redis storage backend."""
        try:
            # Parse Redis URI
            # Format: redis://[username]:[password]@[host]:[port]/[db]
            logger.info(f"Initializing Redis session storage: {self.storage_uri}")
            parts = self.storage_uri[8:].split('@')
            if len(parts) == 2:
                auth, host_port = parts
                username, password = auth.split(':')
            else:
                username = None
                password = None
                host_port = parts[0]
            
            host_port_db = host_port.split('/')
            host_port = host_port_db[0]
            db = int(host_port_db[1]) if len(host_port_db) > 1 else 0
            
            host, port = host_port.split(':')
            port = int(port)
            
            logger.info(f"Connecting to Redis at {host}:{port}/db{db}")
            
            # Initialize Redis client with connection pool
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    self.storage_backend = redis.Redis(
                        host=host,
                        port=port,
                        db=db,
                        username=username,
                        password=password,
                        decode_responses=True,
                        socket_timeout=5.0,  # 5 seconds timeout
                        socket_connect_timeout=5.0,
                        retry_on_timeout=True
                    )
                    
                    # Test connection
                    self.storage_backend.ping()
                    logger.info("Redis storage backend initialized successfully")
                    return
                except (redis.ConnectionError, redis.TimeoutError) as redis_err:
                    retry_count += 1
                    logger.warning(f"Redis connection attempt {retry_count}/{max_retries} failed: {str(redis_err)}")
                    if retry_count >= max_retries:
                        raise
                    time.sleep(2)  # Wait 2 seconds before retrying
            
        except ImportError:
            logger.error("Redis package not installed. Cannot use Redis backend.")
            logger.info("Using in-memory session storage")
        except Exception as e:
            logger.error(f"Failed to initialize Redis backend: {str(e)}", exc_info=True)
            logger.info("Using in-memory session storage")
            self.storage_backend = None
    
    def _initialize_file_backend(self):
        """Initialize file-based storage backend."""
        try:
            # Parse file URI
            # Format: file:///path/to/sessions
            file_path = self.storage_uri[7:]
            
            # Create directory if it doesn't exist
            os.makedirs(file_path, exist_ok=True)
            
            # Initialize file backend
            self.storage_backend = FileSessionStorage(file_path)
            
            logger.info(f"File storage backend initialized: {file_path}")
        except Exception as e:
            logger.error(f"Failed to initialize file backend: {str(e)}")
            logger.info("Using in-memory session storage")
            self.storage_backend = None
    
    def create_session(self) -> str:
        """
        Create a new session.
        
        Returns:
            str: Session ID
        """
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Create session data
        session_data = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=self.session_ttl)).isoformat(),
            "context": {
                "dialog_state": "greeting",
                "entities": {},
                "last_intent": None,
                "language": "en"
            }
        }
        
        # Store session
        self._store_session(session_id, session_data)
        
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data by ID.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            dict: Session data if found, None otherwise
        """
        # Try to get session from storage backend
        if self.storage_backend:
            try:
                if isinstance(self.storage_backend, redis.Redis):
                    # For Redis, need to handle serialized data
                    serialized_data = self.storage_backend.get(session_id)
                    if serialized_data:
                        try:
                            # Deserialize JSON data from Redis
                            session_data = json.loads(serialized_data)
                            # Update in-memory cache
                            with self.session_lock:
                                self.sessions[session_id] = session_data
                            logger.debug(f"Retrieved session from Redis: {session_id}")
                            return session_data
                        except json.JSONDecodeError as json_err:
                            logger.error(f"Failed to decode session JSON from Redis: {str(json_err)}")
                            return None
                else:
                    # For other backends like File
                    session_data = self.storage_backend.get(session_id)
                    if session_data:
                        # Update in-memory cache
                        with self.session_lock:
                            self.sessions[session_id] = session_data
                        logger.debug(f"Retrieved session from {type(self.storage_backend).__name__}: {session_id}")
                        return session_data
            except Exception as e:
                logger.error(f"Failed to get session {session_id} from storage backend: {str(e)}", exc_info=True)
        
        # Try to get session from in-memory cache
        with self.session_lock:
            session_data = self.sessions.get(session_id)
        
        if session_data:
            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if expires_at < datetime.now():
                logger.info(f"Session expired: {session_id}")
                self.delete_session(session_id)
                return None
            
            logger.debug(f"Retrieved session from memory cache: {session_id}")
            return session_data
        
        logger.warning(f"Session not found: {session_id}")
        return None
    
    def update_session(self, session_id: str, session_data: Dict) -> bool:
        """
        Update session data.
        
        Args:
            session_id (str): Session ID
            session_data (dict): Updated session data
            
        Returns:
            bool: Success status
        """
        # Update last activity and expiration time
        session_data["last_activity"] = datetime.now().isoformat()
        session_data["expires_at"] = (datetime.now() + timedelta(seconds=self.session_ttl)).isoformat()
        
        # Store updated session
        return self._store_session(session_id, session_data)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            bool: Success status
        """
        success = True
        
        # Delete from in-memory cache
        with self.session_lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.debug(f"Deleted session from memory cache: {session_id}")
        
        # Delete from storage backend
        if self.storage_backend:
            try:
                if isinstance(self.storage_backend, redis.Redis):
                    # For Redis, use delete method
                    deleted = self.storage_backend.delete(session_id)
                    if deleted:
                        logger.info(f"Deleted session from Redis: {session_id}")
                    else:
                        logger.warning(f"Session not found in Redis during deletion: {session_id}")
                else:
                    # For other backends like File
                    success = self.storage_backend.delete(session_id)
                    logger.info(f"Deleted session from {type(self.storage_backend).__name__}: {session_id}")
            except Exception as e:
                logger.error(f"Failed to delete session {session_id} from storage backend: {str(e)}", exc_info=True)
                success = False
        
        return success
    
    def get_context(self, session_id: str) -> Dict:
        """
        Get conversation context for a session.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            dict: Conversation context
        """
        session_data = self.get_session(session_id)
        if not session_data:
            # Create a new session if not found
            session_id = self.create_session()
            session_data = self.get_session(session_id)
        
        return session_data.get("context", {})
    
    def set_context(self, session_id: str, context: Dict) -> bool:
        """
        Set conversation context for a session.
        
        Args:
            session_id (str): Session ID
            context (dict): Updated conversation context
            
        Returns:
            bool: Success status
        """
        session_data = self.get_session(session_id)
        if not session_data:
            # Create a new session if not found
            session_id = self.create_session()
            session_data = self.get_session(session_id)
        
        # Update context
        session_data["context"] = context
        
        # Update session
        return self.update_session(session_id, session_data)
    
    def update_context(self, session_id: str, nlu_result: Dict) -> Dict:
        """
        Update conversation context based on NLU result.
        
        Args:
            session_id (str): Session ID
            nlu_result (dict): NLU processing result
            
        Returns:
            dict: Updated conversation context
        """
        # Get current context
        context = self.get_context(session_id)
        
        # Extract data from NLU result
        intent = nlu_result.get("intent")
        entities = nlu_result.get("entities", {})
        language = nlu_result.get("language", context.get("language", "en"))
        
        # Update context with NLU results
        if intent:
            # Store last intent
            context["last_intent"] = intent
        
        # Update language
        context["language"] = language
        
        # Update entities
        current_entities = context.get("entities", {})
        for entity_type, entity_values in entities.items():
            current_entities[entity_type] = entity_values
        
        context["entities"] = current_entities
        
        # Store updated context
        self.set_context(session_id, context)
        
        return context
    
    def _store_session(self, session_id: str, session_data: Dict) -> bool:
        """
        Store session data in memory and backend storage.
        
        Args:
            session_id (str): Session ID
            session_data (dict): Session data
            
        Returns:
            bool: Success status
        """
        try:
            # Store in memory
            with self.session_lock:
                self.sessions[session_id] = session_data
            
            # Store in backend
            if self.storage_backend:
                # Handle Redis backend
                if isinstance(self.storage_backend, redis.Redis):
                    try:
                        # Serialize session data for Redis
                        serialized_data = json.dumps(session_data)
                        
                        # Use setex for automatic expiration (key, seconds, value)
                        success = self.storage_backend.setex(
                            name=session_id,
                            time=self.session_ttl,
                            value=serialized_data
                        )
                        
                        if not success:
                            logger.warning(f"Redis setex returned non-True value for session: {session_id}")
                        
                        logger.debug(f"Stored session in Redis with TTL {self.session_ttl}s: {session_id}")
                        return True
                    except Exception as redis_err:
                        logger.error(f"Redis storage error for session {session_id}: {str(redis_err)}", exc_info=True)
                        # Fall back to in-memory only
                        return True
                else:
                    # Use generic set for other backends (like File)
                    try:
                        self.storage_backend.set(session_id, session_data)  # FileStorage expects dict
                        logger.debug(f"Stored session in {type(self.storage_backend).__name__}: {session_id}")
                        return True
                    except Exception as backend_err:
                        logger.error(f"Storage backend error for session {session_id}: {str(backend_err)}", exc_info=True)
                        # Fall back to in-memory only
                        return True
            
            # If we got here, we're using in-memory only
            logger.debug(f"Stored session in memory only: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store session {session_id}: {str(e)}", exc_info=True)
            return False
    
    def _cleanup_expired_sessions(self):
        """Periodically clean up expired sessions."""
        while True:
            # Sleep for a while
            time.sleep(60)  # Check every minute
            
            try:
                # Get current time
                now = datetime.now()
                
                # Find expired sessions
                expired_sessions = []
                
                with self.session_lock:
                    for session_id, session_data in self.sessions.items():
                        expires_at = datetime.fromisoformat(session_data["expires_at"])
                        if expires_at < now:
                            expired_sessions.append(session_id)
                
                # Delete expired sessions
                for session_id in expired_sessions:
                    self.delete_session(session_id)
                
                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
            except Exception as e:
                logger.error(f"Error in session cleanup: {str(e)}")


class FileSessionStorage:
    """File-based session storage backend."""
    
    def __init__(self, file_path: str):
        """
        Initialize file-based session storage.
        
        Args:
            file_path (str): Path to session storage directory
        """
        self.file_path = file_path
        
        # Create directory if it doesn't exist
        os.makedirs(file_path, exist_ok=True)
    
    def get(self, session_id: str) -> Optional[Dict]:
        """
        Get session data by ID.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            dict: Session data if found, None otherwise
        """
        file_name = os.path.join(self.file_path, f"{session_id}.json")
        
        try:
            if os.path.exists(file_name):
                with open(file_name, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Failed to read session file: {str(e)}")
            return None
    
    def set(self, session_id: str, session_data: Dict) -> bool:
        """
        Store session data.
        
        Args:
            session_id (str): Session ID
            session_data (dict): Session data
            
        Returns:
            bool: Success status
        """
        file_name = os.path.join(self.file_path, f"{session_id}.json")
        
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to write session file: {str(e)}")
            return False
    
    def delete(self, session_id: str) -> bool:
        """
        Delete session data.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            bool: Success status
        """
        file_name = os.path.join(self.file_path, f"{session_id}.json")
        
        try:
            if os.path.exists(file_name):
                os.remove(file_name)
            return True
        except Exception as e:
            logger.error(f"Failed to delete session file: {str(e)}")
            return False
    
    def get_all(self) -> Dict[str, Dict]:
        """
        Get all sessions.
        
        Returns:
            dict: Dictionary of session ID to session data
        """
        sessions = {}
        
        try:
            for file_name in os.listdir(self.file_path):
                if file_name.endswith(".json"):
                    session_id = file_name[:-5]  # Remove ".json" extension
                    session_data = self.get(session_id)
                    if session_data:
                        sessions[session_id] = session_data
            return sessions
        except Exception as e:
            logger.error(f"Failed to get all sessions: {str(e)}")
            return {}