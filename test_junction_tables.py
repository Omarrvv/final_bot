#!/usr/bin/env python3
"""
Test script to verify that the junction tables are working correctly.
"""
import os
import sys
import logging
import json
from typing import Dict, List, Any

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import the necessary modules
from src.knowledge.database import DatabaseManager
from src.knowledge.knowledge_base import KnowledgeBase
# Import removed: from src.utils.component_factory import ComponentFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_itinerary_junction_tables():
    """Test the itinerary junction tables."""
    logger.info("Testing itinerary junction tables...")

    # Initialize the database manager
    db_manager = DatabaseManager(database_uri="postgresql://postgres:postgres@localhost:5432/egypt_chatbot")

    # Get an itinerary
    itineraries = db_manager.execute_query("SELECT id FROM itineraries LIMIT 1")
    if not itineraries:
        logger.error("No itineraries found in the database")
        return

    itinerary_id = itineraries[0]["id"]
    logger.info(f"Testing with itinerary ID: {itinerary_id}")

    # Get the itinerary with related entities
    itinerary = db_manager.get_itinerary(itinerary_id)

    # Check if the itinerary has cities
    if "cities" in itinerary and itinerary["cities"]:
        logger.info(f"Itinerary has {len(itinerary['cities'])} cities")
        for city in itinerary["cities"]:
            logger.info(f"  City: {city.get('name', {}).get('en', 'Unknown')}")
    else:
        logger.warning("Itinerary has no cities")

    # Check if the itinerary has attractions
    if "attractions" in itinerary and itinerary["attractions"]:
        logger.info(f"Itinerary has {len(itinerary['attractions'])} attractions")
        for attraction in itinerary["attractions"]:
            logger.info(f"  Attraction: {attraction.get('name', {}).get('en', 'Unknown')}")
    else:
        logger.warning("Itinerary has no attractions")

def test_tour_package_junction_tables():
    """Test the tour package junction tables."""
    logger.info("Testing tour package junction tables...")

    # Initialize the database manager
    db_manager = DatabaseManager(database_uri="postgresql://postgres:postgres@localhost:5432/egypt_chatbot")

    # Get a tour package
    packages = db_manager.execute_query("SELECT id FROM tour_packages LIMIT 1")
    if not packages:
        logger.error("No tour packages found in the database")
        return

    package_id = packages[0]["id"]
    logger.info(f"Testing with tour package ID: {package_id}")

    # Get the tour package with related entities
    package = db_manager.get_tour_package(package_id)

    # Check if the package has destinations
    if "destinations" in package and package["destinations"]:
        logger.info(f"Tour package has {len(package['destinations'])} destinations")
        for destination in package["destinations"]:
            logger.info(f"  Destination: {destination.get('name', {}).get('en', 'Unknown')}")
    else:
        logger.warning("Tour package has no destinations")

    # Check if the package has attractions
    if "attractions" in package and package["attractions"]:
        logger.info(f"Tour package has {len(package['attractions'])} attractions")
        for attraction in package["attractions"]:
            logger.info(f"  Attraction: {attraction.get('name', {}).get('en', 'Unknown')}")
    else:
        logger.warning("Tour package has no attractions")

def test_attraction_relationships():
    """Test the attraction relationships junction table."""
    logger.info("Testing attraction relationships junction table...")

    # Initialize the database manager
    db_manager = DatabaseManager(database_uri="postgresql://postgres:postgres@localhost:5432/egypt_chatbot")

    # Get an attraction
    attractions = db_manager.execute_query("SELECT id FROM attractions LIMIT 1")
    if not attractions:
        logger.error("No attractions found in the database")
        return

    attraction_id = attractions[0]["id"]
    logger.info(f"Testing with attraction ID: {attraction_id}")

    # Get related attractions
    related_attractions = db_manager.find_related_attractions(attraction_id)

    # Check if there are related attractions
    if related_attractions:
        logger.info(f"Attraction has {len(related_attractions)} related attractions")
        for related in related_attractions:
            logger.info(f"  Related attraction: {related.get('name', {}).get('en', 'Unknown')}")
            logger.info(f"  Relationship type: {related.get('relationship_type', 'Unknown')}")
    else:
        logger.warning("Attraction has no related attractions")

    # Test the knowledge base method
    kb = KnowledgeBase(db_manager)
    kb_related = kb.find_related_attractions(attraction_id)

    # Check if there are related attractions from the knowledge base
    if kb_related:
        logger.info(f"Knowledge base found {len(kb_related)} related attractions")
        for related in kb_related:
            logger.info(f"  Related attraction: {related.get('name', {}).get('en', 'Unknown')}")
    else:
        logger.warning("Knowledge base found no related attractions")

def main():
    """Main function to run all tests."""
    logger.info("Starting junction table tests...")

    # Test itinerary junction tables
    test_itinerary_junction_tables()

    # Test tour package junction tables
    test_tour_package_junction_tables()

    # Test attraction relationships
    test_attraction_relationships()

    logger.info("All tests completed.")

if __name__ == "__main__":
    main()
