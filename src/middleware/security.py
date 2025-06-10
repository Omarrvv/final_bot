"""
Security middleware components for the Egypt Tourism Chatbot API.

This module consolidates security-related middleware functionality including:
- CORS (Cross-Origin Resource Sharing) configuration
- CSRF (Cross-Site Request Forgery) protection
- Security headers and validation

Replaces: cors.py, csrf.py
"""

import logging
import secrets
from typing import List, Optional, Sequence

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

# Configure logger
logger = logging.getLogger(__name__)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware for the application.
    
    Consolidates csrf.py functionality with enhanced security features.
    """

    def __init__(
        self,
        app: ASGIApp,
        secret: str,
        exclude_urls: Optional[List[str]] = None,
        cookie_secure: bool = True,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
    ):
        super().__init__(app)
        self.secret = secret
        self.exclude_urls = set(exclude_urls or [])
        self.cookie_secure = cookie_secure
        self.cookie_name = cookie_name
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        """Process request with CSRF protection."""
        # Skip CSRF protection for safe methods and excluded URLs
        if (
            request.method in ["GET", "HEAD", "OPTIONS", "TRACE"] or
            request.url.path in self.exclude_urls or
            any(request.url.path.startswith(exclude) for exclude in self.exclude_urls)
        ):
            return await call_next(request)

        # Check CSRF token for state-changing methods
        if not self._validate_csrf_token(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token validation failed"
            )

        response = await call_next(request)
        
        # Set CSRF token cookie if not present
        if self.cookie_name not in request.cookies:
            csrf_token = self._generate_csrf_token()
            response.set_cookie(
                key=self.cookie_name,
                value=csrf_token,
                secure=self.cookie_secure,
                httponly=True,
                samesite="strict"
            )

        return response

    def _validate_csrf_token(self, request: Request) -> bool:
        """Validate CSRF token from header against cookie."""
        cookie_token = request.cookies.get(self.cookie_name)
        header_token = request.headers.get(self.header_name)

        if not cookie_token or not header_token:
            return False

        return secrets.compare_digest(cookie_token, header_token)

    def _generate_csrf_token(self) -> str:
        """Generate a secure CSRF token."""
        return secrets.token_urlsafe(32)


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
    Add CORS middleware to the FastAPI application.
    
    Consolidates and enhances cors.py functionality.
    
    Args:
        app: FastAPI application instance
        allowed_origins: List of allowed origins (defaults to common development origins)
        allowed_methods: List of allowed HTTP methods
        allowed_headers: List of allowed headers
        allow_credentials: Whether to allow credentials
        allow_origin_regex: Regex pattern for allowed origins
        max_age: Max age for preflight requests in seconds
    """
    # Default configurations
    if allowed_origins is None:
        allowed_origins = get_default_origins()
    
    if allowed_methods is None:
        allowed_methods = [
            "DELETE",
            "GET", 
            "POST",
            "PUT",
            "PATCH",
            "OPTIONS"
        ]
    
    if allowed_headers is None:
        allowed_headers = [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-Request-ID",
            "X-CSRF-Token",
            "Cache-Control",
            "Pragma"
        ]

    # Log CORS configuration
    logger.info(
        f"Configuring CORS middleware with {len(allowed_origins)} origins, "
        f"{len(allowed_methods)} methods, {len(allowed_headers)} headers"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=allowed_methods,
        allow_headers=allowed_headers,
        allow_origin_regex=allow_origin_regex,
        max_age=max_age,
    )


def add_csrf_middleware(
    app: FastAPI,
    secret: str,
    exclude_urls: Optional[List[str]] = None,
    cookie_secure: bool = True,
) -> None:
    """
    Add CSRF protection middleware to the FastAPI application.
    
    Args:
        app: FastAPI application instance
        secret: Secret key for CSRF token generation
        exclude_urls: URLs to exclude from CSRF protection
        cookie_secure: Whether to set secure flag on CSRF cookies
    """
    if exclude_urls is None:
        exclude_urls = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
            "/api/auth/session",  # Allow session creation without CSRF
        ]

    logger.info(f"Configuring CSRF protection with {len(exclude_urls)} excluded URLs")

    app.add_middleware(
        CSRFProtectionMiddleware,
        secret=secret,
        exclude_urls=exclude_urls,
        cookie_secure=cookie_secure,
    )


def add_security_headers_middleware(app: FastAPI) -> None:
    """
    Add security headers middleware to the application.
    
    Args:
        app: FastAPI application instance
    """
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy (CSP)
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        return response

    logger.info("Added security headers middleware")


def add_trusted_host_middleware(
    app: FastAPI,
    allowed_hosts: Optional[Sequence[str]] = None,
    www_redirect: bool = True
) -> None:
    """
    Add trusted host middleware to prevent Host header attacks.
    
    Args:
        app: FastAPI application instance
        allowed_hosts: Sequence of allowed hostnames
        www_redirect: Whether to redirect www to non-www
    """
    if allowed_hosts is None:
        allowed_hosts = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "*.localhost",
            "*.local"
        ]

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts,
        www_redirect=www_redirect
    )

    logger.info(f"Added trusted host middleware with {len(allowed_hosts)} allowed hosts")


def get_default_origins(frontend_url: Optional[str] = None) -> List[str]:
    """
    Get default CORS origins for development and production.
    
    Enhanced version from cors.py with additional origins.
    
    Args:
        frontend_url: Optional frontend URL to include
        
    Returns:
        List of default allowed origins
    """
    origins = [
        # Local development
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:5000",
        "http://localhost:5050",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5050",
        "http://127.0.0.1:8000",
        
        # Development with different ports
        "http://localhost:4200",  # Angular dev server
        "http://localhost:8080",  # Vue dev server
        "http://localhost:9000",  # Other common dev port
        
        # Mobile development
        "http://10.0.2.2:3000",  # Android emulator
        "http://192.168.1.100:3000",  # Local network
    ]
    
    if frontend_url:
        origins.append(frontend_url)
    
    return origins


def add_all_security_middleware(
    app: FastAPI,
    secret: str,
    allowed_origins: Optional[List[str]] = None,
    allowed_hosts: Optional[Sequence[str]] = None,
    enable_csrf: bool = True,
    csrf_exclude_urls: Optional[List[str]] = None,
    cookie_secure: bool = False,  # Default to False for development
    frontend_url: Optional[str] = None
) -> None:
    """
    Add all security middleware to the FastAPI application.
    
    This is a convenience function that configures all security middleware
    with sensible defaults.
    
    Args:
        app: FastAPI application instance
        secret: Secret key for CSRF protection
        allowed_origins: CORS allowed origins
        allowed_hosts: Trusted host allowed hosts
        enable_csrf: Whether to enable CSRF protection
        csrf_exclude_urls: URLs to exclude from CSRF protection
        cookie_secure: Whether to use secure cookies
        frontend_url: Frontend URL to add to CORS origins
    """
    logger.info("Configuring comprehensive security middleware")
    
    # Add security headers (should be first)
    add_security_headers_middleware(app)
    
    # Add trusted host middleware
    add_trusted_host_middleware(app, allowed_hosts)
    
    # Add CORS middleware
    add_cors_middleware(
        app, 
        allowed_origins=allowed_origins or get_default_origins(frontend_url)
    )
    
    # Add CSRF protection if enabled
    if enable_csrf:
        add_csrf_middleware(
            app,
            secret=secret,
            exclude_urls=csrf_exclude_urls,
            cookie_secure=cookie_secure
        )
    
    logger.info("Security middleware configuration completed") 