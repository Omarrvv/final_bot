#!/usr/bin/env python3
"""
Script to test the new database methods for tourism_faqs, practical_info, events_festivals, and tour_packages.
"""

import os
import sys
import logging
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.knowledge.database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection string
DB_CONNECTION_STRING = "postgresql://postgres:postgres@localhost:5432/egypt_chatbot"

def test_tourism_faqs():
    """Test the tourism_faqs methods."""
    logger.info("Testing tourism_faqs methods...")

    # Initialize database manager
    db = DatabaseManager(database_uri=DB_CONNECTION_STRING)

    # Test search_tourism_faqs
    faqs = db.search_tourism_faqs(limit=5)
    logger.info(f"Found {len(faqs)} tourism FAQs")

    # Test get_tourism_faq if we have any FAQs
    if faqs:
        faq_id = faqs[0]['id']
        faq = db.get_tourism_faq(faq_id)
        logger.info(f"Retrieved FAQ {faq_id}: {json.dumps(faq, indent=2, default=str)}")

    return len(faqs)

def test_practical_info():
    """Test the practical_info methods."""
    logger.info("Testing practical_info methods...")

    # Initialize database manager
    db = DatabaseManager(database_uri=DB_CONNECTION_STRING)

    # Test search_practical_info
    info_items = db.search_practical_info(limit=5)
    logger.info(f"Found {len(info_items)} practical info items")

    # Test get_practical_info if we have any items
    if info_items:
        info_id = info_items[0]['id']
        info = db.get_practical_info(info_id)
        logger.info(f"Retrieved practical info {info_id}: {json.dumps(info, indent=2, default=str)}")

    return len(info_items)

def test_events_festivals():
    """Test the events_festivals methods."""
    logger.info("Testing events_festivals methods...")

    # Initialize database manager
    db = DatabaseManager(database_uri=DB_CONNECTION_STRING)

    # Test search_events_festivals
    events = db.search_events_festivals(limit=5)
    logger.info(f"Found {len(events)} events/festivals")

    # Test get_event_festival if we have any events
    if events:
        event_id = events[0]['id']
        event = db.get_event_festival(event_id)
        logger.info(f"Retrieved event/festival {event_id}: {json.dumps(event, indent=2, default=str)}")

    return len(events)

def test_tour_packages():
    """Test the tour_packages methods."""
    logger.info("Testing tour_packages methods...")

    # Initialize database manager
    db = DatabaseManager(database_uri=DB_CONNECTION_STRING)

    # Test search_tour_packages
    packages = db.search_tour_packages(limit=5)
    logger.info(f"Found {len(packages)} tour packages")

    # Test get_tour_package if we have any packages
    if packages:
        package_id = packages[0]['id']
        package = db.get_tour_package(package_id)
        logger.info(f"Retrieved tour package {package_id}: {json.dumps(package, indent=2, default=str)}")

    return len(packages)

def main():
    """Main function to test the database methods."""
    try:
        # Test all methods
        faq_count = test_tourism_faqs()
        info_count = test_practical_info()
        event_count = test_events_festivals()
        package_count = test_tour_packages()

        # Print summary
        logger.info("Test Summary:")
        logger.info(f"Tourism FAQs: {faq_count}")
        logger.info(f"Practical Info: {info_count}")
        logger.info(f"Events/Festivals: {event_count}")
        logger.info(f"Tour Packages: {package_count}")

        # Check if we have data in all tables
        if faq_count == 0:
            logger.warning("No tourism FAQs found. Consider adding some data.")
        if info_count == 0:
            logger.warning("No practical info found. Consider adding some data.")
        if event_count == 0:
            logger.warning("No events/festivals found. Consider adding some data.")
        if package_count == 0:
            logger.warning("No tour packages found. Consider adding some data.")

    except Exception as e:
        logger.error(f"Error testing database methods: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
