"""
Targeted tests for RequestLoggingMiddleware coverage.

This module focuses on covering the specific lines that weren't covered
in the main test suite, with a systematic approach.
"""
import pytest
import json
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from unittest.mock import patch, MagicMock, Mock, call
from typing import Callable
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.middleware.request_logger import RequestLoggingMiddleware


@pytest.fixture
def app():
    """Create a test application with specific routes for testing."""
    test_app = FastAPI()
    
    @test_app.get("/test")
    async def test_route():
        return {"message": "Test endpoint"}
    
    @test_app.get("/submit")
    async def submit_route():
        return {"received": {"name": "Test User", "action": "submit_form"}}
    
    @test_app.get("/response-test")
    async def response_test_route():
        return {"result": "success"}
    
    @test_app.get("/other-path")
    async def other_path_route():
        return {"data": "some data"}
    
    return test_app


@pytest.fixture
def client(app):
    """Create test client with request logging middleware."""
    app.add_middleware(
        RequestLoggingMiddleware,
        exclude_paths=set(),
        log_request_body=True,
        log_response_body=True
    )
    return TestClient(app)


class MockJSONResponse(JSONResponse):
    """Mock JSONResponse that raises exception when body is accessed."""
    
    @property
    def body(self):
        # This will be patched, but defining it helps IDE and static checkers
        return b"{}"


class TestRequestLoggerCoverage:
    """Tests specifically targeting uncovered lines."""
    
    def test_request_body_json_decode_exception(self, app):
        """Test exception handling in request body JSON decoding (lines 110-111, 120-121)."""
        # Create a middleware that we can control directly
        middleware = RequestLoggingMiddleware(log_request_body=True)
        
        # Create a mock request with a body method that returns non-JSON data
        mock_request = Mock()
        mock_request.url.path = "/test"
        mock_request.client.host = "testclient"
        mock_request.method = "GET"
        mock_request.headers = {"user-agent": "test-agent", "x-request-id": "test-id"}
        mock_request.body = Mock(return_value=b"not-json-data")
        
        # Create a mock for the call_next function
        async def mock_call_next(request):
            return JSONResponse(content={"status": "ok"})
        
        # Patch the logger to check if warnings are logged
        with patch("src.middleware.request_logger.logger") as mock_logger:
            # Need to run middleware.dispatch in an async context
            import asyncio
            asyncio.run(middleware.dispatch(mock_request, mock_call_next))
            
            # Check that the warning about failed JSON parsing was logged
            warnings = [
                call for call in mock_logger.warning.call_args_list
                if "Failed to log request body" in str(call)
            ]
            assert len(warnings) > 0
    
    def test_response_body_special_paths(self, client):
        """Test special path handling for response bodies (lines 162-169)."""
        with patch("src.middleware.request_logger.logger") as mock_logger:
            # Test the /submit path (line 163)
            client.get("/submit")
            
            # Test the /response-test path (line 167)
            client.get("/response-test")
            
            # Test the default "else" case (line 169)
            client.get("/other-path")
            
            # Verify that each path's special handling was used by checking the debug logs
            debug_calls = mock_logger.debug.call_args_list
            
            # Check for the submit route special case
            submit_logs = [
                call for call in debug_calls
                if "Response body" in str(call) and "received" in str(call)
            ]
            assert len(submit_logs) > 0
            
            # Check for the response-test route special case
            response_test_logs = [
                call for call in debug_calls
                if "Response body" in str(call) and "result" in str(call)
            ]
            assert len(response_test_logs) > 0
            
            # Check for the default case
            other_logs = [
                call for call in debug_calls
                if "Response body" in str(call) and "info" in str(call)
            ]
            assert len(other_logs) > 0
    
    def test_response_body_logging_exception(self, app):
        """Test exception handling in response body logging (lines 157-158, 178-179)."""
        # Use a direct approach with direct mocking of the middleware method
        # Create an instance of the middleware for direct testing
        middleware = RequestLoggingMiddleware(log_response_body=True)
        
        # Mock a request
        mock_request = Mock()
        mock_request.url.path = "/test"
        mock_request.client.host = "testclient"
        mock_request.method = "GET"
        mock_request.headers = {"user-agent": "test-agent", "x-request-id": "test-id"}
        
        # Create a JSONResponse that will be returned
        mock_response = JSONResponse(content={"message": "Test endpoint"})
        
        # Mock the call_next function to return our response
        async def mock_call_next(request):
            return mock_response
        
        # Now we need to cause an exception in the response body handling
        # We'll patch the json.loads function used in the middleware
        with patch("src.middleware.request_logger.json.loads", side_effect=Exception("JSON decode error")):
            with patch("src.middleware.request_logger.logger") as mock_logger:
                # Need to run the dispatch in an async context
                import asyncio
                asyncio.run(middleware.dispatch(mock_request, mock_call_next))
                
                # Check that the warning about failed response body logging was logged
                warnings = [
                    call for call in mock_logger.warning.call_args_list
                    if "Failed to log response body" in str(call)
                ]
                assert len(warnings) > 0


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 