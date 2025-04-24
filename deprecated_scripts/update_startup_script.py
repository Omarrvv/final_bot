#!/usr/bin/env python
"""
Script to update the startup script to use FastAPI instead of Flask

This script:
1. Backs up the current startup script
2. Creates a new startup script that uses uvicorn to run the FastAPI app
"""
import os
import sys
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("update_startup")

# Set up paths
script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
project_root = script_dir.parent
startup_script_path = project_root / "start_chatbot.sh"

def backup_file(file_path, backup_suffix=".bak"):
    """Backup a file by adding a suffix."""
    if os.path.exists(file_path):
        backup_path = f"{file_path}{backup_suffix}"
        shutil.copy2(file_path, backup_path)
        logger.info(f"Backed up {file_path} to {backup_path}")
        return True
    return False

def create_fastapi_startup_script():
    """Create or update the startup script to use FastAPI."""
    
    # Check if startup script exists
    if not startup_script_path.exists():
        logger.warning(f"Startup script not found at {startup_script_path}")
        create_new = True
    else:
        backup_file(startup_script_path)
        create_new = False
    
    # New startup script content
    new_content = """#!/bin/bash
# Start the Egypt Tourism Chatbot using FastAPI

# Set environment variables if needed
# export ENVIRONMENT=production

# Check if Python virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null
then
    echo "uvicorn not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Set the host and port
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-5050}"

echo "Starting Egypt Tourism Chatbot on $HOST:$PORT..."
python -m uvicorn src.main:app --host $HOST --port $PORT --reload

# Exit message
echo "Egypt Tourism Chatbot has stopped."
"""
    
    # Write the new content
    with open(startup_script_path, 'w') as f:
        f.write(new_content)
    
    # Make the script executable
    os.chmod(startup_script_path, 0o755)
    
    if create_new:
        logger.info(f"Created new startup script at {startup_script_path}")
    else:
        logger.info(f"Updated startup script at {startup_script_path}")

def main():
    """Main function to update the startup script."""
    logger.info("Starting startup script update process")
    
    create_fastapi_startup_script()
    
    logger.info("Startup script update completed successfully")
    logger.info(f"The new startup script is located at: {startup_script_path}")
    logger.info("You can start the FastAPI application by running: ./start_chatbot.sh")

if __name__ == "__main__":
    main() 