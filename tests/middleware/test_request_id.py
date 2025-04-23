"""
Tests for the RequestIDMiddleware.

These tests verify that the RequestIDMiddleware properly assigns
and tracks request IDs throughout the request lifecycle.
"""
import pytest
import re
import uuid
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.middleware.request_id import (
    RequestIDMiddleware, 
    add_request_id_middleware, 
    get_request_id, 
    REQUEST_ID_HEADER
)


class TestRequestIDMiddleware:
    """Tests for the RequestIDMiddleware class."""
    
    @pytest.fixture
    def test_app(self):
        """Create a test FastAPI application."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            # Return the request ID from state for testing
            return {"request_id": get_request_id(request)}
        
        return app
    
    def test_middleware_adds_request_id_header(self, test_app):
        """Test that the middleware adds a request ID header to responses."""
        # Add middleware to app
        test_app.add_middleware(
            RequestIDMiddleware,
            header_name=REQUEST_ID_HEADER,
            generate_if_not_present=True,
            return_header=True
        )
        
        client = TestClient(test_app)
        
        # Make a request
        response = client.get("/test")
        
        # Verify response contains request ID header
        assert REQUEST_ID_HEADER in response.headers
        assert response.headers[REQUEST_ID_HEADER]
        
        # Verify request ID is a valid UUID
        request_id = response.headers[REQUEST_ID_HEADER]
        try:
            uuid.UUID(request_id)
            is_valid_uuid = True
        except ValueError:
            is_valid_uuid = False
        
        assert is_valid_uuid, f"Request ID '{request_id}' is not a valid UUID"
    
    def test_middleware_preserves_existing_request_id(self, test_app):
        """Test that the middleware preserves existing request IDs."""
        # Add middleware to app
        test_app.add_middleware(
            RequestIDMiddleware,
            header_name=REQUEST_ID_HEADER,
            generate_if_not_present=True,
            return_header=True
        )
        
        client = TestClient(test_app)
        
        # Create a custom request ID
        custom_request_id = "custom-id-1234"
        
        # Make a request with a custom request ID header
        response = client.get("/test", headers={REQUEST_ID_HEADER: custom_request_id})
        
        # Verify the response has the same request ID
        assert response.headers[REQUEST_ID_HEADER] == custom_request_id
        
        # Verify the request ID was accessible in the endpoint
        assert response.json()["request_id"] == custom_request_id
    
    def test_middleware_generation_when_not_present(self, test_app):
        """Test that the middleware generates a request ID when not provided."""
        # Add middleware to app
        test_app.add_middleware(
            RequestIDMiddleware,
            header_name=REQUEST_ID_HEADER,
            generate_if_not_present=True,
            return_header=True
        )
        
        client = TestClient(test_app)
        
        # Make a request without a request ID header
        response = client.get("/test")
        
        # Verify a request ID was generated and accessible in the endpoint
        assert response.headers[REQUEST_ID_HEADER]
        assert response.json()["request_id"] == response.headers[REQUEST_ID_HEADER]
    
    def test_middleware_respects_generate_flag(self, test_app):
        """Test that the middleware respects the generate_if_not_present flag."""
        # Add middleware to app with generation disabled
        test_app.add_middleware(
            RequestIDMiddleware,
            header_name=REQUEST_ID_HEADER,
            generate_if_not_present=False,
            return_header=True
        )
        
        client = TestClient(test_app)
        
        # Make a request without a request ID header
        response = client.get("/test")
        
        # Verify the request ID is a placeholder ("-")
        assert response.headers[REQUEST_ID_HEADER] == "-"
        assert response.json()["request_id"] == "-"
    
    def test_middleware_respects_return_header_flag(self, test_app):
        """Test that the middleware respects the return_header flag."""
        # Add middleware to app with return_header disabled
        test_app.add_middleware(
            RequestIDMiddleware,
            header_name=REQUEST_ID_HEADER,
            generate_if_not_present=True,
            return_header=False
        )
        
        client = TestClient(test_app)
        
        # Make a request
        response = client.get("/test")
        
        # Verify no request ID header in response
        assert REQUEST_ID_HEADER not in response.headers
        
        # But the ID should still be accessible in the endpoint
        assert response.json()["request_id"] is not None
    
    def test_add_request_id_middleware_helper(self, test_app):
        """Test the add_request_id_middleware helper function."""
        # Use the helper function to add middleware
        add_request_id_middleware(
            test_app,
            header_name="X-Custom-Request-ID",
            generate_if_not_present=True,
            return_header=True
        )
        
        client = TestClient(test_app)
        
        # Make a request
        response = client.get("/test")
        
        # Verify custom header name was used
        assert "X-Custom-Request-ID" in response.headers
        assert response.headers["X-Custom-Request-ID"]
    
    def test_get_request_id_function(self, test_app):
        """Test the get_request_id utility function."""
        # Add middleware to app
        test_app.add_middleware(
            RequestIDMiddleware,
            header_name=REQUEST_ID_HEADER,
            generate_if_not_present=True,
            return_header=True
        )
        
        client = TestClient(test_app)
        
        # Make a request with a custom request ID
        custom_id = "test-request-id-9876"
        response = client.get("/test", headers={REQUEST_ID_HEADER: custom_id})
        
        # Verify get_request_id function returned the correct ID
        assert response.json()["request_id"] == custom_id


if __name__ == "__main__":
    pytest.main(['-xvs', __file__]) 