"""
Redis Client Service

This module provides a service for connecting to Redis and managing connections.
"""
from typing import Optional
import redis.asyncio as redis
import logging
import asyncio
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError

from src.config_unified import settings
from src.utils.logger import get_logger

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Service for connecting to Redis and managing connections.
    """
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None,
                 db: Optional[int] = None, password: Optional[str] = None):
        """
        Initialize the Redis client service.
        
        Args:
            host: Redis host address
            port: Redis port
            db: Redis database number
            password: Redis password
        """
        self.host = host or settings.REDIS_HOST or "localhost"
        self.port = port or settings.REDIS_PORT or 6379
        self.db = db if db is not None else (settings.REDIS_DB or 0)
        self.password = password or settings.REDIS_PASSWORD
        self.client = None
        logger.info(f"Redis client initialized with host={self.host}, port={self.port}, db={self.db}")
    
    async def connect(self, uri: Optional[str] = None) -> bool:
        """
        Connect to Redis and return the client.
        
        Args:
            uri: Optional Redis URI string (e.g., 'redis://localhost:6379/0')
                If provided, this will override host/port/db settings
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if uri:
                logger.info(f"Connecting to Redis using URI: {uri}")
                # Check if we're trying to connect to a Docker service name 'redis'
                if 'redis://redis:' in uri:
                    fallback_uri = uri.replace('redis://redis:', 'redis://localhost:')
                    logger.info(f"Detected Docker hostname 'redis', will try fallback to {fallback_uri} if needed")
                    try:
                        self.client = Redis.from_url(
                            uri,
                            decode_responses=True,
                            socket_connect_timeout=3,
                            socket_timeout=3
                        )
                        await self.client.ping()
                        logger.info("Successfully connected to Redis")
                        return True
                    except (ConnectionError, TimeoutError) as e:
                        logger.warning(f"Failed to connect to {uri}, trying fallback: {str(e)}")
                        self.client = Redis.from_url(
                            fallback_uri,
                            decode_responses=True,
                            socket_connect_timeout=3,
                            socket_timeout=3
                        )
                        await self.client.ping()
                        logger.info(f"Successfully connected to Redis using fallback {fallback_uri}")
                        return True
                else:
                    self.client = Redis.from_url(
                        uri,
                        decode_responses=True,
                        socket_connect_timeout=3,
                        socket_timeout=3
                    )
                    await self.client.ping()
                    logger.info("Successfully connected to Redis")
                    return True
            else:
                # Connect with individual parameters
                connection_params = {
                    "host": self.host,
                    "port": self.port,
                    "db": self.db,
                    "decode_responses": True,
                    "socket_connect_timeout": 3,
                    "socket_timeout": 3
                }
                
                # Add password if it exists
                if self.password:
                    connection_params["password"] = self.password

                # Handle 'redis' hostname specially
                if self.host == 'redis':
                    logger.info(f"Detected Docker hostname 'redis', will try fallback to localhost if needed")
                    try:
                        self.client = Redis(**connection_params)
                        await self.client.ping()
                        logger.info("Successfully connected to Redis")
                        return True
                    except (ConnectionError, TimeoutError) as e:
                        logger.warning(f"Failed to connect to {self.host}, trying localhost fallback: {str(e)}")
                        connection_params["host"] = "localhost"
                        self.client = Redis(**connection_params)
                        await self.client.ping()
                        logger.info("Successfully connected to Redis using localhost fallback")
                        return True
                else:
                    self.client = Redis(**connection_params)
                    await self.client.ping()
                    logger.info("Successfully connected to Redis")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """
        Disconnect from Redis.
        """
        if self.client is not None:
            await self.client.close()
            self.client = None
            logger.info("Disconnected from Redis")
    
    async def get_client(self) -> redis.Redis:
        """
        Get the Redis client, connecting if needed.
        
        Returns:
            Redis client instance
        """
        if self.client is None:
            await self.connect()
        return self.client 