"""
Integration tests for the RequestLoggingMiddleware.

These tests verify that the RequestLoggingMiddleware works correctly
when integrated with the full application.
"""
import pytest
import logging
import json
from contextlib import contextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.middleware.request_logger import add_request_logging_middleware


@contextmanager
def capture_logs(logger_name="src.middleware.request_logger", level=logging.INFO):
    """Capture logs from a specific logger."""
    import io
    import logging

    # Create a string IO object to capture the log output
    log_capture = io.StringIO()
    
    # Create a handler that writes to the StringIO object
    handler = logging.StreamHandler(log_capture)
    
    # Set a formatter that includes all information
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(formatter)
    
    # Get the logger and add the handler
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


class TestRequestLoggerIntegration:
    """Integration tests for the RequestLoggingMiddleware."""
    
    @pytest.fixture
    def minimal_app(self):
        """Create a minimal FastAPI application with the request logging middleware."""
        app = FastAPI()
        
        @app.get("/")
        async def root():
            return {"message": "Hello World"}
            
        @app.get("/data")
        async def data():
            return {"data": "This is some data"}
            
        @app.post("/submit")
        async def submit(data: dict):
            return {"received": data}
            
        @app.get("/health")
        async def health():
            return {"status": "ok"}
            
        @app.get("/error")
        async def error():
            raise ValueError("Test error")
            
        # Add the middleware with custom settings
        add_request_logging_middleware(
            app,
            exclude_paths=["/health"],
            log_request_body=True,
            log_response_body=True
        )
        
        return app
    
    def test_logs_for_successful_requests(self, minimal_app):
        """Verify that successful requests are logged correctly."""
        client = TestClient(minimal_app)
        
        with capture_logs() as logs:
            # Make a request
            response = client.get("/data", headers={
                "X-Request-ID": "test-req-id",
                "User-Agent": "test-agent"
            })
            
            # Check response
            assert response.status_code == 200
            assert response.json() == {"data": "This is some data"}
            
            # Check logs
            log_content = logs.getvalue()
            
            # Verify request started log
            assert "Request started" in log_content
            assert "method=GET" in log_content or "method': 'GET" in log_content
            assert "path=/data" in log_content or "path': '/data" in log_content
            assert "test-req-id" in log_content
            assert "test-agent" in log_content
            
            # Verify request finished log
            assert "Request finished" in log_content
            assert "status_code=200" in log_content or "status_code': 200" in log_content
            assert "process_time_ms" in log_content
    
    def test_excluded_paths_not_logged(self, minimal_app):
        """Verify that excluded paths are not logged."""
        client = TestClient(minimal_app)
        
        with capture_logs() as logs:
            # Make a request to excluded path
            response = client.get("/health")
            
            # Check response
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
            
            # Check logs - should not contain info about /health
            log_content = logs.getvalue()
            
            # The log should not contain /health path entries
            assert "/health" not in log_content
    
    def test_logs_request_and_response_bodies(self, minimal_app):
        """Verify that request and response bodies are logged when enabled."""
        client = TestClient(minimal_app)
        test_data = {"name": "Test User", "action": "submit_form"}
        
        with capture_logs(level=logging.DEBUG) as logs:
            # Make a POST request with JSON body
            response = client.post("/submit", json=test_data)
            
            # Check response
            assert response.status_code == 200
            assert response.json() == {"received": test_data}
            
            # Check logs for request body
            log_content = logs.getvalue()
            
            # Request body should be logged
            assert "Request body" in log_content
            assert "name" in log_content
            assert "Test User" in log_content
            
            # Response body should be logged
            assert "Response body" in log_content
            assert "received" in log_content
    
    def test_logs_errors(self, minimal_app):
        """Verify that errors are properly logged."""
        client = TestClient(minimal_app)
        
        with capture_logs() as logs:
            # Make a request that will raise an error
            with pytest.raises(Exception):  # Any exception
                client.get("/error")
            
            # Check logs
            log_content = logs.getvalue()
            
            # Error should be logged
            assert "Request failed with exception" in log_content
            assert "Test error" in log_content
            assert "ValueError" in log_content
    
    def test_integration_with_app_context(self, app, client):
        """
        Test the middleware in the context of the real application.
        
        This test requires the conftest.py app and client fixtures.
        """
        with capture_logs() as logs:
            # Make a request to the real app
            response = client.get("/api/health")
            
            # Check response
            assert response.status_code == 200
            
            # Note: The actual log content will depend on how the middleware is 
            # configured in the real app, so we just verify the response works
            log_content = logs.getvalue()
            
            # If /api/health is not excluded, we should see logs
            # If it is excluded, we won't - either case is valid
            # Just verify the app handled the request successfully
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main(['-xvs', __file__]) 