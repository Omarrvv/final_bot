"""
Exception Handling Middleware for FastAPI

This middleware provides centralized exception handling for all routes,
converting exceptions into standardized API responses.
"""
import time
import traceback
from typing import Dict, Optional, Callable, Any, Type

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Receive, Scope, Send
import logging
import uuid

from src.utils import exceptions as app_exceptions
from src.middleware.request_id import get_request_id
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling exceptions and converting them to consistent API responses.
    
    This middleware catches exceptions raised during request processing and
    converts them into standardized error responses.
    """
    
    def __init__(
        self,
        app: FastAPI,
        debug: bool = False,
        include_traceback: bool = False
    ):
        """
        Initialize the error handling middleware.
        
        Args:
            app: FastAPI application instance
            debug: Whether to include detailed error information in responses
            include_traceback: Whether to include tracebacks in error responses in debug mode
        """
        super().__init__(app)
        self.debug = debug
        self.include_traceback = include_traceback
        
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process the request and handle any exceptions.
        
        Args:
            request: The incoming request
            call_next: Function to call the next middleware or route handler
            
        Returns:
            The response from the next middleware or route handler, or an error response
        """
        request_id = get_request_id(request)
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            return response
            
        except StarletteHTTPException as exc:
            # Handle built-in HTTP exceptions
            return self._handle_http_exception(exc, request_id)
            
        except RequestValidationError as exc:
            # Handle validation errors from FastAPI/Pydantic
            return self._handle_validation_error(exc, request_id)
            
        except app_exceptions.ChatbotError as exc:
            # Handle application-specific errors
            return self._handle_chatbot_error(exc, request_id)
            
        except Exception as exc:
            # Handle unexpected exceptions
            return self._handle_internal_error(exc, request_id)
    
    def _handle_http_exception(
        self, exc: StarletteHTTPException, request_id: str
    ) -> JSONResponse:
        """Handle HTTP exceptions from Starlette."""
        error_data = {
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "status_code": exc.status_code  # Include status_code for consistency
            }
        }
        
        logger.warning(
            f"HTTP error: {exc.status_code} - {exc.detail}",
            extra={"request_id": request_id}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_data,
            headers=exc.headers if hasattr(exc, "headers") else None
        )
    
    def _handle_validation_error(
        self, exc: RequestValidationError, request_id: str
    ) -> JSONResponse:
        """Handle validation errors from FastAPI/Pydantic."""
        # Format validation errors in a consistent way
        error_details = []
        for error in exc.errors():
            error_details.append({
                "loc": error.get("loc", []),
                "msg": error.get("msg", ""),
                "type": error.get("type", "")
            })
        
        error_data = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation error",
                "details": error_details
            }
        }
        
        logger.warning(
            f"Validation error: {str(exc)}",
            extra={"request_id": request_id}
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_data
        )
    
    def _handle_chatbot_error(
        self, exc: app_exceptions.ChatbotError, request_id: str
    ) -> JSONResponse:
        """Handle application-specific errors."""
        # --- Map Exception Type to Error Code ---
        # Define a simple mapping from exception types to error codes
        error_code_mapping = {
            app_exceptions.ValidationError: "VALIDATION_ERROR",
            app_exceptions.ResourceNotFoundError: "RESOURCE_NOT_FOUND",
            app_exceptions.AuthenticationError: "AUTHENTICATION_ERROR",
            app_exceptions.AuthorizationError: "AUTHORIZATION_ERROR",
            app_exceptions.ConfigurationError: "CONFIGURATION_ERROR",
            app_exceptions.ServiceError: "SERVICE_ERROR",
            app_exceptions.NLUError: "NLU_ERROR",
            app_exceptions.DatabaseError: "DATABASE_ERROR",
            # Add other specific ChatbotError subclasses here
        }
        # Get the specific code or default to a generic one
        error_code = error_code_mapping.get(type(exc), "CHATBOT_ERROR")
        # --- End Mapping ---

        error_data = {
            "error": {
                "code": error_code, # Use the mapped code
                "message": exc.message,
            }
        }
        if exc.details:
            error_data["error"]["details"] = exc.details
        
        # Determine appropriate status code based on exception type
        # Default to 500 for generic ChatbotError or unmapped types
        status_code = 500
        if isinstance(exc, app_exceptions.ValidationError):
            status_code = 400
        elif isinstance(exc, app_exceptions.ResourceNotFoundError):
            status_code = 404
        elif isinstance(exc, (app_exceptions.AuthenticationError, app_exceptions.AuthorizationError)):
            status_code = 401 # Or 403 for AuthorizationError if preferred
        # Add other specific status code mappings here

        # Log the error
        log_method = logger.error if status_code >= 500 else logger.warning
        log_method(
            f"{error_code}: {exc.message}", # Use the mapped code
            extra={"request_id": request_id, "details": exc.details}
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_data
        )
    
    def _handle_internal_error(
        self, exc: Exception, request_id: str
    ) -> JSONResponse:
        """Handle unexpected internal errors."""
        # Format the error for the response
        error_data = {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred"
            }
        }
        
        # Add more details in debug mode
        if self.debug:
            error_data["error"]["message"] = str(exc)
            if self.include_traceback:
                error_data["error"]["traceback"] = traceback.format_exc()
        
        # Log the full error
        logger.exception(
            f"Unexpected error: {str(exc)}",
            extra={"request_id": request_id}
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_data
        )


def add_exception_handler_middleware(
    app: FastAPI,
    debug: bool = False,
    include_traceback: bool = False
) -> None:
    """
    Add the exception handler middleware to a FastAPI application.
    
    Args:
        app: FastAPI application instance
        debug: Whether to include detailed error information in responses
        include_traceback: Whether to include tracebacks in error responses in debug mode
    """
    # Add the middleware - This is the primary handler
    app.add_middleware(
        ExceptionHandlerMiddleware,
        debug=debug,
        include_traceback=include_traceback
    )
    
    # --- REMOVE Redundant Global Handlers --- 
    # The middleware's dispatch method handles these cases.
    # Registering them here intercepts exceptions before the 
    # middleware's specific logic might run as intended.

    # # Also register global exception handlers for consistency
    # middleware = ExceptionHandlerMiddleware(app, debug, include_traceback)
    
    # # Register HTTPException handler
    # @app.exception_handler(StarletteHTTPException)
    # async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    #     return middleware._handle_http_exception(exc, get_request_id(request))
    
    # # Register RequestValidationError handler
    # @app.exception_handler(RequestValidationError)
    # async def validation_exception_handler(request: Request, exc: RequestValidationError):
    #     return middleware._handle_validation_error(exc, get_request_id(request))
    
    # # Register ValidationError handler (Custom)
    # @app.exception_handler(app_exceptions.ValidationError) # Use imported alias
    # async def custom_validation_handler(request: Request, exc: app_exceptions.ValidationError):
    #     # This might still be useful if you want different handling than RequestValidationError
    #     return middleware._handle_chatbot_error(exc, get_request_id(request))
    
    # # Register ChatbotError handler (REMOVED - Handled by middleware dispatch)
    # @app.exception_handler(ChatbotError)
    # async def chatbot_error_handler(request: Request, exc: ChatbotError):
    #     return middleware._handle_chatbot_error(exc, get_request_id(request))
    
    # # Register generic Exception handler (REMOVED - Handled by middleware dispatch)
    # @app.exception_handler(Exception)
    # async def generic_exception_handler(request: Request, exc: Exception):
    #     return middleware._handle_internal_error(exc, get_request_id(request))


# Common exception classes for API usage (Consider moving these to src/utils/exceptions.py)
# If kept here, they need to inherit from app_exceptions.ChatbotError
class BadRequestError(app_exceptions.ChatbotError):
    def __init__(self, message: str = "Bad Request", code: str = "bad_request", details: Optional[Dict] = None):
        super().__init__(message=message, details=details)
        # Override status/code if needed, but base class in utils doesn't take them?
        # self.status_code = status.HTTP_400_BAD_REQUEST 
        # self.code = code


class ConflictError(app_exceptions.ChatbotError):
    def __init__(self, message: str = "Conflict", code: str = "conflict", details: Optional[Dict] = None):
        super().__init__(message=message, details=details)
        # self.status_code = status.HTTP_409_CONFLICT
        # self.code = code


class ServerError(app_exceptions.ChatbotError):
    def __init__(self, message: str = "Internal Server Error", code: str = "server_error", details: Optional[Dict] = None):
        super().__init__(message=message, details=details)
        # self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        # self.code = code 