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


def get_session_service():
    """
    Dependency for getting the session service.

    Returns:
        Session manager instance (from component factory)
    """
    return component_factory.get_session_service()


def get_session_auth() -> SessionAuth:
    """
    Dependency for getting the SessionAuth service.

    Returns:
        SessionAuth instance with session manager
    """
    # Get the session manager from the component factory
    session_manager = component_factory.get_session_service()

    # Create and return a SessionAuth instance with the session manager
    return SessionAuth(session_manager=session_manager)


def get_chatbot():
    """
    Dependency for getting the chatbot instance.

    Returns:
        Chatbot instance
    """
    return component_factory.create_chatbot()


def get_knowledge_base():
    """
    Dependency for getting the knowledge base.

    Returns:
        KnowledgeBase instance
    """
    return component_factory.create_knowledge_base()


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