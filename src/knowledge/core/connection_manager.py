"""
Connection Manager for the Egypt Tourism Chatbot.

This module extracts connection pooling and management logic from the DatabaseManager,
providing a focused, reusable service for managing PostgreSQL connections with
optimized settings and monitoring.
"""

import os
import time
import uuid
import threading
import logging
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages PostgreSQL connections with pooling, monitoring, and optimization.
    
    This service extracts the connection management responsibilities from DatabaseManager,
    providing a clean, focused interface for database connectivity.
    """
    
    def __init__(self, database_uri: str = None):
        """
        Initialize the connection manager.
        
        Args:
            database_uri: PostgreSQL database connection string
        """
        self.database_uri = database_uri or os.environ.get("POSTGRES_URI")
        self.pg_pool = None
        self.lock = threading.RLock()
        
        # Set shorter timeout for tests
        self.operation_timeout = 2 if os.environ.get('TESTING') == 'true' else 10
        
        # Initialize connection pool metrics
        self.pool_metrics = {
            "acquisition_times": [],
            "query_count": 0,
            "error_count": 0,
            "last_metrics_time": time.time()
        }
        
        logger.debug(f"ConnectionManager initialized with URI: {self._mask_uri(self.database_uri)}")
    
    def _mask_uri(self, uri: str) -> str:
        """Mask sensitive information in URI for logging."""
        if not uri or '@' not in uri:
            return uri
        try:
            # Split on @ and show only the host/db part
            return f"postgresql://***@{uri.split('@')[1]}"
        except:
            return "postgresql://***"
    
    def initialize_connection_pool(self) -> bool:
        """
        Initialize PostgreSQL connection pool with optimized settings.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Test if we have database access first
            has_access = self._test_database_access()
            if not has_access:
                logger.error("Database access test failed")
                return False
            
            # Create the connection pool with optimized settings
            min_conn = int(os.environ.get("PG_MIN_CONNECTIONS", "2"))
            max_conn = int(os.environ.get("PG_MAX_CONNECTIONS", "20"))
            
            # Use smaller pool for tests
            if os.environ.get('TESTING') == 'true':
                min_conn = 1
                max_conn = 3
            
            logger.info(f"Creating PostgreSQL connection pool (min={min_conn}, max={max_conn})...")
            
            # Create connection pool with optimized parameters
            self.pg_pool = pool.ThreadedConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                dsn=self.database_uri,
                # Add connection validation and timeout settings
                connect_timeout=5,  # 5 seconds connection timeout
                keepalives=1,       # Enable TCP keepalives
                keepalives_idle=60, # Idle time before sending keepalive
                keepalives_interval=10, # Interval between keepalives
                keepalives_count=3  # Number of keepalives before giving up
            )
            
            # Test the pool
            test_conn = self.get_connection()
            if not test_conn:
                logger.error("Failed to get test connection from pool")
                return False
            
            # Test basic query
            try:
                with test_conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    if not result or result[0] != 1:
                        logger.error("Connection test query failed")
                        return False
            finally:
                self.return_connection(test_conn)
            
            logger.info("PostgreSQL connection pool initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL connection pool: {str(e)}")
            if self.pg_pool:
                try:
                    self.pg_pool.closeall()
                except:
                    pass
                self.pg_pool = None
            return False
    
    def _test_database_access(self) -> bool:
        """Test if we can connect to the database."""
        try:
            test_conn = psycopg2.connect(self.database_uri)
            with test_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                success = result[0] == 1 if result else False
            test_conn.close()
            return success
        except Exception as e:
            logger.warning(f"Database access test failed: {str(e)}")
            return False
    
    def get_connection(self):
        """
        Get a connection from the pool with retry logic and metrics tracking.
        
        Returns:
            Database connection or None if failed
        """
        if not self.pg_pool:
            logger.error("No PostgreSQL connection pool available")
            return None
        
        start_time = time.time()
        retries = 3
        conn = None
        
        for attempt in range(retries):
            try:
                conn = self.pg_pool.getconn()
                if not conn.closed:
                    # Track connection acquisition time
                    acquisition_time_ms = (time.time() - start_time) * 1000
                    self.pool_metrics["acquisition_times"].append(acquisition_time_ms)
                    
                    # Log slow connection acquisitions
                    if acquisition_time_ms > 100:  # More than 100ms is slow
                        logger.warning(f"Slow connection acquisition: {acquisition_time_ms:.2f}ms")
                    
                    # Record metrics periodically
                    self._record_pool_metrics()
                    
                    return conn
                
                logger.warning("Got closed connection from pool, attempting to reconnect...")
                self.pg_pool.putconn(conn)
                
            except Exception as e:
                logger.error(f"Error getting connection on attempt {attempt + 1}: {str(e)}")
                self.pool_metrics["error_count"] += 1
                if attempt == retries - 1:
                    return None
        
        return None
    
    def return_connection(self, conn):
        """
        Safely return a connection to the pool.
        
        Args:
            conn: Database connection to return
        """
        if self.pg_pool and conn:
            try:
                if not conn.closed:
                    self.pg_pool.putconn(conn)
                else:
                    logger.warning("Attempted to return closed connection to pool")
            except Exception as e:
                logger.error(f"Error returning connection to pool: {str(e)}")
    
    def execute_query(self, query: str, params: tuple = None, 
                     fetchall: bool = True, cursor_factory=None):
        """
        Execute a query using a connection from the pool.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetchall: Whether to fetch all results or just one
            cursor_factory: Factory for cursor creation
            
        Returns:
            Query results or None if error occurred
        """
        if not self.pg_pool:
            logger.error("No connection pool available for query execution")
            return None
        
        conn = None
        start_time = time.time()
        
        try:
            conn = self.get_connection()
            if not conn:
                logger.error("Failed to get connection for query execution")
                return None
            
            # Use provided cursor factory or default to RealDictCursor
            factory = cursor_factory or RealDictCursor
            
            with conn.cursor(cursor_factory=factory) as cursor:
                # Execute query
                cursor.execute(query, params)
                
                # Fetch results
                if cursor.description:  # SELECT query
                    if fetchall:
                        results = cursor.fetchall()
                        # Convert to list of dicts if using RealDictCursor
                        if factory == RealDictCursor:
                            results = [dict(row) for row in results]
                        return results
                    else:
                        result = cursor.fetchone()
                        if result and factory == RealDictCursor:
                            return dict(result)
                        return result
                else:  # INSERT/UPDATE/DELETE
                    conn.commit()
                    return cursor.rowcount
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            self.pool_metrics["error_count"] += 1
            
            if conn and not conn.closed:
                try:
                    conn.rollback()
                except Exception as rb_err:
                    logger.error(f"Error during rollback: {str(rb_err)}")
            
            return None
            
        finally:
            execution_time_ms = (time.time() - start_time) * 1000
            self.pool_metrics["query_count"] += 1
            
            # Log slow queries
            if execution_time_ms > 100:  # More than 100ms is slow
                logger.warning(f"Slow query execution: {execution_time_ms:.2f}ms")
                logger.warning(f"Query: {query[:100]}...")
            
            if conn:
                self.return_connection(conn)
    
    def execute_postgres_query(self, query: str, params: tuple = None, 
                              fetchall: bool = True, cursor_factory=None):
        """
        Alias for execute_query to maintain compatibility with DatabaseCore.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetchall: Whether to fetch all results or just one
            cursor_factory: Factory for cursor creation
            
        Returns:
            Query results or None if error occurred
        """
        return self.execute_query(query, params, fetchall, cursor_factory)
    
    def _record_pool_metrics(self):
        """Record connection pool metrics periodically."""
        # Only record metrics every 5 minutes
        current_time = time.time()
        if current_time - self.pool_metrics["last_metrics_time"] < 300:  # 5 minutes
            return
        
        try:
            # Get current pool status
            if not hasattr(self.pg_pool, "_used") or not hasattr(self.pg_pool, "_pool"):
                return
            
            current_connections = len(self.pg_pool._used)
            available_connections = len(self.pg_pool._pool)
            
            # Calculate average acquisition time
            avg_acquisition_time = 0
            if self.pool_metrics["acquisition_times"]:
                avg_acquisition_time = sum(self.pool_metrics["acquisition_times"]) / len(self.pool_metrics["acquisition_times"])
            
            logger.info(f"Pool metrics - Used: {current_connections}, Available: {available_connections}, "
                       f"Avg acquisition: {avg_acquisition_time:.2f}ms, "
                       f"Queries: {self.pool_metrics['query_count']}, "
                       f"Errors: {self.pool_metrics['error_count']}")
            
            # Reset metrics
            self.pool_metrics = {
                "acquisition_times": [],
                "query_count": 0,
                "error_count": 0,
                "last_metrics_time": current_time
            }
            
        except Exception as e:
            logger.error(f"Error recording pool metrics: {e}")
    
    def is_connected(self) -> bool:
        """
        Check if the connection pool is initialized and working.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            if not self.pg_pool:
                return False
            
            # Try to get a connection and run a simple test
            conn = self.get_connection()
            if not conn:
                return False
            
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result[0] == 1 if result else False
            finally:
                self.return_connection(conn)
                
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def get_pool_status(self) -> Dict[str, Any]:
        """
        Get current connection pool status.
        
        Returns:
            Dictionary with pool status information
        """
        if not self.pg_pool:
            return {"status": "not_initialized"}
        
        try:
            return {
                "status": "active",
                "min_connections": self.pg_pool.minconn,
                "max_connections": self.pg_pool.maxconn,
                "used_connections": len(self.pg_pool._used) if hasattr(self.pg_pool, "_used") else 0,
                "available_connections": len(self.pg_pool._pool) if hasattr(self.pg_pool, "_pool") else 0,
                "total_queries": self.pool_metrics["query_count"],
                "total_errors": self.pool_metrics["error_count"]
            }
        except Exception as e:
            logger.error(f"Error getting pool status: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def close(self):
        """Close the connection pool and clean up resources."""
        try:
            if hasattr(self, 'pg_pool') and self.pg_pool:
                self.pg_pool.closeall()
                self.pg_pool = None
                logger.info("Closed PostgreSQL connection pool")
        except Exception as e:
            logger.error(f"Error closing PostgreSQL connection pool: {e}")
    
    def __enter__(self):
        """Support context manager pattern."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connections when exiting context manager."""
        self.close() 