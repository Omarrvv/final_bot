"""
Error Handling Middleware for FastAPI

This module provides middleware for centralized error handling in FastAPI applications.
It captures exceptions and returns appropriate JSON responses.
"""
import traceback
from typing import Callable, Dict, Any, Optional, Type

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling exceptions and returning appropriate responses.
    
    This middleware catches exceptions raised during request processing and
    converts them to standardized JSON responses with appropriate status codes.
    """
    
    def __init__(
        self,
        app: FastAPI,
        error_handlers: Optional[Dict[Type[Exception], Callable]] = None,
    ):
        """
        Initialize the error handling middleware.
        
        Args:
            app: FastAPI application instance
            error_handlers: Dictionary mapping exception types to handler functions
        """
        super().__init__(app)
        self.error_handlers = error_handlers or {}
        
        # Add default handlers if not provided
        if ValidationError not in self.error_handlers:
            self.error_handlers[ValidationError] = self._handle_validation_error
            
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process incoming requests and handle any exceptions.
        
        Args:
            request: The incoming request
            call_next: Function to call the next middleware or route handler
            
        Returns:
            The response from the next middleware or route handler, or an error response
        """
        try:
            return await call_next(request)
        except Exception as exc:
            # Check if we have a specific handler for this exception type
            for exc_type, handler in self.error_handlers.items():
                if isinstance(exc, exc_type):
                    return await handler(request, exc)
            
            # Default error handling
            return await self._handle_generic_error(request, exc)
    
    async def _handle_validation_error(self, request: Request, exc: ValidationError) -> JSONResponse:
        """
        Handle Pydantic validation errors.
        
        Args:
            request: The incoming request
            exc: The validation error
            
        Returns:
            JSON response with validation error details
        """
        errors = exc.errors()
        logger.warning(f"Validation error: {errors}")
        
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={
                "detail": "Validation error",
                "errors": errors,
            }
        )
    
    async def _handle_generic_error(self, request: Request, exc: Exception) -> JSONResponse:
        """
        Handle any unhandled exceptions.
        
        Args:
            request: The incoming request
            exc: The exception
            
        Returns:
            JSON response with error details
        """
        error_id = id(exc)
        exception_type = type(exc).__name__
        exception_msg = str(exc)
        
        # Log the full exception with stack trace
        logger.error(
            f"Unhandled exception: {exception_type} - {exception_msg}",
            extra={
                "error_id": error_id,
                "path": request.url.path,
                "method": request.method,
                "traceback": traceback.format_exc(),
            }
        )
        
        # Determine status code based on exception type
        status_code = HTTP_500_INTERNAL_SERVER_ERROR
        if "not found" in exception_msg.lower() or "does not exist" in exception_msg.lower():
            status_code = HTTP_404_NOT_FOUND
        elif "permission" in exception_msg.lower() or "access" in exception_msg.lower():
            status_code = HTTP_403_FORBIDDEN
        elif "unauthorized" in exception_msg.lower() or "unauthenticated" in exception_msg.lower():
            status_code = HTTP_401_UNAUTHORIZED
        elif "invalid" in exception_msg.lower() or "bad request" in exception_msg.lower():
            status_code = HTTP_400_BAD_REQUEST
        
        # Return a JSON response with error details
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": exception_msg,
                "error_type": exception_type,
                "error_id": str(error_id),
            }
        )


class AppError(Exception):
    """Base class for application-specific errors."""
    status_code = HTTP_500_INTERNAL_SERVER_ERROR
    detail = "An error occurred"
    
    def __init__(self, detail: Optional[str] = None, **kwargs: Any):
        self.detail = detail or self.detail
        self.extra = kwargs
        super().__init__(self.detail)


class NotFoundError(AppError):
    """Error raised when a requested resource is not found."""
    status_code = HTTP_404_NOT_FOUND
    detail = "Resource not found"


class UnauthorizedError(AppError):
    """Error raised when a user is not authenticated."""
    status_code = HTTP_401_UNAUTHORIZED
    detail = "Authentication required"


class ForbiddenError(AppError):
    """Error raised when a user does not have permission for an action."""
    status_code = HTTP_403_FORBIDDEN
    detail = "Permission denied"


class ValidationFailedError(AppError):
    """Error raised when request validation fails."""
    status_code = HTTP_400_BAD_REQUEST
    detail = "Validation failed"


def add_error_handler_middleware(
    app: FastAPI,
    error_handlers: Optional[Dict[Type[Exception], Callable]] = None
) -> None:
    """
    Add error handling middleware to a FastAPI application.
    
    Args:
        app: FastAPI application instance
        error_handlers: Dictionary mapping exception types to handler functions
    """
    app.add_middleware(
        ErrorHandlerMiddleware,
        error_handlers=error_handlers,
    )


async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    """
    Handle application-specific errors.
    
    Args:
        request: The incoming request
        exc: The application error
        
    Returns:
        JSON response with error details
    """
    content = {"detail": exc.detail}
    
    # Add any extra information
    if hasattr(exc, "extra") and exc.extra:
        content.update(exc.extra)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
    ) 