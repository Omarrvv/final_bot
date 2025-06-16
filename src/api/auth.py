"""
Authentication API

This module provides authentication endpoints for the FastAPI application.
Uses lightweight session-based authentication without requiring user accounts.
"""
from fastapi import APIRouter, Depends, Response, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any

from src.utils.logger import get_logger
from src.api.dependencies import get_session_auth
from src.services.auth_service import SessionAuth

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class SessionRequest(BaseModel):
    """Session request schema."""
    metadata: Optional[Dict[str, Any]] = None
    remember_me: Optional[bool] = False


class SessionResponse(BaseModel):
    """Session response schema."""
    session_id: str
    token: str
    token_type: str = "bearer"
    expires_in: int


class MessageResponse(BaseModel):
    """Generic message response schema."""
    message: str


@router.post("/session", response_model=SessionResponse)
async def create_session(
    request: SessionRequest,
    response: Response,
    session_auth: SessionAuth = Depends(get_session_auth),
):
    """
    Create an anonymous session.

    Args:
        request: Session request data
        response: FastAPI response object
        session_auth: Session authentication service

    Returns:
        Session response with session ID and token
    """
    # Get metadata from request or use empty dict
    metadata = request.metadata or {}

    # Add user agent and IP address to metadata if available
    try:
        # These would be added by middleware in a real app
        metadata["user_agent"] = "Web Browser"
        metadata["ip_address"] = "127.0.0.1"
    except Exception as e:
        logger.warning(f"Failed to add request metadata: {str(e)}")

    # Create an anonymous session
    session_result = session_auth.create_anonymous_session(metadata)

    if not session_result or not session_result.get("success"):
        logger.error("Failed to create anonymous session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session",
        )

    # Set session cookie
    token = session_result.get("token")
    if token and response:
        # Set cookie TTL based on remember_me flag
        max_age = 30 * 24 * 3600 if request.remember_me else 24 * 3600  # 30 days or 1 day

        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=max_age,
        )

    logger.info(f"Created anonymous session: {session_result.get('session_id')}")

    # Return session information
    return SessionResponse(
        session_id=session_result.get("session_id"),
        token=token,
        token_type=session_result.get("token_type", "bearer"),
        expires_in=session_result.get("expires_in", 24 * 3600),  # Default 24 hours
    )


@router.post("/end-session", response_model=MessageResponse)
async def end_session(
    response: Response,
    request: Request,
    session_auth: SessionAuth = Depends(get_session_auth),
    token: Optional[str] = None,
):
    """
    End a session by invalidating the token.

    Args:
        response: FastAPI response object
        request: FastAPI request object
        session_auth: Session authentication service
        token: Optional session token (if not provided, use the cookie)

    Returns:
        Success message
    """
    # Get the token from the cookie if not provided
    if not token:
        token = request.cookies.get("session_token")

    # End the session
    if token:
        success = session_auth.end_session(token)

        # Clear the session cookie
        response.delete_cookie(
            key="session_token",
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
        )

        if success:
            logger.info("Session ended successfully")
            return MessageResponse(message="Session ended successfully")

    # Return success even if token wasn't found to avoid leaking information
    logger.warning("No valid session token found for end-session request")
    return MessageResponse(message="Session ended successfully")


@router.post("/validate-session")
async def validate_session(
    request: Request,
    session_auth: SessionAuth = Depends(get_session_auth),
    token: Optional[str] = None,
):
    """
    Validate a session token.

    Args:
        request: FastAPI request object
        session_auth: Session authentication service
        token: Optional session token (if not provided, use the cookie)

    Returns:
        Session data if valid, error if invalid
    """
    # Get the token from the cookie if not provided
    if not token:
        token = request.cookies.get("session_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session token provided",
        )

    # Validate the session
    session_data = session_auth.validate_session(token)

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token",
        )

    # Return session data
    return {
        "valid": True,
        "session_id": session_data.get("session_id"),
        "created_at": session_data.get("created_at"),
        "last_accessed": session_data.get("last_accessed"),
    }


@router.post("/refresh-session", response_model=SessionResponse)
async def refresh_session(
    response: Response,
    request: Request,
    session_auth: SessionAuth = Depends(get_session_auth),
    token: Optional[str] = None,
):
    """
    Refresh a session token.

    Args:
        response: FastAPI response object
        request: FastAPI request object
        session_auth: Session authentication service
        token: Optional session token (if not provided, use the cookie)

    Returns:
        New session token
    """
    # Get the token from the cookie if not provided
    if not token:
        token = request.cookies.get("session_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session token provided",
        )

    # Refresh the session
    refresh_result = session_auth.refresh_session(token)

    if not refresh_result or not refresh_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh session",
        )

    # Set the new token in the cookie
    new_token = refresh_result.get("token")
    if new_token and response:
        response.set_cookie(
            key="session_token",
            value=new_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=refresh_result.get("expires_in", 24 * 3600),
        )

    logger.info(f"Refreshed session: {refresh_result.get('session_id')}")

    # Return the new token
    return SessionResponse(
        session_id=refresh_result.get("session_id"),
        token=new_token,
        token_type=refresh_result.get("token_type", "bearer"),
        expires_in=refresh_result.get("expires_in", 24 * 3600),
    )