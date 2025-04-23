"""
Authentication Middleware for FastAPI

This module provides middleware for handling authentication and session management
in FastAPI applications. It validates session tokens and attaches user information
to requests.
"""
from typing import Callable, Dict, Optional, Union, List, Any, Tuple
import os
import re
import time
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    BaseUser,
    AuthenticationError,
    UnauthenticatedUser,
    SimpleUser,
)
from starlette.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.services.session import SessionService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class User(BaseUser):
    def __init__(self, user_id: str, username: str, role: str = "user"):
        self.user_id = user_id
        self.username = username
        self.role = role
        self._is_authenticated = True

    def __str__(self) -> str:
        return f"User(id={self.user_id}, username={self.username}, role={self.role})"
        
    @property
    def display_name(self) -> str:
        return self.username
        
    @property
    def identity(self) -> str:
        return self.user_id
        
    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated
        
    @is_authenticated.setter
    def is_authenticated(self, value: bool):
        self._is_authenticated = value


class UnauthenticatedUserImpl(UnauthenticatedUser):
    @property
    def display_name(self) -> str:
        return "Guest"
        
    @property
    def identity(self) -> str:
        return ""


class SessionAuthBackend:
    def __init__(self, session_service, public_paths: List[str] = None, testing_mode: bool = None):
        self.session_service = session_service
        self.public_paths = [re.compile(f"^{path}$", re.IGNORECASE) for path in (public_paths or ["/public", "/api/public"])]
        
        # Safely check testing mode
        testing_env = os.getenv("TESTING", "")
        self.testing_mode = testing_mode or (testing_env and testing_env.lower() == "true")
        
        self.security = HTTPBearer(auto_error=False)
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.rate_limit_window = timedelta(minutes=1)
        self.rate_limit_max_requests = 60

        if self.testing_mode:
            logger.info("Testing mode detected for SessionAuthBackend")

    async def authenticate(self, request: Request) -> Tuple[AuthCredentials, BaseUser]:
        """
        Authenticate the request.
        
        Args:
            request: The request to authenticate
            
        Returns:
            Tuple of AuthCredentials and User
        """
        try:
            # In testing mode, either bypass authentication or use a test user
            if self.testing_mode:
                logger.info("Authentication bypassed in test mode")
                # Support test-specific user ID if provided
                user_id = getattr(request, "user_id_for_testing", "test_user_1")
                # Return a test user for authenticated endpoints
                user = User(
                    user_id=user_id,
                    username="test_user",
                    role="user"
                )
                return AuthCredentials(["authenticated"]), user
                
            # Check if path is public
            path = request.url.path.lower().rstrip('/') if request.url.path else ""
            if any(pattern.match(path) for pattern in self.public_paths):
                return AuthCredentials([]), UnauthenticatedUserImpl()

            # Check for session cookie
            session_token = request.cookies.get("session_token")
            if session_token:
                user = await self._validate_session_token(session_token)
                return AuthCredentials(["authenticated"]), user

            # Check for bearer token
            auth = await self.security(request)
            if auth and auth.credentials:
                user = await self._validate_session_token(auth.credentials)
                return AuthCredentials(["authenticated"]), user

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        except HTTPException as e:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def _validate_session_token(self, token: str) -> User:
        try:
            # Testing mode bypass - add proper check and return test user
            if self.testing_mode:
                logger.info("Bypassing token validation in testing mode")
                return User(
                    user_id="test_user_1",
                    username="testuser",
                    role="user"
                )
                
            # Check rate limiting
            if not self._check_rate_limit(token):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )

            # Validate session
            session_data = await self.session_service.validate_session(token)
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid session token"
                )

            # Validate session data format
            if not isinstance(session_data, dict):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid session data format"
                )

            required_fields = ["user_id", "username"]
            if not all(field in session_data for field in required_fields):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing required session data fields"
                )

            return User(
                user_id=session_data["user_id"],
                username=session_data["username"],
                role=session_data.get("role", "user")
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session validation failed"
            )

    def _check_rate_limit(self, token: str) -> bool:
        now = datetime.now()
        
        # Clean up expired entries
        self.rate_limits = {
            t: times for t, times in self.rate_limits.items()
            if any(time > now - self.rate_limit_window for time in times)
        }
        
        # Get request times for this token
        times = self.rate_limits.get(token, [])
        times = [time for time in times if time > now - self.rate_limit_window]
        
        # Check if limit exceeded
        if len(times) >= self.rate_limit_max_requests:
            return False
            
        # Update times
        times.append(now)
        self.rate_limits[token] = times
        return True


class AuthMiddleware:
    def __init__(self, auth_backend: SessionAuthBackend):
        self.auth_backend = auth_backend

    async def __call__(self, request: Request, call_next):
        try:
            credentials, user = await self.auth_backend.authenticate(request)
            request.scope["user"] = user
            response = await call_next(request)
            return response
        except HTTPException as e:
            return self._create_error_response(e.status_code, e.detail, e.headers)
        except Exception as e:
            logger.error(f"Authentication error in dispatch: {str(e)}")
            return self._create_error_response(
                status.HTTP_401_UNAUTHORIZED,
                "Authentication failed",
                {"WWW-Authenticate": "Bearer"}
            )

    def _create_error_response(self, status_code: int, detail: str, headers: Dict[str, str] = None):
        return JSONResponse(
            status_code=status_code,
            content={"detail": detail},
            headers=headers or {}
        )


def add_auth_middleware(app, session_service, public_paths: List[str] = None, testing_mode: bool = False):
    # Check environment variable for testing mode
    testing_env = os.getenv("TESTING", "")
    testing_mode = testing_mode or (testing_env and testing_env.lower() == "true")
    
    # Add more public paths for testing if needed
    if testing_mode and public_paths is None:
        public_paths = ["/public", "/api/public", "/api/health"]
    
    auth_backend = SessionAuthBackend(
        session_service=session_service,
        public_paths=public_paths,
        testing_mode=testing_mode
    )
    
    # Use middleware decorator
    app.middleware("http")(AuthMiddleware(auth_backend))
    
    logger.info(f"Added auth middleware with testing_mode={testing_mode}")
    
    return app 