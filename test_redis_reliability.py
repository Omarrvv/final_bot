#!/usr/bin/env python
"""
Test script for Redis Connection Reliability

This script tests the Redis connection reliability to identify issues with:
1. Connection pooling
2. Retry logic
3. Fallback mechanism
4. Connection stability under load
"""

import os
import sys
import time
import logging
import threading
import random
import concurrent.futures
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("redis_reliability_test")

# Import the RedisSessionManager
try:
    from src.session.redis_manager import RedisSessionManager
    from src.session.redis_connection import RedisConnectionManager
except ImportError:
    logger.error("Failed to import Redis modules. Make sure you're running from the project root.")
    sys.exit(1)

# Redis connection settings
REDIS_URI = os.environ.get("REDIS_URI", "redis://localhost:6379/0")
SESSION_TTL = 3600  # 1 hour

def test_connection_pooling():
    """Test Redis connection pooling"""
    logger.info("Testing Redis connection pooling...")
    
    try:
        # Get Redis client with connection pooling
        redis_client1 = RedisConnectionManager.get_redis_client(REDIS_URI)
        redis_client2 = RedisConnectionManager.get_redis_client(REDIS_URI)
        
        # Check if both clients use the same connection pool
        pool1 = redis_client1.connection_pool
        pool2 = redis_client2.connection_pool
        
        if pool1 is pool2:
            logger.info("✅ Connection pooling is working correctly (same pool instance)")
            
            # Check pool settings
            logger.info(f"Connection pool max connections: {pool1.max_connections}")
            logger.info(f"Connection pool current connections: {len(pool1._available_connections)}")
            
            return True
        else:
            logger.error("❌ Connection pooling is not working correctly (different pool instances)")
            return False
            
    except Exception as e:
        logger.error(f"❌ Connection pooling test failed: {e}")
        return False

def test_concurrent_connections(num_threads=10, operations_per_thread=100):
    """Test concurrent Redis connections"""
    logger.info(f"Testing concurrent Redis connections with {num_threads} threads...")
    
    # Create a session manager
    session_manager = RedisSessionManager(REDIS_URI, SESSION_TTL)
    
    # Create a session to use for testing
    test_session_id = session_manager.create_session(
        user_id="concurrent_test_user",
        metadata={"test_key": "concurrent_test"}
    )
    
    if not test_session_id:
        logger.error("❌ Failed to create test session")
        return False
    
    logger.info(f"Created test session: {test_session_id}")
    
    # Track success/failure counts
    success_count = 0
    failure_count = 0
    lock = threading.Lock()
    
    def worker(thread_id):
        nonlocal success_count, failure_count
        
        local_success = 0
        local_failure = 0
        
        for i in range(operations_per_thread):
            try:
                # Randomly choose an operation
                operation = random.choice(["get", "update", "message"])
                
                if operation == "get":
                    # Get session
                    session = session_manager.get_session(test_session_id)
                    if session:
                        local_success += 1
                    else:
                        local_failure += 1
                        
                elif operation == "update":
                    # Update session
                    result = session_manager.update_session(
                        test_session_id,
                        {f"test_key_{thread_id}_{i}": f"test_value_{thread_id}_{i}"}
                    )
                    if result:
                        local_success += 1
                    else:
                        local_failure += 1
                        
                elif operation == "message":
                    # Add message to session
                    result = session_manager.add_message_to_session(
                        test_session_id,
                        role="user",
                        content=f"Test message from thread {thread_id}, operation {i}"
                    )
                    if result:
                        local_success += 1
                    else:
                        local_failure += 1
                
                # Add a small random delay to simulate real-world usage
                time.sleep(random.uniform(0.001, 0.01))
                
            except Exception as e:
                logger.error(f"Thread {thread_id} operation {i} failed: {e}")
                local_failure += 1
        
        # Update global counters
        with lock:
            nonlocal success_count, failure_count
            success_count += local_success
            failure_count += local_failure
    
    # Create and start threads
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(num_threads)]
        concurrent.futures.wait(futures)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Calculate statistics
    total_operations = num_threads * operations_per_thread
    operations_per_second = total_operations / duration if duration > 0 else 0
    success_rate = (success_count / total_operations) * 100 if total_operations > 0 else 0
    
    logger.info(f"Concurrent test completed in {duration:.2f} seconds")
    logger.info(f"Total operations: {total_operations}")
    logger.info(f"Successful operations: {success_count} ({success_rate:.2f}%)")
    logger.info(f"Failed operations: {failure_count}")
    logger.info(f"Operations per second: {operations_per_second:.2f}")
    
    # Clean up test session
    session_manager.delete_session(test_session_id)
    
    # Test is successful if success rate is high
    if success_rate >= 95:
        logger.info("✅ Concurrent connection test passed")
        return True
    else:
        logger.error("❌ Concurrent connection test failed (success rate < 95%)")
        return False

def test_connection_failure_recovery():
    """Test recovery from connection failures"""
    logger.info("Testing connection failure recovery...")
    
    # Create a session manager
    session_manager = RedisSessionManager(REDIS_URI, SESSION_TTL)
    
    # Create a test session
    test_session_id = session_manager.create_session(
        user_id="recovery_test_user",
        metadata={"test_key": "recovery_test"}
    )
    
    if not test_session_id:
        logger.error("❌ Failed to create test session")
        return False
    
    logger.info(f"Created test session: {test_session_id}")
    
    # Test with invalid Redis URI to force fallback
    invalid_uri = "redis://nonexistent-host:6379/0"
    recovery_manager = RedisSessionManager(invalid_uri, SESSION_TTL)
    
    # Try to get the session (should fail and use local memory)
    session = recovery_manager.get_session(test_session_id)
    
    if session:
        logger.error("❌ Unexpected success getting session with invalid URI")
        return False
    
    # Add a message using the fallback mechanism
    result = recovery_manager.add_message_to_session(
        "local_session_id",
        role="user",
        content="Test message using fallback"
    )
    
    if not result:
        logger.error("❌ Failed to add message using fallback mechanism")
        return False
    
    logger.info("✅ Successfully used fallback mechanism")
    
    # Clean up test session
    session_manager.delete_session(test_session_id)
    
    return True

def main():
    """Main test function"""
    logger.info("Starting Redis connection reliability tests...")
    
    # Test connection pooling
    pooling_success = test_connection_pooling()
    
    # Test concurrent connections
    concurrent_success = test_concurrent_connections(num_threads=20, operations_per_thread=50)
    
    # Test connection failure recovery
    recovery_success = test_connection_failure_recovery()
    
    # Print summary
    logger.info("\nTest Summary:")
    logger.info(f"Connection Pooling: {'✅ PASS' if pooling_success else '❌ FAIL'}")
    logger.info(f"Concurrent Connections: {'✅ PASS' if concurrent_success else '❌ FAIL'}")
    logger.info(f"Connection Failure Recovery: {'✅ PASS' if recovery_success else '❌ FAIL'}")
    
    # Return success if all tests passed
    return pooling_success and concurrent_success and recovery_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
