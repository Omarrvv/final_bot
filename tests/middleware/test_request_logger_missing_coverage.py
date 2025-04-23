"""
Tests to improve coverage for request_logger middleware.
"""
import json
import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock, call
from fastapi.responses import JSONResponse

from src.middleware.request_logger import RequestLoggingMiddleware, add_request_logging_middleware

@pytest.fixture
def app():
    app = FastAPI()
    
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "Test endpoint"}
    
    @app.post("/json-echo")
    async def json_echo(request: Request):
        body = await request.json()
        return body
    
    @app.post("/submit")
    async def submit_endpoint(request: Request):
        body = await request.json()
        return {"success": True, "data": body}
    
    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")
    
    return app

@pytest.fixture
def client_with_excluded_paths(app):
    app.add_middleware(
        RequestLoggingMiddleware,
        exclude_paths={"/health"},
        log_request_body=True,
        log_response_body=True
    )
    return TestClient(app)

@pytest.fixture
def client_with_logging(app):
    app.add_middleware(
        RequestLoggingMiddleware,
        log_request_body=True,
        log_response_body=True
    )
    return TestClient(app)

def test_exclude_paths():
    """Test the exclude_paths parameter."""
    app = FastAPI()
    
    @app.get("/excluded")
    def excluded():
        return {"message": "This path is excluded"}
    
    @app.get("/included")
    def included():
        return {"message": "This path is included"}
    
    # Add middleware with exclude_paths
    app.add_middleware(
        RequestLoggingMiddleware,
        exclude_paths={"/excluded"},
        log_request_body=True,
        log_response_body=True
    )
    
    client = TestClient(app)
    
    # Test excluded path
    with patch('src.middleware.request_logger.logger') as mock_logger:
        response = client.get("/excluded")
        assert response.status_code == 200
        # Verify no log was made for excluded path
        mock_logger.info.assert_not_called()
    
    # Test included path
    with patch('src.middleware.request_logger.logger') as mock_logger:
        response = client.get("/included")
        assert response.status_code == 200
        # Verify log was made for included path
        mock_logger.info.assert_called()

def test_json_request_body_formatting():
    """Test JSON formatting in request body logging."""
    app = FastAPI()
    
    @app.post("/json-echo")
    async def json_echo(request: Request):
        body = await request.json()
        return body
    
    # Add middleware
    app.add_middleware(RequestLoggingMiddleware, log_request_body=True, log_response_body=True)
    client = TestClient(app)
    
    # Test with valid JSON
    with patch('src.middleware.request_logger.logger') as mock_logger:
        test_data = {"test": "data"}
        response = client.post("/json-echo", json=test_data)
        assert response.status_code == 200
        
        # Find the call that logs the request body
        request_body_logged = False
        for call_args in mock_logger.info.call_args_list:
            # Check if the string "Request body:" is in the message for any info call
            if len(call_args[0]) > 0 and "Request body:" in call_args[0][0]:
                request_body_logged = True
                break
        
        assert request_body_logged, "Request body was not properly logged"

def test_json_request_body_invalid_json():
    """Test handling of invalid JSON in request body."""
    app = FastAPI()
    
    # Set up middleware first (before routes)
    middleware = RequestLoggingMiddleware(log_request_body=True, log_response_body=True)
    
    # Use a simple mock function to simulate the next middleware
    async def mock_call_next(request):
        # This function will be called by the middleware
        try:
            # Try to parse JSON (this will fail with our mocked request)
            await request.json()
        except:
            pass
        return JSONResponse({"status": "ok"})
    
    # Use a mock request
    mock_request = MagicMock()
    mock_request.method = "POST"
    mock_request.url.path = "/invalid-json"
    mock_request.client.host = "127.0.0.1"
    mock_request.headers = {"user-agent": "test-client"}
    
    # Mock the body method to raise an exception
    async def mock_body():
        raise Exception("Test error")
    
    mock_request.body = mock_body
    
    # Test the middleware
    with patch('src.middleware.request_logger.logger') as mock_logger:
        # Execute the middleware
        import asyncio
        asyncio.run(middleware.dispatch(mock_request, mock_call_next))
        
        # Check if a warning was logged about the failed request body
        warning_logged = False
        for call_args in mock_logger.warning.call_args_list:
            # Check the message for the warning about failed request body
            if len(call_args[0]) > 0 and "Failed to log request body" in call_args[0][0]:
                warning_logged = True
                break
        
        assert warning_logged, "Warning about failed request body logging was not logged"

def test_test_endpoint_response_body():
    """Test logging of response body for /test endpoint."""
    app = FastAPI()
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "Test endpoint"}
    
    # Add middleware
    app.add_middleware(RequestLoggingMiddleware, log_request_body=True, log_response_body=True)
    client = TestClient(app)
    
    # Test with /test endpoint
    with patch('src.middleware.request_logger.logger') as mock_logger:
        response = client.get("/test")
        assert response.status_code == 200
        
        # Check if any info call contains the response body log message
        response_body_logged = False
        for call_args in mock_logger.info.call_args_list:
            if len(call_args[0]) > 0 and "Response body:" in call_args[0][0]:
                response_body_logged = True
                break
        
        assert response_body_logged, "Response body was not properly logged"

def test_submit_endpoint_response_body():
    """Test logging of response body for /submit endpoint."""
    app = FastAPI()
    
    @app.post("/submit")
    def submit_endpoint():
        return {"success": True}
    
    # Add middleware
    app.add_middleware(RequestLoggingMiddleware, log_request_body=True, log_response_body=True)
    client = TestClient(app)
    
    # Test with /submit endpoint
    with patch('src.middleware.request_logger.logger') as mock_logger:
        response = client.post("/submit", json={"data": "test"})
        assert response.status_code == 200
        
        # Check for logs containing path /submit and response body message
        path_logged = False
        response_body_logged = False
        
        for call_args in mock_logger.info.call_args_list:
            # Check for path in structured log format
            if len(call_args[0]) > 0 and "path=/submit" in call_args[0][0]:
                path_logged = True
            
            # Check for response body logging
            if len(call_args[0]) > 0 and "Response body:" in call_args[0][0]:
                response_body_logged = True
        
        assert path_logged, "Path /submit was not properly logged"
        assert response_body_logged, "Response body was not properly logged"

def test_invalid_response_body():
    """Test handling of invalid JSON in response body."""
    app = FastAPI()
    
    # Set up middleware
    middleware = RequestLoggingMiddleware(log_request_body=True, log_response_body=True)
    
    # Create a mock request
    mock_request = MagicMock()
    mock_request.method = "GET"
    mock_request.url.path = "/invalid-json"
    mock_request.client.host = "127.0.0.1"
    mock_request.headers = {"user-agent": "test-client"}
    
    # Create a mock response with invalid JSON
    mock_response = JSONResponse(content="Not JSON")
    
    # Mock the call_next function to return our mock response
    async def mock_call_next(request):
        return mock_response
    
    # Force the JSON parsing to fail when middleware tries to log the response
    with patch('json.loads', side_effect=Exception("Test error")):
        with patch('src.middleware.request_logger.logger') as mock_logger:
            # Execute middleware
            import asyncio
            asyncio.run(middleware.dispatch(mock_request, mock_call_next))
            
            # Check if warning was logged for failing to log response body
            warning_logged = False
            for call_args in mock_logger.warning.call_args_list:
                if len(call_args[0]) > 0 and "Failed to log response body" in call_args[0][0]:
                    warning_logged = True
                    break
            
            assert warning_logged, "Warning about failed response body logging was not logged"

def test_exception_handling():
    """Test exception handling in the middleware."""
    app = FastAPI()
    
    @app.get("/error")
    def error_endpoint():
        raise ValueError("Test error")
    
    # Add middleware
    app.add_middleware(RequestLoggingMiddleware, log_request_body=True, log_response_body=True)
    client = TestClient(app)
    
    # Test error endpoint
    with patch('src.middleware.request_logger.logger') as mock_logger:
        with pytest.raises(ValueError):
            response = client.get("/error")
        
        # Check if error was logged with correct format
        error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
        assert any("Exception during request:" in call for call in error_calls), \
            "Exception was not properly logged"

def test_add_request_logging_middleware():
    """Test the helper function to add middleware."""
    app = FastAPI()
    
    # Add the middleware using the helper function
    add_request_logging_middleware(app, log_request_body=True, log_response_body=True)
    
    # Verify middleware was added by checking the middleware stack
    middleware_found = False
    for middleware in app.user_middleware:
        if middleware.cls == RequestLoggingMiddleware:
            middleware_found = True
            break
    
    assert middleware_found, "Middleware was not added"
    
    # Create test client to make sure middleware works
    client = TestClient(app)
    
    # Test a request to verify middleware is functional
    with patch('src.middleware.request_logger.logger') as mock_logger:
        response = client.get("/")
        # Verify that logger was called (middleware is active)
        mock_logger.info.assert_called() 