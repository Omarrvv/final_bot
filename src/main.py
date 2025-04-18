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

# Load environment variables early
load_dotenv()

# --- Define Project Root Path ---
# Get the absolute path of the directory containing this file (src/)
src_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get the project root
project_root_dir = os.path.dirname(src_dir)
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

# --- Initialize Chatbot Components --- # (UNCOMMENTED)
from src.utils.factory import component_factory
# from src.utils.container import container # Import the container # Keep container commented if not directly used here

try:
    component_factory.initialize()
    chatbot = component_factory.create_chatbot() # Use factory to create chatbot
    # Ensure chatbot is initialized if factory doesn't handle it
    # chatbot.initialize() # Assuming create_chatbot returns an initialized instance or handles it
    logger.info("Chatbot components initialized successfully.")
except Exception as e:
    logger.error(f"CRITICAL: Failed to initialize chatbot components: {e}", exc_info=True)
    chatbot = None # Ensure chatbot is None if init fails
    # Depending on the desired behavior, you might want to exit or raise the exception
    # raise # Re-raise the exception to potentially stop the server from starting
# --- End Component Initialization ---

# --- Lifespan Event Handler --- 
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handles application startup and shutdown events."""
    # Startup: Initialize Rate Limiter
    logger.info("Application startup: Initializing Rate Limiter...")
    redis_connection = None
    try:
        # Get Redis URI from environment variable
        redis_uri = os.getenv("SESSION_STORAGE_URI", "redis://redis:6379/0")
        
        # Check if we're in local environment (not Docker) by trying to resolve redis hostname
        import socket
        try:
            # Only attempt to resolve hostname if the URI contains redis:// and redis: hostname
            if "redis://redis:" in redis_uri:
                socket.gethostbyname('redis')
                # If we get here, redis hostname resolved, we're in Docker
                logger.info("Redis hostname resolved - using container networking")
            else:
                # If URI doesn't contain redis: hostname, no need to modify
                logger.info(f"Using provided Redis URI: {redis_uri}")
        except socket.gaierror:
            # Cannot resolve redis hostname, we're running locally
            logger.info("Redis hostname not resolved - switching to localhost for local testing")
            # Correctly replace the hostname part
            redis_uri = redis_uri.replace('redis://redis:', 'redis://localhost:')
        
        logger.info(f"Using Redis URI: {redis_uri}")
        
        # Create async redis connection pool
        redis_connection = redis.from_url(redis_uri, encoding="utf-8", decode_responses=True)
        
        # Ping Redis to check connection early
        await redis_connection.ping()
        logger.info("Successfully connected to Redis")
        
        # Initialize rate limiter
        await FastAPILimiter.init(redis_connection)
        logger.info(f"Rate limiter initialized with Redis backend: {redis_uri}")
    except Exception as e:
        logger.error(f"Failed to initialize rate limiter: {e}", exc_info=True)
        # Application can continue without rate limiting, but log error
        
    yield # Application runs here
    
    # Shutdown: Clean up resources if needed
    logger.info("Application shutdown: Cleaning up resources...")
    if redis_connection:
        await redis_connection.aclose()  # Use aclose() instead of close() to fix the deprecation warning
        logger.info("Redis connection closed")

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
from src.models.api_models import (
    ChatMessageRequest, ChatbotResponse, SuggestionsResponse, 
    ResetResponse, LanguagesResponse, FeedbackRequest, FeedbackResponse,
    ResetRequest # Import the moved model
)
from src.chatbot import Chatbot # Ensure Chatbot import exists or add it
# from src.knowledge.database import DatabaseManager # Import DatabaseManager # Keep commented if chatbot handles it
# Potentially import Request for accessing query params/headers if needed later
# from fastapi import HTTPException, Request, Query # Add Query if needed for optional param definition
# from typing import Optional # Add Optional if not present

# Import necessary components for serving static files
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse 

# Import Routers (COMMENT OUT)
from src.api.analytics_api import analytics_router
# Import other routers as they are created (e.g., auth router)

# Include Routers (COMMENT OUT)
app.include_router(analytics_router) # Includes all routes from analytics_api with /stats prefix
# app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])

logger.info("Analytics router included.")

# --- Base App Routes ---
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    logger.info("Health check endpoint called.")
    return {"status": "ok", "service": "Egypt Tourism Chatbot FastAPI backend", "timestamp": datetime.now().isoformat()}

# --- Test Rate Limiting with Redis ---
@app.get("/api/test-rate-limit", tags=["Test"], dependencies=[Depends(RateLimiter(times=5, seconds=60))])
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

# --- Chat and Other Endpoints ---
@app.post("/api/chat", response_model=ChatbotResponse, tags=["Chatbot"])
async def chat_endpoint(chat_request: ChatMessageRequest):
    """Handles incoming chat messages and returns the chatbot's response."""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot service is unavailable due to initialization error.")
    try:
        # Call the chatbot instance to process the message - remove await since it's not an async method
        response = chatbot.process_message(
            user_message=chat_request.message,
            session_id=chat_request.session_id,
            language=chat_request.language
        )
        return response
    except Exception as e:
        logger.error(f"Error in /api/chat endpoint: {e}", exc_info=True)
        # Return a generic error response
        raise HTTPException(status_code=500, detail="An error occurred while processing your message.")

@app.get("/api/suggestions", response_model=SuggestionsResponse, tags=["Chatbot"])
async def get_suggestions(session_id: Optional[str] = None, language: str = "en"):
    """Get suggested messages based on the current conversation state."""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot service is unavailable due to initialization error.")
    try:
        suggestions = chatbot.get_suggestions(session_id=session_id, language=language)
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error in /api/suggestions endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get suggestions.")

@app.post("/api/reset", response_model=ResetResponse, tags=["Chatbot"])
async def reset_session(reset_request: ResetRequest):
    """Reset a conversation session."""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot service is unavailable due to initialization error.")
    try:
        result = chatbot.reset_session(session_id=reset_request.session_id)
        return result
    except Exception as e:
        logger.error(f"Error in /api/reset endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reset session.")

@app.get("/api/languages", response_model=LanguagesResponse, tags=["Chatbot"])
async def get_languages():
    """Get the list of supported languages."""
    # This might eventually come from a config or language detector
    supported_languages = [
        {"code": "en", "name": "English"},
        {"code": "ar", "name": "العربية"}
    ]
    return {"languages": supported_languages}

@app.post("/api/feedback", response_model=FeedbackResponse, tags=["Chatbot"])
async def submit_feedback(feedback: FeedbackRequest):
    """Submit user feedback about a conversation."""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot service is unavailable due to initialization error.")
    try:
        db_manager = chatbot.db_manager
        success = db_manager.log_feedback(
            message_id=feedback.message_id,
            rating=feedback.rating,
            comment=feedback.comment,
            session_id=feedback.session_id,
            user_id=feedback.user_id
        )
        if success:
            return {"success": True, "message": "Feedback recorded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to record feedback")
    except Exception as e:
        logger.error(f"Error in /api/feedback endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing feedback.")

# @app.get("/{full_path:path}", ...)
# async def serve_react_app(...): ...

# Add necessary imports later 