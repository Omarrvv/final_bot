"""
CORS Middleware Configuration for FastAPI

This module provides functions for configuring CORS (Cross-Origin Resource Sharing)
middleware in FastAPI applications with secure defaults.
"""
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.utils.logger import get_logger

logger = get_logger(__name__)


def add_cors_middleware(
    app: FastAPI,
    allowed_origins: Optional[List[str]] = None,
    allowed_methods: Optional[List[str]] = None,
    allowed_headers: Optional[List[str]] = None,
    allow_credentials: bool = True,
    allow_origin_regex: Optional[str] = None,
    max_age: int = 600,
) -> None:
    """
    Add CORS middleware to a FastAPI application with secure defaults.
    
    Args:
        app: FastAPI application instance
        allowed_origins: List of allowed origins (e.g., ["http://localhost:3000", "https://yourdomain.com"])
            If None, defaults to an empty list (no origins allowed)
        allowed_methods: List of allowed HTTP methods
            If None, defaults to ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        allowed_headers: List of allowed HTTP headers
            If None, defaults to standard headers + X-Request-ID and Content-Type
        allow_credentials: Whether to allow credentials (cookies, etc.)
        allow_origin_regex: Regular expression to match allowed origins
            Use this with caution and only when specific origins aren't feasible
        max_age: Maximum age (in seconds) of preflight requests cache
    
    Note:
        This function follows security best practices:
        - Never uses "*" for allowed_origins in production
        - Sets reasonable defaults for allowed methods and headers
        - Enables credentials for established origins
    """
    # Security check: if no allowed origins are provided, default to an empty list
    # rather than allowing all origins with "*"
    if allowed_origins is None:
        allowed_origins = []
        logger.warning("No allowed origins specified for CORS. All origins will be blocked.")
    
    # Enhanced wildcard handling - If "*" is in allowed_origins, use regex instead
    # This ensures that the specific requesting origin is returned in the header
    # rather than the literal "*", which is more secure with credentials
    final_allowed_origins = allowed_origins
    final_origin_regex = allow_origin_regex
    
    if "*" in allowed_origins:
        logger.warning(
            "SECURITY WARNING: CORS is configured to allow ALL origins ('*'). "
            "This is not recommended for production environments. "
            "Consider specifying explicit allowed origins instead."
        )
        
        # When wildcard is used, use regex to match all origins but return the specific origin
        # that made the request, rather than literal "*" in the Access-Control-Allow-Origin header
        if allow_credentials:
            # If credentials are allowed, we MUST use regex to return the specific origin
            # because browsers reject "*" with credentials
            final_allowed_origins = []  # Clear the list to avoid using "*"
            final_origin_regex = ".*"   # Match any origin with regex
    
    # Default allowed methods if not provided
    if allowed_methods is None:
        allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    
    # Default allowed headers if not provided
    if allowed_headers is None:
        allowed_headers = [
            "Authorization",
            "X-Request-ID",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
        ]
    
    # Add the CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=final_allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=allowed_methods,
        allow_headers=allowed_headers,
        allow_origin_regex=final_origin_regex,
        max_age=max_age,
    )
    
    # Log configuration
    if final_allowed_origins:
        logger.info(f"CORS middleware added with allowed origins: {final_allowed_origins}")
    elif final_origin_regex:
        logger.info(f"CORS middleware added with origin regex: {final_origin_regex}")
    else:
        logger.info("CORS middleware added with no allowed origins")


def get_default_origins(frontend_url: Optional[str] = None) -> List[str]:
    """
    Get default allowed origins for different environments.
    
    Args:
        frontend_url: URL of the frontend application if specified in configuration
        
    Returns:
        List of default allowed origins
    """
    # Start with local development origins
    origins = [
        "http://localhost",
        "http://localhost:3000",  # React default
        "http://localhost:8000",  # Backend (if serving frontend)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    
    # Add frontend URL if provided
    if frontend_url:
        origins.append(frontend_url)
        
        # If frontend_url has a www subdomain, also allow non-www
        if frontend_url.startswith("https://www."):
            non_www_url = frontend_url.replace("https://www.", "https://")
            origins.append(non_www_url)
        # If frontend_url doesn't have a www subdomain, also allow www
        elif frontend_url.startswith("https://") and not frontend_url.startswith("https://www."):
            www_url = frontend_url.replace("https://", "https://www.")
            origins.append(www_url)
    
    return origins 