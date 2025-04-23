#!/usr/bin/env python3
"""
Simple script to test the Knowledge Base directly without API authentication.
This bypasses the authentication middleware and allows us to verify the Knowledge Base is working.
"""
import os
import logging
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set feature flags directly
os.environ["USE_NEW_KB"] = "true"
os.environ["USE_POSTGRES"] = "false"

def test_knowledge_base():
    """Test the Knowledge Base directly."""
    logger.info("Testing Knowledge Base directly...")
    
    try:
        # Import here to ensure environment variables are loaded first
        from src.knowledge.database import DatabaseManager
        from src.knowledge.knowledge_base import KnowledgeBase
        
        # Create database manager
        logger.info("Creating DatabaseManager...")
        db_uri = os.getenv("DATABASE_URI", "sqlite:///./data/egypt_chatbot.db")
        db_manager = DatabaseManager(db_uri)
        
        # Test database connection
        logger.info("Testing database connection...")
        if db_manager.connect():
            logger.info("Successfully connected to database")
        else:
            logger.error("Failed to connect to database")
            return
        
        # Create Knowledge Base
        logger.info("Creating KnowledgeBase...")
        kb = KnowledgeBase(db_manager)
        logger.info("Knowledge Base created successfully")
        
        # Test attraction search
        logger.info("\nTesting attraction search...")
        attractions = kb.search_attractions("pyramid", language="en")
        logger.info(f"Found {len(attractions)} attractions matching 'pyramid'")
        for i, attraction in enumerate(attractions[:3]):  # Show up to 3 attractions
            logger.info(f"Attraction {i+1}: {attraction.get('name_en', attraction.get('id', 'Unknown'))}")
        
        # Test specific attraction lookup
        logger.info("\nTesting specific attraction lookup...")
        attraction = kb.get_attraction_by_id("pyramids_of_giza")
        if attraction:
            logger.info(f"Successfully retrieved attraction: {attraction.get('name_en', attraction.get('id', 'Unknown'))}")
            try:
                desc = attraction.get('description_en', 'No description')
                if isinstance(desc, str) and len(desc) > 100:
                    logger.info(f"Description: {desc[:100]}...")
                else:
                    logger.info(f"Description: {desc}")
            except Exception as e:
                logger.error(f"Error displaying description: {str(e)}")
        else:
            logger.info("Failed to retrieve 'pyramids_of_giza' attraction")
        
        # Test restaurant search
        logger.info("\nTesting restaurant search...")
        restaurants = kb.search_restaurants(limit=5)
        logger.info(f"Found {len(restaurants)} restaurants")
        for i, restaurant in enumerate(restaurants[:3]):  # Show up to 3 restaurants
            logger.info(f"Restaurant {i+1}: {restaurant.get('name_en', restaurant.get('id', 'Unknown'))}")
        
        # Test hotel search
        logger.info("\nTesting hotel search...")
        hotels = kb.search_hotels(limit=5)
        logger.info(f"Found {len(hotels)} hotels")
        for i, hotel in enumerate(hotels[:3]):  # Show up to 3 hotels
            logger.info(f"Hotel {i+1}: {hotel.get('name_en', hotel.get('id', 'Unknown'))}")
        
        logger.info("\nKnowledge Base testing completed successfully")
        
    except Exception as e:
        logger.error(f"Error testing Knowledge Base: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_knowledge_base() 