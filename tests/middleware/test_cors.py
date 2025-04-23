"""
Tests for the CORS middleware configuration.

These tests verify that the CORS middleware is properly configured
with secure defaults and appropriate headers.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.middleware.cors import add_cors_middleware, get_default_origins


class TestCORSMiddleware:
    """Tests for the CORS middleware configuration."""
    
    @pytest.fixture
    def test_app(self):
        """Create a test FastAPI application."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "Test endpoint"}
        
        return app
    
    def test_add_cors_middleware_with_defaults(self, test_app):
        """Test that the CORS middleware is added with secure defaults."""
        with patch("src.middleware.cors.logger") as mock_logger:
            # Add middleware with no parameters (should use secure defaults)
            add_cors_middleware(test_app)
            
            # Since no origins are specified, it should log a warning
            mock_logger.warning.assert_called_with(
                "No allowed origins specified for CORS. All origins will be blocked."
            )
            
            # Create client and make request from a different origin
            client = TestClient(test_app)
            response = client.get(
                "/test",
                headers={"Origin": "http://example.com"}
            )
            
            # Should not include CORS headers because no origins are allowed
            assert "access-control-allow-origin" not in response.headers
    
    def test_cors_with_specific_origins(self, test_app):
        """Test CORS middleware with specific allowed origins."""
        allowed_origins = ["http://example.com", "http://localhost:3000"]
        
        with patch("src.middleware.cors.logger") as mock_logger:
            # Add middleware with specific origins
            add_cors_middleware(test_app, allowed_origins=allowed_origins)
            
            # Should log info with the origins
            mock_logger.info.assert_called_with(
                f"CORS middleware added with allowed origins: {allowed_origins}"
            )
            
            # Create client and make request from an allowed origin
            client = TestClient(test_app)
            
            # Test allowed origin
            response = client.get(
                "/test",
                headers={"Origin": "http://example.com"}
            )
            
            # Should include CORS headers for allowed origin
            assert response.headers["access-control-allow-origin"] == "http://example.com"
            
            # Test disallowed origin
            response = client.get(
                "/test",
                headers={"Origin": "http://disallowed.com"}
            )
            
            # Should not include CORS headers for disallowed origin
            assert "access-control-allow-origin" not in response.headers
    
    def test_cors_with_wildcard_warning(self, test_app):
        """Test warning when using wildcard origin."""
        with patch("src.middleware.cors.logger") as mock_logger:
            # Add middleware with wildcard origin
            add_cors_middleware(test_app, allowed_origins=["*"])
            
            # Should log a security warning
            mock_logger.warning.assert_called_with(
                "SECURITY WARNING: CORS is configured to allow ALL origins ('*'). "
                "This is not recommended for production environments. "
                "Consider specifying explicit allowed origins instead."
            )
            
            # Create client and make request from any origin
            client = TestClient(test_app)
            response = client.get(
                "/test",
                headers={"Origin": "http://any-origin.com"}
            )
            
            # Should include CORS headers for any origin
            assert response.headers["access-control-allow-origin"] == "http://any-origin.com"
    
    def test_cors_with_custom_methods(self, test_app):
        """Test CORS middleware with custom allowed methods."""
        allowed_methods = ["GET", "POST"]
        
        # Add middleware with specific origins and methods
        add_cors_middleware(
            test_app, 
            allowed_origins=["http://example.com"],
            allowed_methods=allowed_methods
        )
        
        # Create client
        client = TestClient(test_app)
        
        # Make an OPTIONS request (preflight) to test allowed methods
        response = client.options(
            "/test",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        # Should include allowed methods header
        assert "access-control-allow-methods" in response.headers
        
        # The header might be comma-separated, so split and check
        allowed_methods_header = response.headers["access-control-allow-methods"].split(", ")
        for method in allowed_methods:
            assert method in allowed_methods_header
    
    def test_cors_with_custom_headers(self, test_app):
        """Test CORS middleware with custom allowed headers."""
        allowed_headers = ["X-Custom-Header", "Content-Type"]
        
        # Add middleware with specific origins and headers
        add_cors_middleware(
            test_app, 
            allowed_origins=["http://example.com"],
            allowed_headers=allowed_headers
        )
        
        # Create client
        client = TestClient(test_app)
        
        # Make an OPTIONS request (preflight) to test allowed headers
        response = client.options(
            "/test",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-Custom-Header, Content-Type"
            }
        )
        
        # Should include allowed headers header
        assert "access-control-allow-headers" in response.headers
        
        # The header might be comma-separated, so split and check
        allowed_headers_header = response.headers["access-control-allow-headers"].lower().split(", ")
        for header in allowed_headers:
            assert header.lower() in allowed_headers_header
    
    def test_cors_with_credentials(self, test_app):
        """Test CORS middleware with credentials allowed."""
        # Add middleware with credentials allowed
        add_cors_middleware(
            test_app, 
            allowed_origins=["http://example.com"],
            allow_credentials=True
        )
        
        # Create client
        client = TestClient(test_app)
        
        # Make a request from an allowed origin
        response = client.get(
            "/test",
            headers={"Origin": "http://example.com"}
        )
        
        # Should include allow credentials header
        assert response.headers["access-control-allow-credentials"] == "true"
    
    def test_get_default_origins(self):
        """Test the get_default_origins function."""
        # Test with no frontend URL
        origins = get_default_origins()
        
        # Should include localhost variations
        assert "http://localhost:3000" in origins
        assert "http://localhost:8000" in origins
        assert "http://127.0.0.1:3000" in origins
        
        # Test with frontend URL
        frontend_url = "https://example.com"
        origins = get_default_origins(frontend_url)
        
        # Should include the frontend URL
        assert frontend_url in origins
        # Should include www variation
        assert "https://www.example.com" in origins
        
        # Test with www frontend URL
        frontend_url = "https://www.app.com"
        origins = get_default_origins(frontend_url)
        
        # Should include the frontend URL
        assert frontend_url in origins
        # Should include non-www variation
        assert "https://app.com" in origins


if __name__ == "__main__":
    pytest.main(['-xvs', __file__]) 