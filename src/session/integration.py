"""
Session Manager Integration

This module provides functions to integrate the enhanced session manager into the application.
It handles the transition from the old session management to the new enhanced session manager.
"""

import os
import logging
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware

from src.session.enhanced_session_manager import EnhancedSessionManager
from src.config_unified import settings

# Configure logging
logger = logging.getLogger(__name__)

def integrate_enhanced_session_manager(app: FastAPI) -> EnhancedSessionManager:
    """
    Integrate the enhanced session manager into the FastAPI application.
    
    Args:
        app (FastAPI): The FastAPI application
        
    Returns:
        EnhancedSessionManager: The enhanced session manager instance
    """
    try:
        # Get Redis URI from environment
        redis_uri = os.environ.get("REDIS_URI", "redis://localhost:6379/0")
        
        # Get session TTL from environment (default: 7 days)
        session_ttl = int(os.environ.get("SESSION_TTL", 604800))
        
        # Create enhanced session manager
        session_manager = EnhancedSessionManager(redis_uri=redis_uri, ttl=session_ttl)
        
        # Store in app state
        app.state.enhanced_session_manager = session_manager
        
        # Add session middleware
        app.add_middleware(
            SessionMiddleware,
            session_manager=session_manager,
            cookie_name=settings.session_cookie_name,
            cookie_secure=settings.session_cookie_secure
        )
        
        logger.info("Enhanced session manager integrated successfully")
        return session_manager
    
    except Exception as e:
        logger.error(f"Failed to integrate enhanced session manager: {e}")
        raise

class SessionMiddleware:
    """
    Middleware to handle session management.
    
    This middleware:
    1. Extracts the session ID from the request cookie
    2. Loads the session data if a valid session ID is found
    3. Creates a new session if no valid session ID is found
    4. Attaches the session data to the request state
    5. Updates the session cookie in the response
    """
    
    def __init__(
        self,
        app: FastAPI,
        session_manager: EnhancedSessionManager,
        cookie_name: str = "session_id",
        cookie_secure: bool = False
    ):
        """
        Initialize the session middleware.
        
        Args:
            app (FastAPI): The FastAPI application
            session_manager (EnhancedSessionManager): The session manager instance
            cookie_name (str, optional): The name of the session cookie. Defaults to "session_id".
            cookie_secure (bool, optional): Whether to set the secure flag on the cookie. Defaults to False.
        """
        self.app = app
        self.session_manager = session_manager
        self.cookie_name = cookie_name
        self.cookie_secure = cookie_secure
    
    async def __call__(self, request: Request, call_next):
        """
        Process the request and response.
        
        Args:
            request (Request): The FastAPI request
            call_next: The next middleware or route handler
            
        Returns:
            Response: The FastAPI response
        """
        # Extract session ID from cookie
        session_id = request.cookies.get(self.cookie_name)
        
        # Get session data if session ID exists
        session_data = None
        if session_id:
            session_data = self.session_manager.get_session(session_id)
        
        # Create new session if no valid session found
        if not session_data:
            # Get client info for metadata
            metadata = self._get_client_info(request)
            
            # Create new session
            session_id = self.session_manager.create_session(metadata=metadata)
            session_data = self.session_manager.get_session(session_id)
        
        # Attach session to request state
        request.state.session_id = session_id
        request.state.session_data = session_data
        
        # Process the request
        response = await call_next(request)
        
        # Set session cookie in response
        if session_id:
            response.set_cookie(
                key=self.cookie_name,
                value=session_id,
                httponly=True,
                secure=self.cookie_secure,
                samesite="lax",
                max_age=self.session_manager.ttl
            )
        
        return response
    
    def _get_client_info(self, request: Request) -> Dict[str, Any]:
        """
        Get client information from the request.
        
        Args:
            request (Request): The FastAPI request
            
        Returns:
            Dict[str, Any]: Client information
        """
        return {
            "user_agent": request.headers.get("user-agent", ""),
            "ip_address": request.client.host if request.client else "",
            "language": request.headers.get("accept-language", ""),
            "referer": request.headers.get("referer", "")
        }

def get_session_data(request: Request) -> Optional[Dict[str, Any]]:
    """
    Dependency to get session data from request state.
    
    Args:
        request (Request): The FastAPI request
        
    Returns:
        Optional[Dict[str, Any]]: Session data or None if not found
    """
    return getattr(request.state, "session_data", None)

def get_session_id(request: Request) -> Optional[str]:
    """
    Dependency to get session ID from request state.
    
    Args:
        request (Request): The FastAPI request
        
    Returns:
        Optional[str]: Session ID or None if not found
    """
    return getattr(request.state, "session_id", None)

def get_session_manager(request: Request) -> EnhancedSessionManager:
    """
    Dependency to get session manager from app state.
    
    Args:
        request (Request): The FastAPI request
        
    Returns:
        EnhancedSessionManager: Session manager instance
    """
    return request.app.state.enhanced_session_manager

def add_message_to_session(
    session_id: str,
    role: str,
    content: str,
    session_manager: EnhancedSessionManager = None,
    request: Request = None
) -> bool:
    """
    Add a message to the session.
    
    Args:
        session_id (str): Session ID
        role (str): Message role (user, assistant)
        content (str): Message content
        session_manager (EnhancedSessionManager, optional): Session manager instance. Defaults to None.
        request (Request, optional): FastAPI request. Defaults to None.
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get session manager
    if not session_manager and request:
        session_manager = get_session_manager(request)
    
    if not session_manager:
        logger.error("No session manager available")
        return False
    
    # Add message to session
    return session_manager.add_message_to_session(session_id, role, content)

def get_session_messages(
    session_id: str,
    session_manager: EnhancedSessionManager = None,
    request: Request = None
) -> List[Dict[str, Any]]:
    """
    Get messages from the session.
    
    Args:
        session_id (str): Session ID
        session_manager (EnhancedSessionManager, optional): Session manager instance. Defaults to None.
        request (Request, optional): FastAPI request. Defaults to None.
        
    Returns:
        List[Dict[str, Any]]: Session messages
    """
    # Get session manager
    if not session_manager and request:
        session_manager = get_session_manager(request)
    
    if not session_manager:
        logger.error("No session manager available")
        return []
    
    # Get messages from session
    return session_manager.get_session_messages(session_id)
