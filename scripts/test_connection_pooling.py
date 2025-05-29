#!/usr/bin/env python3
"""
Test script to verify connection pooling optimization.
This script tests the connection pool under load and measures performance.
"""

import os
import sys
import time
import random
import threading
import concurrent.futures
from typing import List, Dict, Any

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.knowledge.database import DatabaseManager
from src.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Test parameters
NUM_THREADS = 10
NUM_QUERIES_PER_THREAD = 20
QUERY_DELAY_MS = 50  # Simulate processing time between queries

def run_queries(db: DatabaseManager, thread_id: int) -> Dict[str, Any]:
    """Run a series of queries and measure performance."""
    results = {
        "thread_id": thread_id,
        "queries_executed": 0,
        "errors": 0,
        "total_time_ms": 0,
        "min_time_ms": float('inf'),
        "max_time_ms": 0,
        "avg_time_ms": 0
    }
    
    query_times = []
    
    for i in range(NUM_QUERIES_PER_THREAD):
        # Choose a random table to query
        table = random.choice(['attractions', 'restaurants', 'accommodations', 'cities'])
        limit = random.randint(1, 10)
        
        # Measure query execution time
        start_time = time.time()
        try:
            query = f"SELECT * FROM {table} LIMIT {limit}"
            db.execute_query(query)
            results["queries_executed"] += 1
        except Exception as e:
            logger.error(f"Thread {thread_id}, Query {i}: Error executing query: {e}")
            results["errors"] += 1
            continue
        
        # Calculate query time
        query_time_ms = (time.time() - start_time) * 1000
        query_times.append(query_time_ms)
        
        # Update statistics
        results["min_time_ms"] = min(results["min_time_ms"], query_time_ms)
        results["max_time_ms"] = max(results["max_time_ms"], query_time_ms)
        
        # Simulate processing time between queries
        time.sleep(QUERY_DELAY_MS / 1000)
    
    # Calculate final statistics
    if query_times:
        results["total_time_ms"] = sum(query_times)
        results["avg_time_ms"] = results["total_time_ms"] / len(query_times)
    else:
        results["min_time_ms"] = 0
    
    return results

def test_connection_pool_performance() -> Dict[str, Any]:
    """Test connection pool performance under load."""
    # Get database URI from environment variable
    database_uri = os.environ.get("POSTGRES_URI")
    if not database_uri:
        logger.error("POSTGRES_URI environment variable not set")
        sys.exit(1)
    
    # Create database managers for each thread
    # This simulates multiple concurrent clients
    db_managers = [DatabaseManager(database_uri=database_uri) for _ in range(NUM_THREADS)]
    
    # Run queries in parallel
    logger.info(f"Starting connection pool test with {NUM_THREADS} threads, {NUM_QUERIES_PER_THREAD} queries per thread")
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(run_queries, db_managers[i], i) for i in range(NUM_THREADS)]
        thread_results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    total_time = time.time() - start_time
    
    # Aggregate results
    total_queries = sum(r["queries_executed"] for r in thread_results)
    total_errors = sum(r["errors"] for r in thread_results)
    avg_query_time = sum(r["avg_time_ms"] for r in thread_results) / len(thread_results)
    min_query_time = min(r["min_time_ms"] for r in thread_results)
    max_query_time = max(r["max_time_ms"] for r in thread_results)
    
    # Close all database managers
    for db in db_managers:
        db.close()
    
    # Return aggregated results
    return {
        "total_threads": NUM_THREADS,
        "total_queries": total_queries,
        "total_errors": total_errors,
        "total_time_seconds": total_time,
        "queries_per_second": total_queries / total_time,
        "avg_query_time_ms": avg_query_time,
        "min_query_time_ms": min_query_time,
        "max_query_time_ms": max_query_time
    }

def check_connection_pool_recommendations() -> List[Dict[str, Any]]:
    """Check connection pool recommendations from the database."""
    # Get database URI from environment variable
    database_uri = os.environ.get("POSTGRES_URI")
    if not database_uri:
        logger.error("POSTGRES_URI environment variable not set")
        sys.exit(1)
    
    # Initialize database manager
    db = DatabaseManager(database_uri=database_uri)
    
    try:
        # Get recommendations
        recommendations = db.execute_query("SELECT * FROM get_connection_pool_recommendations()")
        return recommendations or []
    except Exception as e:
        logger.error(f"Error getting connection pool recommendations: {e}")
        return []
    finally:
        db.close()

def main():
    """Main function to run the connection pool test."""
    # Run performance test
    results = test_connection_pool_performance()
    
    # Print results
    logger.info("Connection Pool Performance Test Results:")
    logger.info(f"Total threads: {results['total_threads']}")
    logger.info(f"Total queries: {results['total_queries']}")
    logger.info(f"Total errors: {results['total_errors']}")
    logger.info(f"Total time: {results['total_time_seconds']:.2f} seconds")
    logger.info(f"Queries per second: {results['queries_per_second']:.2f}")
    logger.info(f"Average query time: {results['avg_query_time_ms']:.2f} ms")
    logger.info(f"Min query time: {results['min_query_time_ms']:.2f} ms")
    logger.info(f"Max query time: {results['max_query_time_ms']:.2f} ms")
    
    # Check for recommendations
    logger.info("\nChecking for connection pool recommendations...")
    recommendations = check_connection_pool_recommendations()
    
    if recommendations:
        logger.info("Connection Pool Recommendations:")
        for rec in recommendations:
            logger.info(f"- {rec['recommendation']}: Current={rec['current_value']}, Suggested={rec['suggested_value']} (Priority: {rec['priority']})")
    else:
        logger.info("No connection pool recommendations available.")

if __name__ == "__main__":
    main()
