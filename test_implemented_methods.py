"""
Test script for the implemented methods in the KnowledgeBase class.
This script tests the search_itineraries, search_tour_packages, and _format_tour_package_data methods.
"""
import os
import sys
import json
import logging
from typing import Dict, List, Any

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import the KnowledgeBase class
from src.knowledge.knowledge_base import KnowledgeBase
from src.knowledge.database import DatabaseManager
from src.utils.factory import component_factory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_search_tour_packages():
    """Test the search_tour_packages method."""
    try:
        # Initialize the database manager
        db_manager = component_factory.create_database_manager()

        # Initialize the knowledge base
        kb = KnowledgeBase(db_manager=db_manager)

        logger.info("Testing search_tour_packages with text query...")
        # Test with text query
        results = kb.search_tour_packages(query="Nile", limit=5)
        logger.info(f"Found {len(results)} tour packages with text query 'Nile'")
        for result in results:
            logger.info(f"Tour package: {result.get('name', {}).get('en', 'Unknown')}")

        logger.info("\nTesting search_tour_packages with structured query...")
        # Test with structured query
        query = {"text": "Luxor", "min_duration": 3}
        results = kb.search_tour_packages(query=query, limit=5)
        logger.info(f"Found {len(results)} tour packages with structured query {query}")
        for result in results:
            logger.info(f"Tour package: {result.get('name', {}).get('en', 'Unknown')}, Duration: {result.get('duration_days', 'Unknown')}")

        logger.info("\nTesting search_tour_packages with category filter...")
        # Test with category filter
        results = kb.search_tour_packages(category_id="luxury", limit=5)
        logger.info(f"Found {len(results)} luxury tour packages")
        for result in results:
            logger.info(f"Tour package: {result.get('name', {}).get('en', 'Unknown')}, Category: {result.get('category_id', 'Unknown')}")

        return True
    except Exception as e:
        logger.error(f"Error testing search_tour_packages: {str(e)}", exc_info=True)
        return False

def test_search_itineraries():
    """Test the search_itineraries method."""
    try:
        # Initialize the database manager
        db_manager = component_factory.create_database_manager()

        # Initialize the knowledge base
        kb = KnowledgeBase(db_manager=db_manager)

        logger.info("Testing search_itineraries with text query...")
        # Test with text query
        results = kb.search_itineraries(query="Cairo", limit=5)
        logger.info(f"Found {len(results)} itineraries with text query 'Cairo'")
        for result in results:
            logger.info(f"Itinerary: {result.get('name', {}).get('en', 'Unknown')}")

        logger.info("\nTesting search_itineraries with structured query...")
        # Test with structured query
        query = {"text": "Luxor", "min_duration": 3}
        results = kb.search_itineraries(query=query, limit=5)
        logger.info(f"Found {len(results)} itineraries with structured query {query}")
        for result in results:
            logger.info(f"Itinerary: {result.get('name', {}).get('en', 'Unknown')}, Duration: {result.get('duration_days', 'Unknown')}")

        logger.info("\nTesting search_itineraries with region filter...")
        # Test with region filter
        query = {"region": "Upper Egypt"}
        results = kb.search_itineraries(query=query, limit=5)
        logger.info(f"Found {len(results)} itineraries in Upper Egypt")
        for result in results:
            logger.info(f"Itinerary: {result.get('name', {}).get('en', 'Unknown')}, Regions: {result.get('regions', [])}")

        return True
    except Exception as e:
        logger.error(f"Error testing search_itineraries: {str(e)}", exc_info=True)
        return False

def test_format_tour_package_data():
    """Test the _format_tour_package_data method."""
    try:
        # Initialize the database manager
        db_manager = component_factory.create_database_manager()

        # Initialize the knowledge base
        kb = KnowledgeBase(db_manager=db_manager)

        logger.info("Testing _format_tour_package_data...")

        # Create a test tour package with various data formats
        test_package = {
            "id": "test_package",
            "name": "Test Tour Package",
            "description": "A test tour package for Egypt",
            "duration_days": 7,
            "price": "1000 USD",
            "included_services": "Transportation,Accommodation,Guide",
            "excluded_services": "Flights,Visa",
            "itinerary": json.dumps({
                "day1": "Arrival in Cairo",
                "day2": "Pyramids of Giza"
            }),
            "tags": "luxury,family"
        }

        # Format the test package
        formatted_package = kb._format_tour_package_data(test_package)

        # Verify the formatting
        logger.info("Formatted tour package:")
        logger.info(f"ID: {formatted_package.get('id')}")
        logger.info(f"Name: {formatted_package.get('name')}")
        logger.info(f"Description: {formatted_package.get('description')}")
        logger.info(f"Duration: {formatted_package.get('duration_days')}")
        logger.info(f"Price: {formatted_package.get('price')}")
        logger.info(f"Included services: {formatted_package.get('included_services')}")
        logger.info(f"Excluded services: {formatted_package.get('excluded_services')}")
        logger.info(f"Itinerary: {formatted_package.get('itinerary')}")
        logger.info(f"Tags: {formatted_package.get('tags')}")

        # Verify that the name is properly formatted as a dictionary
        assert isinstance(formatted_package.get('name'), dict)
        assert 'en' in formatted_package.get('name')

        # Verify that included_services and excluded_services are lists
        assert isinstance(formatted_package.get('included_services'), list)
        assert isinstance(formatted_package.get('excluded_services'), list)

        # Verify that itinerary is a dictionary
        assert isinstance(formatted_package.get('itinerary'), dict)

        # Verify that tags is a list
        assert isinstance(formatted_package.get('tags'), list)

        return True
    except Exception as e:
        logger.error(f"Error testing _format_tour_package_data: {str(e)}", exc_info=True)
        return False

def main():
    """Run all tests."""
    logger.info("Starting tests for implemented methods...")

    # Test search_tour_packages
    logger.info("\n=== Testing search_tour_packages ===")
    if test_search_tour_packages():
        logger.info("search_tour_packages test passed!")
    else:
        logger.error("search_tour_packages test failed!")

    # Test search_itineraries
    logger.info("\n=== Testing search_itineraries ===")
    if test_search_itineraries():
        logger.info("search_itineraries test passed!")
    else:
        logger.error("search_itineraries test failed!")

    # Test _format_tour_package_data
    logger.info("\n=== Testing _format_tour_package_data ===")
    if test_format_tour_package_data():
        logger.info("_format_tour_package_data test passed!")
    else:
        logger.error("_format_tour_package_data test failed!")

    logger.info("\nAll tests completed!")

if __name__ == "__main__":
    main()
