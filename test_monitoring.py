#!/usr/bin/env python
"""
Test script for database and vector search monitoring.
This script tests the monitoring implementations to ensure they work correctly.
"""

import os
import sys
import logging
import time
import numpy as np
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the database manager and vector DB
try:
    from src.knowledge.database import DatabaseManager
    from src.knowledge.vector_db import VectorDB
    logger.info("Successfully imported DatabaseManager and VectorDB")
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def test_database_monitoring():
    """Test the database query monitoring."""
    logger.info("Testing database query monitoring...")
    
    # Database connection URI
    postgres_uri = os.environ.get("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot_migration_test")
    
    try:
        # Create a database manager instance
        db_manager = DatabaseManager(database_uri=postgres_uri)
        logger.info("Successfully created DatabaseManager instance")
        
        # Test a fast query
        logger.info("Executing a fast query...")
        result = db_manager.execute_postgres_query("SELECT 1 as test")
        logger.info(f"Fast query result: {result}")
        
        # Test a slow query
        logger.info("Executing a slow query...")
        result = db_manager.execute_postgres_query("""
            SELECT pg_sleep(0.2), * 
            FROM attractions 
            CROSS JOIN cities
        """)
        logger.info(f"Slow query returned {len(result)} rows")
        
        # Test a very slow query
        logger.info("Executing a very slow query...")
        result = db_manager.execute_postgres_query("""
            SELECT pg_sleep(0.6), * 
            FROM attractions 
            CROSS JOIN cities 
            CROSS JOIN accommodations
        """)
        logger.info(f"Very slow query returned {len(result)} rows")
        
        # Test a query with parameters
        logger.info("Executing a query with parameters...")
        result = db_manager.execute_postgres_query(
            "SELECT * FROM attractions WHERE city = %s", 
            ("cairo",)
        )
        logger.info(f"Parameterized query returned {len(result)} rows")
        
        # Test a query that fails
        logger.info("Executing a query that will fail...")
        try:
            result = db_manager.execute_postgres_query("SELECT * FROM nonexistent_table")
        except Exception as e:
            logger.info(f"Query failed as expected: {e}")
        
        logger.info("Database query monitoring tests completed")
        return True
    except Exception as e:
        logger.error(f"Database monitoring test failed: {e}", exc_info=True)
        return False

def test_vector_search_monitoring():
    """Test the vector search monitoring."""
    logger.info("Testing vector search monitoring...")
    
    try:
        # Create a vector DB instance
        vector_db = VectorDB(content_path="./test_vectors")
        logger.info("Successfully created VectorDB instance")
        
        # Create some test vectors
        logger.info("Creating test vectors...")
        vector_db.vectors = {
            "attractions": {
                "test1": {
                    "vector": np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32),
                    "metadata": {"type": "historical", "city": "cairo"}
                },
                "test2": {
                    "vector": np.array([0.2, 0.3, 0.4, 0.5], dtype=np.float32),
                    "metadata": {"type": "museum", "city": "luxor"}
                },
                "test3": {
                    "vector": np.array([0.3, 0.4, 0.5, 0.6], dtype=np.float32),
                    "metadata": {"type": "beach", "city": "alexandria"}
                }
            }
        }
        
        # Test a basic vector search
        logger.info("Executing a basic vector search...")
        query_vector = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        results = vector_db.search(
            collection="attractions",
            query_vector=query_vector,
            limit=2,
            query_text="test query"
        )
        logger.info(f"Vector search returned {len(results)} results")
        
        # Test a vector search with filters
        logger.info("Executing a vector search with filters...")
        results = vector_db.search(
            collection="attractions",
            query_vector=query_vector,
            filters={"city": "cairo"},
            limit=2,
            query_text="cairo attractions"
        )
        logger.info(f"Filtered vector search returned {len(results)} results")
        
        # Test a vector search with no results
        logger.info("Executing a vector search with no results...")
        results = vector_db.search(
            collection="nonexistent",
            query_vector=query_vector,
            limit=2,
            query_text="nonexistent collection"
        )
        logger.info(f"Empty vector search returned {len(results)} results")
        
        # Test a slow vector search
        logger.info("Executing a slow vector search...")
        
        # Create a mock embedding model
        def mock_embedding_model(text, language):
            time.sleep(0.1)  # Simulate slow embedding generation
            return np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        
        # Test the search_attractions method
        results = vector_db.search_attractions(
            query="pyramids",
            embedding_model=mock_embedding_model,
            filters={"type": "historical"},
            language="en",
            limit=2
        )
        logger.info(f"Attraction search returned {len(results)} results")
        
        logger.info("Vector search monitoring tests completed")
        return True
    except Exception as e:
        logger.error(f"Vector search monitoring test failed: {e}", exc_info=True)
        return False

def main():
    """Main function to run the monitoring tests."""
    logger.info("Starting monitoring tests")
    
    # Test database monitoring
    db_success = test_database_monitoring()
    
    # Test vector search monitoring
    vector_success = test_vector_search_monitoring()
    
    if db_success and vector_success:
        logger.info("All monitoring tests passed")
        return 0
    else:
        logger.error("Some monitoring tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
