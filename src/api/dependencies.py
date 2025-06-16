"""
Dependencies for FastAPI route handlers.

This module provides dependency functions for FastAPI routes, enabling
dependency injection for services like authentication, session management,
and other components.
"""
from typing import Any, Dict, Optional
import time

from fastapi import Depends, HTTPException, Request, status

# PHASE 0C FIX: Remove direct imports from higher layers to maintain architectural boundaries
# from src.session.enhanced_session_manager import EnhancedSessionManager  # Moved to lazy import
# from src.services.component_factory import component_factory  # Moved to lazy import
from src.utils.logger import get_logger
from src.services.auth_service import SessionAuth

logger = get_logger(__name__)


def get_session_service(request: Request):
    """
    Dependency for getting the session service from app.state singleton.

    Args:
        request: FastAPI request object

    Returns:
        Session manager instance (from app.state)
    """
    if not hasattr(request.app.state, 'session_manager') or not request.app.state.session_manager:
        logger.error("Session manager not found in app.state")
        raise HTTPException(status_code=503, detail="Session service unavailable")
    return request.app.state.session_manager


def get_session_auth(request: Request) -> SessionAuth:
    """
    Dependency for getting the SessionAuth service from app.state singleton.

    Args:
        request: FastAPI request object

    Returns:
        SessionAuth instance with session manager from app.state
    """
    # Get the session manager from app.state
    session_manager = get_session_service(request)

    # Create and return a SessionAuth instance with the session manager
    return SessionAuth(session_manager=session_manager)


def get_chatbot(request: Request):
    """
    Dependency for getting the chatbot instance from app.state singleton.

    Args:
        request: FastAPI request object

    Returns:
        Chatbot instance from app.state
    """
    if not hasattr(request.app.state, 'chatbot') or not request.app.state.chatbot:
        logger.error("Chatbot not found in app.state")
        raise HTTPException(status_code=503, detail="Chatbot service unavailable")
    return request.app.state.chatbot


def get_knowledge_base(request: Request):
    """
    Dependency for getting the knowledge base from app.state singleton.

    Args:
        request: FastAPI request object

    Returns:
        KnowledgeBase instance from chatbot in app.state
    """
    chatbot = get_chatbot(request)
    if not hasattr(chatbot, 'knowledge_base') or not chatbot.knowledge_base:
        logger.error("Knowledge base not found in chatbot")
        raise HTTPException(status_code=503, detail="Knowledge base service unavailable")
    return chatbot.knowledge_base


def get_nlu_engine(request: Request):
    """
    Dependency for getting the NLU engine from app.state singleton.

    Args:
        request: FastAPI request object

    Returns:
        NLU engine instance from chatbot in app.state
    """
    chatbot = get_chatbot(request)
    if not hasattr(chatbot, 'nlu_engine') or not chatbot.nlu_engine:
        logger.error("NLU engine not found in chatbot")
        raise HTTPException(status_code=503, detail="NLU engine service unavailable")
    return chatbot.nlu_engine


def get_database_manager(request: Request):
    """
    Dependency for getting the database manager from app.state singleton.

    Args:
        request: FastAPI request object

    Returns:
        Database manager instance from chatbot in app.state
    """
    chatbot = get_chatbot(request)
    if not hasattr(chatbot, 'db_manager') or not chatbot.db_manager:
        logger.error("Database manager not found in chatbot")
        raise HTTPException(status_code=503, detail="Database service unavailable")
    return chatbot.db_manager


# --- PHASE 5: LEGACY CODE REMOVED ---
# All deprecated factory-based dependencies have been removed as part of Phase 5 cleanup.
# Only optimized singleton dependencies remain.


# --- AUTHENTICATION DEPENDENCIES ---

def require_auth(request: Request) -> Dict[str, Any]:
    """
    Dependency for requiring authentication.

    This dependency function extracts user information from the request scope
    and raises an exception if the user is not authenticated.

    Args:
        request: FastAPI request object

    Returns:
        Authenticated user data

    Raises:
        HTTPException: If authentication fails or user is not found in request scope
    """
    # Check if user exists in request scope (set by AuthMiddleware)
    if not hasattr(request, "scope") or "user" not in request.scope:
        logger.warning("Authentication required but user not found in request scope")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    # Get user from request scope
    user = request.scope.get("user")

    # Check if user is authenticated
    if not hasattr(user, "is_authenticated") or not user.is_authenticated:
        logger.warning("Unauthenticated user tried to access protected route")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    # Return user data as dictionary
    return {
        "user_id": user.user_id,
        "username": user.username,
        "data": user.data,
    }


def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Dependency for optionally getting authenticated user.

    This dependency function extracts user information from the request scope
    but does not raise an exception if the user is not authenticated.

    Args:
        request: FastAPI request object

    Returns:
        Authenticated user data or None if not authenticated
    """
    # Check if user exists in request scope
    if not hasattr(request, "scope") or "user" not in request.scope:
        return None

    # Get user from request scope
    user = request.scope.get("user")

    # Check if user is authenticated
    if not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return None

    # Return user data as dictionary
    return {
        "user_id": user.user_id,
        "username": user.username,
        "data": user.data,
    }


# --- DEBUG DEPENDENCIES ---

def get_container_debug_info(request: Request) -> Dict[str, Any]:
    """
    Debugging endpoint dependency for checking container state.
    
    Shows current cache state and singleton verification.
    """
    from src.core.container import container
    
    return {
        "debug_info": container.get_cache_info(),
        "timestamp": time.time()
    }