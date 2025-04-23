"""
FastAPI entry point for the Egypt Tourism Chatbot.
This file serves as a secondary entry point during the migration from Flask to FastAPI.
It launches the FastAPI application defined in main.py
"""
import os
import sys
import asyncio
import logging
import uvicorn
from dotenv import load_dotenv

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# Configure logging
logger = logging.getLogger("fastapi_runner")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def run_fastapi_app():
    """Run the FastAPI application using uvicorn."""
    try:
        # Set environment variable to indicate FastAPI is active
        os.environ["USE_NEW_API"] = "true"
        logger.info("Setting USE_NEW_API=true for FastAPI mode")
        
        # Get host and port from environment variables or use defaults
        host = os.getenv("API_HOST", "0.0.0.0")
        port = int(os.getenv("FASTAPI_PORT", "5050"))  # Different port than Flask app
        
        logger.info(f"Starting FastAPI application on {host}:{port}")
        
        # Set the reload flag based on the environment
        reload_enabled = os.getenv("FASTAPI_RELOAD", "false").lower() == "true"
        log_level = os.getenv("LOG_LEVEL", "info").lower()
        
        # Run the uvicorn server with the FastAPI app
        uvicorn.run(
            "src.main:app",  # Path to the FastAPI app instance
            host=host,
            port=port,
            reload=reload_enabled,
            log_level=log_level
        )
    except Exception as e:
        logger.error(f"Error starting FastAPI application: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting the FastAPI entry point")
    run_fastapi_app() 