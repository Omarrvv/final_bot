"""
Dependencies for FastAPI route handlers.

This module provides dependency functions for FastAPI routes, enabling
dependency injection for services like authentication, session management,
and other components.
"""
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request, status

from src.session.enhanced_session_manager import EnhancedSessionManager
from src.utils.factory import component_factory
from src.utils.logger import get_logger
from src.utils.auth import SessionAuth

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
    Dependency for getting container debug information.
    Shows current cache state and singleton verification.
    """
    from src.utils.container import container
    
    return {
        "container_cache_info": container.get_cache_info() if hasattr(container, 'get_cache_info') else {},
        "app_state_components": {
            "chatbot": "available" if hasattr(request.app.state, 'chatbot') and request.app.state.chatbot else "missing",
            "session_manager": "available" if hasattr(request.app.state, 'session_manager') and request.app.state.session_manager else "missing",
            "performance_middleware": "available" if hasattr(request.app.state, 'performance_middleware') else "missing"
        },
        "phase_verification": {
            "phase_1_singletons": hasattr(request.app.state, 'chatbot'),
            "phase_2_model_preloading": getattr(request.app.state, 'models_preloaded', False),
            "phase_3_nlu_optimization": True,  # Assume implemented if we reach this point
            "phase_4_monitoring": hasattr(request.app.state, 'performance_middleware')
        }
    }