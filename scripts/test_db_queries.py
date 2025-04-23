#!/usr/bin/env python3
"""
Script to test database queries directly against PostgreSQL.
"""

import os
import sys
import logging
import json

# Setup simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set environment variables
os.environ['POSTGRES_URI'] = 'postgresql://omarmohamed@localhost:5432/postgres'
os.environ['USE_POSTGRES'] = 'true'

try:
    from src.knowledge.database import DatabaseManager
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

def main():
    """Test database queries directly."""
    try:
        # Create db manager
        db_manager = DatabaseManager()
        logger.info('Connected to PostgreSQL successfully')

        # Test restaurants query
        restaurant_query = {"cuisine": "egyptian"}
        restaurants = db_manager.search_restaurants(query=restaurant_query)
        logger.info(f'Found {len(restaurants)} Egyptian restaurants')
        for r in restaurants:
            logger.info(f'- {r.get("name", {}).get("en", "Unknown")}')

        # Test hotels query
        hotel_query = {"city": "cairo"}
        hotels = db_manager.search_hotels(query=hotel_query)
        logger.info(f'Found {len(hotels)} hotels in Cairo')
        for h in hotels:
            logger.info(f'- {h.get("name", {}).get("en", "Unknown")}')

        # Test attractions query
        attraction_query = {"type": "historic"}
        attractions = db_manager.search_attractions(query=attraction_query)
        logger.info(f'Found {len(attractions)} historic attractions')
        for a in attractions:
            logger.info(f'- {a.get("name", {}).get("en", "Unknown")}')
    
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 