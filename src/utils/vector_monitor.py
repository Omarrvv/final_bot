"""
Vector search monitoring module for the Egypt Tourism Chatbot.
Provides utilities for monitoring and logging vector search operations.
"""
import time
import uuid
import logging
import json
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

# Configure a separate logger for vector search metrics
vector_metrics_logger = logging.getLogger("vector_metrics")
vector_metrics_logger.setLevel(logging.INFO)

# Add a file handler for vector metrics
try:
    import os
    os.makedirs("logs", exist_ok=True)
    vector_metrics_handler = logging.FileHandler("logs/vector_metrics.log")
    vector_metrics_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    vector_metrics_logger.addHandler(vector_metrics_handler)
except Exception as e:
    logger.error(f"Failed to set up vector metrics logger: {e}")

class VectorMonitor:
    """
    Monitor and log vector search operations for performance analysis.
    """
    
    # Thresholds for vector search classification
    SLOW_SEARCH_THRESHOLD_MS = 50  # Searches taking longer than 50ms are considered slow
    VERY_SLOW_SEARCH_THRESHOLD_MS = 200  # Searches taking longer than 200ms are considered very slow
    
    @staticmethod
    def log_vector_search(collection: str, 
                         query_text: Optional[str] = None,
                         filters: Optional[Dict] = None,
                         limit: int = 10,
                         execution_time_ms: float = 0,
                         result_count: int = 0,
                         top_score: Optional[float] = None,
                         avg_score: Optional[float] = None,
                         search_id: str = None,
                         cache_hit: bool = False,
                         error: Optional[str] = None) -> None:
        """
        Log a vector search operation with execution metrics.
        
        Args:
            collection (str): Collection name
            query_text (str, optional): Original query text
            filters (dict, optional): Search filters
            limit (int): Maximum number of results
            execution_time_ms (float): Search execution time in milliseconds
            result_count (int): Number of results returned
            top_score (float, optional): Highest similarity score
            avg_score (float, optional): Average similarity score
            search_id (str, optional): Unique identifier for the search
            cache_hit (bool): Whether the result was from cache
            error (str, optional): Error message if search failed
        """
        # Generate search ID if not provided
        if not search_id:
            search_id = str(uuid.uuid4())
            
        # Determine performance category
        if execution_time_ms >= VectorMonitor.VERY_SLOW_SEARCH_THRESHOLD_MS:
            performance = "VERY_SLOW"
        elif execution_time_ms >= VectorMonitor.SLOW_SEARCH_THRESHOLD_MS:
            performance = "SLOW"
        else:
            performance = "NORMAL"
            
        # Create metrics record
        metrics = {
            "search_id": search_id,
            "collection": collection,
            "execution_time_ms": execution_time_ms,
            "result_count": result_count,
            "limit": limit,
            "performance": performance,
            "timestamp": time.time(),
            "success": error is None,
            "cache_hit": cache_hit
        }
        
        # Add optional metrics
        if query_text:
            metrics["query_length"] = len(query_text)
            
        if filters:
            metrics["filter_count"] = len(filters)
            
        if top_score is not None:
            metrics["top_score"] = top_score
            
        if avg_score is not None:
            metrics["avg_score"] = avg_score
            
        # Add error information if present
        if error:
            metrics["error"] = str(error)
            
        # Log metrics as JSON
        vector_metrics_logger.info(json.dumps(metrics))
        
        # Log detailed search information for slow searches
        if performance != "NORMAL" or error:
            log_message = (
                f"[{performance}] Vector search {search_id} on {collection} took {execution_time_ms:.2f}ms, "
                f"returned {result_count}/{limit} results"
            )
            
            if cache_hit:
                log_message += " (CACHE HIT)"
                
            if top_score is not None:
                log_message += f", top score: {top_score:.4f}"
                
            if avg_score is not None:
                log_message += f", avg score: {avg_score:.4f}"
                
            if query_text:
                # Truncate long queries for logging
                truncated_query = query_text[:50] + "..." if len(query_text) > 50 else query_text
                log_message += f", query: '{truncated_query}'"
                
            if filters:
                log_message += f", filters: {filters}"
                
            if error:
                log_message += f", error: {error}"
                
            if performance == "VERY_SLOW":
                logger.warning(log_message)
            elif performance == "SLOW":
                logger.info(log_message)
            elif error:
                logger.error(log_message)
                
    @staticmethod
    def monitor_vector_search(func):
        """
        Decorator to monitor and log vector search operations.
        
        Args:
            func: Function that performs a vector search
            
        Returns:
            Decorated function with vector search monitoring
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract search parameters
            collection = kwargs.get('collection', args[1] if len(args) > 1 else None)
            query_text = kwargs.get('query', None)
            filters = kwargs.get('filters', None)
            limit = kwargs.get('limit', 10)
            
            # Generate search ID
            search_id = str(uuid.uuid4())
            
            # Record start time
            start_time = time.time()
            
            try:
                # Execute the search
                result = func(*args, **kwargs)
                
                # Calculate execution time
                execution_time_ms = (time.time() - start_time) * 1000
                
                # Determine result metrics
                result_count = len(result) if isinstance(result, (list, tuple)) else 0
                
                # Calculate score metrics if results are (id, score) tuples
                top_score = None
                avg_score = None
                
                if result_count > 0 and isinstance(result[0], tuple) and len(result[0]) > 1:
                    scores = [item[1] for item in result]
                    top_score = max(scores) if scores else None
                    avg_score = sum(scores) / len(scores) if scores else None
                    
                # Determine if this was a cache hit (approximate)
                cache_hit = execution_time_ms < 5  # Assume very fast searches are cache hits
                
                # Log the search
                VectorMonitor.log_vector_search(
                    collection=collection,
                    query_text=query_text,
                    filters=filters,
                    limit=limit,
                    execution_time_ms=execution_time_ms,
                    result_count=result_count,
                    top_score=top_score,
                    avg_score=avg_score,
                    search_id=search_id,
                    cache_hit=cache_hit
                )
                
                return result
                
            except Exception as e:
                # Calculate execution time
                execution_time_ms = (time.time() - start_time) * 1000
                
                # Log the failed search
                VectorMonitor.log_vector_search(
                    collection=collection,
                    query_text=query_text,
                    filters=filters,
                    limit=limit,
                    execution_time_ms=execution_time_ms,
                    result_count=0,
                    search_id=search_id,
                    error=str(e)
                )
                
                # Re-raise the exception
                raise
                
        return wrapper
