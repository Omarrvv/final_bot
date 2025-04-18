"""
Error handling utilities for the Egypt Tourism Chatbot.
Provides standardized error handling and response formatting.
"""
import logging
import traceback
from typing import Dict, Any, Optional, Tuple, Union
from flask import jsonify, Response

from src.utils.exceptions import (
    ChatbotError, ConfigurationError, AuthenticationError, 
    AuthorizationError, ResourceNotFoundError, ValidationError,
    ServiceError, NLUError, DatabaseError
)

logger = logging.getLogger(__name__)

class ErrorHandler:
    """
    Centralized error handler for the application.
    Ensures consistent error responses and proper logging.
    """
    
    def __init__(self, include_traceback: bool = False):
        """
        Initialize the error handler.
        
        Args:
            include_traceback (bool): Whether to include tracebacks in error responses
        """
        self.include_traceback = include_traceback
        self.error_map = {
            ConfigurationError: (500, "CONFIGURATION_ERROR"),
            AuthenticationError: (401, "AUTHENTICATION_ERROR"),
            AuthorizationError: (403, "AUTHORIZATION_ERROR"),
            ResourceNotFoundError: (404, "RESOURCE_NOT_FOUND"),
            ValidationError: (400, "VALIDATION_ERROR"),
            ServiceError: (502, "SERVICE_ERROR"),
            NLUError: (500, "NLU_ERROR"),
            DatabaseError: (500, "DATABASE_ERROR"),
            ChatbotError: (500, "INTERNAL_ERROR")
        }
    
    def handle_exception(self, exception: Exception) -> Tuple[Response, int]:
        """
        Handle an exception and return an appropriate response.
        
        Args:
            exception (Exception): The exception to handle
            
        Returns:
            tuple: (Response, status_code)
        """
        if isinstance(exception, ChatbotError):
            return self._handle_chatbot_error(exception)
        else:
            return self._handle_generic_exception(exception)
    
    def _handle_chatbot_error(self, error: ChatbotError) -> Tuple[Response, int]:
        """
        Handle a ChatbotError.
        
        Args:
            error (ChatbotError): The error to handle
            
        Returns:
            tuple: (Response, status_code)
        """
        # Find the error type to determine status code
        for error_type, (status_code, error_code) in self.error_map.items():
            if isinstance(error, error_type):
                self._log_error(error, status_code)
                return self._create_error_response(
                    message=error.message,
                    error_code=error_code,
                    details=error.details,
                    status_code=status_code
                )
        
        # If no specific mapping found, use generic handling
        return self._handle_generic_exception(error)
    
    def _handle_generic_exception(self, exception: Exception) -> Tuple[Response, int]:
        """
        Handle a generic exception.
        
        Args:
            exception (Exception): The exception to handle
            
        Returns:
            tuple: (Response, status_code)
        """
        status_code = 500
        error_code = "INTERNAL_SERVER_ERROR"
        
        self._log_error(exception, status_code)
        
        return self._create_error_response(
            message=str(exception),
            error_code=error_code,
            status_code=status_code
        )
    
    def _create_error_response(self, message: str, error_code: str, 
                             status_code: int, details: Optional[Dict[str, Any]] = None) -> Tuple[Response, int]:
        """
        Create a standardized error response.
        
        Args:
            message (str): Error message
            error_code (str): Error code
            status_code (int): HTTP status code
            details (Dict, optional): Additional error details
            
        Returns:
            tuple: (Response, status_code)
        """
        response_data = {
            "status": "error",
            "message": message,
            "error_code": error_code
        }
        
        if details:
            response_data["details"] = details
            
        if self.include_traceback:
            response_data["traceback"] = traceback.format_exc()
            
        return jsonify(response_data), status_code
    
    def _log_error(self, exception: Exception, status_code: int) -> None:
        """
        Log an error with appropriate severity.
        
        Args:
            exception (Exception): The exception to log
            status_code (int): HTTP status code
        """
        error_msg = f"{type(exception).__name__}: {str(exception)}"
        
        if status_code >= 500:
            logger.error(error_msg, exc_info=True)
        elif status_code >= 400:
            logger.warning(error_msg)
        else:
            logger.info(error_msg)
            
# Create a global error handler instance
error_handler = ErrorHandler(include_traceback=False) 