"""
Test file for database access methods.
This file tests the search_restaurants, search_accommodations, and other database access methods.
"""
import os
import sys
import logging
import pytest
from typing import Dict, List, Any, Optional

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.knowledge.database import DatabaseManager
from src.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

# Test database URI
TEST_DB_URI = os.environ.get("TEST_POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot_test")

@pytest.fixture
def db_manager():
    """Fixture for DatabaseManager instance."""
    # Use the test database URI
    db_manager = DatabaseManager(database_uri=TEST_DB_URI)
    yield db_manager
    db_manager.close()

def test_search_restaurants(db_manager):
    """Test the search_restaurants method."""
    logger.info("Testing search_restaurants method")
    
    # Test with empty query (should return all restaurants up to limit)
    restaurants = db_manager.search_restaurants(limit=5)
    assert isinstance(restaurants, list)
    logger.info(f"Found {len(restaurants)} restaurants with empty query")
    
    # Test with string query (text search)
    text_query = "restaurant"
    text_results = db_manager.search_restaurants(query=text_query, limit=5)
    assert isinstance(text_results, list)
    logger.info(f"Found {len(text_results)} restaurants with text query '{text_query}'")
    
    # Test with dictionary query
    dict_query = {"city": "cairo"}
    dict_results = db_manager.search_restaurants(query=dict_query, limit=5)
    assert isinstance(dict_results, list)
    logger.info(f"Found {len(dict_results)} restaurants with dictionary query {dict_query}")
    
    # Test with filters
    filters = {"cuisine": "egyptian"}
    filter_results = db_manager.search_restaurants(filters=filters, limit=5)
    assert isinstance(filter_results, list)
    logger.info(f"Found {len(filter_results)} restaurants with filters {filters}")
    
    # Test with both query and filters
    combined_results = db_manager.search_restaurants(query=dict_query, filters=filters, limit=5)
    assert isinstance(combined_results, list)
    logger.info(f"Found {len(combined_results)} restaurants with query {dict_query} and filters {filters}")

def test_search_accommodations(db_manager):
    """Test the search_accommodations method."""
    logger.info("Testing search_accommodations method")
    
    # Test with empty query (should return all accommodations up to limit)
    accommodations = db_manager.search_accommodations(limit=5)
    assert isinstance(accommodations, list)
    logger.info(f"Found {len(accommodations)} accommodations with empty query")
    
    # Test with string query (text search)
    text_query = "hotel"
    text_results = db_manager.search_accommodations(query=text_query, limit=5)
    assert isinstance(text_results, list)
    logger.info(f"Found {len(text_results)} accommodations with text query '{text_query}'")
    
    # Test with dictionary query
    dict_query = {"city": "cairo"}
    dict_results = db_manager.search_accommodations(query=dict_query, limit=5)
    assert isinstance(dict_results, list)
    logger.info(f"Found {len(dict_results)} accommodations with dictionary query {dict_query}")
    
    # Test with filters
    filters = {"type": "hotel"}
    filter_results = db_manager.search_accommodations(filters=filters, limit=5)
    assert isinstance(filter_results, list)
    logger.info(f"Found {len(filter_results)} accommodations with filters {filters}")
    
    # Test with both query and filters
    combined_results = db_manager.search_accommodations(query=dict_query, filters=filters, limit=5)
    assert isinstance(combined_results, list)
    logger.info(f"Found {len(combined_results)} accommodations with query {dict_query} and filters {filters}")

def test_search_attractions(db_manager):
    """Test the search_attractions method."""
    logger.info("Testing search_attractions method")
    
    # Test with empty query (should return all attractions up to limit)
    attractions = db_manager.search_attractions(limit=5)
    assert isinstance(attractions, list)
    logger.info(f"Found {len(attractions)} attractions with empty query")
    
    # Test with string query (text search)
    text_query = "pyramid"
    text_results = db_manager.search_attractions(query=text_query, limit=5)
    assert isinstance(text_results, list)
    logger.info(f"Found {len(text_results)} attractions with text query '{text_query}'")
    
    # Test with dictionary query
    dict_query = {"city": "giza"}
    dict_results = db_manager.search_attractions(query=dict_query, limit=5)
    assert isinstance(dict_results, list)
    logger.info(f"Found {len(dict_results)} attractions with dictionary query {dict_query}")
    
    # Test with filters
    filters = {"type": "monument"}
    filter_results = db_manager.search_attractions(filters=filters, limit=5)
    assert isinstance(filter_results, list)
    logger.info(f"Found {len(filter_results)} attractions with filters {filters}")
    
    # Test with both query and filters
    combined_results = db_manager.search_attractions(query=dict_query, filters=filters, limit=5)
    assert isinstance(combined_results, list)
    logger.info(f"Found {len(combined_results)} attractions with query {dict_query} and filters {filters}")

def test_crud_operations(db_manager):
    """Test CRUD operations for different entity types."""
    logger.info("Testing CRUD operations")
    
    # Test restaurant CRUD
    test_restaurant = {
        "id": "test_restaurant_1",
        "name_en": "Test Restaurant",
        "name_ar": "مطعم اختبار",
        "description_en": "A test restaurant",
        "description_ar": "مطعم اختبار",
        "cuisine": "Test Cuisine",
        "city": "test_city",
        "region": "test_region",
        "latitude": 30.0,
        "longitude": 31.0,
        "data": {"rating": 4.5, "price_range": "moderate"}
    }
    
    # Insert
    insert_result = db_manager.insert_restaurant(test_restaurant)
    assert insert_result is True
    logger.info(f"Inserted test restaurant: {test_restaurant['id']}")
    
    # Get
    restaurant = db_manager.get_restaurant(test_restaurant["id"])
    assert restaurant is not None
    assert restaurant["name_en"] == test_restaurant["name_en"]
    logger.info(f"Retrieved test restaurant: {restaurant['id']}")
    
    # Update
    update_data = {"description_en": "Updated test restaurant"}
    update_result = db_manager.update_restaurant(test_restaurant["id"], update_data)
    assert update_result is True
    logger.info(f"Updated test restaurant: {test_restaurant['id']}")
    
    # Get updated
    updated_restaurant = db_manager.get_restaurant(test_restaurant["id"])
    assert updated_restaurant is not None
    assert updated_restaurant["description_en"] == update_data["description_en"]
    logger.info(f"Retrieved updated test restaurant: {updated_restaurant['id']}")
    
    # Delete
    delete_result = db_manager.delete_restaurant(test_restaurant["id"])
    assert delete_result is True
    logger.info(f"Deleted test restaurant: {test_restaurant['id']}")
    
    # Verify deletion
    deleted_restaurant = db_manager.get_restaurant(test_restaurant["id"])
    assert deleted_restaurant is None
    logger.info(f"Verified deletion of test restaurant: {test_restaurant['id']}")

if __name__ == "__main__":
    # Run the tests directly if this file is executed
    db_manager = DatabaseManager(database_uri=TEST_DB_URI)
    
    try:
        print("Testing search_restaurants...")
        test_search_restaurants(db_manager)
        
        print("Testing search_accommodations...")
        test_search_accommodations(db_manager)
        
        print("Testing search_attractions...")
        test_search_attractions(db_manager)
        
        print("Testing CRUD operations...")
        test_crud_operations(db_manager)
        
        print("All tests passed!")
    finally:
        db_manager.close()
