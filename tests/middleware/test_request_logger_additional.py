"""
Additional tests for RequestLoggingMiddleware.

These tests focus on edge cases and exception handling to improve test coverage.
"""
import pytest
import json
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from unittest.mock import patch, MagicMock, call, Mock
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.middleware.request_logger import RequestLoggingMiddleware


class StreamingJsonResponse(JSONResponse):
    """A custom JSON response that will raise an exception when its body is accessed."""
    
    @property
    def body(self):
        raise Exception("Error accessing response body")


@pytest.fixture
def app_with_special_routes():
    """Create a test app with routes for specific test paths."""
    app = FastAPI()
    
    @app.post("/submit")
    async def submit_endpoint(request: Request):
        body = await request.json()
        return {"received": body}
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "Test endpoint"}
    
    @app.get("/response-test")
    async def response_test_endpoint():
        return {"result": "success"}
        
    @app.get("/other-path")
    async def other_path_endpoint():
        # This will trigger the default case in response body logging
        return {"data": "some data"}
    
    @app.post("/text-endpoint")
    async def text_endpoint(request: Request):
        # This endpoint accepts text content
        body = await request.body()
        return {"received": body.decode()}
    
    @app.get("/error-response")
    async def error_response_endpoint():
        # Return a response that will cause an error when logged
        return StreamingJsonResponse(content={"error": "test"})
    
    return app


@pytest.fixture
def client(app_with_special_routes):
    """Create a standard test client."""
    app_with_special_routes.add_middleware(
        RequestLoggingMiddleware,
        log_request_body=True,
        log_response_body=True
    )
    return TestClient(app_with_special_routes)


class TestRequestLoggerEdgeCases:
    """Tests focusing on edge cases in the RequestLoggingMiddleware."""

    def test_non_json_request_body_handling(self, client):
        """Test handling of non-JSON request body."""
        # Initialize the middleware directly instead of using TestClient
        middleware = RequestLoggingMiddleware(log_request_body=True, log_response_body=True)
        
        # Create a mock request
        mock_request = Mock()
        mock_request.url.path = "/text-endpoint"
        mock_request.client.host = "127.0.0.1"
        mock_request.method = "POST"
        mock_request.headers = {"user-agent": "test-client", "x-request-id": "test-id"}
        
        # Mock the body method to return non-JSON data (with synchronous return)
        mock_request.body = Mock(return_value=b"This is plain text")
        
        # Mock call_next to simulate endpoint behavior
        async def mock_call_next(request):
            return JSONResponse({"status": "ok"})
        
        # Execute middleware and check for warning log
        with patch("src.middleware.request_logger.logger") as mock_logger:
            # Execute middleware
            import asyncio
            asyncio.run(middleware.dispatch(mock_request, mock_call_next))
            
            # Check warning logs using the same pattern as successful tests
            warnings = [
                call for call in mock_logger.warning.call_args_list
                if "Failed to log request body" in str(call)
            ]
            assert len(warnings) > 0, "Warning about failed request body logging was not found"
    
    def test_special_response_paths(self, client):
        """Test special handling for different response paths."""
        with patch("src.middleware.request_logger.logger") as mock_logger:
            # Test /submit path
            response = client.post("/submit", json={"name": "Test User", "action": "submit_form"})
            assert response.status_code == 200
            
            # Test /test path
            response = client.get("/test")
            assert response.status_code == 200
            
            # Test /response-test path
            response = client.get("/response-test")
            assert response.status_code == 200
            
            # Test default case (other path)
            response = client.get("/other-path")
            assert response.status_code == 200
            
            # Verify that response body was logged for each path
            debug_calls = [
                call for call in mock_logger.debug.call_args_list 
                if "Response body" in str(call)
            ]
            
            # We should have at least one debug log for each request
            assert len(debug_calls) >= 4
    
    def test_response_body_logging_exception(self, client):
        """Test exception handling during response body logging."""
        # Initialize the middleware with response body logging enabled
        middleware = RequestLoggingMiddleware(log_request_body=False, log_response_body=True)
        
        # Create a mock request
        mock_request = Mock()
        mock_request.url.path = "/test"
        mock_request.client.host = "127.0.0.1"
        mock_request.method = "GET"
        mock_request.headers = {"user-agent": "test-client", "x-request-id": "test-id"}
        
        # Create a JSONResponse that will cause an error when accessed
        mock_response = JSONResponse(content={"message": "Test endpoint"})
        
        # Mock call_next to return our response
        async def mock_call_next(request):
            return mock_response
        
        # Cause an exception in the response body handling by patching json.loads
        with patch("src.middleware.request_logger.json.loads", side_effect=Exception("Test error")):
            with patch("src.middleware.request_logger.logger") as mock_logger:
                # Execute middleware
                import asyncio
                asyncio.run(middleware.dispatch(mock_request, mock_call_next))
                
                # Check warning logs using the same pattern as successful tests
                warnings = [
                    call for call in mock_logger.warning.call_args_list
                    if "Failed to log response body" in str(call)
                ]
                assert len(warnings) > 0, "Warning about failed response body logging was not found"
    
    def test_request_body_access_exception(self, client):
        """Test exception handling when accessing the request body."""
        # Need to patch the Request.body method that the middleware calls
        with patch("starlette.requests.Request.body", side_effect=Exception("Mock body access error")):
            with patch("src.middleware.request_logger.logger") as mock_logger:
                try:
                    # This might fail due to the patched exception, but we just want to verify the warning
                    client.post("/submit", json={"test": "data"})
                except:
                    pass
                
                # Verify that the warning about failed body access was logged
                warning_calls = [
                    call for call in mock_logger.warning.call_args_list 
                    if "Failed to log request body" in str(call)
                ]
                assert len(warning_calls) > 0


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 