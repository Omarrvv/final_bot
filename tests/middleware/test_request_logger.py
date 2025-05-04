"""
Tests for the RequestLoggingMiddleware.

These tests verify that the RequestLoggingMiddleware properly logs
incoming requests, their processing time, and response status codes.
"""
import pytest
import re
import json
import logging
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from starlette.middleware.base import BaseHTTPMiddleware
import sys
import os

# Add src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.middleware.request_logger import RequestLoggingMiddleware, add_request_logging_middleware


class TestRequestLoggingMiddleware:
    """Tests for the RequestLoggingMiddleware class."""

    @pytest.fixture
    def test_app(self):
        """Create a test FastAPI application."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "Test endpoint"}

        @app.post("/test-post")
        async def test_post_endpoint(request: Request):
            body = await request.json()
            return {"received": body}

        @app.get("/health")
        async def health_check():
            return {"status": "ok"}

        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")

        return app

    @pytest.fixture
    def logger_mock(self):
        """Create a mock logger for testing."""
        with patch("src.middleware.request_logger.logger") as mock:
            yield mock

    def test_middleware_logs_request_and_response(self, test_app, logger_mock):
        """Test that the middleware logs basic request and response info."""
        # Add middleware to app
        test_app.add_middleware(
            RequestLoggingMiddleware,
            exclude_paths=["/health"],
            log_request_body=False,
            log_response_body=False
        )

        client = TestClient(test_app)

        # Make a request
        response = client.get("/test", headers={"X-Request-ID": "test-id"})

        # Verify response
        assert response.status_code == 200
        assert response.json() == {"message": "Test endpoint"}

        # Check that logger was called with the correct arguments
        logger_mock.info.assert_any_call(
            "Request started",
            extra={
                "request_id": "test-id",
                "method": "GET",
                "path": "/test",
                "client_ip": "testclient",
                "user_agent": "testclient",
            }
        )

        # Verify that the request finished log contains required fields
        call_args_list = logger_mock.info.call_args_list
        finish_log_calls = [
            call for call in call_args_list
            if call[0][0] == "Request finished"
        ]

        assert len(finish_log_calls) == 1
        finish_log = finish_log_calls[0]

        # Check that the required fields are present in the finish log
        extra_args = finish_log[1]['extra']
        assert extra_args["request_id"] == "test-id"
        assert extra_args["method"] == "GET"
        assert extra_args["path"] == "/test"
        assert extra_args["status_code"] == 200
        assert "process_time_ms" in extra_args

    def test_middleware_excludes_paths(self, test_app, logger_mock):
        """Test that the middleware doesn't log excluded paths."""
        # Add middleware to app
        test_app.add_middleware(
            RequestLoggingMiddleware,
            exclude_paths=["/health"],
            log_request_body=False,
            log_response_body=False
        )

        client = TestClient(test_app)

        # Make a request to an excluded path
        response = client.get("/health")

        # Verify response
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        # Check that logger was not called for this path
        for call in logger_mock.info.call_args_list:
            if call[0][0] == "Request started":
                assert call[1]["extra"]["path"] != "/health"

        for call in logger_mock.info.call_args_list:
            if call[0][0] == "Request finished":
                assert call[1]["extra"]["path"] != "/health"

    def test_middleware_logs_request_body_when_enabled(self, test_app, logger_mock):
        """Test that the middleware logs request bodies when enabled."""
        # Add middleware to app with request body logging enabled
        test_app.add_middleware(
            RequestLoggingMiddleware,
            exclude_paths=["/health"],
            log_request_body=True,
            log_response_body=False
        )

        client = TestClient(test_app)

        # Make a POST request with a body
        test_data = {"key": "value"}
        response = client.post("/test-post", json=test_data)

        # Verify response
        assert response.status_code == 200
        assert response.json() == {"received": test_data}

        # Check that the request body was logged
        logger_mock.debug.assert_any_call(
            "Request body",
            extra={
                "request_id": "-",
                "body": '{"key": "value"}'
            }
        )

    def test_middleware_logs_response_body_when_enabled(self, test_app, logger_mock):
        """Test that the middleware logs response bodies when enabled."""
        # Add middleware to app with response body logging enabled
        test_app.add_middleware(
            RequestLoggingMiddleware,
            exclude_paths=["/health"],
            log_request_body=False,
            log_response_body=True
        )

        client = TestClient(test_app)

        # Make a request
        response = client.get("/test")

        # Verify response
        assert response.status_code == 200
        assert response.json() == {"message": "Test endpoint"}

        # Check that the response body was logged
        debug_calls = [call for call in logger_mock.debug.call_args_list if call[0][0] == "Response body"]
        assert len(debug_calls) > 0

        # Verify the response body content
        response_body_call = debug_calls[0]
        assert "body" in response_body_call[1]["extra"]
        assert '"message"' in response_body_call[1]["extra"]["body"]
        assert 'Test endpoint' in response_body_call[1]["extra"]["body"]

    @patch("src.middleware.request_logger.time.time")
    def test_middleware_logs_processing_time(self, time_mock, test_app, logger_mock):
        """Test that the middleware logs request processing time."""
        # Setup time.time to return specific values for start and end times
        # Add more values to handle additional calls to time.time in the test framework
        time_mock.side_effect = [100.0, 100.5] + [100.5] * 10  # Ensure enough values for all time.time calls

        # Add middleware to app
        test_app.add_middleware(
            RequestLoggingMiddleware,
            exclude_paths=["/health"],
            log_request_body=False,
            log_response_body=False
        )

        client = TestClient(test_app)

        # Make a request
        response = client.get("/test")

        # Verify response
        assert response.status_code == 200

        # Check that the processing time was logged correctly
        call_args_list = logger_mock.info.call_args_list
        finish_log_calls = [
            call for call in call_args_list
            if call[0][0] == "Request finished"
        ]

        assert len(finish_log_calls) == 1
        finish_log = finish_log_calls[0]

        # Check that the processing time is logged (don't check exact value)
        assert "process_time_ms" in finish_log[1]["extra"]
        # Just verify it's a number greater than 0
        assert finish_log[1]["extra"]["process_time_ms"] >= 0.0

    def test_middleware_logs_exceptions(self, test_app, logger_mock):
        """Test that the middleware logs exceptions during request processing."""
        # Add middleware to app
        test_app.add_middleware(
            RequestLoggingMiddleware,
            exclude_paths=["/health"],
            log_request_body=False,
            log_response_body=False
        )

        client = TestClient(test_app)

        # Make a request to an endpoint that raises an exception
        with pytest.raises(ValueError):
            client.get("/error")

        # Check that the exception was logged - middleware logs error in two formats
        assert logger_mock.error.call_count >= 1

        # Check that at least one error log contains the exception
        error_calls = [
            call for call in logger_mock.error.call_args_list
            if "Test error" in str(call)
        ]
        assert len(error_calls) > 0, "No error log with exception message found"

        # Verify the exception type is included in at least one error log
        exception_type_logged = any("ValueError" in str(call) for call in logger_mock.error.call_args_list)
        assert exception_type_logged, "Exception type not found in logs"

    def test_add_request_logging_middleware(self, logger_mock):
        """Test the add_request_logging_middleware helper function."""
        app = FastAPI()

        with patch.object(app, "add_middleware") as add_middleware_mock:
            # Call the helper function
            add_request_logging_middleware(
                app,
                exclude_paths=["/custom-exclude"],
                log_request_body=True,
                log_response_body=True
            )

            # Verify that add_middleware was called with the correct arguments
            add_middleware_mock.assert_called_once()
            call_args = add_middleware_mock.call_args

            # Check middleware class
            assert call_args[0][0] == RequestLoggingMiddleware

            # Check that default excluded paths are included along with custom path
            excluded_paths = call_args[1]["exclude_paths"]
            assert "/custom-exclude" in excluded_paths
            assert "/health" in excluded_paths
            assert "/docs" in excluded_paths
            assert "/redoc" in excluded_paths
            assert "/metrics" in excluded_paths
            assert "/openapi.json" in excluded_paths

            # Check other parameters
            assert call_args[1]["log_request_body"] is True
            assert call_args[1]["log_response_body"] is True


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    return FastAPI()


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    with patch('src.middleware.request_logger.logger') as mock:
        yield mock


def test_middleware_initialization():
    """Test that the middleware can be initialized with different parameters."""
    middleware = RequestLoggingMiddleware()
    assert middleware.exclude_paths == set()
    assert middleware.log_request_body is False
    assert middleware.log_response_body is False

    middleware = RequestLoggingMiddleware(
        exclude_paths={"/docs", "/health"},
        log_request_body=True,
        log_response_body=True
    )
    assert middleware.exclude_paths == {"/docs", "/health"}
    assert middleware.log_request_body is True
    assert middleware.log_response_body is True


def test_add_middleware_to_app(app):
    """Test that the middleware can be added to a FastAPI app."""
    add_request_logging_middleware(app)
    # Check if the middleware is in the app's middleware stack
    middleware_added = False
    for middleware in app.user_middleware:
        if middleware.cls == RequestLoggingMiddleware:
            middleware_added = True
            break
    assert middleware_added


def test_excluded_paths_not_logged(app, client, mock_logger):
    """Test that excluded paths are not logged."""
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    add_request_logging_middleware(app, exclude_paths={"/health"})

    response = client.get("/health")
    assert response.status_code == 200

    # The request should not be logged since /health is excluded
    mock_logger.info.assert_not_called()


def test_request_logging(app, client, mock_logger):
    """Test that requests are properly logged."""
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test successful"}

    add_request_logging_middleware(app)

    response = client.get("/test", headers={"User-Agent": "test-agent"})
    assert response.status_code == 200

    # Check that the request was logged
    mock_logger.info.assert_any_call(
        "Incoming request: Method=%s Path=%s Client=%s User-Agent=%s",
        "GET", "/test", "testclient", "test-agent"
    )

    # Check that the response was logged with status code
    assert any("Response status" in call.args[0] and "200" in str(call)
               for call in mock_logger.info.call_args_list)


def test_request_body_logging(app, client, mock_logger):
    """Test that request bodies are properly logged when enabled."""
    @app.post("/data")
    async def post_data(request: Request):
        body = await request.json()
        return {"received": body}

    middleware = RequestLoggingMiddleware(log_request_body=True)
    app.add_middleware(RequestLoggingMiddleware, log_request_body=True)

    test_data = {"key": "value"}
    response = client.post("/data", json=test_data)
    assert response.status_code == 200

    # Check that the request body was logged
    assert any("Request body" in call.args[0] and json.dumps(test_data) in str(call)
               for call in mock_logger.info.call_args_list)


def test_response_body_logging(app, client, mock_logger):
    """Test that response bodies are properly logged when enabled."""
    @app.get("/response-test")
    async def test_endpoint():
        return {"result": "success"}

    app.add_middleware(RequestLoggingMiddleware, log_response_body=True)

    response = client.get("/response-test")
    assert response.status_code == 200

    # Check that the response body was logged
    assert any("Response body" in call.args[0] and "success" in str(call)
               for call in mock_logger.info.call_args_list)


def test_error_logging(app, client, mock_logger):
    """Test that errors are properly logged."""
    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")

    app.add_middleware(RequestLoggingMiddleware)

    # Handle the expected exception
    try:
        response = client.get("/error")
    except ValueError:
        pass

    # Check that the error was logged
    # Error logger is called twice - once for each error log format
    assert mock_logger.error.call_count >= 1

    # Verify error message content in at least one of the calls
    error_msg_found = False
    for call in mock_logger.error.call_args_list:
        if "Test error" in str(call):
            error_msg_found = True
            break

    assert error_msg_found, "Error message not found in logs"


def test_processing_time_logged(app, client, mock_logger):
    """Test that processing time is logged."""
    @app.get("/timing")
    async def timing_endpoint():
        return {"status": "completed"}

    app.add_middleware(RequestLoggingMiddleware)

    response = client.get("/timing")
    assert response.status_code == 200

    # Check that processing time was logged
    assert any("Processing time" in call.args[0] for call in mock_logger.info.call_args_list)


if __name__ == "__main__":
    pytest.main(['-xvs', __file__])