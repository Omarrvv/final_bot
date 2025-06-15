"""
Main FastAPI application entry point for the Egypt Tourism Chatbot.
Phase 4: Added performance monitoring and comprehensive health checks.
"""
import os
import sys
import logging
import time
from logging.handlers import RotatingFileHandler
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
import uvicorn

# Fix Python path when running from src directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
# UNIFIED CONFIGURATION - Single source of truth
try:
    from src.config_unified import settings
except ImportError:
    from config_unified import settings

try:
    from .middleware.core import add_core_middleware
    from .middleware.auth import add_auth_middleware
    from .middleware.security import add_csrf_middleware
    from .middleware.performance import add_performance_middleware
except ImportError:
    from middleware.core import add_core_middleware
    from middleware.auth import add_auth_middleware
    from middleware.security import add_csrf_middleware
    from middleware.performance import add_performance_middleware

# Add this to handle imports properly
if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables early
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
print(f"Loading .env file from: {dotenv_path}")
load_dotenv(dotenv_path=dotenv_path)

# Environment variables are loaded from .env file

# Import models and routers
from src.chatbot import Chatbot
from src.utils.factory import component_factory
# NOTE: settings imported from unified config above - no more conflicts!
# Import routers
from src.api.analytics_api import analytics_router
from src.api.routes.chat import router as chat_router
from src.api.routes.session import router as session_router
from src.api.routes.misc import router as misc_router
from src.api.routes.knowledge_base import router as knowledge_base_router
# Auth router for session-based authentication
from src.api.auth import router as auth_router
# Import database router
from src.api.routes.db_routes import router as database_router
# Import enhanced session manager
from src.session.enhanced_session_manager import EnhancedSessionManager
from src.session.integration import integrate_enhanced_session_manager
# Phase 4: Health check router
try:
    from .api.routes.health import router as health_router
except ImportError:
    from api.routes.health import router as health_router

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
session_manager = None  # For auth middleware

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Handles application startup and shutdown events.
    """
    print("[DEBUG] LIFESPAN STARTED!")
    global chatbot_instance, session_manager
    logger.info("Application startup: Initializing components...")

    # Initialize components using the factory
    logger.info("LIFESPAN: Attempting component_factory.initialize()...")
    component_factory.initialize()
    logger.info("LIFESPAN: component_factory.initialize() finished.")

    # Create enhanced session manager first
    logger.info("Setting up enhanced session manager...")
    try:
        # Use our enhanced session manager
        session_manager = integrate_enhanced_session_manager(app)
        app.state.session_manager = session_manager
        logger.info(f"Enhanced session manager initialized: {type(session_manager).__name__}")
    except Exception as e:
        logger.error(f"Failed to set up enhanced session manager: {e}", exc_info=True)
        logger.warning("Falling back to standard session manager")
        try:
            # Fallback to cached container session manager (Phase 1 optimization)
            from src.utils.container import container
            session_manager = container.get("session_manager")
            app.state.session_manager = session_manager
            logger.info(f"Fallback session manager initialized via cached container: {type(session_manager).__name__}")
        except Exception as e2:
            logger.error(f"Failed to set up fallback session manager: {e2}", exc_info=True)
            logger.warning("Session management will use minimal implementation")

    # PHASE 2: AI Model Preloading Optimization
    logger.info("🚀 PHASE 2: Starting AI model preloading during startup...")
    preload_start_time = time.time()
    
    # Create chatbot using cached container (Phase 1 optimization)
    logger.info("LIFESPAN: Creating chatbot via cached container...")
    from src.utils.container import container
    chatbot_instance = container.get("chatbot")
    logger.info("LIFESPAN: Chatbot created via cached container (Phase 1 optimized).")

    # PHASE 3: Async Model Loading Optimization  
    logger.info("🚀 PHASE 3: Starting async AI model loading optimization...")
    model_load_start = time.time()
    
    try:
        # Get NLU engine from container for async model loading
        from src.utils.container import container
        nlu_engine = container.get("nlu_engine")
        
        # Phase 3: Trigger async model loading in background
        logger.info("⚡ Phase 3: Starting async model loading in background...")
        
        # Check if the engine supports async loading
        if hasattr(nlu_engine, '_load_models_async'):
            # Load models asynchronously for maximum speed
            await nlu_engine._load_models_async()
            logger.info("🎯 Phase 3: Async model loading completed successfully")
        else:
            logger.info("📚 Using synchronous model loading (models already loaded)")
        
        # Phase 3: Smart Model Warmup (only if models are loaded)
        if hasattr(nlu_engine, '_models_loaded') and nlu_engine._models_loaded:
            logger.info("🔥 Phase 3: Warming up models with strategic queries...")
            warmup_start = time.time()
            
            # Strategic warmup queries for tourism chatbot
            warmup_queries = [
                ("hello", "Basic greeting pattern"),
                ("pyramids", "Common attraction query"),
                ("hotel in cairo", "Service + location query"),
                ("مرحبا", "Arabic greeting"),
                ("weather", "Practical information")
            ]
            
            warmup_success = 0
            for i, (query, description) in enumerate(warmup_queries, 1):
                try:
                    logger.info(f"  Warmup {i}/{len(warmup_queries)}: {description} - '{query}'")
                    
                    # Use async processing for warmup
                    await nlu_engine.process_async(
                        text=query,
                        session_id="phase3_warmup",
                        language="auto"
                    )
                    warmup_success += 1
                    
                except Exception as warmup_error:
                    logger.warning(f"  ⚠️ Warmup {i} failed: {warmup_error}")
            
            warmup_time = time.time() - warmup_start
            logger.info(f"🎯 Phase 3: Model warmup completed - {warmup_success}/{len(warmup_queries)} successful in {warmup_time:.2f}s")
        
        model_load_time = time.time() - model_load_start
        logger.info(f"🏆 PHASE 3: Complete model optimization finished in {model_load_time:.2f}s")
        
        # Force regenerate intent embeddings after successful model loading
        logger.info("🔄 Force regenerating intent embeddings after async model loading...")
        try:
            if hasattr(nlu_engine, 'force_regenerate_intent_embeddings'):
                success = nlu_engine.force_regenerate_intent_embeddings()
                if success:
                    logger.info("✅ Intent embeddings successfully regenerated during startup")
                else:
                    logger.warning("⚠️ Intent embedding regeneration failed during startup")
            else:
                logger.warning("⚠️ NLU engine does not support intent embedding regeneration")
        except Exception as regenerate_error:
            logger.error(f"❌ Error regenerating intent embeddings: {regenerate_error}")
        
    except Exception as e:
        logger.error(f"❌ Phase 3 model optimization failed: {e}", exc_info=True)
        logger.warning("⚠️ Falling back to on-demand model loading")

    # Calculate total preload time
    total_preload_time = time.time() - preload_start_time
    logger.info(f"🚀 PHASE 2 COMPLETE: Total preload time {total_preload_time:.2f}s")

    app.state.chatbot = chatbot_instance # Assign to app.state
    app.state.models_preloaded = True  # Flag to indicate models are ready
    logger.info("Chatbot components initialized successfully and attached to app state.")


    yield # Application runs here

    # Shutdown: Clean up resources
    logger.info("Application shutdown: Cleaning up resources...")

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
# Add core middleware first so it captures all requests including those that might be rejected by CORS
add_core_middleware(app, log_request_body=False, log_response_body=False, debug=settings.debug)
logger.info("Core middleware (logging, error handling, request ID) added")

# Phase 1C: Add standardized error handling middleware
try:
    from src.middleware.error_handler import standard_error_handler
    app.middleware("http")(standard_error_handler)
    logger.info("✅ Phase 1C: Standardized error handling middleware added")
except Exception as e:
    logger.error(f"Failed to add error handling middleware: {e}", exc_info=True)
    logger.warning("Standardized error handling will be disabled")

# Phase 4: Add performance monitoring middleware
try:
    performance_middleware = add_performance_middleware(app, slow_request_threshold=1.0)
    logger.info("✅ Phase 4: Performance monitoring middleware added")
except Exception as e:
    logger.error(f"Failed to add performance middleware: {e}", exc_info=True)
    logger.warning("Performance monitoring will be disabled")

# --- CORS Middleware Configuration ---
try:
    from src.middleware.security import add_cors_middleware, get_default_origins

    # Get allowed origins from settings
    allowed_origins = settings.allowed_origins
    if not allowed_origins:
        # Use the default origins function if no origins specified
        allowed_origins = get_default_origins(settings.frontend_url)
        logger.warning(f"No CORS allowed_origins specified. Using defaults: {allowed_origins}")

    # Add CORS middleware with comprehensive configuration
    add_cors_middleware(
        app=app,
        allowed_origins=allowed_origins,
        allow_credentials=True,
        # Use default methods and headers from security middleware (more comprehensive)
        # This ensures proper CORS headers are sent for OPTIONS requests
    )
except Exception as e:
    logger.error(f"Failed to add CORS middleware: {e}", exc_info=True)
    logger.warning("CORS protection will be disabled. This is a security risk.")

# --- Add Auth Middleware ---
# SECURITY FIX: Enable authentication middleware with enhanced control
should_enable_auth = (
    settings.env == "production" or 
    settings.force_security_in_dev or 
    not settings.debug
)

if should_enable_auth:
    try:
        # Add auth middleware with session manager
        add_auth_middleware(
            app=app,
            session_manager=session_manager,
            public_paths=[
                "/docs", "/redoc", "/openapi.json", "/api/health",
                "/api/v1/auth/session", "/api/v1/auth/validate-session",
                "/api/v1/auth/refresh-session", "/api/v1/auth/end-session",
                "/api/chat", "/api/reset", "/api/suggestions",
                "/api/languages", "/api/feedback",
                "/", "/static", "/{full_path:path}"  # Keep essential paths public
            ],
            testing_mode=(settings.env == "development")
        )
        logger.info("✅ Session-based authentication middleware ENABLED")
        logger.info(f"   Reason: production={settings.env == 'production'}, "
                   f"force_security={settings.force_security_in_dev}, "
                   f"debug={not settings.debug}")
    except Exception as e:
        logger.error(f"❌ Failed to add authentication middleware: {e}", exc_info=True)
        if settings.env == "production":
            raise RuntimeError("Cannot start in production without authentication middleware")
        logger.warning("Authentication middleware will be disabled")
else:
    logger.warning("⚠️ Authentication middleware DISABLED")
    logger.warning(f"   Reason: production={settings.env == 'production'}, "
                  f"force_security={settings.force_security_in_dev}, "
                  f"debug={not settings.debug}")

# --- Add CSRF Middleware ---
# SECURITY FIX: Enable CSRF protection with enhanced control
should_enable_csrf = (
    settings.env == "production" or 
    settings.force_security_in_dev or 
    not settings.debug
)

if should_enable_csrf:
    try:
        exclude_urls = [
            "/docs", "/redoc", "/openapi.json", "/api/health",
            "/api/csrf-token", "/api/chat", "/api/reset",
            "/api/suggestions", "/api/languages", "/api/feedback",
            "/api/sessions", "/", "/static", "/{full_path:path}"
            # Exclude read-only API endpoints but protect state-changing ones
        ]

        add_csrf_middleware(
            app=app,
            secret=settings.jwt_secret,
            exclude_urls=exclude_urls,
            cookie_secure=(settings.env == "production")
        )
        logger.info("✅ CSRF middleware ENABLED")
        logger.info(f"   Reason: production={settings.env == 'production'}, "
                   f"force_security={settings.force_security_in_dev}, "
                   f"debug={not settings.debug}")
    except Exception as e:
        logger.error(f"❌ Failed to add CSRF middleware: {e}", exc_info=True)
        if settings.env == "production":
            raise RuntimeError("Cannot start in production without CSRF protection")
        logger.warning("CSRF protection will be disabled")
else:
    logger.warning("⚠️ CSRF middleware DISABLED")
    logger.warning(f"   Reason: production={settings.env == 'production'}, "
                  f"force_security={settings.force_security_in_dev}, "
                  f"debug={not settings.debug}")

# --- Include routers ---
app.include_router(chat_router, prefix="/api")
app.include_router(session_router, prefix="/api")
app.include_router(misc_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(knowledge_base_router)
# Include auth router for session-based authentication
app.include_router(auth_router)
logger.info("Session-based authentication routes enabled")
# Add database router for direct DB access (debugging/testing only)
app.include_router(database_router)
# Phase 4: Include health check router
app.include_router(health_router)
logger.info("API routers included")

# Basic health check endpoint with CORS support
@app.get("/api/health", tags=["Health"])
@app.options("/api/health", tags=["Health"])
async def health_check():
    """Check the health status of the API."""
    # Simply return OK status without checking for initialized chatbot
    # This makes the health check much faster and less dependent on initialization
    return {"status": "ok", "message": "API is running"}

# --- Serve frontend files ---
# First, try to serve the static HTML frontend if it exists
react_build_path = os.path.join(project_root_dir, 'react-frontend', 'build')
static_folder_path = os.path.join(src_dir, 'static')

# Check if static folder exists and prioritize it
if os.path.exists(static_folder_path) and os.path.exists(os.path.join(static_folder_path, 'index.html')):
    logger.info(f"Serving static HTML frontend from: {static_folder_path}")
    app.mount("/static", StaticFiles(directory=static_folder_path), name="static")

    # Serve the HTML frontend
    @app.get("/")
    async def serve_frontend():
        index_path = os.path.join(static_folder_path, "index.html")
        if os.path.exists(index_path):
            logger.info(f"Serving index.html from: {index_path}")
            return FileResponse(index_path)
        else:
            logger.error(f"index.html not found at: {index_path}")
            return JSONResponse(
                status_code=404,
                content={"error": "Frontend not found"}
            )

    # Serve other static files
    @app.get("/{full_path:path}")
    async def serve_static_files(full_path: str, request: Request):
        # Skip API routes - use standardized error handling
        if full_path.startswith("api/"):
            from src.utils.error_responses import SecureErrorHandler
            from src.middleware.error_handler import get_request_id
            raise SecureErrorHandler.not_found_error("API endpoint", get_request_id(request))

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

    logger.info("Static HTML frontend serving enabled")
# Fallback to React frontend if static HTML frontend doesn't exist
elif os.path.exists(react_build_path) and os.path.exists(os.path.join(react_build_path, 'index.html')):
    logger.info(f"Static HTML frontend not found. Falling back to React frontend from: {react_build_path}")

    # Mount static files directory from React build
    app.mount("/static", StaticFiles(directory=os.path.join(react_build_path, "static")), name="react_static")

    # Serve other static files from the root of the build directory
    static_files = ["favicon.ico", "logo192.png", "logo512.png", "manifest.json", "robots.txt"]
    for file in static_files:
        file_path = os.path.join(react_build_path, file)
        if os.path.exists(file_path):
            @app.get(f"/{file}")
            async def serve_static_file(file=file, file_path=file_path):
                return FileResponse(file_path)

    # Serve the React frontend index.html
    @app.get("/")
    async def serve_frontend():
        index_path = os.path.join(react_build_path, "index.html")
        logger.info(f"Serving React index.html from: {index_path}")
        return FileResponse(index_path)

    # Serve React frontend for all non-API routes (client-side routing)
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str, request: Request):
        # Skip API routes - use standardized error handling
        if full_path.startswith("api/"):
            from src.utils.error_responses import SecureErrorHandler
            from src.middleware.error_handler import get_request_id
            raise SecureErrorHandler.not_found_error("API endpoint", get_request_id(request))

        # Check for specific file in the build directory
        file_path = os.path.join(react_build_path, full_path)
        if os.path.exists(file_path) and not os.path.isdir(file_path):
            return FileResponse(file_path)

        # Default to index.html for client-side routing
        index_path = os.path.join(react_build_path, "index.html")
        return FileResponse(index_path)

    logger.info("React frontend serving enabled")
else:
    logger.warning(f"Neither React frontend build nor static folder found")
    logger.warning("Frontend serving disabled")

    # Serve a simple message if no frontend is available
    @app.get("/")
    async def serve_frontend_fallback():
        return JSONResponse(
            content={
                "message": "Egypt Tourism Chatbot API is running",
                "status": "ok",
                "frontend": "not available"
            }
        )

print(f"[DEBUG] APP ID: {id(app)}, MODULE: {app.__module__}")
# Entry point for direct execution
if __name__ == "__main__":
    # Use unified configuration instead of bypassing with os.getenv()
    host = settings.api_host
    port = settings.api_port
    logger.info(f"Starting uvicorn server on {host}:{port} (from unified config)")
    logger.info(f"Environment: {settings.env}, Debug: {settings.debug}")
    uvicorn.run(app, host=host, port=port)