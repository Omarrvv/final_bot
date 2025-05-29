#!/usr/bin/env python3
"""
Test script to verify the implementation of the missing methods in the KnowledgeBase class:
1. search_transportation
2. search_tour_packages
3. find_hotels_near_attraction
"""

import os
import sys
import logging
import json
from typing import Dict, List, Any, Optional

# Configure logging - set to DEBUG for more detailed output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Ensure output goes to stdout
)
logger = logging.getLogger(__name__)

# Enable debug logging for all modules
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger('src.knowledge.knowledge_base').setLevel(logging.DEBUG)
logging.getLogger('src.knowledge.database').setLevel(logging.DEBUG)
logging.getLogger('src.knowledge.cross_table_queries').setLevel(logging.DEBUG)

# Print confirmation that the script is running
print("=== TEST SCRIPT STARTING ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import the required modules
try:
    from src.knowledge.knowledge_base import KnowledgeBase
    from src.knowledge.database import DatabaseManager
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)

# Database connection string
DB_CONNECTION_STRING = "postgresql://postgres:postgres@localhost:5432/egypt_chatbot"

def test_search_transportation():
    """Test the search_transportation method."""
    logger.info("=== Testing search_transportation method ===")
    print("\n=== Testing search_transportation method ===")

    try:
        # Initialize the database manager and knowledge base
        print("Initializing DatabaseManager and KnowledgeBase...")
        db_manager = DatabaseManager(database_uri=DB_CONNECTION_STRING)
        kb = KnowledgeBase(db_manager=db_manager)
        print(f"Database manager initialized: {db_manager}")
        print(f"Knowledge base initialized: {kb}")

        # Test with a text query
        print("\nTest 1: Testing with text query 'train'...")
        logger.info("Testing with text query 'train'...")
        results = kb.search_transportation(query="train", limit=5)
        print(f"Results: {results}")
        print(f"Found {len(results)} transportation options for 'train'")
        logger.info(f"Found {len(results)} transportation options for 'train'")

        # Test with origin and destination
        print("\nTest 2: Testing with origin 'cairo' and destination 'luxor'...")
        logger.info("Testing with origin 'cairo' and destination 'luxor'...")
        results = kb.search_transportation(origin="cairo", destination="luxor", limit=5)
        print(f"Results: {results}")
        print(f"Found {len(results)} transportation options from Cairo to Luxor")
        logger.info(f"Found {len(results)} transportation options from Cairo to Luxor")

        # Test with transportation type
        print("\nTest 3: Testing with transportation type 'train'...")
        logger.info("Testing with transportation type 'train'...")
        results = kb.search_transportation(transportation_type="train", limit=5)
        print(f"Results: {results}")
        print(f"Found {len(results)} train transportation options")
        logger.info(f"Found {len(results)} train transportation options")

        # Test with all parameters
        print("\nTest 4: Testing with all parameters...")
        logger.info("Testing with all parameters...")
        results = kb.search_transportation(
            query="express",
            origin="cairo",
            destination="aswan",
            transportation_type="train",
            limit=5
        )
        print(f"Results: {results}")
        print(f"Found {len(results)} express train options from Cairo to Aswan")
        logger.info(f"Found {len(results)} express train options from Cairo to Aswan")

        # Print a sample result if available
        if results:
            print("\nSample transportation result:")
            logger.info("Sample transportation result:")
            sample_result = json.dumps(results[0], indent=2, default=str)
            print(sample_result)
            logger.info(sample_result)

        return True
    except Exception as e:
        print(f"ERROR: {e}")
        logger.error(f"Error testing search_transportation: {e}", exc_info=True)
        return False

def test_search_tour_packages():
    """Test the search_tour_packages method."""
    logger.info("=== Testing search_tour_packages method ===")
    print("\n=== Testing search_tour_packages method ===")

    try:
        # Initialize the database manager and knowledge base
        print("Initializing DatabaseManager and KnowledgeBase...")
        db_manager = DatabaseManager(database_uri=DB_CONNECTION_STRING)
        kb = KnowledgeBase(db_manager=db_manager)
        print(f"Database manager initialized: {db_manager}")
        print(f"Knowledge base initialized: {kb}")

        # Test with a text query
        print("\nTest 1: Testing with text query 'nile'...")
        logger.info("Testing with text query 'nile'...")
        results = kb.search_tour_packages(query="nile", limit=5)
        print(f"Results: {results}")
        print(f"Found {len(results)} tour packages for 'nile'")
        logger.info(f"Found {len(results)} tour packages for 'nile'")

        # Test with category_id
        print("\nTest 2: Testing with category_id 'luxury'...")
        logger.info("Testing with category_id 'luxury'...")
        results = kb.search_tour_packages(category_id="luxury", limit=5)
        print(f"Results: {results}")
        print(f"Found {len(results)} luxury tour packages")
        logger.info(f"Found {len(results)} luxury tour packages")

        # Test with duration parameters
        print("\nTest 3: Testing with min_duration=3, max_duration=7...")
        logger.info("Testing with min_duration=3, max_duration=7...")
        results = kb.search_tour_packages(min_duration=3, max_duration=7, limit=5)
        print(f"Results: {results}")
        print(f"Found {len(results)} tour packages with duration between 3 and 7 days")
        logger.info(f"Found {len(results)} tour packages with duration between 3 and 7 days")

        # Test with all parameters
        print("\nTest 4: Testing with all parameters...")
        logger.info("Testing with all parameters...")
        results = kb.search_tour_packages(
            query="cruise",
            category_id="luxury",
            min_duration=5,
            max_duration=10,
            limit=5
        )
        print(f"Results: {results}")
        print(f"Found {len(results)} luxury cruise tour packages with duration between 5 and 10 days")
        logger.info(f"Found {len(results)} luxury cruise tour packages with duration between 5 and 10 days")

        # Print a sample result if available
        if results:
            print("\nSample tour package result:")
            logger.info("Sample tour package result:")
            sample_result = json.dumps(results[0], indent=2, default=str)
            print(sample_result)
            logger.info(sample_result)

        return True
    except Exception as e:
        print(f"ERROR: {e}")
        logger.error(f"Error testing search_tour_packages: {e}", exc_info=True)
        return False

def test_find_hotels_near_attraction():
    """Test the find_hotels_near_attraction method."""
    logger.info("=== Testing find_hotels_near_attraction method ===")
    print("\n=== Testing find_hotels_near_attraction method ===")

    try:
        # Initialize the database manager and knowledge base
        print("Initializing DatabaseManager and KnowledgeBase...")
        db_manager = DatabaseManager(database_uri=DB_CONNECTION_STRING)
        kb = KnowledgeBase(db_manager=db_manager)
        print(f"Database manager initialized: {db_manager}")
        print(f"Knowledge base initialized: {kb}")

        # Test with attraction_id
        print("\nTest 1: Testing with attraction_id 'pyramids_of_giza'...")
        logger.info("Testing with attraction_id 'pyramids_of_giza'...")
        results = kb.find_hotels_near_attraction(attraction_id="pyramids_of_giza", limit=5)
        print(f"Results: {results}")
        print(f"Found {len(results)} hotels near the Pyramids of Giza")
        logger.info(f"Found {len(results)} hotels near the Pyramids of Giza")

        # Test with attraction_name
        print("\nTest 2: Testing with attraction_name 'Karnak Temple'...")
        logger.info("Testing with attraction_name 'Karnak Temple'...")
        results = kb.find_hotels_near_attraction(attraction_name="Karnak Temple", limit=5)
        print(f"Results: {results}")
        print(f"Found {len(results)} hotels near Karnak Temple")
        logger.info(f"Found {len(results)} hotels near Karnak Temple")

        # Test with city
        print("\nTest 3: Testing with city 'luxor'...")
        logger.info("Testing with city 'luxor'...")
        results = kb.find_hotels_near_attraction(city="luxor", limit=5)
        print(f"Results: {results}")
        print(f"Found {len(results)} hotels in Luxor")
        logger.info(f"Found {len(results)} hotels in Luxor")

        # Print a sample result if available
        if results:
            print("\nSample hotel result:")
            logger.info("Sample hotel result:")
            sample_result = json.dumps(results[0], indent=2, default=str)
            print(sample_result)
            logger.info(sample_result)

        return True
    except Exception as e:
        print(f"ERROR: {e}")
        logger.error(f"Error testing find_hotels_near_attraction: {e}", exc_info=True)
        return False

def main():
    """Main function to run all tests."""
    logger.info("Starting tests for missing KnowledgeBase methods...")
    print("\n=== Starting tests for missing KnowledgeBase methods ===")

    # Test search_transportation
    print("\n\n==== TESTING SEARCH_TRANSPORTATION ====")
    transportation_result = test_search_transportation()
    print(f"search_transportation test result: {'✅ PASS' if transportation_result else '❌ FAIL'}")

    # Test search_tour_packages
    print("\n\n==== TESTING SEARCH_TOUR_PACKAGES ====")
    tour_packages_result = test_search_tour_packages()
    print(f"search_tour_packages test result: {'✅ PASS' if tour_packages_result else '❌ FAIL'}")

    # Test find_hotels_near_attraction
    print("\n\n==== TESTING FIND_HOTELS_NEAR_ATTRACTION ====")
    hotels_result = test_find_hotels_near_attraction()
    print(f"find_hotels_near_attraction test result: {'✅ PASS' if hotels_result else '❌ FAIL'}")

    # Print summary
    print("\n\n=== Test Summary ===")
    logger.info("\n=== Test Summary ===")
    print(f"search_transportation: {'✅ PASS' if transportation_result else '❌ FAIL'}")
    print(f"search_tour_packages: {'✅ PASS' if tour_packages_result else '❌ FAIL'}")
    print(f"find_hotels_near_attraction: {'✅ PASS' if hotels_result else '❌ FAIL'}")
    logger.info(f"search_transportation: {'✅ PASS' if transportation_result else '❌ FAIL'}")
    logger.info(f"search_tour_packages: {'✅ PASS' if tour_packages_result else '❌ FAIL'}")
    logger.info(f"find_hotels_near_attraction: {'✅ PASS' if hotels_result else '❌ FAIL'}")

    # Overall result
    if transportation_result and tour_packages_result and hotels_result:
        print("\n✅ All tests passed!")
        logger.info("✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        logger.error("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
