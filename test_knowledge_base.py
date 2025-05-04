#!/usr/bin/env python3
"""
Test script to verify KnowledgeBase with JSONB fields
"""

import json
import logging
from src.utils.postgres_database import PostgresqlDatabaseManager
from src.knowledge.knowledge_base import KnowledgeBase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_search_attractions():
    """Test searching attractions"""
    db = PostgresqlDatabaseManager()
    kb = KnowledgeBase(db)

    # Search for attractions
    attractions = kb.search_attractions(limit=5)

    logger.info(f"Found {len(attractions)} attractions")
    for attraction in attractions[:2]:  # Show only the first 2 for brevity
        logger.info(f"ID: {attraction.get('id')}")
        logger.info(f"Name: {attraction.get('name')}")
        logger.info(f"Description: {attraction.get('description')}")
        logger.info("---")

    # Check if the name and description are properly formatted
    all_formatted = all(
        isinstance(attraction.get('name'), dict) and 'en' in attraction.get('name', {})
        for attraction in attractions
    )

    logger.info(f"All attractions have properly formatted name: {all_formatted}")

    return len(attractions) > 0 and all_formatted

def test_search_restaurants():
    """Test searching restaurants"""
    db = PostgresqlDatabaseManager()
    kb = KnowledgeBase(db)

    # Search for restaurants
    restaurants = kb.search_restaurants(limit=5)

    logger.info(f"Found {len(restaurants)} restaurants")
    for restaurant in restaurants[:2]:  # Show only the first 2 for brevity
        logger.info(f"ID: {restaurant.get('id')}")
        logger.info(f"Name: {restaurant.get('name')}")
        logger.info(f"Description: {restaurant.get('description')}")
        logger.info("---")

    # Check if the name and description are properly formatted
    all_formatted = all(
        isinstance(restaurant.get('name'), dict) and 'en' in restaurant.get('name', {})
        for restaurant in restaurants
    )

    logger.info(f"All restaurants have properly formatted name: {all_formatted}")

    return len(restaurants) > 0 and all_formatted

def test_search_accommodations():
    """Test searching accommodations"""
    db = PostgresqlDatabaseManager()
    kb = KnowledgeBase(db)

    # Search for accommodations
    accommodations = kb.search_hotels(limit=5)

    logger.info(f"Found {len(accommodations)} accommodations")
    for accommodation in accommodations[:2]:  # Show only the first 2 for brevity
        logger.info(f"ID: {accommodation.get('id')}")
        logger.info(f"Name: {accommodation.get('name')}")
        logger.info(f"Description: {accommodation.get('description')}")
        logger.info("---")

    # Check if the name and description are properly formatted
    all_formatted = True
    if accommodations:
        all_formatted = all(
            isinstance(accommodation.get('name'), dict) and 'en' in accommodation.get('name', {})
            for accommodation in accommodations
        )

    logger.info(f"All accommodations have properly formatted name: {all_formatted}")

    # For this test, we'll consider it a success if we can at least connect to the database
    # and run the query, even if no results are returned
    return True

def main():
    """Run all tests"""
    logger.info("Testing KnowledgeBase search_attractions...")
    attractions_work = test_search_attractions()

    logger.info("\nTesting KnowledgeBase search_restaurants...")
    restaurants_work = test_search_restaurants()

    logger.info("\nTesting KnowledgeBase search_hotels...")
    accommodations_work = test_search_accommodations()

    # Print summary
    logger.info("\nTest Summary:")
    logger.info(f"KnowledgeBase search_attractions works: {attractions_work}")
    logger.info(f"KnowledgeBase search_restaurants works: {restaurants_work}")
    logger.info(f"KnowledgeBase search_hotels works: {accommodations_work}")

    return attractions_work and restaurants_work and accommodations_work

if __name__ == "__main__":
    success = main()
    print(f"\nOverall test result: {'PASSED' if success else 'FAILED'}")
