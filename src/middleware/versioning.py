"""
API Versioning Middleware
Adds consistent version headers to all API responses.
QUICK WIN: Non-breaking enhancement for better API design.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class APIVersioningMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add consistent API version headers to all responses.
    This is a quick win that improves API design without breaking existing functionality.
    """
    
    def __init__(self, app, api_version: str = "v1"):
        super().__init__(app)
        self.api_version = api_version
    
    async def dispatch(self, request: Request, call_next):
        """Add version headers to all API responses"""
        response = await call_next(request)
        
        # Only add headers to API endpoints
        if request.url.path.startswith("/api"):
            # Add standard API version headers
            response.headers["X-API-Version"] = self.api_version
            response.headers["X-API-Spec"] = "OpenAPI 3.0"
            
            # Add deprecation warning for legacy endpoints
            if not request.url.path.startswith("/api/v1"):
                response.headers["X-API-Deprecated"] = "true"
                response.headers["X-API-Deprecation-Info"] = f"Use /api/v1{request.url.path[4:]} instead"
                response.headers["X-API-Sunset"] = "2025-06-01"  # 6 months from now
            
            # Add content type if not set
            if "content-type" not in response.headers:
                response.headers["Content-Type"] = "application/json"
        
        return response

def add_versioning_middleware(app, api_version: str = "v1"):
    """
    Add API versioning middleware to the FastAPI app.
    
    Args:
        app: FastAPI application instance
        api_version: Current API version (default: v1)
    """
    app.add_middleware(APIVersioningMiddleware, api_version=api_version)
    logger.info(f"✅ API versioning middleware added (version: {api_version})")
