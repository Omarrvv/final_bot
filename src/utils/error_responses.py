"""
Secure error response handlers for the Egypt Tourism Chatbot API.
Part of Phase 1C: Error Handling Standardization

This module provides secure error handling that prevents information disclosure
while maintaining proper error tracking and user-friendly messages.
"""

from fastapi import HTTPException
from typing import Dict, Any, Optional, List
import logging
import uuid
from datetime import datetime, timezone

from ..models.error_models import StandardErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)

def _get_timestamp() -> str:
    """Get current UTC timestamp as ISO format string"""
    return datetime.now(timezone.utc).isoformat()

class SecureErrorHandler:
    """Handle errors securely without information disclosure"""

    @staticmethod
    def database_error(original_error: Exception, request_id: str = None) -> HTTPException:
        """
        Handle database errors securely without exposing internal details.
        
        Args:
            original_error: The original database exception
            request_id: Optional request ID for tracking
            
        Returns:
            HTTPException with secure error details
        """
        request_id = request_id or str(uuid.uuid4())
        
        # Log the full error internally for debugging
        logger.error(f"Database error [{request_id}]: {str(original_error)}", exc_info=True)
        
        # Return sanitized error to user
        error_response = StandardErrorResponse(
            error="service_unavailable",
            message="Service temporarily unavailable. Please try again later.",
            request_id=request_id,
            timestamp=_get_timestamp()
        )
        
        return HTTPException(
            status_code=500,
            detail=error_response.model_dump()
        )

    @staticmethod
    def validation_error(errors: List[Dict[str, Any]], request_id: str = None) -> HTTPException:
        """
        Handle validation errors with detailed field information.
        
        Args:
            errors: List of validation error details
            request_id: Optional request ID for tracking
            
        Returns:
            HTTPException with validation error details
        """
        request_id = request_id or str(uuid.uuid4())
        
        # Convert validation errors to standard format
        error_details = []
        for error in errors:
            detail = ErrorDetail(
                field=error.get("field"),
                message=error.get("message", "Invalid value"),
                code=error.get("code", "validation_error")
            )
            error_details.append(detail)
        
        error_response = StandardErrorResponse(
            error="validation_failed",
            message="Input validation failed",
            details=error_details,
            request_id=request_id,
            timestamp=_get_timestamp()
        )
        
        return HTTPException(
            status_code=422,
            detail=error_response.model_dump()
        )

    @staticmethod
    def authentication_error(message: str = "Authentication required", request_id: str = None) -> HTTPException:
        """
        Handle authentication errors securely.
        
        Args:
            message: User-friendly error message
            request_id: Optional request ID for tracking
            
        Returns:
            HTTPException with authentication error details
        """
        request_id = request_id or str(uuid.uuid4())
        
        error_response = StandardErrorResponse(
            error="authentication_failed",
            message=message,
            request_id=request_id,
            timestamp=_get_timestamp()
        )
        
        return HTTPException(
            status_code=401,
            detail=error_response.model_dump()
        )

    @staticmethod
    def authorization_error(message: str = "Insufficient permissions", request_id: str = None) -> HTTPException:
        """
        Handle authorization errors securely.
        
        Args:
            message: User-friendly error message
            request_id: Optional request ID for tracking
            
        Returns:
            HTTPException with authorization error details
        """
        request_id = request_id or str(uuid.uuid4())
        
        error_response = StandardErrorResponse(
            error="authorization_failed",
            message=message,
            request_id=request_id,
            timestamp=_get_timestamp()
        )
        
        return HTTPException(
            status_code=403,
            detail=error_response.model_dump()
        )

    @staticmethod
    def not_found_error(resource: str = "Resource", request_id: str = None) -> HTTPException:
        """
        Handle not found errors securely.
        
        Args:
            resource: Type of resource that was not found
            request_id: Optional request ID for tracking
            
        Returns:
            HTTPException with not found error details
        """
        request_id = request_id or str(uuid.uuid4())
        
        error_response = StandardErrorResponse(
            error="not_found",
            message=f"{resource} not found",
            request_id=request_id,
            timestamp=_get_timestamp()
        )
        
        return HTTPException(
            status_code=404,
            detail=error_response.model_dump()
        )

    @staticmethod
    def rate_limit_error(message: str = "Rate limit exceeded", request_id: str = None) -> HTTPException:
        """
        Handle rate limiting errors.
        
        Args:
            message: User-friendly error message
            request_id: Optional request ID for tracking
            
        Returns:
            HTTPException with rate limit error details
        """
        request_id = request_id or str(uuid.uuid4())
        
        error_response = StandardErrorResponse(
            error="rate_limit_exceeded",
            message=message,
            request_id=request_id,
            timestamp=_get_timestamp()
        )
        
        return HTTPException(
            status_code=429,
            detail=error_response.model_dump()
        )

    @staticmethod
    def internal_server_error(original_error: Exception = None, request_id: str = None) -> HTTPException:
        """
        Handle unexpected internal server errors securely.
        
        Args:
            original_error: The original exception (logged but not exposed)
            request_id: Optional request ID for tracking
            
        Returns:
            HTTPException with generic internal server error
        """
        request_id = request_id or str(uuid.uuid4())
        
        # Log the full error internally for debugging
        if original_error:
            logger.error(f"Internal server error [{request_id}]: {str(original_error)}", exc_info=True)
        
        error_response = StandardErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred. Please try again later.",
            request_id=request_id,
            timestamp=_get_timestamp()
        )
        
        return HTTPException(
            status_code=500,
            detail=error_response.model_dump()
        ) 