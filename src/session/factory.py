"""
Session factory for creating session manager instances.
This module provides a factory class to instantiate the appropriate session manager.
"""

import os
import logging
from typing import Optional, Union

from .memory_manager import MemorySessionManager
from .redis_manager import RedisSessionManager

logger = logging.getLogger(__name__)

class SessionFactory:
    """Factory class to create session manager instances"""
    
    @staticmethod
    def create_session_manager(config=None):
        """
        Create the appropriate session manager based on configuration
        
        Args:
            config (dict, optional): Configuration dictionary
            
        Returns:
            Union[RedisSessionManager, MemorySessionManager]: Session manager instance
        """
        # Get config or use environment variables
        config = config or {}
        
        # Check if Redis should be used
        use_redis = config.get('USE_REDIS', os.getenv('USE_REDIS', 'false')).lower() in ('true', '1', 'yes')
        
        # Also check if session storage URI starts with redis://
        session_storage_uri = config.get('SESSION_STORAGE_URI', os.getenv('SESSION_STORAGE_URI'))
        if session_storage_uri and session_storage_uri.startswith('redis://'):
            use_redis = True
            redis_uri = session_storage_uri
        else:
            # Get Redis URI from config or environment (legacy method)
            redis_uri = config.get('REDIS_URI', os.getenv('REDIS_URI'))
            
        if use_redis:
            if not redis_uri:
                logger.warning("Redis session manager requested but neither SESSION_STORAGE_URI nor REDIS_URI found. Falling back to memory session manager.")
                return MemorySessionManager()
            
            try:
                # Get session TTL (default: 1 hour)
                session_ttl = int(config.get('SESSION_TTL', os.getenv('SESSION_TTL', 3600)))
                return RedisSessionManager(redis_uri, session_ttl)
            except Exception as e:
                logger.error(f"Failed to create Redis session manager: {e}")
                logger.warning("Falling back to memory session manager")
                return MemorySessionManager()
        else:
            logger.info("Using memory session manager")
            return MemorySessionManager()
    
    @staticmethod
    def get_session_manager_type():
        """
        Get the type of session manager that would be created
        
        Returns:
            str: 'redis' or 'memory'
        """
        use_redis = os.getenv('USE_REDIS', 'false').lower() in ('true', '1', 'yes')
        
        # Check for SESSION_STORAGE_URI first
        session_storage_uri = os.getenv('SESSION_STORAGE_URI')
        if session_storage_uri and session_storage_uri.startswith('redis://'):
            return 'redis'
            
        # Legacy check
        redis_uri = os.getenv('REDIS_URI')
        if use_redis and redis_uri:
            return 'redis'
            
        return 'memory' 