"""
Main FastAPI application entry point for the Egypt Tourism Chatbot.
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from fastapi import FastAPI, Request, Depends, Query, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware # Import CORS
import time
from starlette.routing import Match 
# Rate Limiting Imports
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter  # Uncomment this import
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager # Add asynccontextmanager
from pydantic import BaseModel # Import BaseModel if defining ResetRequest here temporarily
import asyncio # Add asyncio import

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

# Change relative imports to absolute imports
from src.chatbot import Chatbot
from src.utils.factory import component_factory
from src.models.api_models import (
    ChatMessageRequest, ChatbotResponse, SuggestionsResponse, 
    ResetResponse, LanguagesResponse, FeedbackRequest, FeedbackResponse,
    ResetRequest # Import the moved model
)
from src.api.analytics_api import analytics_router

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
# Construct the absolute path to the project root directory
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # Old way
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
logger.info("Logging setup complete.") # Add confirmation log

# --- End Logging Setup ---

# --- Global variables ---
chatbot_instance: Optional["Chatbot"] = None  # Use string literal for forward reference

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handles application startup and shutdown events."""
    global chatbot_instance
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

    # Initialize Rate Limiter
    logger.info("Application startup: Initializing Rate Limiter...")
    is_testing = os.getenv("TESTING") == "true"
    is_docker = os.path.exists("/.dockerenv")
    
    # Determine Redis URI based on environment
    redis_uri = "redis://redis:6379/1" if is_docker else "redis://localhost:6379/1"
    
    if is_testing:
        logger.warning("TESTING environment detected. Skipping Rate Limiter initialization.")
    else:
        try:
            redis_connection = await redis.from_url(
                redis_uri,
                encoding="utf-8",
                decode_responses=True
            )
            await FastAPILimiter.init(redis_connection)
            logger.info("Rate Limiter initialized successfully.")
        except ImportError as e:
            logger.error(f"Redis library not installed: {e}")
            logger.warning("Rate limiting disabled. Run: pip install redis")
        except Exception as e:
            logger.error(f"Failed to initialize rate limiter: {e}", exc_info=True)
            logger.warning("Rate limiting disabled due to initialization error.")

    yield # Application runs here
    
    # Shutdown: Clean up resources
    logger.info("Application shutdown: Cleaning up resources...")
    
    # Close Redis connection if it exists
    if 'redis_connection' in locals():
        await redis_connection.close()
        logger.info("Redis connection closed.")
    
    # Close DB connections
    if chatbot_instance and hasattr(chatbot_instance, 'db_manager'):
        try:
            chatbot_instance.db_manager.close()
            logger.info("Database connections closed.")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}", exc_info=True)
    
    logger.info("Application shutdown complete.")

# Create FastAPI app instance with lifespan
app = FastAPI(
    title="Egypt Tourism Chatbot API (Minimal Debug)",
    description="Minimal API for debugging startup issues.",
    version="0.1.0",
    lifespan=lifespan  # Add lifespan for Redis initialization
)

logger.info("FastAPI app instance created.")

# --- CORS Middleware Configuration --- (Keep for basic functionality)
allowed_origins = ["*"] # Allow all for simplified debugging

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins, 
    allow_credentials=True,       
    allow_methods=["*"],          
    allow_headers=["*"],          
)
logger.info("CORS middleware added.")
# --- End CORS Middleware Configuration ---

# --- Performance Monitoring Middleware --- (COMMENT OUT FOR DEBUGGING)
# class PerformanceMonitor:
#    ...
# performance_monitor = PerformanceMonitor() 
# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#    ...
# --- End Performance Monitoring Middleware ---

# --- Add Minimal API routes --- 

# Import necessary components and models # (UNCOMMENTED)
# from src.knowledge.database import DatabaseManager # Import DatabaseManager # Keep commented if chatbot handles it
# Potentially import Request for accessing query params/headers if needed later
from fastapi import HTTPException, Request, Query # Add Query if needed for optional param definition
from typing import Optional # Add Optional if not present

# Import necessary components for serving static files
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse 

# Import Routers (COMMENT OUT)
# Import other routers as they are created (e.g., auth router)

# Include Routers (COMMENT OUT)
app.include_router(analytics_router) # Includes all routes from analytics_api with /stats prefix
# app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])

logger.info("Analytics router included.")

# --- Base App Routes ---
@app.get("/api/health", response_model=None, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    logger.info("Health check endpoint called.")
    return {"status": "ok", "message": "API is running"}

# --- Test Rate Limiting with Redis ---
@app.get("/api/test-rate-limit", response_model=None, tags=["Test"], dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def test_rate_limit():
    """
    Test endpoint for rate limiting.
    Limited to 5 requests per minute.
    """
    logger.info("Rate limit test endpoint called.")
    return {
        "status": "ok", 
        "message": "If you see this, rate limiting with Redis is working!",
        "timestamp": datetime.now().isoformat()
    }

# --- Test Database Connectivity ---
@app.get("/api/test-db", response_model=None, tags=["Test"])
async def test_db():
    """
    Test endpoint for database connectivity.
    Attempts to get Abu Simbel attraction directly from the database.
    """
    logger.info("DB test endpoint called.")
    try:
        # Use the component factory to get the database manager
        db_manager = component_factory.db_manager
        if not db_manager:
            return {"status": "error", "message": "DB Manager not initialized"}
        
        # Try to get Abu Simbel directly
        attraction = db_manager.get_attraction("abu_simbel")
        
        # Try to get a restaurant
        restaurant = db_manager.get_restaurant("abou_el_sid_cairo")
        
        # Try to get an accommodation
        accommodation = db_manager.get_accommodation("mena_house_hotel")
        
        return {
            "status": "ok", 
            "db_type": db_manager.db_type,
            "attraction_found": attraction is not None,
            "attraction_name": attraction.get("name", {}).get("en") if attraction else None,
            "restaurant_found": restaurant is not None,
            "restaurant_name": restaurant.get("name", {}).get("en") if restaurant else None,
            "accommodation_found": accommodation is not None,
            "accommodation_name": accommodation.get("name", {}).get("en") if accommodation else None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in test-db endpoint: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

# --- Chat and Other Endpoints ---
@app.post("/api/chat", response_model=ChatbotResponse, tags=["Chatbot"])
async def chat_endpoint(chat_request: ChatMessageRequest, request: Request): 
    """Handles incoming chat messages and returns the chatbot's response."""
    logger.info(f"--- Received request for /api/chat: lang={chat_request.language}, session={chat_request.session_id} ---")
    if not hasattr(request.app.state, 'chatbot') or request.app.state.chatbot is None:
        logger.error("Chatbot not initialized or not found in app state, returning 503")
        raise HTTPException(status_code=503, detail="Chatbot service is unavailable due to initialization error.")
    try:
        response = await request.app.state.chatbot.process_message(
            message=chat_request.message,
            session_id=chat_request.session_id,
            language=chat_request.language
        )
        logger.info(f"--- Returning response for /api/chat: {response} ---")
        return response
    except Exception as e:
        logger.error(f"Error in /api/chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error processing chat message.")

@app.get("/api/suggestions", response_model=SuggestionsResponse, tags=["Chatbot"])
async def get_suggestions(request: Request, session_id: Optional[str] = None, language: str = "en"): 
    """Get suggested messages based on the current conversation state."""
    if not hasattr(request.app.state, 'chatbot') or request.app.state.chatbot is None:
        logger.error("Chatbot not initialized or not found in app state (suggestions), returning 503")
        raise HTTPException(status_code=503, detail="Chatbot service is unavailable due to initialization error.")
    try:
        suggestions = request.app.state.chatbot.get_suggestions(session_id=session_id, language=language)
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error in /api/suggestions endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error getting suggestions.")

@app.post("/api/reset", response_model=ResetResponse, tags=["Chatbot"])
async def reset_session(reset_request: ResetRequest, request: Request): 
    """Reset a conversation session."""
    if not hasattr(request.app.state, 'chatbot') or request.app.state.chatbot is None:
        logger.error("Chatbot not initialized or not found in app state (reset), returning 503")
        raise HTTPException(status_code=503, detail="Chatbot service is unavailable due to initialization error.")
    try:
        result = request.app.state.chatbot.reset_session(session_id=reset_request.session_id)
        return result
    except Exception as e:
        logger.error(f"Error in /api/reset endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error resetting session.")

@app.get("/api/languages", response_model=LanguagesResponse, tags=["Chatbot"])
async def get_languages(request: Request): 
    """Get available languages for the chatbot."""
    if not hasattr(request.app.state, 'chatbot') or request.app.state.chatbot is None:
        logger.error("Chatbot not initialized or not found in app state (languages), returning 503")
        raise HTTPException(status_code=503, detail="Chatbot service is unavailable due to initialization error.")
    try:
        supported_languages = request.app.state.chatbot.nlu_engine.supported_languages
        langs_map = {'en': 'English', 'ar': 'العربية'}
        
        available_languages = [
            {"code": code, "name": langs_map[code]}
            for code in supported_languages 
            if code in langs_map
        ]
        
        return {"languages": available_languages}
    except AttributeError as e:
         logger.error(f"Error accessing NLU engine or languages: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail="Internal server error retrieving languages: NLU component issue.")
    except Exception as e:
        logger.error(f"Error in /api/languages endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error retrieving languages.")

@app.post("/api/feedback", response_model=FeedbackResponse, tags=["Chatbot"])
async def submit_feedback(feedback: FeedbackRequest, request: Request): 
    """Submit user feedback about a conversation."""
    if not hasattr(request.app.state, 'chatbot') or request.app.state.chatbot is None:
        logger.error("Chatbot not initialized or not found in app state (feedback), returning 503")
        raise HTTPException(status_code=503, detail="Chatbot service is unavailable due to initialization error.")
    try:
        db_manager = request.app.state.chatbot.db_manager 
        event_data = feedback.model_dump()

        # Properly get the current event loop
        loop = asyncio.get_running_loop()

        # Run the synchronous DB call in the default executor
        success = await loop.run_in_executor(
            None,  # Use default executor
            db_manager.log_analytics_event,
            "user_feedback",  # event_type
            event_data,       # event_data
            feedback.session_id, # session_id
            feedback.user_id     # user_id
        )

        if success:
            logger.info(f"Successfully logged feedback for session {feedback.session_id}")
            return FeedbackResponse(success=True, message="Feedback submitted successfully.")
        else:
            logger.error(f"Failed to log feedback for session {feedback.session_id}")
            raise HTTPException(status_code=500, detail="Failed to submit feedback")
    except AttributeError as e:
        logger.error(f"Error accessing DB manager for feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error submitting feedback: DB component issue.")
    except Exception as e:
        logger.error(f"Error in /api/feedback endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error submitting feedback.")

# @app.get("/{full_path:path}", ...)
# async def serve_react_app(...): ...

# Add necessary imports later 