#!/usr/bin/env python

"""
Verify Rate Limiter Script

This script verifies the configuration and functionality of the FastAPI rate limiter.
It checks if the rate limiter is properly configured and validates its connection to Redis.
"""

import os
import sys
import time
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from redis import Redis
from redis.exceptions import RedisError
from src.utils.settings import get_api_settings

# Load environment variables
load_dotenv()

def verify_rate_limiter_config():
    """
    Verify the rate limiter configuration in the settings.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    try:
        api_settings = get_api_settings()
        
        print("[INFO] Checking rate limiter configuration")
        
        # Check if rate limiting is enabled
        if not api_settings.rate_limiting_enabled:
            print("[INFO] Rate limiting is disabled in settings (RATE_LIMITING_ENABLED=false)")
            return True
        
        print(f"[INFO] Rate limiting is enabled with the following configuration:")
        print(f"  - Max requests: {api_settings.rate_limit_requests}")
        print(f"  - Time window: {api_settings.rate_limit_window_seconds} seconds")
        
        # Validate configuration values
        if api_settings.rate_limit_requests <= 0:
            print(f"[ERROR] Invalid rate_limit_requests: {api_settings.rate_limit_requests}. Should be greater than 0.")
            return False
        
        if api_settings.rate_limit_window_seconds <= 0:
            print(f"[ERROR] Invalid rate_limit_window_seconds: {api_settings.rate_limit_window_seconds}. Should be greater than 0.")
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error checking rate limiter configuration: {e}")
        return False

def verify_rate_limiter_dependencies():
    """
    Verify that the necessary dependencies for the rate limiter are available.
    
    Returns:
        bool: True if dependencies are available, False otherwise
    """
    try:
        api_settings = get_api_settings()
        
        # Skip if rate limiting is disabled
        if not api_settings.rate_limiting_enabled:
            print("[INFO] Skipping dependency check as rate limiting is disabled")
            return True
        
        print("[INFO] Checking rate limiter dependencies")
        
        # Check if slowapi is installed
        try:
            import slowapi
            from slowapi import Limiter
            from slowapi.errors import RateLimitExceeded
            print("[INFO] slowapi is installed")
        except ImportError:
            print("[ERROR] slowapi is not installed. Run 'pip install slowapi'")
            return False
        
        # Check if Redis is available (required for distributed rate limiting)
        if api_settings.use_redis:
            try:
                # Connect to Redis
                redis_client = Redis(
                    host=api_settings.redis_host,
                    port=api_settings.redis_port,
                    db=api_settings.redis_db,
                    decode_responses=True,
                    socket_timeout=5
                )
                
                # Check if connection is established
                if not redis_client.ping():
                    print("[ERROR] Failed to ping Redis server for rate limiter")
                    return False
                
                print("[INFO] Redis connection for rate limiter is working")
                
                # Check redis-py-cluster if using Redis Cluster
                if api_settings.redis_host.startswith("redis-cluster"):
                    try:
                        import rediscluster
                        print("[INFO] redis-py-cluster is installed")
                    except ImportError:
                        print("[WARNING] redis-py-cluster is not installed. This might be required if using Redis Cluster.")
                
            except RedisError as e:
                print(f"[ERROR] Redis error for rate limiter: {e}")
                return False
        else:
            print("[INFO] Redis is not used, rate limiter will use in-memory storage")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error checking rate limiter dependencies: {e}")
        return False

def verify_fastapi_limiter_import():
    """
    Verify that FastAPILimiter can be imported and initialized.
    
    Returns:
        bool: True if import is successful, False otherwise
    """
    try:
        api_settings = get_api_settings()
        
        # Skip if rate limiting is disabled
        if not api_settings.rate_limiting_enabled:
            print("[INFO] Skipping FastAPILimiter check as rate limiting is disabled")
            return True
        
        print("[INFO] Checking FastAPILimiter import")
        
        # Try to import FastAPILimiter
        try:
            from fastapi_limiter import FastAPILimiter
            print("[INFO] FastAPILimiter is importable")
        except ImportError:
            print("[ERROR] fastapi-limiter is not installed. Run 'pip install fastapi-limiter'")
            return False
        
        # Check if Redis is required but not available
        if api_settings.use_redis:
            try:
                import aioredis
                print("[INFO] aioredis is installed for FastAPILimiter")
            except ImportError:
                print("[ERROR] aioredis is not installed. Run 'pip install aioredis'")
                return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error checking FastAPILimiter import: {e}")
        return False

def verify_rate_limiter_initialization():
    """
    Simulate the rate limiter initialization process.
    
    Returns:
        bool: True if initialization would succeed, False otherwise
    """
    try:
        api_settings = get_api_settings()
        
        # Skip if rate limiting is disabled
        if not api_settings.rate_limiting_enabled:
            print("[INFO] Skipping initialization check as rate limiting is disabled")
            return True
        
        print("[INFO] Verifying rate limiter initialization logic")
        
        # Check if initialization code in main.py would work
        if api_settings.use_redis:
            # Check Redis connection string format
            redis_uri = f"redis://{api_settings.redis_host}:{api_settings.redis_port}/{api_settings.redis_db}"
            print(f"[INFO] Rate limiter would use Redis at: {redis_uri}")
            
            # Try to connect to Redis
            try:
                redis_client = Redis.from_url(
                    redis_uri,
                    decode_responses=True,
                    socket_timeout=5
                )
                
                if not redis_client.ping():
                    print("[ERROR] Failed to ping Redis for rate limiter initialization")
                    return False
                
                print("[INFO] Redis connection for rate limiter initialization would succeed")
                
            except RedisError as e:
                print(f"[ERROR] Redis error for rate limiter initialization: {e}")
                return False
            except Exception as e:
                print(f"[ERROR] Error connecting to Redis for rate limiter: {e}")
                return False
        else:
            print("[INFO] Rate limiter would use in-memory storage (no Redis)")
        
        print("[INFO] Rate limiter initialization logic is valid")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error verifying rate limiter initialization: {e}")
        return False

def main():
    """Main function to run the verification process."""
    print("\n==== Starting Rate Limiter Verification ====\n")
    
    # Verify rate limiter configuration
    if not verify_rate_limiter_config():
        print("\n[FAIL] Rate limiter configuration verification failed")
        return False
    print("\n[PASS] Rate limiter configuration verification passed")
    
    # Verify rate limiter dependencies
    if not verify_rate_limiter_dependencies():
        print("\n[FAIL] Rate limiter dependencies verification failed")
        return False
    print("\n[PASS] Rate limiter dependencies verification passed")
    
    # Verify FastAPILimiter import
    if not verify_fastapi_limiter_import():
        print("\n[FAIL] FastAPILimiter import verification failed")
        return False
    print("\n[PASS] FastAPILimiter import verification passed")
    
    # Verify rate limiter initialization
    if not verify_rate_limiter_initialization():
        print("\n[FAIL] Rate limiter initialization verification failed")
        return False
    print("\n[PASS] Rate limiter initialization verification passed")
    
    print("\n==== Rate Limiter Verification Completed Successfully ====\n")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 