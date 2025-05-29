#!/usr/bin/env python3
"""
Test script to verify database optimizations.
This script tests the database performance before and after optimizations.
"""

import os
import sys
import time
import json
import random
import logging
from typing import Dict, Any, List, Tuple

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.knowledge.database import DatabaseManager
from src.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

class DatabaseOptimizationTester:
    """Class to test database optimizations."""

    def __init__(self, database_uri: str):
        """Initialize the tester with a database URI."""
        self.database_uri = database_uri
        self.db = DatabaseManager(database_uri=database_uri)

    def close(self):
        """Close the database connection."""
        if self.db:
            self.db.close()

    def test_jsonb_performance(self) -> Dict[str, Any]:
        """Test JSONB query performance."""
        logger.info("Testing JSONB query performance...")

        # Test queries with parameters
        query_params = [
            ("SELECT * FROM attractions WHERE name->>%s ILIKE %s LIMIT 5", ('en', '%pyramid%')),
            ("SELECT * FROM restaurants WHERE name->>%s ILIKE %s LIMIT 5", ('en', '%cafe%')),
            ("SELECT * FROM accommodations WHERE name->>%s ILIKE %s LIMIT 5", ('en', '%hotel%')),
            ("SELECT * FROM cities WHERE name->>%s ILIKE %s LIMIT 5", ('en', '%cairo%'))
        ]

        results = {}
        for query, params in query_params:
            # Run the query multiple times to get average performance
            times = []
            for _ in range(5):
                start_time = time.time()
                self.db.execute_query(query, params)
                query_time = (time.time() - start_time) * 1000  # Convert to ms
                times.append(query_time)

            # Calculate statistics
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            # Store results
            query_name = query.split("FROM")[1].split("WHERE")[0].strip()
            results[query_name] = {
                "avg_time_ms": avg_time,
                "min_time_ms": min_time,
                "max_time_ms": max_time
            }

            logger.info(f"{query_name}: Avg={avg_time:.2f}ms, Min={min_time:.2f}ms, Max={max_time:.2f}ms")

        return results

    def test_vector_search_performance(self) -> Dict[str, Any]:
        """Test vector search performance."""
        logger.info("Testing vector search performance...")

        # Get a sample embedding
        embedding_query = """
            SELECT embedding
            FROM attractions
            WHERE embedding IS NOT NULL
            LIMIT 1
        """
        embedding_result = self.db.execute_query(embedding_query)
        if not embedding_result:
            logger.error("No embeddings found in the database")
            return {}

        embedding = embedding_result[0]['embedding']

        # Test vector search on different tables
        tables = ['attractions', 'restaurants', 'accommodations', 'cities']
        results = {}

        for table in tables:
            # Run vector search multiple times to get average performance
            times = []
            for _ in range(3):
                start_time = time.time()
                self.db.vector_search(table, embedding, limit=5)
                search_time = (time.time() - start_time) * 1000  # Convert to ms
                times.append(search_time)

            # Calculate statistics
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            # Store results
            results[table] = {
                "avg_time_ms": avg_time,
                "min_time_ms": min_time,
                "max_time_ms": max_time
            }

            logger.info(f"Vector search on {table}: Avg={avg_time:.2f}ms, Min={min_time:.2f}ms, Max={max_time:.2f}ms")

        return results

    def test_connection_pool(self) -> Dict[str, Any]:
        """Test connection pool performance."""
        logger.info("Testing connection pool performance...")

        # Get connection pool stats
        try:
            stats = self.db.execute_query("SELECT * FROM connection_pool_monitoring ORDER BY hour DESC LIMIT 1")
            if stats:
                logger.info(f"Connection pool stats: {json.dumps(stats[0], default=str)}")
                return stats[0]
            else:
                logger.warning("No connection pool stats available")
                return {}
        except Exception as e:
            logger.error(f"Error getting connection pool stats: {e}")
            return {}

    def test_query_cache(self) -> Dict[str, Any]:
        """Test query cache performance."""
        logger.info("Testing query cache performance...")

        # Test cached nearby attractions query
        try:
            # Get a sample location (Cairo)
            cairo_coords = (30.0444, 31.2357)

            # Run uncached query with proper parameter binding
            start_time = time.time()
            uncached_query = """
                SELECT a.*,
                       ST_Distance(
                           a.geom,
                           ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                           true
                       ) / 1000 AS distance_km
                FROM attractions a
                WHERE ST_DWithin(
                    a.geom,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                    %s * 1000
                )
                ORDER BY distance_km
                LIMIT %s
            """
            params = (
                cairo_coords[1], cairo_coords[0],  # Longitude, Latitude for ST_MakePoint
                cairo_coords[1], cairo_coords[0],  # Longitude, Latitude for ST_MakePoint in ST_DWithin
                5.0,  # Radius in km
                10    # Limit
            )
            self.db.execute_query(uncached_query, params)
            uncached_time = (time.time() - start_time) * 1000  # Convert to ms

            # Skip cached query test if function doesn't exist
            try:
                # Check if cached_nearby_attractions function exists
                check_query = """
                    SELECT 1 FROM pg_proc
                    WHERE proname = 'cached_nearby_attractions'
                """
                function_exists = self.db.execute_query(check_query)

                if function_exists:
                    # Run cached query
                    start_time = time.time()
                    cached_query = """
                        SELECT cached_nearby_attractions(%s, %s, %s, %s)
                    """
                    self.db.execute_query(cached_query, (cairo_coords[0], cairo_coords[1], 5.0, 10))
                    first_cached_time = (time.time() - start_time) * 1000  # Convert to ms

                    # Run cached query again (should be faster)
                    start_time = time.time()
                    self.db.execute_query(cached_query, (cairo_coords[0], cairo_coords[1], 5.0, 10))
                    second_cached_time = (time.time() - start_time) * 1000  # Convert to ms
                else:
                    logger.warning("cached_nearby_attractions function not found, skipping cache test")
                    first_cached_time = 0
                    second_cached_time = 0
            except Exception as e:
                logger.warning(f"Error testing cached query: {e}")
                first_cached_time = 0
                second_cached_time = 0

            # Try to get cache stats if available
            try:
                cache_stats = self.db.execute_query("SELECT * FROM get_cache_stats()")
            except Exception:
                cache_stats = None

            results = {
                "uncached_time_ms": uncached_time,
                "first_cached_time_ms": first_cached_time,
                "second_cached_time_ms": second_cached_time,
                "speedup_factor": uncached_time / second_cached_time if second_cached_time > 0 else 0,
                "cache_stats": cache_stats[0] if cache_stats else {}
            }

            logger.info(f"Query cache performance: Uncached={uncached_time:.2f}ms")
            if first_cached_time > 0:
                logger.info(f"First cached={first_cached_time:.2f}ms, Second cached={second_cached_time:.2f}ms")
                logger.info(f"Cache speedup factor: {results['speedup_factor']:.2f}x")

            return results
        except Exception as e:
            logger.error(f"Error testing query cache: {e}")
            return {}

def main():
    """Main function to run the database optimization tests."""
    # Get database URI from environment variable
    database_uri = os.environ.get("POSTGRES_URI")
    if not database_uri:
        logger.error("POSTGRES_URI environment variable not set")
        sys.exit(1)

    # Initialize tester
    tester = DatabaseOptimizationTester(database_uri)

    try:
        # Run tests
        logger.info("Starting database optimization tests...")

        jsonb_results = tester.test_jsonb_performance()
        vector_results = tester.test_vector_search_performance()
        pool_results = tester.test_connection_pool()
        cache_results = tester.test_query_cache()

        # Print summary
        logger.info("\nDatabase Optimization Test Summary:")
        logger.info("----------------------------------")

        logger.info("\nJSONB Query Performance:")
        for table, stats in jsonb_results.items():
            logger.info(f"- {table}: Avg={stats['avg_time_ms']:.2f}ms")

        logger.info("\nVector Search Performance:")
        for table, stats in vector_results.items():
            logger.info(f"- {table}: Avg={stats['avg_time_ms']:.2f}ms")

        if cache_results:
            logger.info("\nQuery Cache Performance:")
            logger.info(f"- Uncached: {cache_results['uncached_time_ms']:.2f}ms")
            logger.info(f"- Cached: {cache_results['second_cached_time_ms']:.2f}ms")
            logger.info(f"- Speedup: {cache_results['speedup_factor']:.2f}x")

        logger.info("\nTests completed successfully!")

    finally:
        # Close database connection
        tester.close()

if __name__ == "__main__":
    main()
