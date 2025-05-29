#!/usr/bin/env python
"""
Test script for Redis Session Manager resilience.
This script tests the Redis Session Manager's ability to handle Redis failures.
"""

import os
import sys
import time
import logging
import threading
import subprocess
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the RedisSessionManager
try:
    from src.session.redis_manager import RedisSessionManager
    logger.info("Successfully imported RedisSessionManager")
except ImportError as e:
    logger.error(f"Failed to import RedisSessionManager: {e}")
    sys.exit(1)

class RedisController:
    """Helper class to start and stop Redis for testing"""
    
    def __init__(self, redis_port=6379):
        self.redis_port = redis_port
        self.redis_process = None
        
    def start_redis(self):
        """Start Redis server"""
        try:
            # Check if Redis is already running
            result = subprocess.run(
                ["redis-cli", "-p", str(self.redis_port), "ping"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.stdout.strip() == "PONG":
                logger.info("Redis is already running")
                return True
                
            # Start Redis server
            logger.info(f"Starting Redis server on port {self.redis_port}")
            self.redis_process = subprocess.Popen(
                ["redis-server", "--port", str(self.redis_port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for Redis to start
            time.sleep(1)
            
            # Check if Redis is running
            result = subprocess.run(
                ["redis-cli", "-p", str(self.redis_port), "ping"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.stdout.strip() == "PONG":
                logger.info("Redis server started successfully")
                return True
            else:
                logger.error(f"Failed to start Redis server: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting Redis server: {e}")
            return False
            
    def stop_redis(self):
        """Stop Redis server"""
        try:
            if self.redis_process:
                logger.info("Stopping Redis server")
                self.redis_process.terminate()
                self.redis_process.wait(timeout=5)
                self.redis_process = None
                logger.info("Redis server stopped")
                return True
                
            # If we didn't start Redis, try to shut it down with redis-cli
            logger.info("Shutting down Redis server with redis-cli")
            result = subprocess.run(
                ["redis-cli", "-p", str(self.redis_port), "shutdown"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            logger.info("Redis server shutdown initiated")
            return True
                
        except Exception as e:
            logger.error(f"Error stopping Redis server: {e}")
            return False

def test_redis_resilience():
    """Test the Redis Session Manager's resilience to Redis failures"""
    # Redis connection URI
    redis_uri = os.environ.get("REDIS_URI", "redis://localhost:6379/0")
    
    # Create Redis controller
    redis_controller = RedisController()
    
    try:
        # Start Redis
        if not redis_controller.start_redis():
            logger.error("Failed to start Redis, skipping test")
            return False
            
        # Create a Redis Session Manager instance
        session_manager = RedisSessionManager(redis_uri=redis_uri)
        logger.info("Successfully created RedisSessionManager instance")
        
        # Create a test session
        session_id = "test-resilience-123"
        
        # Create session data
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "state": "greeting",
            "history": [],
            "entities": {},
            "context": {
                "dialog_state": "greeting",
                "last_attraction": "pyramids"
            }
        }
        
        # Save the session
        logger.info(f"Saving session {session_id}")
        result = session_manager.save_session(session_id, session_data)
        logger.info(f"Save session result: {result}")
        
        # Get the session
        logger.info(f"Getting session {session_id}")
        session = session_manager.get_session(session_id)
        logger.info(f"Session retrieved successfully: {session is not None}")
        
        # Stop Redis to simulate failure
        logger.info("Stopping Redis to simulate failure")
        redis_controller.stop_redis()
        time.sleep(2)  # Wait for Redis to stop
        
        # Try to get the session after Redis failure
        logger.info(f"Getting session {session_id} after Redis failure")
        session = session_manager.get_session(session_id)
        if session is not None:
            logger.info("Session retrieved from local cache successfully")
        else:
            logger.error("Failed to retrieve session from local cache")
            return False
            
        # Add a message to the session
        logger.info(f"Adding message to session {session_id} after Redis failure")
        result = session_manager.add_message_to_session(
            session_id=session_id,
            role="user",
            content="Hello, how can I learn about the pyramids?"
        )
        logger.info(f"Add message result: {result}")
        
        # Get the session messages
        logger.info(f"Getting messages for session {session_id} after Redis failure")
        messages = session_manager.get_session_messages(session_id)
        if messages and len(messages) > 0:
            logger.info(f"Retrieved {len(messages)} messages from local cache")
        else:
            logger.error("Failed to retrieve messages from local cache")
            return False
            
        # Restart Redis
        logger.info("Restarting Redis")
        if not redis_controller.start_redis():
            logger.error("Failed to restart Redis")
            return False
            
        # Create a new session manager to test reconnection
        logger.info("Creating new session manager to test reconnection")
        new_session_manager = RedisSessionManager(redis_uri=redis_uri)
        
        # Try to get the session after Redis restart
        logger.info(f"Getting session {session_id} after Redis restart")
        session = new_session_manager.get_session(session_id)
        if session is not None:
            logger.info("Session retrieved after Redis restart")
        else:
            logger.warning("Session not found after Redis restart (expected if not synced back)")
            
        logger.info("All resilience tests completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False
    finally:
        # Make sure Redis is running again
        redis_controller.start_redis()

if __name__ == "__main__":
    logger.info("Starting Redis Session Manager resilience test")
    success = test_redis_resilience()
    if success:
        logger.info("Redis Session Manager resilience test passed")
        sys.exit(0)
    else:
        logger.error("Redis Session Manager resilience test failed")
        sys.exit(1)
