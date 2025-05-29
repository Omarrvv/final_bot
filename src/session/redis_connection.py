"""
Redis connection manager with enhanced connection pooling, retry logic, and fallback mechanism.
Implements exponential backoff, circuit breaker pattern, and health monitoring.
"""

import time
import logging
import threading
import functools
import random
from typing import Any, Callable, Dict, Optional, TypeVar, cast, List, Tuple
from redis import Redis, ConnectionPool, RedisError
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for return type
T = TypeVar('T')

class RedisConnectionManager:
    """
    Enhanced Redis connection manager with connection pooling, retry logic, and fallback mechanism.
    Implements circuit breaker pattern and health monitoring.
    """

    # Class-level variables for connection pools
    _pools: Dict[str, ConnectionPool] = {}
    _pools_lock = threading.RLock()

    # In-memory fallback cache
    _memory_cache: Dict[str, Dict[str, Any]] = {}
    _memory_cache_lock = threading.RLock()

    # Health check status
    _health_status: Dict[str, Dict[str, Any]] = {}
    _health_status_lock = threading.RLock()

    # Circuit breaker settings
    _circuit_breaker_threshold = 3  # Number of failures before opening circuit (reduced for faster response)
    _circuit_breaker_reset_time = 15  # Seconds before trying to close circuit (reduced for faster recovery)

    # Health check settings
    _health_check_interval = 3  # seconds (reduced for more frequent checks)
    _health_check_timeout = 1.0  # seconds

    # Retry settings
    _max_retries = 2  # Reduced to fail faster
    _retry_base_delay = 0.1  # seconds
    _retry_max_delay = 0.5  # seconds (reduced for faster failure detection)

    # Connection pool settings
    _max_connections = 30
    _connection_timeout = 1.5  # seconds (reduced for faster timeout)

    @classmethod
    def get_connection_pool(cls, redis_uri: str) -> ConnectionPool:
        """
        Get or create a connection pool for the given Redis URI.

        Args:
            redis_uri (str): Redis connection URI

        Returns:
            ConnectionPool: Redis connection pool
        """
        with cls._pools_lock:
            if redis_uri not in cls._pools:
                logger.info(f"Creating new Redis connection pool for {redis_uri}")
                cls._pools[redis_uri] = ConnectionPool.from_url(
                    redis_uri,
                    max_connections=cls._max_connections,
                    socket_timeout=cls._connection_timeout,
                    socket_connect_timeout=cls._connection_timeout,
                    health_check_interval=30,  # Check connection health every 30 seconds
                    retry_on_timeout=True
                )
            return cls._pools[redis_uri]

    @classmethod
    def get_redis_client(cls, redis_uri: str) -> Redis:
        """
        Get a Redis client with connection pooling and enhanced retry logic.

        Args:
            redis_uri (str): Redis connection URI

        Returns:
            Redis: Redis client
        """
        # Configure retry with exponential backoff
        retry = Retry(
            ExponentialBackoff(cap=cls._retry_max_delay, base=cls._retry_base_delay),
            cls._max_retries
        )

        # Get connection pool
        pool = cls.get_connection_pool(redis_uri)

        # Create Redis client with retry
        return Redis(connection_pool=pool, retry=retry)

    @classmethod
    def with_redis_fallback(cls, fallback_value: T) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """
        Decorator to add fallback mechanism to Redis operations.

        Args:
            fallback_value (T): Value to return if Redis operation fails

        Returns:
            Callable: Decorated function
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                # Get Redis URI from first argument (self)
                redis_uri = getattr(args[0], 'redis_uri', None)
                if not redis_uri:
                    logger.error(f"No Redis URI found in arguments for {func.__name__}")
                    return fallback_value

                # Check if circuit is open (too many failures)
                if cls.is_circuit_open(redis_uri):
                    logger.warning(f"Circuit is open for {redis_uri}, using fallback for {func.__name__}")
                    return fallback_value

                # Check if Redis is healthy
                if not cls.is_redis_healthy(redis_uri):
                    logger.warning(f"Redis is unhealthy, using fallback for {func.__name__}")
                    return fallback_value

                # Try to execute the function with retries
                for attempt in range(cls._max_retries + 1):
                    try:
                        result = func(*args, **kwargs)

                        # Record successful operation
                        cls.record_operation_result(redis_uri, True)

                        return result

                    except RedisError as e:
                        # Record failed operation
                        cls.record_operation_result(redis_uri, False)

                        # Log the error
                        if attempt < cls._max_retries:
                            # Calculate backoff time
                            backoff = min(cls._retry_base_delay * (2 ** attempt), cls._retry_max_delay)
                            # Add jitter
                            backoff = backoff * (0.5 + random.random())

                            logger.warning(f"Redis error in {func.__name__} (attempt {attempt+1}/{cls._max_retries+1}): {e}. Retrying in {backoff:.2f}s")
                            time.sleep(backoff)
                        else:
                            logger.error(f"Redis error in {func.__name__} (final attempt): {e}")

                            # Check if we should open the circuit
                            if cls.should_open_circuit(redis_uri):
                                logger.error(f"Opening circuit for {redis_uri} due to repeated failures")
                                cls.open_circuit(redis_uri)

                            # Return fallback value after all retries
                            return fallback_value

                # This should never be reached, but just in case
                return fallback_value

            return wrapper
        return decorator

    @classmethod
    def with_memory_cache(cls, key_func: Callable[..., str], ttl: int = 300) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """
        Decorator to add in-memory caching to Redis operations.

        Args:
            key_func (Callable): Function to generate cache key from arguments
            ttl (int, optional): Cache TTL in seconds. Defaults to 300.

        Returns:
            Callable: Decorated function
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                # Generate cache key
                cache_key = key_func(*args, **kwargs)

                # Check if value is in memory cache
                with cls._memory_cache_lock:
                    if cache_key in cls._memory_cache:
                        cache_entry = cls._memory_cache[cache_key]
                        # Check if entry is still valid
                        if time.time() < cache_entry["expires"]:
                            return cast(T, cache_entry["value"])

                # Execute the function
                result = func(*args, **kwargs)

                # Store result in memory cache
                if result is not None:
                    with cls._memory_cache_lock:
                        cls._memory_cache[cache_key] = {
                            "value": result,
                            "expires": time.time() + ttl
                        }

                return result
            return wrapper
        return decorator

    @classmethod
    def is_redis_healthy(cls, redis_uri: str) -> bool:
        """
        Check if Redis is healthy using enhanced health monitoring.

        Args:
            redis_uri (str): Redis connection URI

        Returns:
            bool: True if Redis is healthy, False otherwise
        """
        # Initialize health status if not exists
        cls._init_health_status(redis_uri)

        # Check if circuit is open
        if cls.is_circuit_open(redis_uri):
            logger.debug(f"Circuit is open for {redis_uri}, reporting as unhealthy")
            return False

        with cls._health_status_lock:
            health_status = cls._health_status[redis_uri]

            # Check if we need to perform a health check
            current_time = time.time()
            if (current_time - health_status["last_check"]) < cls._health_check_interval:
                return health_status["is_healthy"]

            # Update last health check time
            health_status["last_check"] = current_time

        try:
            # Get Redis client
            redis_client = cls.get_redis_client(redis_uri)

            # Ping Redis with timeout
            start_time = time.time()
            redis_client.ping()
            response_time = time.time() - start_time

            # Check if response time is too slow (more than 500ms)
            if response_time > 0.5:
                logger.warning(f"Redis response time is slow: {response_time:.3f}s for {redis_uri}")

            # Update health metrics
            with cls._health_status_lock:
                health_status = cls._health_status[redis_uri]
                health_status["is_healthy"] = True
                health_status["last_success"] = current_time
                health_status["response_times"].append(response_time)
                health_status["success_count"] += 1

                # Keep only the last 10 response times
                if len(health_status["response_times"]) > 10:
                    health_status["response_times"].pop(0)

                # Calculate average response time
                health_status["avg_response_time"] = sum(health_status["response_times"]) / len(health_status["response_times"])

                # Reset consecutive failures
                health_status["consecutive_failures"] = 0

                # If circuit was previously open, log recovery
                if health_status.get("circuit_open", False):
                    logger.info(f"Redis connection recovered for {redis_uri}")
                    health_status["circuit_open"] = False

            # Log health status periodically
            if current_time - health_status.get("last_log", 0) > 60:  # Log every minute
                cls._log_health_status(redis_uri)
                with cls._health_status_lock:
                    health_status["last_log"] = current_time

            return True

        except RedisError as e:
            # Update health metrics
            with cls._health_status_lock:
                health_status = cls._health_status[redis_uri]
                health_status["is_healthy"] = False
                health_status["last_failure"] = current_time
                health_status["consecutive_failures"] += 1
                health_status["failure_count"] += 1
                health_status["last_error"] = str(e)

                # Check if we should open the circuit
                if health_status["consecutive_failures"] >= cls._circuit_breaker_threshold:
                    if not health_status.get("circuit_open", False):
                        logger.error(f"Opening circuit for {redis_uri} due to {health_status['consecutive_failures']} consecutive failures")
                        cls.open_circuit(redis_uri)

            # Log the error (with different levels based on consecutive failures)
            if health_status["consecutive_failures"] <= 1:
                logger.warning(f"Redis health check failed for {redis_uri}: {e}")
            else:
                logger.error(f"Redis health check failed for {redis_uri} ({health_status['consecutive_failures']} consecutive failures): {e}")

            # Log health status on repeated failures
            if health_status["consecutive_failures"] % 5 == 0:  # Log every 5 failures
                cls._log_health_status(redis_uri)

            return False

    @classmethod
    def _init_health_status(cls, redis_uri: str) -> None:
        """
        Initialize health status for a Redis URI.

        Args:
            redis_uri (str): Redis connection URI
        """
        with cls._health_status_lock:
            if redis_uri not in cls._health_status:
                cls._health_status[redis_uri] = {
                    "is_healthy": False,
                    "last_check": 0,
                    "last_success": 0,
                    "last_failure": 0,
                    "consecutive_failures": 0,
                    "failure_count": 0,
                    "success_count": 0,
                    "response_times": [],
                    "avg_response_time": 0,
                    "circuit_open": False,
                    "circuit_open_until": 0,
                    "last_error": None,
                    "last_log": 0
                }

    @classmethod
    def _log_health_status(cls, redis_uri: str) -> None:
        """
        Log health status for a Redis URI.

        Args:
            redis_uri (str): Redis connection URI
        """
        with cls._health_status_lock:
            if redis_uri not in cls._health_status:
                return

            health_status = cls._health_status[redis_uri]

            # Format timestamps
            last_check = datetime.fromtimestamp(health_status["last_check"]).strftime("%H:%M:%S") if health_status["last_check"] else "never"
            last_success = datetime.fromtimestamp(health_status["last_success"]).strftime("%H:%M:%S") if health_status["last_success"] else "never"
            last_failure = datetime.fromtimestamp(health_status["last_failure"]).strftime("%H:%M:%S") if health_status["last_failure"] else "never"

            # Log health status
            logger.info(f"Redis health status for {redis_uri}:")
            logger.info(f"  Healthy: {health_status['is_healthy']}")
            logger.info(f"  Last check: {last_check}")
            logger.info(f"  Last success: {last_success}")
            logger.info(f"  Last failure: {last_failure}")
            logger.info(f"  Consecutive failures: {health_status['consecutive_failures']}")
            logger.info(f"  Total failures: {health_status['failure_count']}")
            logger.info(f"  Total successes: {health_status['success_count']}")
            logger.info(f"  Average response time: {health_status['avg_response_time']:.6f}s")
            logger.info(f"  Circuit open: {health_status['circuit_open']}")

            if health_status["circuit_open"]:
                circuit_open_until = datetime.fromtimestamp(health_status["circuit_open_until"]).strftime("%H:%M:%S")
                logger.info(f"  Circuit open until: {circuit_open_until}")

            if health_status["last_error"]:
                logger.info(f"  Last error: {health_status['last_error']}")

    @classmethod
    def record_operation_result(cls, redis_uri: str, success: bool) -> None:
        """
        Record the result of a Redis operation for health monitoring.

        Args:
            redis_uri (str): Redis connection URI
            success (bool): Whether the operation was successful
        """
        # Initialize health status if not exists
        cls._init_health_status(redis_uri)

        with cls._health_status_lock:
            health_status = cls._health_status[redis_uri]

            if success:
                health_status["success_count"] += 1
                health_status["consecutive_failures"] = 0
                health_status["is_healthy"] = True
                health_status["last_success"] = time.time()
            else:
                health_status["failure_count"] += 1
                health_status["consecutive_failures"] += 1
                health_status["last_failure"] = time.time()

                # Check if we should mark Redis as unhealthy
                if health_status["consecutive_failures"] >= 3:
                    health_status["is_healthy"] = False

    @classmethod
    def should_open_circuit(cls, redis_uri: str) -> bool:
        """
        Check if the circuit breaker should be opened for a Redis URI.

        Args:
            redis_uri (str): Redis connection URI

        Returns:
            bool: True if the circuit should be opened, False otherwise
        """
        # Initialize health status if not exists
        cls._init_health_status(redis_uri)

        with cls._health_status_lock:
            health_status = cls._health_status[redis_uri]

            # Check if circuit is already open
            if health_status["circuit_open"]:
                return False

            # Check if we have enough consecutive failures to open the circuit
            return health_status["consecutive_failures"] >= cls._circuit_breaker_threshold

    @classmethod
    def open_circuit(cls, redis_uri: str) -> None:
        """
        Open the circuit breaker for a Redis URI.

        Args:
            redis_uri (str): Redis connection URI
        """
        # Initialize health status if not exists
        cls._init_health_status(redis_uri)

        with cls._health_status_lock:
            health_status = cls._health_status[redis_uri]

            # Open the circuit
            health_status["circuit_open"] = True
            health_status["circuit_open_until"] = time.time() + cls._circuit_breaker_reset_time
            health_status["is_healthy"] = False

            logger.warning(f"Circuit opened for {redis_uri} until {datetime.fromtimestamp(health_status['circuit_open_until']).strftime('%H:%M:%S')}")

    @classmethod
    def is_circuit_open(cls, redis_uri: str) -> bool:
        """
        Check if the circuit breaker is open for a Redis URI.

        Args:
            redis_uri (str): Redis connection URI

        Returns:
            bool: True if the circuit is open, False otherwise
        """
        # Initialize health status if not exists
        cls._init_health_status(redis_uri)

        with cls._health_status_lock:
            health_status = cls._health_status[redis_uri]

            # Check if circuit is open
            if not health_status["circuit_open"]:
                return False

            # Check if it's time to try closing the circuit
            current_time = time.time()
            if current_time >= health_status["circuit_open_until"]:
                # Try to close the circuit
                health_status["circuit_open"] = False
                logger.info(f"Attempting to close circuit for {redis_uri}")
                return False

            # Circuit is still open
            return True

    @classmethod
    def cleanup_memory_cache(cls) -> int:
        """
        Clean up expired entries from memory cache.

        Returns:
            int: Number of entries removed
        """
        removed = 0
        current_time = time.time()

        with cls._memory_cache_lock:
            # Find expired entries
            expired_keys = [
                key for key, entry in cls._memory_cache.items()
                if current_time >= entry["expires"]
            ]

            # Remove expired entries
            for key in expired_keys:
                del cls._memory_cache[key]
                removed += 1

        return removed

    @classmethod
    def get_health_metrics(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get health metrics for all Redis URIs.

        Returns:
            Dict[str, Dict[str, Any]]: Health metrics
        """
        with cls._health_status_lock:
            # Create a copy of the health status
            return {uri: status.copy() for uri, status in cls._health_status.items()}
