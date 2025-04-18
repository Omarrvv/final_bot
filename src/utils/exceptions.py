"""
Custom exceptions for the Egypt Tourism Chatbot.
Provides standardized error handling across the application.
"""
from typing import Optional, Dict, Any

class ChatbotError(Exception):
    """Base exception class for the chatbot application."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.
        
        Args:
            message (str): Error message
            details (Dict, optional): Additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ConfigurationError(ChatbotError):
    """Exception raised when there's an issue with configuration."""
    pass

class AuthenticationError(ChatbotError):
    """Exception raised when there's an authentication issue."""
    pass

class AuthorizationError(ChatbotError):
    """Exception raised when a user is not authorized for an action."""
    pass

class ResourceNotFoundError(ChatbotError):
    """Exception raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str, message: Optional[str] = None):
        """
        Initialize the exception.
        
        Args:
            resource_type (str): Type of resource (e.g., "attraction", "session")
            resource_id (str): ID of the resource that wasn't found
            message (str, optional): Custom error message
        """
        default_message = f"{resource_type.capitalize()} not found: {resource_id}"
        super().__init__(message or default_message, {
            "resource_type": resource_type,
            "resource_id": resource_id
        })

class ValidationError(ChatbotError):
    """Exception raised when input validation fails."""
    
    def __init__(self, errors: Dict[str, str], message: Optional[str] = None):
        """
        Initialize the exception.
        
        Args:
            errors (Dict[str, str]): Validation errors by field
            message (str, optional): Custom error message
        """
        super().__init__(message or "Validation failed", {"errors": errors})

class ServiceError(ChatbotError):
    """Exception raised when an external service call fails."""
    
    def __init__(self, service_name: str, method: str, error: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.
        
        Args:
            service_name (str): Name of the service
            method (str): Method that was called
            error (str): Error message
            details (Dict, optional): Additional error details
        """
        message = f"Service '{service_name}.{method}' failed: {error}"
        error_details = details or {}
        error_details.update({
            "service": service_name,
            "method": method
        })
        super().__init__(message, error_details)

class NLUError(ChatbotError):
    """Exception raised when NLU processing fails."""
    pass

class DatabaseError(ChatbotError):
    """Exception raised when database operations fail."""
    pass 