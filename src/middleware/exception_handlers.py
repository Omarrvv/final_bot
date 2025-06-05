"""
Exception Handlers Module for FastAPI

This module provides centralized exception handling for FastAPI applications.
"""
import logging
import traceback
from typing import Any, Dict, Union, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config_unified import settings

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(settings.log_level.upper())


class APIError(Exception):
    """Base exception class for API errors."""
    
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
        self.headers = headers
        super().__init__(self.detail)


class NotFoundError(APIError):
    """Exception raised when a resource is not found."""
    
    def __init__(self, detail: str = "Resource not found", code: str = "not_found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            code=code
        )


class ValidationAPIError(APIError):
    """Exception raised for validation errors."""
    
    def __init__(self, detail: str = "Validation error", code: str = "validation_error", errors=None):
        self.errors = errors or []
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            code=code
        )


class AuthenticationError(APIError):
    """Exception raised for authentication errors."""
    
    def __init__(self, detail: str = "Authentication failed", code: str = "authentication_error"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code=code,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(APIError):
    """Exception raised for authorization errors."""
    
    def __init__(self, detail: str = "Not authorized", code: str = "authorization_error"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            code=code
        )


class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, detail: str = "Rate limit exceeded", code: str = "rate_limit_error"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            code=code
        )


def create_error_response(
    status_code: int,
    detail: str,
    code: str = "error",
    errors: Optional[list] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        detail: Error message
        code: Error code
        errors: List of specific errors (optional)
        request_id: Unique request identifier (optional)
        
    Returns:
        Dict[str, Any]: Standardized error response
    """
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": detail,
            "status_code": status_code
        }
    }
    
    if errors:
        response["error"]["errors"] = errors
        
    if request_id:
        response["request_id"] = request_id
        
    return response


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """
    Handle API errors.
    
    Args:
        request: FastAPI request object
        exc: API error exception
        
    Returns:
        JSONResponse: Standardized error response
    """
    if exc.status_code >= 500:
        logger.error(
            f"Internal Server Error: {exc.detail}",
            exc_info=True,
            extra={"path": request.url.path, "method": request.method}
        )
    else:
        logger.warning(
            f"API Error ({exc.code}): {exc.detail}",
            extra={"path": request.url.path, "method": request.method}
        )
    
    request_id = getattr(request.state, "request_id", None)
    errors = getattr(exc, "errors", None)
    
    content = create_error_response(
        status_code=exc.status_code,
        detail=exc.detail,
        code=exc.code,
        errors=errors,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers or {}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle FastAPI validation errors.
    
    Args:
        request: FastAPI request object
        exc: Validation error exception
        
    Returns:
        JSONResponse: Standardized error response
    """
    errors = []
    for error in exc.errors():
        error_detail = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", "")
        }
        errors.append(error_detail)
    
    logger.warning(
        "Validation error",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": errors
        }
    )
    
    request_id = getattr(request.state, "request_id", None)
    
    content = create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Request validation failed",
        code="validation_error",
        errors=errors,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle Starlette HTTP exceptions.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSONResponse: Standardized error response
    """
    if exc.status_code >= 500:
        logger.error(
            f"Internal Server Error: {exc.detail}",
            exc_info=True,
            extra={"path": request.url.path, "method": request.method}
        )
    else:
        logger.warning(
            f"HTTP Error ({exc.status_code}): {exc.detail}",
            extra={"path": request.url.path, "method": request.method}
        )
    
    request_id = getattr(request.state, "request_id", None)
    
    content = create_error_response(
        status_code=exc.status_code,
        detail=exc.detail,
        code=f"http_{exc.status_code}",
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers or {}
    )


async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request object
        exc: Pydantic validation error
        
    Returns:
        JSONResponse: Standardized error response
    """
    errors = []
    for error in exc.errors():
        error_detail = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", "")
        }
        errors.append(error_detail)
    
    logger.warning(
        "Pydantic validation error",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": errors
        }
    )
    
    request_id = getattr(request.state, "request_id", None)
    
    content = create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Data validation failed",
        code="validation_error",
        errors=errors,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle generic exceptions.
    
    Args:
        request: FastAPI request object
        exc: Generic exception
        
    Returns:
        JSONResponse: Standardized error response
    """
    logger.exception(
        f"Unhandled exception: {str(exc)}",
        extra={"path": request.url.path, "method": request.method}
    )
    
    # Don't expose detailed error information in production
    detail = str(exc) if settings.DEBUG else "An unexpected error occurred"
    
    request_id = getattr(request.state, "request_id", None)
    
    content = create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail,
        code="internal_error",
        request_id=request_id
    )
    
    if settings.DEBUG:
        # Include traceback in debug mode
        content["error"]["traceback"] = traceback.format_exc()
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_handler)
    app.add_exception_handler(Exception, generic_exception_handler) 