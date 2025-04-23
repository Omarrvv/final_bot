"""
Tests for the Exception Handler middleware.

These tests verify that the exception handler middleware properly catches
and handles different types of exceptions, converting them to consistent API responses.
"""
import pytest
from fastapi import FastAPI, status, HTTPException, Request, Depends
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.middleware.exception_handler import (
    ExceptionHandlerMiddleware,
    add_exception_handler_middleware
)
from src.utils import exceptions as app_exceptions


class TestExceptionHandlerMiddleware:
    """Tests for the ExceptionHandlerMiddleware class."""
    
    @pytest.fixture
    def test_app(self):
        """Create a test FastAPI application with exception-raising endpoints."""
        app = FastAPI()
        
        @app.get("/ok")
        async def ok_endpoint():
            return {"status": "ok"}
        
        @app.get("/http-exception")
        async def http_exception_endpoint():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Bad request error"
            )
        
        @app.get("/chatbot-error")
        async def chatbot_error_endpoint():
            raise app_exceptions.ChatbotError(
                message="Custom error message",
                details={"reason": "test error"}
            )
        
        @app.get("/validation-error")
        async def validation_error_endpoint():
            raise app_exceptions.ValidationError(
                message="Validation failed",
                errors={"field": "username", "error": "Cannot be empty"}
            )
        
        @app.get("/not-found-error")
        async def not_found_error_endpoint():
            raise app_exceptions.ResourceNotFoundError(
                resource_type="test",
                resource_id="123",
                message="Resource not found"
            )
        
        @app.get("/unauthorized-error")
        async def unauthorized_error_endpoint():
            raise app_exceptions.AuthenticationError(
                message="Authentication required",
                details={"token": "invalid"}
            )
        
        @app.get("/forbidden-error")
        async def forbidden_error_endpoint():
            raise app_exceptions.AuthorizationError(
                message="Access denied",
                details={"required_role": "admin"}
            )
        
        @app.get("/unexpected-error")
        async def unexpected_error_endpoint():
            raise ValueError("Unexpected error occurred")
        
        return app
    
    def test_middleware_allows_successful_requests(self, test_app):
        """Test that successful requests pass through the middleware unchanged."""
        # Add middleware to app
        add_exception_handler_middleware(test_app)
        
        client = TestClient(test_app)
        
        # Make a successful request
        response = client.get("/ok")
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "ok"}
    
    def test_middleware_handles_http_exceptions(self, test_app):
        """Test that HTTP exceptions are properly handled."""
        # Add middleware to app
        add_exception_handler_middleware(test_app)
        
        client = TestClient(test_app)
        
        # Make a request that raises an HTTP exception
        response = client.get("/http-exception")
        
        # Verify response
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Bad request error"
    
    def test_middleware_handles_chatbot_errors(self, test_app):
        """Test that ChatbotError exceptions are properly handled."""
        # Add middleware to app
        add_exception_handler_middleware(test_app)
        
        client = TestClient(test_app)
        
        # Make a request that raises a ChatbotError
        response = client.get("/chatbot-error")
        
        # Verify response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "CHATBOT_ERROR"
        assert data["error"]["message"] == "Custom error message"
        assert data["error"]["details"] == {"reason": "test error"}
    
    def test_middleware_handles_validation_errors(self, test_app):
        """Test that ValidationError exceptions are properly handled."""
        # Add middleware to app
        add_exception_handler_middleware(test_app)
        
        client = TestClient(test_app)
        
        # Make a request that raises a ValidationError
        response = client.get("/validation-error")
        
        # Verify response
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["message"] == "Validation failed"
        assert data["error"]["details"] == {"errors": {"field": "username", "error": "Cannot be empty"}}
    
    def test_middleware_handles_not_found_errors(self, test_app):
        """Test that NotFoundError exceptions are properly handled."""
        # Add middleware to app
        add_exception_handler_middleware(test_app)
        
        client = TestClient(test_app)
        
        # Make a request that raises a NotFoundError
        response = client.get("/not-found-error")
        
        # Verify response
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert data["error"]["message"] == "Resource not found"
        assert data["error"]["details"] == {"resource_type": "test", "resource_id": "123"}
    
    def test_middleware_handles_unauthorized_errors(self, test_app):
        """Test that UnauthorizedError exceptions are properly handled."""
        # Add middleware to app
        add_exception_handler_middleware(test_app)
        
        client = TestClient(test_app)
        
        # Make a request that raises an UnauthorizedError
        response = client.get("/unauthorized-error")
        
        # Verify response
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"
        assert data["error"]["message"] == "Authentication required"
        assert data["error"]["details"] == {"token": "invalid"}
    
    def test_middleware_handles_forbidden_errors(self, test_app):
        """Test that ForbiddenError exceptions are properly handled."""
        # Add middleware to app
        add_exception_handler_middleware(test_app)
        
        client = TestClient(test_app)
        
        # Make a request that raises a ForbiddenError
        response = client.get("/forbidden-error")
        
        # Verify response
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "AUTHORIZATION_ERROR"
        assert data["error"]["message"] == "Access denied"
        assert data["error"]["details"] == {"required_role": "admin"}
    
    def test_middleware_handles_unexpected_errors(self, test_app):
        """Test that unexpected exceptions are properly handled."""
        # Add middleware to app in non-debug mode
        add_exception_handler_middleware(test_app, debug=False)
        
        client = TestClient(test_app)
        
        # Make a request that raises an unexpected error
        response = client.get("/unexpected-error")
        
        # Verify response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        # In non-debug mode, message should be generic
        assert data["error"]["message"] == "An unexpected error occurred"
        # Should not have traceback in non-debug mode
        assert "traceback" not in data["error"]
    
    def test_middleware_debug_mode(self, test_app):
        """Test that debug mode provides more detailed error information."""
        # Add middleware to app in debug mode with traceback
        add_exception_handler_middleware(test_app, debug=True, include_traceback=True)
        
        client = TestClient(test_app)
        
        # Make a request that raises an unexpected error
        response = client.get("/unexpected-error")
        
        # Verify response
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        # In debug mode, message should contain the actual error
        assert "Unexpected error occurred" in data["error"]["message"]
        # Should have traceback in debug mode
        assert "traceback" in data["error"]
        assert "ValueError" in data["error"]["traceback"]
    
    def test_middleware_logs_errors(self, test_app):
        """Test that the middleware logs errors appropriately."""
        with patch("src.middleware.exception_handler.logger") as mock_logger:
            # Add middleware to app
            add_exception_handler_middleware(test_app)
            
            client = TestClient(test_app)
            
            # Make a request that raises an error
            response = client.get("/unexpected-error")
            
            # Verify that logger.exception was called
            mock_logger.exception.assert_called_once()
            call_args = mock_logger.exception.call_args[0]
            assert "Unexpected error" in call_args[0]


if __name__ == "__main__":
    pytest.main(['-xvs', __file__]) 