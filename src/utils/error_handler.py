from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class UnifiedErrorHandler:
    """Unified error handling for consistent error responses."""

    @staticmethod
    def handle_database_error(operation: str, error: Exception,
                            fallback_value: Any = None) -> Any:
        """Handle database operation errors consistently."""
        logger.error(f"Database error in {operation}: {str(error)}")

        if fallback_value is not None:
            return fallback_value
        elif 'search' in operation.lower():
            return []  # Empty list for search operations
        else:
            return None

    @staticmethod
    def handle_api_error(service: str, error: Exception,
                        language: str = "en") -> Dict[str, Any]:
        """Handle API service errors consistently."""
        logger.error(f"API error in {service}: {str(error)}")

        fallback_messages = {
            "en": "I'm sorry, I'm having trouble processing your request right now. Please try again later.",
            "ar": "عذرًا، أواجه صعوبة في معالجة طلبك الآن. يرجى المحاولة مرة أخرى لاحقًا."
        }

        return {
            "text": fallback_messages.get(language, fallback_messages["en"]),
            "error": str(error),
            "fallback": True,
            "source": "error_handler"
        }

    @staticmethod
    def handle_missing_method(class_name: str, method_name: str,
                            language: str = "en") -> Dict[str, Any]:
        """Handle missing method calls gracefully."""
        logger.error(f"Missing method {method_name} in {class_name}")

        fallback_messages = {
            "en": "This feature is temporarily unavailable. Please try a different query.",
            "ar": "هذه الميزة غير متاحة مؤقتًا. يرجى تجربة استعلام مختلف."
        }

        return {
            "text": fallback_messages.get(language, fallback_messages["en"]),
            "error": f"Method {method_name} not implemented",
            "fallback": True,
            "source": "error_handler"
        }

# Standalone functions for backward compatibility
def handle_db_connection_error(error: Exception, language: str = "en") -> Dict[str, Any]:
    """Handle database connection errors."""
    return UnifiedErrorHandler.handle_api_error("database", error, language)

def handle_api_timeout(error: Exception, language: str = "en") -> Dict[str, Any]:
    """Handle API timeout errors."""
    return UnifiedErrorHandler.handle_api_error("api_timeout", error, language)
