"""
Utilities for testing middleware components.

This module provides common fixtures and utility functions for middleware testing.
"""
import io
import logging
import pytest
from contextlib import contextmanager
from typing import Optional, Callable, Generator, Any

from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


@contextmanager
def capture_logs(logger_name: str = "src.middleware", level: int = logging.INFO) -> Generator[io.StringIO, None, None]:
    """
    Context manager to capture logs from a specific logger.
    
    Args:
        logger_name: The name of the logger to capture logs from
        level: The logging level to set during capture
        
    Yields:
        StringIO object containing the captured logs
    """
    log_capture = io.StringIO()
    
    # Create a handler that writes to the StringIO object
    handler = logging.StreamHandler(log_capture)
    
    # Set a formatter that includes all information
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(formatter)
    
    # Get the logger and configure it
    logger = logging.getLogger(logger_name)
    original_level = logger.level
    logger.setLevel(level)
    logger.addHandler(handler)
    
    try:
        yield log_capture
    finally:
        # Clean up
        logger.removeHandler(handler)
        logger.setLevel(original_level)


@pytest.fixture
def simple_test_app() -> FastAPI:
    """
    Fixture to create a simple FastAPI application with test endpoints.
    
    Returns:
        A FastAPI application with test endpoints
    """
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "Test endpoint"}
    
    @app.post("/test-post")
    async def test_post_endpoint(data: dict):
        return {"received": data}
    
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
        
    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")
    
    return app


class TestMiddleware(BaseHTTPMiddleware):
    """A simple test middleware for testing purposes."""
    
    def __init__(
        self,
        app: FastAPI,
        process_request_func: Optional[Callable] = None,
        process_response_func: Optional[Callable] = None,
    ):
        """
        Initialize the test middleware.
        
        Args:
            app: FastAPI application
            process_request_func: Optional function to process requests
            process_response_func: Optional function to process responses
        """
        super().__init__(app)
        self.process_request_func = process_request_func
        self.process_response_func = process_response_func
        self.requests = []
        self.responses = []
        
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Process requests and responses for testing.
        
        Args:
            request: The incoming request
            call_next: Function to call the next middleware
            
        Returns:
            The response from the next middleware
        """
        # Track request
        self.requests.append(request)
        
        # Run custom request processing if provided
        if self.process_request_func:
            await self.process_request_func(request)
        
        # Call the next middleware
        response = await call_next(request)
        
        # Track response
        self.responses.append(response)
        
        # Run custom response processing if provided
        if self.process_response_func:
            response = await self.process_response_func(request, response)
        
        return response


@pytest.fixture
def test_app_with_middleware(simple_test_app: FastAPI) -> tuple[FastAPI, TestMiddleware]:
    """
    Add a test middleware to a FastAPI app.
    
    Args:
        simple_test_app: FastAPI application
    
    Returns:
        Tuple of (app, middleware_instance)
    """
    middleware = TestMiddleware(simple_test_app)
    simple_test_app.add_middleware(BaseHTTPMiddleware, dispatch=middleware.dispatch)
    return simple_test_app, middleware


def assert_log_contains(log_content: str, expected_terms: list[str]) -> None:
    """
    Assert that log content contains all expected terms.
    
    Args:
        log_content: The log content as a string
        expected_terms: List of terms that should be in the log
    
    Raises:
        AssertionError: If any term is not found in the log
    """
    for term in expected_terms:
        assert term in log_content, f"Expected '{term}' in log content, but not found."


def assert_log_excludes(log_content: str, excluded_terms: list[str]) -> None:
    """
    Assert that log content does not contain any excluded terms.
    
    Args:
        log_content: The log content as a string
        excluded_terms: List of terms that should not be in the log
    
    Raises:
        AssertionError: If any excluded term is found in the log
    """
    for term in excluded_terms:
        assert term not in log_content, f"Found unexpected '{term}' in log content." 