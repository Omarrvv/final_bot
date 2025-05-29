#!/usr/bin/env python3
"""
Test script for the Vector Search Service.

This script tests the functionality of the VectorSearchService class,
including embedding standardization, error handling, and search operations.
"""

import os
import sys
import json
import logging
import numpy as np
from typing import List, Dict, Any

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.knowledge.database import DatabaseManager
from src.services.vector_search_service import VectorSearchService, VectorSearchError
from src.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

class VectorSearchTester:
    """Test class for vector search functionality."""

    def __init__(self, db_uri: str):
        """Initialize with database URI."""
        self.db = DatabaseManager(database_uri=db_uri)
        self.service = VectorSearchService(self.db)

    def test_embedding_standardization(self) -> bool:
        """Test embedding standardization with various input formats."""
        logger.info("Testing embedding standardization...")

        test_cases = [
            # List of floats
            ([0.1, 0.2, 0.3], True),
            # List of integers
            ([1, 2, 3], True),
            # List of mixed types
            ([1, 2.5, "3"], True),
            # NumPy array
            (np.array([0.1, 0.2, 0.3]), True),
            # JSON string (array)
            ("[0.1, 0.2, 0.3]", True),
            # Comma-separated string
            ("0.1,0.2,0.3", True),
            # Invalid string
            ("not an embedding", False),
            # None
            (None, False),
            # Empty list
            ([], True),
        ]

        success = True
        for embedding, should_succeed in test_cases:
            try:
                result = self.service.standardize_embedding(embedding)
                if should_succeed:
                    logger.info(f"Successfully standardized {type(embedding).__name__}: {result[:3]}...")
                else:
                    logger.error(f"Expected failure but got success for {embedding}")
                    success = False
            except VectorSearchError as e:
                if should_succeed:
                    logger.error(f"Expected success but got error for {embedding}: {e}")
                    success = False
                else:
                    logger.info(f"Got expected error for {embedding}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error for {embedding}: {e}")
                success = False

        return success

    def test_vector_search_basic(self) -> bool:
        """Test basic vector search functionality."""
        logger.info("Testing basic vector search...")

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

            # Perform search
            results = self.service.search('attractions', embedding, limit=5)

            if not results:
                logger.error("No results returned from vector search")
                return False

            logger.info(f"Vector search returned {len(results)} results")
            logger.info(f"First result: {results[0].get('name', 'Unknown')} (distance: {results[0].get('distance', 'N/A')})")

            return True
        except Exception as e:
            logger.error(f"Error in basic vector search test: {e}")
            return False

    def test_table_specific_methods(self) -> bool:
        """Test table-specific search methods."""
        logger.info("Testing table-specific search methods...")

        try:
            # Get a sample embedding
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

            # Test each table-specific method
            methods = [
                (self.service.search_attractions, "attractions"),
                (self.service.search_restaurants, "restaurants"),
                (self.service.search_hotels, "hotels"),
                (self.service.search_cities, "cities")
            ]

            success = True
            for method, name in methods:
                try:
                    results = method(embedding, limit=3)
                    logger.info(f"{name.capitalize()} search returned {len(results)} results")
                except Exception as e:
                    logger.error(f"Error in {name} search: {e}")
                    success = False

            return success
        except Exception as e:
            logger.error(f"Error in table-specific methods test: {e}")
            return False

    def test_error_handling(self) -> bool:
        """Test error handling in vector search."""
        logger.info("Testing error handling...")

        try:
            # Test with invalid table name
            try:
                self.service.search('invalid_table', [0.1, 0.2, 0.3])
                logger.error("Expected error for invalid table, but got success")
                return False
            except VectorSearchError as e:
                logger.info(f"Got expected error for invalid table: {e}")

            # Test with invalid embedding
            try:
                self.service.search('attractions', "not an embedding")
                logger.error("Expected error for invalid embedding, but got success")
                return False
            except VectorSearchError as e:
                logger.info(f"Got expected error for invalid embedding: {e}")

            return True
        except Exception as e:
            logger.error(f"Unexpected error in error handling test: {e}")
            return False

    def run_all_tests(self) -> bool:
        """Run all vector search tests."""
        tests = [
            self.test_embedding_standardization,
            self.test_vector_search_basic,
            self.test_table_specific_methods,
            self.test_error_handling
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
        logger.info(f"Vector search tests completed: {success_rate:.1f}% success rate")

        return all(results)

def main():
    """Main function to run the tests."""
    # Get database URI from environment variable
    database_uri = os.environ.get("POSTGRES_URI")
    if not database_uri:
        logger.error("POSTGRES_URI environment variable not set")
        sys.exit(1)

    # Initialize tester
    tester = VectorSearchTester(database_uri)

    # Run tests
    success = tester.run_all_tests()

    # Close database connection
    tester.db.close()

    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
