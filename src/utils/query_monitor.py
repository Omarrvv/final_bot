"""
Query monitoring module for the Egypt Tourism Chatbot.
Provides utilities for monitoring and logging database queries.
"""
import time
import uuid
import logging
import json
from typing import Any, Dict, List, Optional, Tuple, Union
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

# Configure a separate logger for query metrics
query_metrics_logger = logging.getLogger("query_metrics")
query_metrics_logger.setLevel(logging.INFO)

# Add a file handler for query metrics
try:
    import os
    os.makedirs("logs", exist_ok=True)
    query_metrics_handler = logging.FileHandler("logs/query_metrics.log")
    query_metrics_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    query_metrics_logger.addHandler(query_metrics_handler)
except Exception as e:
    logger.error(f"Failed to set up query metrics logger: {e}")

class QueryMonitor:
    """
    Monitor and log database queries for performance analysis.
    """
    
    # Thresholds for query classification
    SLOW_QUERY_THRESHOLD_MS = 100  # Queries taking longer than 100ms are considered slow
    VERY_SLOW_QUERY_THRESHOLD_MS = 500  # Queries taking longer than 500ms are considered very slow
    
    @staticmethod
    def log_query(query: str, params: Optional[Tuple] = None, 
                 execution_time_ms: float = 0, 
                 rows_affected: int = 0,
                 query_id: str = None,
                 error: Optional[str] = None) -> None:
        """
        Log a database query with execution metrics.
        
        Args:
            query (str): SQL query string
            params (tuple, optional): Query parameters
            execution_time_ms (float): Query execution time in milliseconds
            rows_affected (int): Number of rows affected or returned
            query_id (str, optional): Unique identifier for the query
            error (str, optional): Error message if query failed
        """
        # Generate query ID if not provided
        if not query_id:
            query_id = str(uuid.uuid4())
            
        # Determine query type
        query_type = "SELECT" if query.strip().upper().startswith(("SELECT", "WITH")) else "MODIFY"
        
        # Determine performance category
        if execution_time_ms >= QueryMonitor.VERY_SLOW_QUERY_THRESHOLD_MS:
            performance = "VERY_SLOW"
        elif execution_time_ms >= QueryMonitor.SLOW_QUERY_THRESHOLD_MS:
            performance = "SLOW"
        else:
            performance = "NORMAL"
            
        # Create metrics record
        metrics = {
            "query_id": query_id,
            "query_type": query_type,
            "execution_time_ms": execution_time_ms,
            "rows_affected": rows_affected,
            "performance": performance,
            "timestamp": time.time(),
            "success": error is None
        }
        
        # Add error information if present
        if error:
            metrics["error"] = str(error)
            
        # Log metrics as JSON
        query_metrics_logger.info(json.dumps(metrics))
        
        # Log detailed query information for slow queries
        if performance != "NORMAL" or error:
            # Sanitize parameters for logging
            safe_params = QueryMonitor._sanitize_params(params) if params else None
            
            log_message = (
                f"[{performance}] Query {query_id} took {execution_time_ms:.2f}ms, "
                f"affected {rows_affected} rows. "
                f"Query: {query.strip()}"
            )
            
            if safe_params:
                log_message += f", Params: {safe_params}"
                
            if error:
                log_message += f", Error: {error}"
                
            if performance == "VERY_SLOW":
                logger.warning(log_message)
            elif performance == "SLOW":
                logger.info(log_message)
            elif error:
                logger.error(log_message)
                
    @staticmethod
    def _sanitize_params(params: Tuple) -> Tuple:
        """
        Sanitize query parameters for logging to avoid exposing sensitive data.
        
        Args:
            params (tuple): Query parameters
            
        Returns:
            tuple: Sanitized parameters
        """
        # List of parameter patterns that might contain sensitive data
        sensitive_patterns = ["password", "token", "secret", "key", "auth"]
        
        # If params is not a tuple or list, return as is
        if not isinstance(params, (tuple, list)):
            return params
            
        # Create a new list for sanitized parameters
        sanitized = []
        
        for param in params:
            # Check if parameter might contain sensitive information
            if isinstance(param, str) and any(pattern in param.lower() for pattern in sensitive_patterns):
                sanitized.append("***REDACTED***")
            else:
                sanitized.append(param)
                
        return tuple(sanitized)
        
    @staticmethod
    def monitor_query(func):
        """
        Decorator to monitor and log database queries.
        
        Args:
            func: Function that executes a database query
            
        Returns:
            Decorated function with query monitoring
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract query and params from args or kwargs
            query = args[1] if len(args) > 1 else kwargs.get('query')
            params = args[2] if len(args) > 2 else kwargs.get('params')
            
            # Generate query ID
            query_id = str(uuid.uuid4())
            
            # Record start time
            start_time = time.time()
            
            try:
                # Execute the query
                result = func(*args, **kwargs)
                
                # Calculate execution time
                execution_time_ms = (time.time() - start_time) * 1000
                
                # Determine rows affected
                if result is None:
                    rows_affected = 0
                elif isinstance(result, int):
                    rows_affected = result
                elif isinstance(result, (list, tuple)):
                    rows_affected = len(result)
                elif isinstance(result, dict):
                    rows_affected = 1
                else:
                    rows_affected = 0
                    
                # Log the query
                QueryMonitor.log_query(
                    query=query,
                    params=params,
                    execution_time_ms=execution_time_ms,
                    rows_affected=rows_affected,
                    query_id=query_id
                )
                
                return result
                
            except Exception as e:
                # Calculate execution time
                execution_time_ms = (time.time() - start_time) * 1000
                
                # Log the failed query
                QueryMonitor.log_query(
                    query=query,
                    params=params,
                    execution_time_ms=execution_time_ms,
                    rows_affected=0,
                    query_id=query_id,
                    error=str(e)
                )
                
                # Re-raise the exception
                raise
                
        return wrapper
