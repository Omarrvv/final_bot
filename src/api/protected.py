"""
Protected API Endpoints

This module provides protected API endpoints that require authentication.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, List

from src.utils.dependencies import require_auth
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/protected", tags=["Protected"])


class UserProfileResponse(BaseModel):
    """User profile response schema."""
    user_id: int
    username: str
    roles: List[str]


class ApiKeyResponse(BaseModel):
    """API key response schema."""
    key: str
    name: str
    created_at: str
    expires_at: str


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(user: Dict[str, Any] = Depends(require_auth)):
    """
    Get the authenticated user's profile.

    Args:
        user: Authenticated user data

    Returns:
        User profile data
    """
    logger.info(f"Profile accessed by user: {user['username']}")

    return UserProfileResponse(
        user_id=user["user_id"],
        username=user["username"],
        roles=user["data"].get("roles", []),
    )


@router.get("/keys", response_model=List[ApiKeyResponse])
async def get_api_keys(user: Dict[str, Any] = Depends(require_auth)):
    """
    Get the authenticated user's API keys.

    Args:
        user: Authenticated user data

    Returns:
        List of API keys
    """
    logger.info(f"API keys accessed by user: {user['username']}")

    # In a real application, you would fetch the API keys from a database
    # This is a simple example that returns mock data
    return [
        ApiKeyResponse(
            key="key_1234567890",
            name="Default API Key",
            created_at="2023-01-01T00:00:00Z",
            expires_at="2024-01-01T00:00:00Z",
        ),
        ApiKeyResponse(
            key="key_0987654321",
            name="Secondary API Key",
            created_at="2023-06-01T00:00:00Z",
            expires_at="2024-06-01T00:00:00Z",
        ),
    ]