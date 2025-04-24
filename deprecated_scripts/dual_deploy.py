#!/usr/bin/env python3
"""
Dual deployment script for the Egypt Tourism Chatbot.
This script runs both the legacy Flask app and the new FastAPI app in parallel,
allowing for gradual migration and testing of the new API endpoints.
"""
import os
import sys
import time
import signal
import subprocess
import argparse
import logging
from threading import Thread

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("dual_deploy")

# Store process objects
processes = []

def signal_handler(sig, frame):
    """Handle termination signals to gracefully shut down both applications."""
    logger.info(f"Received signal {sig}, shutting down all processes...")
    for process in processes:
        if process and process.poll() is None:  # Check if process exists and is running
            logger.info(f"Terminating process: {process.args}")
            process.terminate()
    
    # Wait for processes to terminate gracefully
    time.sleep(2)
    
    # Force kill any remaining processes
    for process in processes:
        if process and process.poll() is None:
            logger.warning(f"Force killing process: {process.args}")
            try:
                process.kill()
            except:
                pass
    
    logger.info("All processes terminated. Exiting.")
    sys.exit(0)

def run_flask_app():
    """Run the legacy Flask application."""
    try:
        # Configure environment for Flask app
        env = os.environ.copy()
        env["FLASK_APP"] = "app.py"
        env["FLASK_ENV"] = os.getenv("FLASK_ENV", "development")
        
        flask_port = os.getenv("FLASK_PORT", "5000")
        host = os.getenv("API_HOST", "0.0.0.0")
        
        logger.info(f"Starting Flask app on {host}:{flask_port}")
        
        # Start Flask process
        flask_cmd = [
            sys.executable, 
            "app.py",
            "--port", 
            flask_port
        ]
        
        flask_process = subprocess.Popen(
            flask_cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        processes.append(flask_process)
        
        # Log output from process
        logger.info(f"Flask process started with PID: {flask_process.pid}")
        for line in flask_process.stdout:
            logger.info(f"[Flask] {line.strip()}")
            
        # If we get here, the process has terminated
        return_code = flask_process.wait()
        logger.error(f"Flask process exited with code: {return_code}")
        
    except Exception as e:
        logger.error(f"Error running Flask app: {e}", exc_info=True)

def run_fastapi_app():
    """Run the new FastAPI application."""
    try:
        # Configure environment for FastAPI app
        env = os.environ.copy()
        env["USE_NEW_API"] = "true"
        
        fastapi_port = os.getenv("FASTAPI_PORT", "5050")
        host = os.getenv("API_HOST", "0.0.0.0")
        
        logger.info(f"Starting FastAPI app on {host}:{fastapi_port}")
        
        # Start FastAPI process
        fastapi_cmd = [
            sys.executable, 
            "src/main_fastapi.py"
        ]
        
        fastapi_process = subprocess.Popen(
            fastapi_cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        processes.append(fastapi_process)
        
        # Log output from process
        logger.info(f"FastAPI process started with PID: {fastapi_process.pid}")
        for line in fastapi_process.stdout:
            logger.info(f"[FastAPI] {line.strip()}")
            
        # If we get here, the process has terminated
        return_code = fastapi_process.wait()
        logger.error(f"FastAPI process exited with code: {return_code}")
        
    except Exception as e:
        logger.error(f"Error running FastAPI app: {e}", exc_info=True)

def main():
    """Main function to parse arguments and run the applications."""
    parser = argparse.ArgumentParser(description="Run both Flask and FastAPI applications in parallel")
    parser.add_argument("--flask-only", action="store_true", help="Run only the Flask application")
    parser.add_argument("--fastapi-only", action="store_true", help="Run only the FastAPI application")
    args = parser.parse_args()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start processes based on arguments
        if args.flask_only and args.fastapi_only:
            logger.error("Cannot specify both --flask-only and --fastapi-only")
            sys.exit(1)
        
        if args.flask_only:
            logger.info("Running Flask application only")
            flask_thread = Thread(target=run_flask_app)
            flask_thread.start()
            flask_thread.join()
        elif args.fastapi_only:
            logger.info("Running FastAPI application only")
            fastapi_thread = Thread(target=run_fastapi_app)
            fastapi_thread.start()
            fastapi_thread.join()
        else:
            logger.info("Running both Flask and FastAPI applications")
            flask_thread = Thread(target=run_flask_app)
            fastapi_thread = Thread(target=run_fastapi_app)
            
            flask_thread.start()
            fastapi_thread.start()
            
            flask_thread.join()
            fastapi_thread.join()
            
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
        signal_handler(signal.SIGTERM, None)

if __name__ == "__main__":
    main() 