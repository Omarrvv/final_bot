#!/usr/bin/env python3
"""
Test script to verify that the application works with the updated JSONB schema.
This script tests database operations after removing legacy columns.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.knowledge.database import DatabaseManager
from src.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

def test_get_attraction(db: DatabaseManager) -> bool:
    """Test getting an attraction by ID."""
    logger.info("Testing get_attraction...")

    # Get a sample attraction ID
    attractions = db.execute_query("SELECT id FROM attractions LIMIT 1")
    if not attractions:
        logger.error("No attractions found in the database")
        return False

    attraction_id = attractions[0]['id']
    logger.info(f"Testing with attraction ID: {attraction_id}")

    # Get the attraction
    attraction = db.get_attraction(attraction_id)
    if not attraction:
        logger.error(f"Failed to get attraction with ID {attraction_id}")
        return False

    # Verify JSONB fields
    if 'name' not in attraction or not isinstance(attraction['name'], dict):
        logger.error(f"Attraction {attraction_id} has invalid or missing name field: {attraction.get('name')}")
        return False

    if 'description' not in attraction or not isinstance(attraction['description'], dict):
        logger.error(f"Attraction {attraction_id} has invalid or missing description field: {attraction.get('description')}")
        return False

    logger.info(f"Successfully retrieved attraction {attraction_id} with JSONB fields")
    return True

def test_get_restaurant(db: DatabaseManager) -> bool:
    """Test getting a restaurant by ID."""
    logger.info("Testing get_restaurant...")

    # Get a sample restaurant ID
    restaurants = db.execute_query("SELECT id FROM restaurants LIMIT 1")
    if not restaurants:
        logger.error("No restaurants found in the database")
        return False

    restaurant_id = restaurants[0]['id']
    logger.info(f"Testing with restaurant ID: {restaurant_id}")

    # Get the restaurant
    restaurant = db.get_restaurant(restaurant_id)
    if not restaurant:
        logger.error(f"Failed to get restaurant with ID {restaurant_id}")
        return False

    # Verify JSONB fields
    if 'name' not in restaurant or not isinstance(restaurant['name'], dict):
        logger.error(f"Restaurant {restaurant_id} has invalid or missing name field: {restaurant.get('name')}")
        return False

    if 'description' not in restaurant or not isinstance(restaurant['description'], dict):
        logger.error(f"Restaurant {restaurant_id} has invalid or missing description field: {restaurant.get('description')}")
        return False

    logger.info(f"Successfully retrieved restaurant {restaurant_id} with JSONB fields")
    return True

def test_search_restaurants(db: DatabaseManager) -> bool:
    """Test searching restaurants."""
    logger.info("Testing search_restaurants...")

    # Search for restaurants
    restaurants = db.search_restaurants(query="restaurant", limit=5)
    if not restaurants:
        logger.error("No restaurants found in search")
        return False

    # Verify JSONB fields in search results
    for restaurant in restaurants:
        if 'name' not in restaurant or not isinstance(restaurant['name'], dict):
            logger.error(f"Restaurant {restaurant.get('id')} has invalid or missing name field: {restaurant.get('name')}")
            return False

        if 'description' not in restaurant or not isinstance(restaurant['description'], dict):
            logger.error(f"Restaurant {restaurant.get('id')} has invalid or missing description field: {restaurant.get('description')}")
            return False

    logger.info(f"Successfully searched restaurants with JSONB fields")
    return True

def test_vector_search(db: DatabaseManager) -> bool:
    """Test vector search with JSONB fields."""
    logger.info("Testing vector_search...")

    # Get a sample embedding
    embedding_query = """
        SELECT embedding
        FROM attractions
        WHERE embedding IS NOT NULL
        LIMIT 1
    """
    embedding_result = db.execute_query(embedding_query)
    if not embedding_result:
        logger.error("No embeddings found in the database")
        return False

    # Parse the embedding from string to list of floats
    embedding_str = embedding_result[0]['embedding']
    logger.info(f"Embedding type: {type(embedding_str)}")
    logger.info(f"Embedding value: {embedding_str[:100]}...")  # Show first 100 chars

    if isinstance(embedding_str, str):
        try:
            # Try to parse as JSON first
            import json
            embedding = json.loads(embedding_str)
            logger.info(f"Parsed embedding using JSON: {len(embedding)} elements")
        except json.JSONDecodeError:
            # If that fails, try manual parsing
            logger.info("JSON parsing failed, trying manual parsing")
            # Remove brackets and split by comma
            embedding_values = embedding_str.strip('[]').split(',')
            embedding = [float(val) for val in embedding_values]
            logger.info(f"Parsed embedding manually: {len(embedding)} elements")
    else:
        embedding = embedding_str
        logger.info(f"Using embedding as is: {type(embedding)}")

    # Perform vector search using the vector_search_attractions method
    try:
        # The DatabaseManager has specific methods for each table
        results = db.vector_search_attractions(embedding, limit=5)
        if not results:
            logger.error("No results found in vector search")
            return False

        # Verify JSONB fields in vector search results
        for result in results:
            if 'name' not in result or not isinstance(result['name'], dict):
                logger.error(f"Vector search result {result.get('id')} has invalid or missing name field: {result.get('name')}")
                return False

            if 'description' not in result or not isinstance(result['description'], dict):
                logger.error(f"Vector search result {result.get('id')} has invalid or missing description field: {result.get('description')}")
                return False

        logger.info(f"Successfully performed vector search with JSONB fields")
        return True
    except Exception as e:
        logger.error(f"Error in vector search: {e}")
        return False

def main():
    """Main function to run the tests."""
    logger.info("Starting JSONB schema tests...")

    # Get database URI from environment variable
    database_uri = os.environ.get("POSTGRES_URI")
    if not database_uri:
        logger.error("POSTGRES_URI environment variable not set")
        sys.exit(1)

    # Initialize database manager
    db = DatabaseManager(database_uri=database_uri)

    # Run tests
    tests = [
        test_get_attraction,
        test_get_restaurant,
        test_search_restaurants,
        test_vector_search
    ]

    success = True
    for test in tests:
        try:
            if not test(db):
                success = False
        except Exception as e:
            logger.error(f"Error in test {test.__name__}: {e}")
            success = False

    # Close database connection
    db.close()

    if success:
        logger.info("All tests passed! The application works with the JSONB schema.")
        sys.exit(0)
    else:
        logger.error("Some tests failed. The application may not work correctly with the JSONB schema.")
        sys.exit(1)

if __name__ == "__main__":
    main()
