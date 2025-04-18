#!/usr/bin/env python
"""
Test script for Redis session integration.
This script tests the SessionManager with Redis to verify it's working correctly.
"""
import os
import sys
import logging
from datetime import datetime
import time

# Set up path to import from src
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("redis_session_test")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_redis_session():
    """Test session creation and retrieval with Redis backend."""
    from src.utils.session import SessionManager
    
    # Get Redis URI from environment
    redis_uri = os.getenv("SESSION_STORAGE_URI", "redis://redis:6379/1")
    if not redis_uri.startswith("redis://"):
        logger.error(f"Error: SESSION_STORAGE_URI must point to Redis. Current value: {redis_uri}")
        return False
    
    logger.info(f"Testing SessionManager with Redis URI: {redis_uri}")
    
    try:
        # Initialize session manager with Redis backend
        session_manager = SessionManager(session_ttl=3600, storage_uri=redis_uri)
        
        # Create a new session
        session_id = session_manager.create_session()
        logger.info(f"Created new session with ID: {session_id}")
        
        # Get context (should be initial context)
        context = session_manager.get_context(session_id)
        logger.info(f"Initial context: {context}")
        
        # Update context
        test_data = {
            "test_key": "test_value",
            "timestamp": datetime.now().isoformat()
        }
        context.update(test_data)
        success = session_manager.set_context(session_id, context)
        logger.info(f"Updated context (success={success}): {context}")
        
        # Retrieve session data directly to verify it was saved
        session_data = session_manager.get_session(session_id)
        if not session_data:
            logger.error("Error: Session data not found after creation")
            return False
        
        logger.info(f"Retrieved session data: {session_data}")
        
        # Verify context was saved correctly
        retrieved_context = session_data.get("context", {})
        if retrieved_context.get("test_key") != "test_value":
            logger.error("Error: Context data doesn't match what was saved")
            return False
        
        logger.info("Test was successful! Session data was correctly saved and retrieved from Redis.")
        
        # Sleep briefly to demonstrate session persistence
        logger.info("Waiting 5 seconds to simulate application restart...")
        time.sleep(5)
        
        # Create a new session manager (simulate application restart)
        logger.info("Creating a new session manager instance (simulating restart)")
        new_session_manager = SessionManager(session_ttl=3600, storage_uri=redis_uri)
        
        # Try to retrieve the same session
        retrieved_session = new_session_manager.get_session(session_id)
        if not retrieved_session:
            logger.error("Error: Session not found after simulated restart")
            return False
        
        # Verify context data is still intact
        retrieved_context = retrieved_session.get("context", {})
        if retrieved_context.get("test_key") != "test_value":
            logger.error("Error: Context data lost or changed after simulated restart")
            return False
        
        logger.info(f"Successfully retrieved session after simulated restart: {retrieved_context}")
        logger.info("Redis session integration test PASSED!")
        
        # Cleanup - Delete the test session
        new_session_manager.delete_session(session_id)
        logger.info(f"Cleaned up test session: {session_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during Redis session test: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Starting Redis session integration test")
    success = test_redis_session()
    if success:
        logger.info("All Redis session tests completed successfully")
        sys.exit(0)
    else:
        logger.error("Redis session tests failed")
        sys.exit(1) 