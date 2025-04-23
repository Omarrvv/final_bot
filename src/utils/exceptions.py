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
    
    def __init__(self, resource_type: str = None, resource_id: str = None, message: Optional[str] = None):
        """
        Initialize the exception.
        
        Args:
            resource_type (str, optional): Type of resource (e.g., "attraction", "session")
            resource_id (str, optional): ID of the resource that wasn't found
            message (str, optional): Custom error message
        """
        # Allow creating with just a message for backward compatibility with tests
        if message is None and resource_type is not None:
            # Check if resource_type is actually a message (string)
            if isinstance(resource_type, str) and resource_id is None:
                message = resource_type
                resource_type = None
            else:
                message = f"{resource_type.capitalize()} not found: {resource_id}"
        
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
            
        super().__init__(message or "Resource not found", details)

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
    
    def __init__(self, service_name: str = None, method: str = None, error: str = None, 
                 details: Optional[Dict[str, Any]] = None, message: Optional[str] = None):
        """
        Initialize the exception.
        
        Args:
            service_name (str, optional): Name of the service
            method (str, optional): Method that was called
            error (str, optional): Error message
            details (Dict, optional): Additional error details
            message (str, optional): Custom error message (for backward compatibility)
        """
        if message is None:
            if service_name and method and error:
                message = f"Service '{service_name}.{method}' failed: {error}"
            elif service_name and not method and not error:
                # Allow simple message in service_name for backward compatibility
                message = service_name
                service_name = None
            else:
                message = error or "Service call failed"
                
        error_details = details or {}
        if service_name:
            error_details["service"] = service_name
        if method:
            error_details["method"] = method
            
        super().__init__(message, error_details)

class NLUError(ChatbotError):
    """Exception raised when NLU processing fails."""
    pass

class DatabaseError(ChatbotError):
    """Exception raised when database operations fail."""
    pass 