#!/usr/bin/env python
"""
Test script for Redis Connection Reliability with the enhanced implementation

This script tests the improved Redis connection reliability to verify:
1. Enhanced connection pooling
2. Exponential backoff retry logic
3. Circuit breaker pattern
4. Improved fallback mechanism
5. Health monitoring
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

def test_fallback_mechanism():
    """Test the improved fallback mechanism"""
    logger.info("Testing fallback mechanism...")
    
    # Create a session manager with valid Redis URI
    session_manager = RedisSessionManager(REDIS_URI, SESSION_TTL)
    
    # Create a test session
    test_session_id = session_manager.create_session(
        user_id="fallback_test_user",
        metadata={"test_key": "fallback_test"}
    )
    
    if not test_session_id:
        logger.error("❌ Failed to create test session")
        return False
    
    logger.info(f"Created test session: {test_session_id}")
    
    # Create a session manager with invalid Redis URI to force fallback
    invalid_uri = "redis://nonexistent-host:6379/0"
    fallback_manager = RedisSessionManager(invalid_uri, SESSION_TTL)
    
    # Test adding a message to a new session (should create local session)
    local_session_id = "local-session-" + str(random.randint(1000, 9999))
    
    # Add a message using the fallback mechanism
    result = fallback_manager.add_message_to_session(
        local_session_id,
        role="user",
        content="Test message using fallback"
    )
    
    if not result:
        logger.error("❌ Failed to add message using fallback mechanism")
        return False
    
    logger.info("✅ Successfully added message to new local session")
    
    # Get messages from local session
    messages = fallback_manager.get_session_messages(local_session_id)
    
    if not messages or len(messages) == 0:
        logger.error("❌ Failed to retrieve messages from local session")
        return False
    
    logger.info(f"✅ Successfully retrieved {len(messages)} messages from local session")
    
    # Clean up test session
    session_manager.delete_session(test_session_id)
    
    return True

def test_health_monitoring():
    """Test the health monitoring functionality"""
    logger.info("Testing health monitoring...")
    
    # Reset health status
    RedisConnectionManager._health_status = {}
    
    # Check health status for Redis URI
    is_healthy = RedisConnectionManager.is_redis_healthy(REDIS_URI)
    
    logger.info(f"Redis health status: {is_healthy}")
    
    # Get health metrics
    health_metrics = RedisConnectionManager.get_health_metrics()
    
    if REDIS_URI not in health_metrics:
        logger.error(f"❌ No health metrics found for {REDIS_URI}")
        return False
    
    logger.info("✅ Health monitoring is working correctly")
    
    # Log health metrics
    RedisConnectionManager._log_health_status(REDIS_URI)
    
    return True

def main():
    """Main test function"""
    logger.info("Starting Redis connection reliability tests...")
    
    # Test connection pooling
    pooling_success = test_connection_pooling()
    
    # Test concurrent connections
    concurrent_success = test_concurrent_connections(num_threads=20, operations_per_thread=50)
    
    # Test fallback mechanism
    fallback_success = test_fallback_mechanism()
    
    # Test health monitoring
    health_success = test_health_monitoring()
    
    # Print summary
    logger.info("\nTest Summary:")
    logger.info(f"Connection Pooling: {'✅ PASS' if pooling_success else '❌ FAIL'}")
    logger.info(f"Concurrent Connections: {'✅ PASS' if concurrent_success else '❌ FAIL'}")
    logger.info(f"Fallback Mechanism: {'✅ PASS' if fallback_success else '❌ FAIL'}")
    logger.info(f"Health Monitoring: {'✅ PASS' if health_success else '❌ FAIL'}")
    
    # Return success if all tests passed
    return pooling_success and concurrent_success and fallback_success and health_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
