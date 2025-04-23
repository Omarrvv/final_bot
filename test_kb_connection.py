#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_kb_connection():
    """Test Knowledge Base connection to database."""
    try:
        logger.info("Testing Knowledge Base connection to database")
        
        # First test DatabaseManager directly
        from src.knowledge.database import DatabaseManager
        
        database_uri = os.environ.get('DATABASE_URI', 'sqlite:///./data/egypt_chatbot.db')
        db_manager = DatabaseManager(database_uri)
        
        # Test connection
        connected = db_manager.connect()
        if not connected:
            logger.error("Failed to connect to database")
            return False
        
        logger.info(f"Successfully connected to database: {database_uri}")
        
        # Test simple query
        try:
            # Try to get attractions
            attractions = db_manager.get_all_attractions(limit=3)
            logger.info(f"Successfully retrieved {len(attractions)} attractions")
            
            # Try to get restaurants
            restaurants = db_manager.get_all_restaurants(limit=3)
            logger.info(f"Successfully retrieved {len(restaurants)} restaurants")
            
            # Try to get accommodations
            accommodations = db_manager.get_all_accommodations(limit=3)
            logger.info(f"Successfully retrieved {len(accommodations)} accommodations")
            
        except Exception as e:
            logger.error(f"Error querying database: {str(e)}")
            return False
        
        # Now test KnowledgeBase with DatabaseManager
        from src.knowledge.knowledge_base import KnowledgeBase
        
        kb = KnowledgeBase(db_manager)
        
        # Test KnowledgeBase methods
        try:
            # Search attractions
            attractions = kb.search_attractions(query="pyramid", limit=3)
            logger.info(f"KB search found {len(attractions)} attractions matching 'pyramid'")
            
            # Search restaurants
            restaurants = kb.search_restaurants(limit=3)
            logger.info(f"KB retrieved {len(restaurants)} restaurants")
            
            # Search hotels
            hotels = kb.search_hotels(limit=3)
            logger.info(f"KB retrieved {len(hotels)} hotels")
            
            return True
            
        except Exception as e:
            logger.error(f"Error using KnowledgeBase: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing KB connection: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_kb_connection()
    sys.exit(0 if success else 1) 