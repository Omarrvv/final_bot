"""
Error handling middleware for standardized error responses.
Part of Phase 1C: Error Handling Standardization

This middleware ensures all errors are handled consistently across the API
with proper request tracking and secure error responses.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uuid
import logging
from datetime import datetime, timezone
from typing import Union

from ..models.error_models import StandardErrorResponse, ErrorDetail
from ..utils.error_responses import SecureErrorHandler

logger = logging.getLogger(__name__)

async def standard_error_handler(request: Request, call_next):
    """
    Middleware to standardize all error responses and add request tracking.
    
    This middleware:
    1. Adds a unique request ID to each request
    2. Catches and standardizes all exceptions
    3. Ensures no internal information is leaked
    4. Provides consistent error response format
    """
    # Generate unique request ID for tracking
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    try:
        # Process the request
        response = await call_next(request)
        return response
        
    except RequestValidationError as e:
        # Handle Pydantic validation errors
        logger.warning(f"Validation error [{request_id}]: {str(e)}")
        
        # Convert Pydantic errors to our standard format
        validation_errors = []
        for error in e.errors():
            validation_errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "code": error["type"]
            })
        
        # Use our secure error handler
        http_exception = SecureErrorHandler.validation_error(validation_errors, request_id)
        return JSONResponse(
            status_code=http_exception.status_code,
            content=http_exception.detail
        )
        
    except HTTPException as e:
        # Handle FastAPI HTTPExceptions
        logger.info(f"HTTP exception [{request_id}]: {e.status_code} - {str(e.detail)}")
        
        # Check if it's already in our standard format
        if isinstance(e.detail, dict) and "request_id" in e.detail:
            # Already standardized, just return it
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail
            )
        else:
            # Convert to standard format
            error_response = StandardErrorResponse(
                error=f"http_{e.status_code}",
                message=str(e.detail) if isinstance(e.detail, str) else "HTTP error occurred",
                request_id=request_id,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            return JSONResponse(
                status_code=e.status_code,
                content=error_response.model_dump()
            )
            
    except StarletteHTTPException as e:
        # Handle Starlette HTTPExceptions
        logger.info(f"Starlette HTTP exception [{request_id}]: {e.status_code} - {str(e.detail)}")
        
        error_response = StandardErrorResponse(
            error=f"http_{e.status_code}",
            message=str(e.detail) if e.detail else "HTTP error occurred",
            request_id=request_id,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        return JSONResponse(
            status_code=e.status_code,
            content=error_response.model_dump()
        )
        
    except Exception as e:
        # Handle all other unexpected errors
        logger.error(f"Unexpected error [{request_id}]: {str(e)}", exc_info=True)
        
        # Use our secure error handler for internal server errors
        http_exception = SecureErrorHandler.internal_server_error(e, request_id)
        return JSONResponse(
            status_code=http_exception.status_code,
            content=http_exception.detail
        )

def get_request_id(request: Request) -> str:
    """
    Get the request ID from the request state.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        The request ID string
    """
    return getattr(request.state, 'request_id', str(uuid.uuid4()))

def generate_request_id() -> str:
    """
    Generate a new request ID.
    
    Returns:
        A new UUID string for request tracking
    """
    return str(uuid.uuid4()) 