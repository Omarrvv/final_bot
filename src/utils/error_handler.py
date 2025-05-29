"""
Enhanced error handling utilities for the Egypt Tourism Chatbot.
Provides consistent error handling, logging, and fallback mechanisms.
"""

import logging
import traceback
import json
import time
from typing import Dict, Any, Optional, Callable, TypeVar, List, Union
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for return type
T = TypeVar('T')

class ErrorHandler:
    """
    Enhanced error handling utilities for the Egypt Tourism Chatbot.
    """
    
    @staticmethod
    def with_fallback(fallback_value: T, log_level: int = logging.ERROR) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """
        Decorator to add fallback mechanism to functions.
        
        Args:
            fallback_value: Value to return if function fails
            log_level: Logging level for errors (default: ERROR)
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Log the error with appropriate level
                    logger.log(log_level, f"Error in {func.__name__}: {str(e)}")
                    if log_level >= logging.ERROR:
                        logger.debug(f"Traceback: {traceback.format_exc()}")
                    
                    # Return fallback value
                    return fallback_value
            return wrapper
        return decorator
    
    @staticmethod
    def with_retry(max_retries: int = 3, retry_delay: float = 0.5, 
                  fallback_value: Optional[T] = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """
        Decorator to add retry mechanism to functions.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            fallback_value: Value to return if all retries fail
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        
                        if attempt < max_retries:
                            # Log retry attempt
                            logger.warning(f"Retry {attempt+1}/{max_retries} for {func.__name__} due to: {str(e)}")
                            time.sleep(retry_delay)
                        else:
                            # Log final failure
                            logger.error(f"All {max_retries} retries failed for {func.__name__}: {str(e)}")
                            logger.debug(f"Traceback: {traceback.format_exc()}")
                
                # If fallback_value is provided, return it
                if fallback_value is not None:
                    return fallback_value
                
                # Otherwise, re-raise the last exception
                raise last_exception
            return wrapper
        return decorator
    
    @staticmethod
    def format_error_response(error: Exception, query: Optional[str] = None, 
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format an error into a standardized response structure.
        
        Args:
            error: The exception that occurred
            query: The original query that caused the error
            context: Additional context information
            
        Returns:
            Formatted error response
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        response = {
            "success": False,
            "error": {
                "type": error_type,
                "message": error_message,
                "timestamp": time.time()
            }
        }
        
        if query:
            response["query"] = query
        
        if context:
            response["context"] = context
        
        return response
    
    @staticmethod
    def log_error(error: Exception, module: str, function: str, 
                 log_level: int = logging.ERROR, include_traceback: bool = True) -> None:
        """
        Log an error with consistent formatting.
        
        Args:
            error: The exception to log
            module: Module where the error occurred
            function: Function where the error occurred
            log_level: Logging level
            include_traceback: Whether to include traceback
        """
        error_message = f"Error in {module}.{function}: {str(error)}"
        
        logger.log(log_level, error_message)
        
        if include_traceback and log_level >= logging.ERROR:
            logger.debug(f"Traceback: {traceback.format_exc()}")
    
    @staticmethod
    def safe_json_loads(json_str: str, default_value: Any = None) -> Any:
        """
        Safely parse JSON string with error handling.
        
        Args:
            json_str: JSON string to parse
            default_value: Value to return if parsing fails
            
        Returns:
            Parsed JSON or default value
        """
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Error parsing JSON: {str(e)}")
            return default_value
    
    @staticmethod
    def safe_dict_get(data: Dict[str, Any], key_path: Union[str, List[str]], 
                     default_value: Any = None) -> Any:
        """
        Safely get a value from a nested dictionary.
        
        Args:
            data: Dictionary to get value from
            key_path: Key or list of keys to traverse
            default_value: Value to return if key not found
            
        Returns:
            Value at key path or default value
        """
        if not data:
            return default_value
        
        # Convert string key to list
        if isinstance(key_path, str):
            keys = key_path.split('.')
        else:
            keys = key_path
        
        current = data
        try:
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default_value
            return current
        except Exception as e:
            logger.debug(f"Error accessing dict path {key_path}: {str(e)}")
            return default_value
