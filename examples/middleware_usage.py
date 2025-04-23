"""
Examples of how to use the RequestLoggingMiddleware.

This module provides examples of how to configure and use the RequestLoggingMiddleware
in different scenarios.
"""
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.middleware.request_logger import RequestLoggingMiddleware, add_request_logging_middleware


def basic_usage_example():
    """
    Example of basic usage of the RequestLoggingMiddleware.
    """
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"message": "Hello World"}
    
    # Add the middleware using the helper function
    add_request_logging_middleware(app)
    
    # The middleware is now configured to log all requests except for the default
    # excluded paths: /health, /metrics, /docs, /redoc, /openapi.json
    
    return app


def custom_configuration_example():
    """
    Example of custom configuration for the RequestLoggingMiddleware.
    """
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"message": "Hello World"}
    
    # Add the middleware with custom configuration
    add_request_logging_middleware(
        app,
        exclude_paths=["/health", "/metrics", "/internal"],  # Custom excluded paths
        log_request_body=True,  # Log request bodies
        log_response_body=True,  # Log response bodies
    )
    
    return app


def direct_middleware_usage_example():
    """
    Example of directly adding the middleware instead of using the helper function.
    """
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"message": "Hello World"}
    
    # Add the middleware directly
    app.add_middleware(
        RequestLoggingMiddleware,
        exclude_paths=["/health", "/admin", "/internal"],
        log_request_body=True,
        log_response_body=False,
    )
    
    return app


def multiple_middleware_example():
    """
    Example of using RequestLoggingMiddleware with other middleware.
    """
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"message": "Hello World"}
    
    # Create a custom middleware
    class CustomHeaderMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Custom-Header"] = "Custom Value"
            return response
    
    # Add middleware in the correct order
    # The RequestLoggingMiddleware should be added first so it captures all requests
    add_request_logging_middleware(app)
    
    # Add other middleware after
    app.add_middleware(CustomHeaderMiddleware)
    
    # Now the request flow is:
    # 1. RequestLoggingMiddleware logs the incoming request
    # 2. CustomHeaderMiddleware processes the request
    # 3. Route handler is called
    # 4. CustomHeaderMiddleware adds a custom header to the response
    # 5. RequestLoggingMiddleware logs the response
    
    return app


def production_configuration_example():
    """
    Example of a production configuration for the RequestLoggingMiddleware.
    """
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"message": "Hello World"}
    
    # In production, we want to:
    # - Exclude sensitive paths
    # - Not log request/response bodies (which may contain sensitive info)
    # - Add additional excluded paths for health checks, metrics, etc.
    add_request_logging_middleware(
        app,
        exclude_paths=[
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/internal",
            "/admin",
            "/auth",  # Don't log auth endpoints to avoid logging credentials
        ],
        log_request_body=False,
        log_response_body=False,
    )
    
    return app


def debugging_configuration_example():
    """
    Example of a debugging configuration for the RequestLoggingMiddleware.
    """
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"message": "Hello World"}
    
    # For debugging, we want:
    # - Log everything, including request and response bodies
    # - Minimal excluded paths
    add_request_logging_middleware(
        app,
        exclude_paths=[
            # Just exclude swagger docs to reduce noise
            "/docs",
            "/redoc",
            "/openapi.json",
        ],
        log_request_body=True,
        log_response_body=True,
    )
    
    return app


if __name__ == "__main__":
    # This won't run the examples but shows how you'd import and use them
    print("Example FastAPI applications with RequestLoggingMiddleware")
    print("To run a FastAPI app, use uvicorn:")
    print("uvicorn examples.middleware_usage:app --reload")
    
    # Create an app for demonstration
    app = basic_usage_example() 