"""
Test script to verify the fixes for the Egypt Tourism Chatbot.
This script tests:
1. The enhanced_search method with JSONB columns
2. The _format_restaurant_data method to fix "'str' object has no attribute 'get'" error
3. The cross-table queries to improve the success rate
"""
import os
import sys
import json
import logging
from typing import Dict, List, Any

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import the necessary classes
from src.knowledge.knowledge_base import KnowledgeBase
from src.knowledge.database import DatabaseManager
from src.knowledge.cross_table_queries import CrossTableQueryManager
from src.utils.factory import component_factory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_search():
    """Test the enhanced_search method with JSONB columns."""
    try:
        # Initialize the database manager
        db_manager = component_factory.create_database_manager()
        
        # Test enhanced_search with transportation_routes table
        logger.info("Testing enhanced_search with transportation_routes table...")
        results = db_manager.enhanced_search(
            table="transportation_routes",
            search_text="Cairo",
            limit=5
        )
        logger.info(f"Found {len(results)} transportation routes with text 'Cairo'")
        for result in results:
            logger.info(f"Transportation route: {result.get('id')}, Origin: {result.get('origin_id')}, Destination: {result.get('destination_id')}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing enhanced_search: {str(e)}", exc_info=True)
        return False

def test_format_restaurant_data():
    """Test the _format_restaurant_data method to fix "'str' object has no attribute 'get'" error."""
    try:
        # Initialize the database manager
        db_manager = component_factory.create_database_manager()
        
        # Initialize the knowledge base
        kb = KnowledgeBase(db_manager=db_manager)
        
        # Create test restaurant data with various formats
        test_restaurants = [
            {
                "id": "test_restaurant_1",
                "name": "Test Restaurant 1"  # String name
            },
            {
                "id": "test_restaurant_2",
                "name": json.dumps({"en": "Test Restaurant 2", "ar": "مطعم اختبار 2"})  # JSON string name
            },
            {
                "id": "test_restaurant_3",
                "name": {"en": "Test Restaurant 3", "ar": "مطعم اختبار 3"}  # Dict name
            },
            {
                "id": "test_restaurant_4",
                "name_en": "Test Restaurant 4",  # Separate name fields
                "name_ar": "مطعم اختبار 4"
            },
            {
                "id": "test_restaurant_5"  # No name field
            }
        ]
        
        logger.info("Testing _format_restaurant_data with various name formats...")
        for restaurant in test_restaurants:
            formatted = kb._format_restaurant_data(restaurant)
            logger.info(f"Restaurant ID: {formatted.get('id')}")
            logger.info(f"Formatted name: {formatted.get('name')}")
            # Verify that name is a dictionary with 'en' and 'ar' keys
            assert isinstance(formatted.get('name'), dict)
            assert 'en' in formatted.get('name')
            assert 'ar' in formatted.get('name')
        
        return True
    except Exception as e:
        logger.error(f"Error testing _format_restaurant_data: {str(e)}", exc_info=True)
        return False

def test_cross_table_queries():
    """Test the cross-table queries to improve the success rate."""
    try:
        # Initialize the database manager
        db_manager = component_factory.create_database_manager()
        
        # Initialize the cross-table query manager
        ctq_manager = CrossTableQueryManager(db_manager)
        
        # Test find_restaurants_near_attraction
        logger.info("Testing find_restaurants_near_attraction...")
        restaurants = ctq_manager.find_restaurants_near_attraction(
            attraction_name="Pyramids of Giza",
            city="Cairo",
            limit=5
        )
        logger.info(f"Found {len(restaurants)} restaurants near Pyramids of Giza")
        for restaurant in restaurants:
            logger.info(f"Restaurant: {restaurant.get('name', {}).get('en', 'Unknown')}")
        
        # Test find_hotels_near_attraction
        logger.info("\nTesting find_hotels_near_attraction...")
        hotels = ctq_manager.find_hotels_near_attraction(
            attraction_name="Luxor Temple",
            city="Luxor",
            limit=5
        )
        logger.info(f"Found {len(hotels)} hotels near Luxor Temple")
        for hotel in hotels:
            logger.info(f"Hotel: {hotel.get('name', {}).get('en', 'Unknown')}")
        
        # Test find_attractions_in_itinerary_cities
        logger.info("\nTesting find_attractions_in_itinerary_cities...")
        attractions_by_city = ctq_manager.find_attractions_in_itinerary_cities(
            itinerary_name="Classic Egypt Tour",
            limit=5
        )
        logger.info(f"Found attractions in {len(attractions_by_city)} cities")
        for city, attractions in attractions_by_city.items():
            logger.info(f"City: {city}, Attractions: {len(attractions)}")
            for attraction in attractions:
                logger.info(f"  - {attraction.get('name', {}).get('en', 'Unknown')}")
        
        # Test find_events_near_attraction
        logger.info("\nTesting find_events_near_attraction...")
        events = ctq_manager.find_events_near_attraction(
            attraction_name="Egyptian Museum",
            city="Cairo",
            limit=5
        )
        logger.info(f"Found {len(events)} events near Egyptian Museum")
        for event in events:
            logger.info(f"Event: {event.get('name', {}).get('en', 'Unknown')}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing cross_table_queries: {str(e)}", exc_info=True)
        return False

def main():
    """Run all tests."""
    logger.info("Starting tests for fixes...")
    
    # Test enhanced_search
    logger.info("\n=== Testing enhanced_search ===")
    if test_enhanced_search():
        logger.info("enhanced_search test passed!")
    else:
        logger.error("enhanced_search test failed!")
    
    # Test _format_restaurant_data
    logger.info("\n=== Testing _format_restaurant_data ===")
    if test_format_restaurant_data():
        logger.info("_format_restaurant_data test passed!")
    else:
        logger.error("_format_restaurant_data test failed!")
    
    # Test cross-table queries
    logger.info("\n=== Testing cross-table queries ===")
    if test_cross_table_queries():
        logger.info("cross-table queries test passed!")
    else:
        logger.error("cross-table queries test failed!")
    
    logger.info("\nAll tests completed!")

if __name__ == "__main__":
    main()
