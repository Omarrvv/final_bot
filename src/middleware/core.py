"""
Core middleware components for the Egypt Tourism Chatbot API.

This module consolidates essential middleware functionality including:
- Request/Response logging
- Request ID generation and tracking  
- Error handling and exception processing
- Request monitoring and metrics

Replaces: logging.py, logging_middleware.py, request_logger.py, request_id.py,
         error_handler.py, exception_handler.py, exception_handlers.py
"""

import json
import logging
import time
import traceback
import uuid
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

# Configure logger
logger = logging.getLogger(__name__)

# Constants
REQUEST_ID_HEADER = "X-Request-ID"
MAX_BODY_SIZE = 10 * 1024  # 10KB


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware for generating and tracking request IDs.
    
    Consolidates request_id.py functionality.
    """

    def __init__(
        self, 
        app: FastAPI,
        header_name: str = REQUEST_ID_HEADER,
        generate_if_not_present: bool = True,
        return_header: bool = True
    ):
        super().__init__(app)
        self.header_name = header_name
        self.generate_if_not_present = generate_if_not_present
        self.return_header = return_header

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add request ID."""
        request_id = self._get_or_generate_request_id(request)
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        if self.return_header:
            response.headers[self.header_name] = request_id
            
        return response

    def _get_or_generate_request_id(self, request: Request) -> str:
        """Get existing request ID or generate new one."""
        existing_id = request.headers.get(self.header_name)
        
        if existing_id and existing_id.strip():
            return existing_id.strip()
        
        if self.generate_if_not_present:
            return str(uuid.uuid4())
        
        return ""


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive request/response logging middleware.
    
    Consolidates logging.py, logging_middleware.py, and request_logger.py functionality.
    """

    def __init__(
        self,
        app: ASGIApp,
        log_request_body: bool = False,
        log_response_body: bool = False,
        exclude_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.exclude_paths = set(exclude_paths or ["/health", "/metrics"])

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request with comprehensive logging."""
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
            duration = (time.time() - start_time) * 1000
            
            # Log response
            await self._log_response(request, response, duration, request_id)
            
            return response
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"Request {request_id} failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "duration_ms": duration,
                    "error": str(e)
                }
            )
            raise

    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request details."""
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client": self._get_client_info(request)
        }
        
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body and len(body) < MAX_BODY_SIZE:
                    log_data["body"] = body.decode('utf-8')[:MAX_BODY_SIZE]
            except Exception as e:
                log_data["body_error"] = str(e)
        
        logger.info(f"Request {request_id} started", extra=log_data)

    async def _log_response(self, request: Request, response: Response, 
                          duration: float, request_id: str):
        """Log response details."""
        log_data = {
            "request_id": request_id,
            "status_code": response.status_code,
            "duration_ms": round(duration, 2),
            "headers": dict(response.headers)
        }
        
        if self.log_response_body and hasattr(response, 'body'):
            try:
                if hasattr(response.body, 'decode'):
                    body_str = response.body.decode('utf-8')
                    if len(body_str) < MAX_BODY_SIZE:
                        log_data["body"] = body_str[:MAX_BODY_SIZE]
            except Exception as e:
                log_data["body_error"] = str(e)
        
        log_level = logging.ERROR if response.status_code >= 500 else logging.INFO
        logger.log(log_level, f"Request {request_id} completed", extra=log_data)

    def _get_client_info(self, request: Request) -> Dict[str, Any]:
        """Extract client information from request."""
        return {
            "host": request.client.host if request.client else "unknown",
            "port": request.client.port if request.client else None,
            "user_agent": request.headers.get("user-agent", "unknown")
        }


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive error handling middleware.
    
    Consolidates error_handler.py, exception_handler.py, and exception_handlers.py functionality.
    """

    def __init__(
        self,
        app: FastAPI,
        debug: bool = False,
        include_traceback: bool = False,
        error_handlers: Optional[Dict[type, Callable]] = None,
    ):
        super().__init__(app)
        self.debug = debug
        self.include_traceback = include_traceback
        self.custom_handlers = error_handlers or {}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request with comprehensive error handling."""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        try:
            return await call_next(request)
        except Exception as exc:
            return await self._handle_exception(request, exc, request_id)

    async def _handle_exception(
        self, request: Request, exc: Exception, request_id: str
    ) -> JSONResponse:
        """Handle different types of exceptions."""
        # Check for custom handlers first
        for exc_type, handler in self.custom_handlers.items():
            if isinstance(exc, exc_type):
                return await handler(request, exc)

        # Handle specific exception types
        if isinstance(exc, StarletteHTTPException):
            return self._handle_http_exception(exc, request_id)
        elif isinstance(exc, RequestValidationError):
            return self._handle_validation_error(exc, request_id)
        elif isinstance(exc, ValidationError):
            return self._handle_pydantic_validation_error(exc, request_id)
        else:
            return self._handle_internal_error(exc, request_id)

    def _handle_http_exception(
        self, exc: StarletteHTTPException, request_id: str
    ) -> JSONResponse:
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "message": exc.detail,
                    "status_code": exc.status_code,
                    "request_id": request_id
                }
            }
        )

    def _handle_validation_error(
        self, exc: RequestValidationError, request_id: str
    ) -> JSONResponse:
        """Handle FastAPI validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": " -> ".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "type": "validation_error",
                    "message": "Request validation failed",
                    "details": errors,
                    "request_id": request_id
                }
            }
        )

    def _handle_pydantic_validation_error(
        self, exc: ValidationError, request_id: str
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": " -> ".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "type": "data_validation_error",
                    "message": "Data validation failed",
                    "details": errors,
                    "request_id": request_id
                }
            }
        )

    def _handle_internal_error(
        self, exc: Exception, request_id: str
    ) -> JSONResponse:
        """Handle internal server errors."""
        logger.error(
            f"Internal error in request {request_id}: {str(exc)}",
            extra={
                "request_id": request_id,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc() if self.include_traceback else None
            }
        )

        error_detail = {
            "type": "internal_error",
            "message": "An internal server error occurred",
            "request_id": request_id
        }

        if self.debug:
            error_detail["debug_info"] = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc)
            }
            
            if self.include_traceback:
                error_detail["debug_info"]["traceback"] = traceback.format_exc()

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": error_detail}
        )


# Utility functions
def get_request_id(request: Request) -> str:
    """Get request ID from request state or generate new one."""
    return getattr(request.state, 'request_id', str(uuid.uuid4()))


def add_core_middleware(
    app: FastAPI,
    log_request_body: bool = False,
    log_response_body: bool = False,
    debug: bool = False,
    include_traceback: bool = False,
    exclude_paths: Optional[List[str]] = None
) -> None:
    """
    Add all core middleware to the FastAPI application.
    
    Args:
        app: FastAPI application instance
        log_request_body: Whether to log request bodies
        log_response_body: Whether to log response bodies
        debug: Enable debug mode for error handling
        include_traceback: Include tracebacks in error responses
        exclude_paths: Paths to exclude from logging
    """
    # Add middleware in reverse order (last added = first executed)
    app.add_middleware(
        ErrorHandlerMiddleware,
        debug=debug,
        include_traceback=include_traceback
    )
    
    app.add_middleware(
        LoggingMiddleware,
        log_request_body=log_request_body,
        log_response_body=log_response_body,
        exclude_paths=exclude_paths
    )
    
    app.add_middleware(RequestIDMiddleware)


# Custom exceptions for the application
class APIError(Exception):
    """Base API error class."""
    
    def __init__(
        self, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An unexpected error occurred",
        code: str = "internal_error",
        headers: Optional[Dict[str, str]] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.code = code
        self.headers = headers or {}


class NotFoundError(APIError):
    """Resource not found error."""
    
    def __init__(self, detail: str = "Resource not found", code: str = "not_found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            code=code
        )


class ValidationAPIError(APIError):
    """Validation error."""
    
    def __init__(self, detail: str = "Validation error", code: str = "validation_error", errors=None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            code=code
        )
        self.errors = errors or []


class AuthenticationError(APIError):
    """Authentication error."""
    
    def __init__(self, detail: str = "Authentication failed", code: str = "authentication_error"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code=code
        )


class AuthorizationError(APIError):
    """Authorization error."""
    
    def __init__(self, detail: str = "Not authorized", code: str = "authorization_error"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            code=code
        ) 