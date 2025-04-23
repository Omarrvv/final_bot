"""
CSRF Middleware Configuration for FastAPI using starlette-csrf.

This module provides functions for configuring CSRF protection middleware
in FastAPI applications with secure defaults.
"""
from typing import List, Optional, Callable
import re

from fastapi import FastAPI, Request, Response
from starlette_csrf import CSRFMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.logger import get_logger

logger = get_logger(__name__)


def add_csrf_middleware(
    app: FastAPI,
    secret: str,
    exclude_urls: Optional[List[str]] = None,
    cookie_secure: bool = True,
) -> None:
    """
    Add CSRF middleware to a FastAPI application.
    
    Args:
        app: FastAPI application instance
        secret: Secret key for CSRF token generation
        exclude_urls: URLs to exclude from CSRF protection
        cookie_secure: Whether cookie should use secure flag
    """
    # Get default exclude URLs if not provided
    if exclude_urls is None:
        exclude_urls = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/health",
            "/api/csrf-token"
        ]
    
    # Convert string patterns to regex patterns
    exempt_urls = [re.compile(f"^{pattern}") for pattern in exclude_urls]
    
    # Add CSRF middleware directly
    app.add_middleware(
        CSRFMiddleware,
        secret=secret,
        cookie_secure=cookie_secure,
        cookie_samesite="lax",
        cookie_path="/",
        header_name="X-CSRF-Token",
        cookie_name="csrftoken",
        safe_methods={"GET", "HEAD", "OPTIONS", "TRACE"},
        exempt_urls=exempt_urls,
    )
    
    logger.info("CSRF protection middleware added")
    if exclude_urls:
        logger.info(f"CSRF protection excluded for: {exclude_urls}") 