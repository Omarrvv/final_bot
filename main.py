"""
Main entry point for the Egypt Tourism Chatbot API.

This script starts the FastAPI application using uvicorn.
"""
import os
import logging
import uvicorn

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import app after loading environment variables
# Transition from src.app to src.main as per architectural unification
from src.main import app

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Get host and port from environment variables or use defaults
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "5050"))
    
    # Log startup message
    logging.info(f"Starting Egypt Tourism Chatbot API at http://{host}:{port}")
    
    # Start the server with src.main.app instead of src.app.app
    uvicorn.run(
        "src.main:app",  # Updated to use main.py instead of app.py
        host=host,
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        reload=os.getenv("DEBUG", "false").lower() == "true",
        workers=int(os.getenv("API_WORKERS", "1")),
    ) 