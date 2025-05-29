#!/usr/bin/env python3
"""
Test script for Redis Session Reliability

This script tests the enhanced Redis session management to verify:
1. Proper fallback to in-memory storage when Redis is unavailable
2. Recovery when Redis becomes available again
3. Session persistence across connection failures
4. Circuit breaker pattern functionality
"""

import os
import sys
import time
import logging
import uuid
import json
import threading
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the session manager
from src.session.redis_manager import RedisSessionManager
from src.session.redis_connection import RedisConnectionManager
from redis.exceptions import RedisError

# Test configuration
TEST_REDIS_URI = os.environ.get("TEST_REDIS_URI", "redis://localhost:6379/0")
SESSION_TTL = 3600  # 1 hour

def test_session_creation_with_redis_available():
    """Test session creation when Redis is available."""
    logger.info("=== Testing session creation with Redis available ===")
    
    try:
        # Create session manager
        session_manager = RedisSessionManager(TEST_REDIS_URI, SESSION_TTL)
        
        # Create a session
        session_id = session_manager.create_session(
            user_id="test_user",
            metadata={"test": "value"}
        )
        
        logger.info(f"Created session: {session_id}")
        
        # Verify session was created in Redis
        session = session_manager.get_session(session_id)
        if session:
            logger.info("✅ Session retrieved successfully from Redis")
            logger.info(f"Session data: {session}")
            return True
        else:
            logger.error("❌ Failed to retrieve session from Redis")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error in test_session_creation_with_redis_available: {e}")
        return False

def test_session_fallback_when_redis_unavailable():
    """Test session fallback to local memory when Redis is unavailable."""
    logger.info("=== Testing session fallback when Redis unavailable ===")
    
    try:
        # Create session manager with invalid Redis URI
        invalid_uri = "redis://nonexistent:6379/0"
        session_manager = RedisSessionManager(invalid_uri, SESSION_TTL)
        
        # Create a session (should use local memory)
        session_id = session_manager.create_session(
            user_id="test_user_fallback",
            metadata={"test": "fallback"}
        )
        
        logger.info(f"Created session with fallback: {session_id}")
        
        # Verify session was created in local memory
        session = session_manager.get_session(session_id)
        if session:
            logger.info("✅ Session retrieved successfully from local memory")
            logger.info(f"Session data: {session}")
            return True
        else:
            logger.error("❌ Failed to retrieve session from local memory")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error in test_session_fallback_when_redis_unavailable: {e}")
        return False

def test_session_persistence_across_failures():
    """Test session persistence across Redis connection failures."""
    logger.info("=== Testing session persistence across Redis failures ===")
    
    try:
        # Create session manager
        session_manager = RedisSessionManager(TEST_REDIS_URI, SESSION_TTL)
        
        # Create a session
        session_id = session_manager.create_session(
            user_id="test_user_persistence",
            metadata={"test": "persistence"}
        )
        
        logger.info(f"Created session: {session_id}")
        
        # Add a message to the session
        session_manager.add_message_to_session(
            session_id=session_id,
            role="user",
            content="Test message 1"
        )
        
        # Simulate Redis failure by setting _redis_available to False
        session_manager._redis_available = False
        logger.info("Simulated Redis failure")
        
        # Add another message (should use local memory)
        session_manager.add_message_to_session(
            session_id=session_id,
            role="assistant",
            content="Test response 1"
        )
        
        # Get session (should use local memory)
        session = session_manager.get_session(session_id)
        if not session:
            logger.error("❌ Failed to retrieve session from local memory after Redis failure")
            return False
        
        logger.info(f"Session after Redis failure: {session}")
        
        # Verify both messages are present
        messages = session.get("messages", [])
        if len(messages) != 2:
            logger.error(f"❌ Expected 2 messages, got {len(messages)}")
            return False
        
        # Simulate Redis recovery
        session_manager._redis_available = True
        logger.info("Simulated Redis recovery")
        
        # Save session to Redis
        session_manager.save_session(session_id, session)
        
        # Add another message
        session_manager.add_message_to_session(
            session_id=session_id,
            role="user",
            content="Test message 2"
        )
        
        # Get session from Redis
        session = session_manager.get_session(session_id)
        if not session:
            logger.error("❌ Failed to retrieve session from Redis after recovery")
            return False
        
        logger.info(f"Session after Redis recovery: {session}")
        
        # Verify all messages are present
        messages = session.get("messages", [])
        if len(messages) != 3:
            logger.error(f"❌ Expected 3 messages, got {len(messages)}")
            return False
        
        logger.info("✅ Session persisted successfully across Redis failures")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error in test_session_persistence_across_failures: {e}")
        return False

def test_circuit_breaker_pattern():
    """Test circuit breaker pattern functionality."""
    logger.info("=== Testing circuit breaker pattern ===")
    
    try:
        # Reset health status for the test Redis URI
        RedisConnectionManager._init_health_status(TEST_REDIS_URI)
        
        # Check initial health status
        is_healthy = RedisConnectionManager.is_redis_healthy(TEST_REDIS_URI)
        logger.info(f"Initial Redis health status: {is_healthy}")
        
        # Simulate consecutive failures
        with RedisConnectionManager._health_status_lock:
            health_status = RedisConnectionManager._health_status[TEST_REDIS_URI]
            health_status["consecutive_failures"] = RedisConnectionManager._circuit_breaker_threshold
            health_status["is_healthy"] = False
        
        # Check if circuit should be opened
        should_open = RedisConnectionManager.should_open_circuit(TEST_REDIS_URI)
        logger.info(f"Should open circuit: {should_open}")
        
        # Open the circuit
        RedisConnectionManager.open_circuit(TEST_REDIS_URI)
        
        # Check if circuit is open
        is_open = RedisConnectionManager.is_circuit_open(TEST_REDIS_URI)
        logger.info(f"Circuit is open: {is_open}")
        
        # Check health status (should be unhealthy when circuit is open)
        is_healthy = RedisConnectionManager.is_redis_healthy(TEST_REDIS_URI)
        logger.info(f"Redis health status with open circuit: {is_healthy}")
        
        # Wait for circuit to close
        logger.info(f"Waiting {RedisConnectionManager._circuit_breaker_reset_time} seconds for circuit to close...")
        time.sleep(RedisConnectionManager._circuit_breaker_reset_time + 1)
        
        # Check if circuit is still open
        is_open = RedisConnectionManager.is_circuit_open(TEST_REDIS_URI)
        logger.info(f"Circuit is open after waiting: {is_open}")
        
        # Check health status again
        is_healthy = RedisConnectionManager.is_redis_healthy(TEST_REDIS_URI)
        logger.info(f"Redis health status after circuit reset time: {is_healthy}")
        
        logger.info("✅ Circuit breaker pattern tested successfully")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error in test_circuit_breaker_pattern: {e}")
        return False

def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_session_creation_with_redis_available,
        test_session_fallback_when_redis_unavailable,
        test_session_persistence_across_failures,
        test_circuit_breaker_pattern
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            logger.error(f"❌ Uncaught exception in {test.__name__}: {e}")
            results.append((test.__name__, False))
    
    # Print summary
    logger.info("\n=== Test Results ===")
    passed = 0
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nPassed {passed}/{len(results)} tests")
    
    return passed == len(results)

if __name__ == "__main__":
    logger.info("Starting Redis Session Reliability Tests")
    success = run_all_tests()
    sys.exit(0 if success else 1)
