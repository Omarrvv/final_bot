"""
Main FastAPI application entry point for the Egypt Tourism Chatbot.
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from fastapi import FastAPI, Request, Depends, Query, HTTPException
from fastapi.staticfiles import StaticFiles 
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import time
from starlette.routing import Match
from typing import Optional, AsyncGenerator, List, Dict, Any, Union
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
import asyncio
import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from src.config import settings
from .middleware.request_logger import add_request_logging_middleware
from .middleware.auth import add_auth_middleware
from .middleware.csrf import add_csrf_middleware

# Add this to handle imports properly
if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables early
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
print(f"Loading .env file from: {dotenv_path}")
load_dotenv(dotenv_path=dotenv_path)

# Print key environment variables for debugging
print(f"USE_NEW_KB value: {os.getenv('USE_NEW_KB')}")
print(f"USE_NEW_API value: {os.getenv('USE_NEW_API')}")

# Import models and routers
from src.chatbot import Chatbot
from src.utils.factory import component_factory
from src.utils.settings import settings
from src.services.session import SessionService
from src.models.api_models import (
    ChatMessageRequest, ChatbotResponse, SuggestionsResponse, 
    ResetResponse, LanguagesResponse, FeedbackRequest, FeedbackResponse,
    ResetRequest
)
from src.api.analytics_api import analytics_router
from src.api.routes.chat import router as chat_router
from src.api.routes.session import router as session_router
from src.api.routes.misc import router as misc_router
from src.routes.knowledge_base import router as knowledge_base_router
# Import auth and protected routers
from src.api.auth import router as auth_router
from src.api.protected import router as protected_router
from src.utils.exceptions import ChatbotError
# Import database router
from src.routes.db_routes import router as database_router

# --- Define Project Root Path ---
# Get the absolute path of the directory containing this file (src/)
src_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get the project root
project_root_dir = os.path.dirname(src_dir)

# Create necessary directories
os.makedirs(os.path.join(project_root_dir, 'data'), exist_ok=True)
os.makedirs(os.path.join(project_root_dir, 'logs'), exist_ok=True)
os.makedirs(os.path.join(project_root_dir, 'configs'), exist_ok=True)
os.makedirs(os.path.join(project_root_dir, 'configs/response_templates'), exist_ok=True)

# --- End Project Root Path ---

# Ensure proper Python path (using the calculated project_root_dir)
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)

# --- Logging Setup --- 
def setup_logging():
    """Configures logging for the application."""
    # Use the calculated project_root_dir for logs directory
    logs_dir = os.path.join(project_root_dir, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    log_file = os.path.join(logs_dir, f'egypt_chatbot_{datetime.now().strftime("%Y%m%d")}.log')
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout) # Log to stdout
    console_handler.setFormatter(formatter)

    # Create file handler for rotating logs (10MB max size, keep 10 backup files)
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=10)
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicates if re-run
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

# Call logging setup immediately
setup_logging()
# Define logger in the global scope AFTER setup
logger = logging.getLogger(__name__) 
logger.info("Logging setup complete.")

# --- End Logging Setup ---

# --- Global variables ---
chatbot_instance: Optional["Chatbot"] = None  # Use string literal for forward reference
session_service: Optional[SessionService] = None  # For auth middleware

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Handles application startup and shutdown events.
    """
    print("[DEBUG] LIFESPAN STARTED!")
    global chatbot_instance, session_service
    logger.info("Application startup: Initializing components...")
    
    # Initialize components using the factory
    logger.info("LIFESPAN: Attempting component_factory.initialize()...")
    component_factory.initialize()
    logger.info("LIFESPAN: component_factory.initialize() finished.")

    logger.info("LIFESPAN: Attempting component_factory.create_chatbot()...")
    chatbot_instance = component_factory.create_chatbot()
    logger.info("LIFESPAN: component_factory.create_chatbot() finished.")
    
    app.state.chatbot = chatbot_instance # Assign to app.state
    logger.info("Chatbot components initialized successfully and attached to app state.")

    # Initialize Redis for session management
    logger.info("Setting up session service...")
    try:
        # Get session service from factory
        session_service = component_factory.get_session_service()
        
        # Handle the case where session_service might be None or a mock
        if session_service and hasattr(session_service, 'redis_uri'):
            # Connect to Redis properly within the async context
            from redis.asyncio import Redis
            redis_uri = session_service.redis_uri
            logger.info(f"Connecting to Redis using URI: {redis_uri}")
            
            redis_client = await Redis.from_url(
                redis_uri,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3
            )
            
            # Update the session service with the real Redis client
            session_service.redis = redis_client
            app.state.session_service = session_service
            logger.info("Redis connection established for SessionService")
    except Exception as e:
        logger.error(f"Failed to set up session service Redis connection: {e}", exc_info=True)
        logger.warning("Session management will use mock Redis client")


    yield # Application runs here
    
    # Shutdown: Clean up resources
    logger.info("Application shutdown: Cleaning up resources...")
    
    # Close Redis connection for SessionService
    if session_service and hasattr(session_service, 'redis') and session_service.redis:
        try:
            await session_service.redis.close()
            logger.info("SessionService Redis connection closed.")
        except Exception as e:
            logger.error(f"Error closing SessionService Redis connection: {e}", exc_info=True)
    
    # Close DB connections
    if chatbot_instance and hasattr(chatbot_instance, 'db_manager'):
        db_manager = chatbot_instance.db_manager
        if hasattr(db_manager, 'close'):
            try:
                db_manager.close()
                logger.info("Database connections closed.")
            except Exception as e:
                logger.error(f"Error closing database manager: {e}")
        else:
            logger.info("No close() method found on db_manager; skipping DB shutdown.")
    
    logger.info("Application shutdown complete.")

# Create FastAPI app instance with lifespan
app = FastAPI(
    title="Egypt Tourism Chatbot API",
    description="API for the Egypt Tourism Chatbot providing information about Egypt's attractions, accommodations, and more.",
    version="1.0.0",
    lifespan=lifespan  
)

logger.info("FastAPI app instance created.")

# --- Middleware Configuration ---
# Add request logging middleware first so it captures all requests including those that might be rejected by CORS
add_request_logging_middleware(app)
logger.info("Request logging middleware added")

# --- CORS Middleware Configuration ---
try:
    from src.middleware.cors import add_cors_middleware, get_default_origins
    
    # Get allowed origins from settings
    allowed_origins = settings.allowed_origins
    if not allowed_origins:
        # Use the default origins function if no origins specified
        allowed_origins = get_default_origins(settings.frontend_url)
        logger.warning(f"No CORS allowed_origins specified. Using defaults: {allowed_origins}")
    
    # Add CORS middleware with our secure implementation
    add_cors_middleware(
        app=app,
        allowed_origins=allowed_origins,
        allow_credentials=True,
        allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allowed_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    )
except Exception as e:
    logger.error(f"Failed to add CORS middleware: {e}", exc_info=True)
    logger.warning("CORS protection will be disabled. This is a security risk.")

# --- Add Auth Middleware ---
import os
is_testing = os.getenv("TESTING", "").lower() == "true" or os.getenv("AUTH_TESTING_MODE", "").lower() == "true"
if is_testing:
    logger.warning("Skipping authentication middleware in test mode")
else:
    try:
        from src.middleware.auth import add_auth_middleware
        from src.services.session import SessionService
        from unittest.mock import MagicMock

        # Create a temporary mock session service for middleware setup
        temp_session_service = SessionService(MagicMock())

        # Define public paths for auth bypass
        public_paths = [
            "/api/chat", "/api/health", "/api/suggestions",
            "/api/languages", "/api/reset", "/api/feedback",
            "/api/v1/auth/login", "/api/v1/auth/logout"
        ]

        add_auth_middleware(
            app=app,
            session_service=temp_session_service,
            public_paths=public_paths,
            testing_mode=False
        )
        logger.info("Authentication middleware added")
    except Exception as e:
        logger.error(f"Failed to add auth middleware: {e}", exc_info=True)
        logger.warning("Authentication will be disabled")

# --- Add CSRF Middleware ---
try:
    exclude_urls = [
        "/docs", "/redoc", "/openapi.json", "/api/health",
        "/api/csrf-token", "/api/chat", "/api/reset", 
        "/api/suggestions", "/api/languages", "/api/feedback",
        "/api/v1/auth/login", "/api/v1/auth/logout"  # Add auth endpoints
    ]
    
    add_csrf_middleware(
        app=app,
        secret=settings.jwt_secret,
        exclude_urls=exclude_urls,
        cookie_secure=settings.env != "development"
    )
    logger.info("CSRF middleware added")
except Exception as e:
    logger.error(f"Failed to add CSRF middleware: {e}", exc_info=True)
    logger.warning("CSRF protection will be disabled")

# --- Include routers ---
app.include_router(chat_router, prefix="/api")
app.include_router(session_router, prefix="/api")
app.include_router(misc_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(knowledge_base_router)
# Include auth and protected routers
app.include_router(auth_router)
app.include_router(protected_router)
# Add database router for direct DB access (debugging/testing only)
app.include_router(database_router)
logger.info("API routers included")

# Basic health check endpoint
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Check the health status of the API."""
    # Simply return OK status without checking for initialized chatbot
    # This makes the health check much faster and less dependent on initialization
    return {"status": "ok", "message": "API is running"}

# --- Serve static files ---
# Set up static file serving for React build
static_folder_path = os.path.join(project_root_dir, 'react-frontend', 'build')
if os.path.exists(static_folder_path):
    logger.info(f"Serving static files from: {static_folder_path}")
    app.mount("/static", StaticFiles(directory=os.path.join(static_folder_path, "static")), name="static")
    
    # Serve React app (catch-all route for client-side routing)
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Check for specific file
        file_path = os.path.join(static_folder_path, full_path)
        if os.path.exists(file_path) and not os.path.isdir(file_path):
            return FileResponse(file_path)
            
        # Default to index.html for client-side routing
        index_path = os.path.join(static_folder_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
            
        # Fallback
        return JSONResponse(
            status_code=404,
            content={"error": "Not found"}
        )
else:
    logger.warning(f"Static folder not found at: {static_folder_path}")
    logger.warning("Static file serving disabled")

print(f"[DEBUG] APP ID: {id(app)}, MODULE: {app.__module__}")
# Entry point for direct execution
if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "5050"))
    host = os.getenv("API_HOST", "0.0.0.0")
    logger.info(f"Starting uvicorn server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)