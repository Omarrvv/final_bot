#!/usr/bin/env python
"""
Test script for Redis session integration with FastAPI.
This script tests the SessionService with Redis to verify it's working correctly.
"""
import os
import sys
import logging
import asyncio
import json
from datetime import datetime
import time
import uuid

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

async def test_redis_session_service():
    """Test session creation and retrieval with Redis backend."""
    # Import required modules
    from redis.asyncio import Redis
    from src.services.session import SessionService
    
    # Get Redis connection info from environment
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))
    redis_password = os.getenv("REDIS_PASSWORD", None)
    
    logger.info(f"Testing SessionService with Redis at {redis_host}:{redis_port}/{redis_db}")
    
    try:
        # Create Redis client
        redis_connection_params = {
            "host": redis_host,
            "port": redis_port,
            "db": redis_db,
            "decode_responses": True,
        }
        
        if redis_password:
            redis_connection_params["password"] = redis_password
            
        redis_client = Redis(**redis_connection_params)
        
        # Test Redis connection
        await redis_client.ping()
        logger.info("Successfully connected to Redis")
        
        # Create session service
        session_service = SessionService(redis_client)
        
        # Test creating a session
        user_id = str(uuid.uuid4())
        test_user_data = {
            "user_id": user_id,
            "username": f"test_user_{int(time.time())}",
            "roles": ["user"],
            "test_timestamp": datetime.now().isoformat()
        }
        
        # Create session
        token = await session_service.create_session(user_data=test_user_data)
        logger.info(f"Created session with token: {token[:10]}...")
        
        # Validate session
        session_data = await session_service.validate_session(token)
        if not session_data:
            logger.error("Failed to validate session")
            return False
        
        # Check session data
        logger.info(f"Retrieved session data: {json.dumps(session_data, indent=2)}")
        if session_data.get("user_id") != user_id:
            logger.error(f"Session data mismatch: expected user_id {user_id}, got {session_data.get('user_id')}")
            return False
            
        # Invalidate session
        invalidated = await session_service.invalidate_session(token)
        if not invalidated:
            logger.error("Failed to invalidate session")
            return False
            
        logger.info("Session invalidated successfully")
        
        # Verify session is invalidated
        invalid_session = await session_service.validate_session(token)
        if invalid_session:
            logger.error("Session should be invalid but is still valid")
            return False
            
        logger.info("Session validation after invalidation correctly returned None")
        
        # Close Redis connection
        await redis_client.close()
        logger.info("Redis connection closed")
        
        logger.info("✅ All SessionService tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error testing SessionService: {str(e)}", exc_info=True)
        return False

async def main():
    """Main entry point for the script."""
    success = await test_redis_session_service()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 