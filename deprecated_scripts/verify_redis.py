#!/usr/bin/env python

"""
Verify Redis Script

This script verifies the Redis connection and basic operations for the Egypt Chatbot.
It tests connection, write, read, and delete operations to ensure Redis is properly configured.
"""

import os
import sys
import time
import random
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from redis import Redis
from redis.exceptions import RedisError
from src.utils.settings import settings

# Load environment variables
load_dotenv()

def verify_redis_connection():
    """
    Verify that we can connect to Redis using the configured settings.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    # Check if Redis is enabled
    use_redis = os.getenv("USE_REDIS", "true").lower() == "true"
    if not use_redis:
        print("[INFO] Redis is disabled in settings (USE_REDIS=false)")
        return True
    
    # Get Redis connection details
    redis_url = settings.redis_url
    host = "localhost"
    port = 6379
    db = 0
    
    # Parse Redis URL if available
    if redis_url and redis_url.startswith("redis://"):
        print(f"[INFO] Using Redis URL from settings: {redis_url}")
        # Extract host, port, db from redis_url
        parts = redis_url.replace("redis://", "").split(":")
        if len(parts) >= 1:
            host_parts = parts[0].split("@")
            host = host_parts[-1]  # Take the part after @ if it exists
        if len(parts) >= 2:
            port_db = parts[1].split("/")
            port = int(port_db[0])
            if len(port_db) > 1 and port_db[1]:
                db = int(port_db[1])
    else:
        # Use individual settings
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))
        db = int(os.getenv("REDIS_DB", "0"))
    
    print(f"[INFO] Testing Redis connection to {host}:{port}/{db}")
    
    try:
        # Connect to Redis
        redis_client = Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            socket_timeout=5
        )
        
        # Check if connection is established
        if not redis_client.ping():
            print("[ERROR] Failed to ping Redis server")
            return False
        
        print("[INFO] Successfully connected to Redis server")
        return True
        
    except RedisError as e:
        print(f"[ERROR] Redis connection error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error during Redis connection: {e}")
        return False

def verify_redis_operations():
    """
    Verify basic Redis operations: write, read, and delete.
    
    Returns:
        bool: True if all operations succeed, False otherwise
    """
    # Check if Redis is enabled
    use_redis = os.getenv("USE_REDIS", "true").lower() == "true"
    if not use_redis:
        print("[INFO] Skipping Redis operations test as Redis is disabled")
        return True
    
    print("[INFO] Testing basic Redis operations (write, read, delete)")
    
    try:
        # Get Redis connection details
        redis_url = settings.redis_url
        host = "localhost"
        port = 6379
        db = 0
        
        # Parse Redis URL if available
        if redis_url and redis_url.startswith("redis://"):
            # Extract host, port, db from redis_url
            parts = redis_url.replace("redis://", "").split(":")
            if len(parts) >= 1:
                host_parts = parts[0].split("@")
                host = host_parts[-1]  # Take the part after @ if it exists
            if len(parts) >= 2:
                port_db = parts[1].split("/")
                port = int(port_db[0])
                if len(port_db) > 1 and port_db[1]:
                    db = int(port_db[1])
        else:
            # Use individual settings
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            db = int(os.getenv("REDIS_DB", "0"))
        
        # Connect to Redis
        redis_client = Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            socket_timeout=5
        )
        
        # Create a test key with random value
        test_key = f"test_egypt_chatbot_{random.randint(1, 10000)}"
        test_value = f"test_value_{time.time()}"
        
        # Write operation
        redis_client.set(test_key, test_value, ex=60)  # Set with 60s expiration
        print(f"[INFO] Write operation: Successfully set key '{test_key}'")
        
        # Read operation
        retrieved_value = redis_client.get(test_key)
        if retrieved_value != test_value:
            print(f"[ERROR] Read operation failed: Expected '{test_value}', got '{retrieved_value}'")
            return False
        print(f"[INFO] Read operation: Successfully retrieved value for key '{test_key}'")
        
        # Delete operation
        redis_client.delete(test_key)
        if redis_client.exists(test_key):
            print(f"[ERROR] Delete operation failed: Key '{test_key}' still exists")
            return False
        print(f"[INFO] Delete operation: Successfully deleted key '{test_key}'")
        
        # Test session-specific namespace
        session_key = f"session:test_{random.randint(1, 10000)}"
        session_data = {"test": "data", "timestamp": str(time.time())}
        
        # Convert dict to hash
        redis_client.hset(session_key, mapping=session_data)
        print(f"[INFO] Successfully created test session '{session_key}'")
        
        # Read hash
        retrieved_data = redis_client.hgetall(session_key)
        if not retrieved_data or retrieved_data.get("test") != "data":
            print(f"[ERROR] Failed to retrieve test session data")
            return False
        print(f"[INFO] Successfully retrieved test session data")
        
        # Clean up
        redis_client.delete(session_key)
        
        return True
        
    except RedisError as e:
        print(f"[ERROR] Redis operation error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error during Redis operations: {e}")
        return False

def verify_redis_manager():
    """
    Verify the Redis session manager if it's configured.
    
    Returns:
        bool: True if verification passes, False otherwise
    """
    # Check if Redis is enabled
    use_redis = os.getenv("USE_REDIS", "true").lower() == "true"
    if not use_redis:
        print("[INFO] Skipping Redis manager test as Redis is disabled")
        return True
    
    try:
        from src.session.redis_manager import RedisSessionManager
        
        print("[INFO] Testing RedisSessionManager initialization")
        
        # Initialize the manager
        redis_uri = settings.redis_url
        manager = RedisSessionManager(redis_uri)
        
        # Create a test session
        user_id = "test_user"
        session_id = manager.create_session(user_id)
        
        if not session_id:
            print("[ERROR] Failed to create test session")
            return False
        print(f"[INFO] Successfully created test session '{session_id}'")
        
        # Retrieve the session
        session = manager.get_session(session_id)
        if not session or session.get("user_id") != user_id:
            print("[ERROR] Failed to retrieve test session")
            return False
        print(f"[INFO] Successfully retrieved test session '{session_id}'")
        
        # Add a test message
        message = {
            "role": "user",
            "content": "Test message",
            "timestamp": time.time()
        }
        added = manager.add_message_to_session(session_id, message)
        if not added:
            print("[ERROR] Failed to add message to test session")
            return False
        print(f"[INFO] Successfully added message to test session '{session_id}'")
        
        # Get session messages
        messages = manager.get_session_messages(session_id)
        if not messages or len(messages) == 0:
            print("[ERROR] Failed to retrieve messages from test session")
            return False
        print(f"[INFO] Successfully retrieved {len(messages)} messages from test session")
        
        # Delete the session
        deleted = manager.delete_session(session_id)
        if not deleted:
            print(f"[WARNING] Failed to delete test session '{session_id}'")
        else:
            print(f"[INFO] Successfully deleted test session '{session_id}'")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] Failed to import RedisSessionManager: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error during Redis manager verification: {e}")
        return False

def main():
    """Main function to run the verification process."""
    print("\n==== Starting Redis Verification ====\n")
    
    # Verify Redis connection
    if not verify_redis_connection():
        print("\n[FAIL] Redis connection verification failed")
        return False
    print("\n[PASS] Redis connection verification passed")
    
    # Verify Redis operations
    if not verify_redis_operations():
        print("\n[FAIL] Redis operations verification failed")
        return False
    print("\n[PASS] Redis operations verification passed")
    
    # Verify Redis manager
    if not verify_redis_manager():
        print("\n[FAIL] Redis manager verification failed")
        return False
    print("\n[PASS] Redis manager verification passed")
    
    print("\n==== Redis Verification Completed Successfully ====\n")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 