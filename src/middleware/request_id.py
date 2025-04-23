"""
Request ID Middleware for FastAPI

This module provides middleware for assigning and managing request IDs
in FastAPI applications to improve traceability and debugging.
"""
import uuid
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Context variable to store the request ID for the current request
REQUEST_ID_CTX_KEY = "request_id"

# Header name for request ID
REQUEST_ID_HEADER = "X-Request-ID"


def get_request_id(request: Request) -> str:
    """
    Get the request ID from the request state.
    
    Args:
        request: The request object
        
    Returns:
        The request ID, or "-" if not available
    """
    return getattr(request.state, REQUEST_ID_CTX_KEY, "-")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware for managing request IDs.
    
    This middleware ensures that each request has a unique ID, either
    from the incoming X-Request-ID header or a newly generated one.
    The ID is stored in request.state and added to the response headers.
    """
    
    def __init__(
        self, 
        app: FastAPI,
        header_name: str = REQUEST_ID_HEADER,
        generate_if_not_present: bool = True,
        return_header: bool = True
    ):
        """
        Initialize the request ID middleware.
        
        Args:
            app: FastAPI application instance
            header_name: Name of the request ID header
            generate_if_not_present: Whether to generate a request ID if not provided
            return_header: Whether to include the request ID in response headers
        """
        super().__init__(app)
        self.header_name = header_name
        self.generate_if_not_present = generate_if_not_present
        self.return_header = return_header
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and ensure it has a request ID.
        
        Args:
            request: The incoming request
            call_next: Function to call the next middleware or handler
            
        Returns:
            The response from the next handler
        """
        # Get or generate request ID
        request_id = self._get_or_generate_request_id(request)
        
        # Store the request ID in request state
        request.state.request_id = request_id
        
        # Process the request
        response = await call_next(request)
        
        # Add request ID to response headers if configured
        if self.return_header:
            response.headers[self.header_name] = request_id
            
        return response
    
    def _get_or_generate_request_id(self, request: Request) -> str:
        """
        Get the request ID from headers or generate a new one.
        
        Args:
            request: The incoming request
            
        Returns:
            The request ID (from headers or newly generated)
        """
        # Try to get the request ID from the header
        request_id = request.headers.get(self.header_name)
        
        # Generate a new request ID if not present and configured to do so
        if not request_id and self.generate_if_not_present:
            request_id = str(uuid.uuid4())
            
        # If we still don't have a request ID, use a placeholder
        return request_id or "-"


def add_request_id_middleware(
    app: FastAPI,
    header_name: str = REQUEST_ID_HEADER,
    generate_if_not_present: bool = True,
    return_header: bool = True
) -> None:
    """
    Add request ID middleware to a FastAPI application.
    
    Args:
        app: FastAPI application instance
        header_name: Name of the request ID header
        generate_if_not_present: Whether to generate a request ID if not provided
        return_header: Whether to include the request ID in response headers
    """
    app.add_middleware(
        RequestIDMiddleware,
        header_name=header_name,
        generate_if_not_present=generate_if_not_present,
        return_header=return_header
    ) 