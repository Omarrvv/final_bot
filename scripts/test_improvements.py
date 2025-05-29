#!/usr/bin/env python3
"""
Test script to verify the improvements made to the Egypt Tourism Chatbot.

This script tests:
1. Vector search with standardized embeddings
2. JSONB queries with proper parameter binding
3. Spatial queries with proper parameter binding
4. Connection pooling optimizations
"""

import os
import sys
import time
import json
import logging
import concurrent.futures
from typing import Dict, Any, List

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.knowledge.database import DatabaseManager
from src.services.vector_search_service import VectorSearchService
from src.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

class ImprovementsTester:
    """Test class for the improvements made to the Egypt Tourism Chatbot."""
    
    def __init__(self, db_uri: str):
        """Initialize with database URI."""
        self.db = DatabaseManager(database_uri=db_uri)
        self.vector_service = VectorSearchService(self.db)
    
    def close(self):
        """Close database connections."""
        if self.db:
            self.db.close()
    
    def test_vector_search(self) -> bool:
        """Test vector search with standardized embeddings."""
        logger.info("Testing vector search with standardized embeddings...")
        
        try:
            # Get a sample embedding from the database
            query = """
                SELECT embedding 
                FROM attractions 
                WHERE embedding IS NOT NULL 
                LIMIT 1
            """
            result = self.db.execute_postgres_query(query)
            if not result:
                logger.error("No embeddings found in the database")
                return False
            
            embedding = result[0]['embedding']
            logger.info(f"Using embedding of type {type(embedding).__name__}")
            
            # Test vector search on different tables
            tables = ['attractions', 'restaurants', 'accommodations', 'cities']
            
            for table in tables:
                # Perform search
                results = self.vector_service.search(table, embedding, limit=5)
                
                if not results:
                    logger.warning(f"No results returned from vector search on {table}")
                    continue
                
                logger.info(f"Vector search on {table} returned {len(results)} results")
                logger.info(f"First result: {results[0].get('name', 'Unknown')} (distance: {results[0].get('distance', 'N/A')})")
            
            return True
        except Exception as e:
            logger.error(f"Error in vector search test: {e}")
            return False
    
    def test_jsonb_queries(self) -> bool:
        """Test JSONB queries with proper parameter binding."""
        logger.info("Testing JSONB queries with proper parameter binding...")
        
        try:
            # Test queries with parameters
            query_params = [
                ("SELECT * FROM attractions WHERE name->>%s ILIKE %s LIMIT 5", ('en', '%pyramid%')),
                ("SELECT * FROM restaurants WHERE name->>%s ILIKE %s LIMIT 5", ('en', '%cafe%')),
                ("SELECT * FROM accommodations WHERE name->>%s ILIKE %s LIMIT 5", ('en', '%hotel%')),
                ("SELECT * FROM cities WHERE name->>%s ILIKE %s LIMIT 5", ('en', '%cairo%'))
            ]
            
            for query, params in query_params:
                # Execute query
                results = self.db.execute_query(query, params)
                
                if not results:
                    logger.warning(f"No results returned from JSONB query: {query}")
                    continue
                
                logger.info(f"JSONB query returned {len(results)} results")
                logger.info(f"First result: {results[0].get('name', 'Unknown')}")
            
            return True
        except Exception as e:
            logger.error(f"Error in JSONB queries test: {e}")
            return False
    
    def test_spatial_queries(self) -> bool:
        """Test spatial queries with proper parameter binding."""
        logger.info("Testing spatial queries with proper parameter binding...")
        
        try:
            # Get a sample location (Cairo)
            cairo_coords = (30.0444, 31.2357)
            
            # Test spatial query with proper parameter binding
            query = """
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
            
            # Execute query
            results = self.db.execute_query(query, params)
            
            if not results:
                logger.warning("No results returned from spatial query")
                return False
            
            logger.info(f"Spatial query returned {len(results)} results")
            logger.info(f"First result: {results[0].get('name', 'Unknown')} (distance: {results[0].get('distance_km', 'N/A')} km)")
            
            # Test cached nearby attractions function
            try:
                cached_query = """
                    SELECT cached_nearby_attractions(%s, %s, %s, %s)
                """
                cached_results = self.db.execute_query(cached_query, (cairo_coords[0], cairo_coords[1], 5.0, 10))
                
                if cached_results and cached_results[0].get('cached_nearby_attractions'):
                    logger.info("Cached nearby attractions function works correctly")
                else:
                    logger.warning("Cached nearby attractions function returned no results")
            except Exception as e:
                logger.warning(f"Error testing cached nearby attractions: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Error in spatial queries test: {e}")
            return False
    
    def test_connection_pooling(self) -> bool:
        """Test connection pooling optimizations."""
        logger.info("Testing connection pooling optimizations...")
        
        try:
            # Test concurrent database access
            num_threads = 10
            num_queries = 5
            
            def run_queries():
                """Run a set of queries."""
                try:
                    for _ in range(num_queries):
                        self.db.execute_query("SELECT * FROM attractions LIMIT 5")
                    return True
                except Exception as e:
                    logger.error(f"Error in thread: {e}")
                    return False
            
            # Run queries concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(run_queries) for _ in range(num_threads)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            success_rate = sum(results) / len(results) * 100
            logger.info(f"Connection pooling test: {success_rate:.1f}% success rate")
            
            # Get connection pool statistics
            try:
                stats = self.db.execute_query("SELECT * FROM get_current_db_connections()")
                if stats:
                    logger.info(f"Database connections: {json.dumps(stats[0], default=str)}")
            except Exception as e:
                logger.warning(f"Error getting connection statistics: {e}")
            
            return all(results)
        except Exception as e:
            logger.error(f"Error in connection pooling test: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests."""
        tests = [
            self.test_vector_search,
            self.test_jsonb_queries,
            self.test_spatial_queries,
            self.test_connection_pooling
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
                status = "PASSED" if result else "FAILED"
                logger.info(f"Test {test.__name__}: {status}")
            except Exception as e:
                logger.error(f"Error in test {test.__name__}: {e}")
                results.append(False)
        
        success_rate = sum(results) / len(results) * 100
        logger.info(f"All tests completed: {success_rate:.1f}% success rate")
        
        return all(results)

def main():
    """Main function to run the tests."""
    # Get database URI from environment variable
    database_uri = os.environ.get("POSTGRES_URI")
    if not database_uri:
        logger.error("POSTGRES_URI environment variable not set")
        sys.exit(1)
    
    # Initialize tester
    tester = ImprovementsTester(database_uri)
    
    try:
        # Run tests
        success = tester.run_all_tests()
        
        # Exit with appropriate status code
        sys.exit(0 if success else 1)
    finally:
        # Close database connection
        tester.close()

if __name__ == "__main__":
    main()
