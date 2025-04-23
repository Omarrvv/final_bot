"""
Logging Middleware for FastAPI

This middleware logs details about incoming requests and outgoing responses,
providing visibility into API traffic and performance metrics.
"""
import time
import logging
from typing import Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

# Import the request_id utility if available
try:
    from .request_id import get_request_id
except ImportError:
    def get_request_id(request: Request) -> Optional[str]:
        return None

# Set up logging
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs information about incoming requests and outgoing responses.
    
    Features:
    - Logs request method, path, and user agent
    - Logs response status code and processing time
    - Includes request ID in logs if available
    - Adds different log levels based on response status
    """
    
    def __init__(
        self,
        app: ASGIApp,
        log_request_body: bool = False,
        log_response_body: bool = False,
    ):
        """
        Initialize the middleware.
        
        Args:
            app: ASGI application
            log_request_body: Whether to log request bodies (default: False)
            log_response_body: Whether to log response bodies (default: False)
        """
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process the request and log details.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            Response: The response from the handler
        """
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        request_id = get_request_id(request)
        
        # Prepare log context
        log_context = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "client_ip": client_host,
            "user_agent": user_agent,
        }
        
        # Log incoming request
        logger.info(
            f"Request started: {method} {path}{query_params}",
            extra=log_context
        )
        
        # Log request body if configured and available
        if self.log_request_body:
            try:
                body = await request.body()
                if body:
                    logger.debug(
                        f"Request body: {body.decode('utf-8')}",
                        extra=log_context
                    )
                    # Reset the request body
                    await request.body()
            except Exception as e:
                logger.warning(
                    f"Failed to log request body: {str(e)}",
                    extra=log_context
                )
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Update log context with response info
            log_context.update({
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2)
            })
            
            # Choose log level based on status code
            if response.status_code >= 500:
                log_level = logging.ERROR
                log_msg = f"Request failed: {method} {path} - {response.status_code}"
            elif response.status_code >= 400:
                log_level = logging.WARNING
                log_msg = f"Request error: {method} {path} - {response.status_code}"
            else:
                log_level = logging.INFO
                log_msg = f"Request completed: {method} {path} - {response.status_code}"
            
            # Add processing time to log message
            log_msg += f" ({log_context['process_time_ms']}ms)"
            
            # Log response
            logger.log(log_level, log_msg, extra=log_context)
            
            # Log response body if configured
            if self.log_response_body and hasattr(response, "body"):
                try:
                    body = response.body.decode("utf-8")
                    logger.debug(f"Response body: {body}", extra=log_context)
                except Exception as e:
                    logger.warning(
                        f"Failed to log response body: {str(e)}",
                        extra=log_context
                    )
            
            return response
            
        except Exception as exc:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Update log context
            log_context.update({
                "error": str(exc),
                "process_time_ms": round(process_time * 1000, 2)
            })
            
            # Log the error
            logger.exception(
                f"Request failed with exception: {method} {path}",
                extra=log_context
            )
            
            # Re-raise the exception for other middleware to handle
            raise


def add_logging_middleware(
    app: FastAPI,
    log_request_body: bool = False,
    log_response_body: bool = False,
) -> None:
    """
    Add the logging middleware to a FastAPI application.
    
    Args:
        app: FastAPI application instance
        log_request_body: Whether to log request bodies (default: False)
        log_response_body: Whether to log response bodies (default: False)
    """
    app.add_middleware(
        LoggingMiddleware,
        log_request_body=log_request_body,
        log_response_body=log_response_body,
    ) 