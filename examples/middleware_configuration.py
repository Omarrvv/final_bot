"""
Example of complete middleware configuration for FastAPI.

This module demonstrates how to configure all middleware components
for a FastAPI application in the correct order with appropriate settings.
"""
import os
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse

from src.middleware.request_logger import add_request_logging_middleware
from src.middleware.request_id import add_request_id_middleware
from src.middleware.cors import add_cors_middleware, get_default_origins
from src.middleware.exception_handler import add_exception_handler_middleware


def create_app(debug: bool = False):
    """
    Create a FastAPI application with all middleware properly configured.
    
    Args:
        debug: Whether to run the application in debug mode
        
    Returns:
        A configured FastAPI application
    """
    # Create the FastAPI app
    app = FastAPI(
        title="Egypt Tourism Chatbot API",
        description="API for the Egypt Tourism Chatbot",
        version="1.0.0",
        docs_url="/docs" if debug else None  # Hide docs in production
    )
    
    # --- Middleware Configuration ---
    # The order of middleware is important. The first middleware added is
    # the outermost in the ASGI chain and will be executed first on the request
    # and last on the response.
    
    # 1. Request ID Middleware (first, so all logs have request IDs)
    add_request_id_middleware(app)
    
    # 2. Request Logging Middleware (logs all incoming requests and responses)
    add_request_logging_middleware(
        app,
        exclude_paths=[
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json"
        ],
        log_request_body=debug,  # Only log bodies in debug mode
        log_response_body=debug  # Only log response bodies in debug mode
    )
    
    # 3. Exception Handler Middleware (convert exceptions to appropriate responses)
    add_exception_handler_middleware(
        app,
        debug=debug,
        include_traceback=debug  # Only include tracebacks in debug mode
    )
    
    # 4. CORS Middleware (handle cross-origin requests)
    # Get allowed origins from environment or use defaults
    frontend_url = os.environ.get("FRONTEND_URL")
    allowed_origins = get_default_origins(frontend_url)
    
    # Add CORS middleware with appropriate settings
    add_cors_middleware(
        app,
        allowed_origins=allowed_origins,
        allow_credentials=True
    )
    
    # --- Route Configuration ---
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "message": "API is running"}
    
    # Example error endpoint to demonstrate error handling
    @app.get("/example-error")
    async def example_error():
        """Example endpoint that raises an error to demonstrate error handling."""
        raise ValueError("This is an example error")
    
    # Add routes for actual API endpoints (typically imported from router modules)
    # app.include_router(api_router, prefix="/api")
    
    return app


# Example usage
if __name__ == "__main__":
    import uvicorn
    
    # Create the app with debug mode enabled for local development
    app = create_app(debug=True)
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5050,
        log_level="info"
    ) 