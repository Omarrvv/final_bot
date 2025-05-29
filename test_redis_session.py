#!/usr/bin/env python
"""
Test script for Redis Session Manager.
This script tests the Redis Session Manager implementation to ensure it works correctly.
"""

import os
import sys
import logging
import json
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

def test_redis_session_manager():
    """Test the Redis Session Manager implementation."""
    # Redis connection URI
    redis_uri = os.environ.get("REDIS_URI", "redis://localhost:6379/0")
    
    try:
        # Create a Redis Session Manager instance
        session_manager = RedisSessionManager(redis_uri=redis_uri)
        logger.info("Successfully created RedisSessionManager instance")
        
        # Create a test session
        session_id = "test-session-123"
        
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
        logger.info(f"Get session result: {json.dumps(session, indent=2)}")
        
        # Get the context
        logger.info(f"Getting context for session {session_id}")
        context = session_manager.get_context(session_id)
        logger.info(f"Get context result: {json.dumps(context, indent=2)}")
        
        # Add a message to the session
        logger.info(f"Adding message to session {session_id}")
        result = session_manager.add_message_to_session(
            session_id=session_id,
            role="user",
            content="Hello, how can I learn about the pyramids?"
        )
        logger.info(f"Add message result: {result}")
        
        # Get the session messages
        logger.info(f"Getting messages for session {session_id}")
        messages = session_manager.get_session_messages(session_id)
        logger.info(f"Get messages result: {json.dumps(messages, indent=2)}")
        
        # Delete the session
        logger.info(f"Deleting session {session_id}")
        result = session_manager.delete_session(session_id)
        logger.info(f"Delete session result: {result}")
        
        logger.info("All tests completed successfully")
        return True
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Starting Redis Session Manager test")
    success = test_redis_session_manager()
    if success:
        logger.info("Redis Session Manager test passed")
        sys.exit(0)
    else:
        logger.error("Redis Session Manager test failed")
        sys.exit(1)
