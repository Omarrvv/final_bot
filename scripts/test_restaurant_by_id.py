#!/usr/bin/env python3
"""
Script to test retrieving a specific restaurant by ID.
"""

import os
import sys
import logging
import json
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test_restaurant_by_id")

# Load environment variables
load_dotenv()

# Set PostgreSQL flag
os.environ["USE_POSTGRES"] = "true"

from src.knowledge.database import DatabaseManager

def main():
    """Test retrieving a specific restaurant by ID."""
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Test connection
    if not db_manager.connect():
        logger.error("Failed to connect to database")
        return
    
    logger.info(f"Connected to database (type: {db_manager.db_type.name})")
    
    # Specific restaurant ID to test
    restaurant_id = "koshary_el_tahrir"
    
    # Get restaurant by ID
    logger.info(f"Getting restaurant with ID: {restaurant_id}")
    restaurant = db_manager.get_restaurant(restaurant_id)
    
    if restaurant:
        logger.info(f"Successfully retrieved restaurant: {restaurant.get('name_en')}")
        logger.info(f"Description: {restaurant.get('description_en')}")
        logger.info(f"Location: {restaurant.get('city')} ({restaurant.get('latitude')}, {restaurant.get('longitude')})")
        logger.info(f"Cuisine: {restaurant.get('cuisine')}")
        logger.info(f"Full restaurant data: {json.dumps(restaurant, indent=2, default=str)}")
    else:
        logger.error(f"Restaurant with ID {restaurant_id} not found")
    
    # Close connection
    db_manager.close()
    logger.info("Database connection closed")

if __name__ == "__main__":
    main() 