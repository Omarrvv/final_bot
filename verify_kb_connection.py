#!/usr/bin/env python
"""
Verify Knowledge Base connection to SQLite database.
This script tests the connection between the KnowledgeBase and SQLite.
"""
import os
import sys
import logging
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
logger.info("Loading environment variables from .env file")
load_dotenv()

# Ensure USE_NEW_KB is True and USE_POSTGRES is False
os.environ['USE_NEW_KB'] = 'true'
os.environ['USE_POSTGRES'] = 'false'
os.environ['DATABASE_URI'] = 'sqlite:///./data/egypt_chatbot.db'

logger.info(f"USE_NEW_KB = {os.getenv('USE_NEW_KB')}")
logger.info(f"USE_POSTGRES = {os.getenv('USE_POSTGRES')}")
logger.info(f"DATABASE_URI = {os.getenv('DATABASE_URI')}")

# Add project root to Python path if needed
sys.path.append('.')

# Import required modules after setting environment variables
try:
    from src.knowledge.database import DatabaseManager
    from src.knowledge.knowledge_base import KnowledgeBase
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    sys.exit(1)

def verify_database_connection():
    """Verify database connection and structure."""
    try:
        logger.info("Creating DatabaseManager instance")
        db_manager = DatabaseManager(database_uri=os.getenv('DATABASE_URI'))
        
        logger.info("Testing database connection")
        if not db_manager.connect():
            logger.error("Failed to connect to database")
            return False
            
        logger.info("Database connection successful")
        
        # Check if tables exist
        tables_to_check = ['attractions', 'restaurants', 'accommodations', 'cities']
        for table in tables_to_check:
            exists = db_manager._table_exists(table)
            logger.info(f"Table '{table}' exists: {exists}")
            if not exists:
                logger.warning(f"Table '{table}' does not exist")
        
        # Count records in tables
        for table in tables_to_check:
            if db_manager._table_exists(table):
                if table == 'attractions':
                    count = len(db_manager.get_all_attractions(limit=1000))
                elif table == 'restaurants':
                    count = len(db_manager.get_all_restaurants(limit=1000))
                elif table == 'accommodations':
                    count = len(db_manager.get_all_accommodations(limit=1000))
                else:
                    continue  # Skip other tables for now
                logger.info(f"Table '{table}' has {count} records")
        
        return True
    except Exception as e:
        logger.error(f"Database verification failed: {str(e)}", exc_info=True)
        return False

def verify_knowledge_base():
    """Verify KnowledgeBase connection and functionality."""
    try:
        logger.info("Creating DatabaseManager for Knowledge Base")
        db_manager = DatabaseManager(database_uri=os.getenv('DATABASE_URI'))
        
        logger.info("Creating Knowledge Base instance")
        kb = KnowledgeBase(db_manager=db_manager)
        
        # Test basic KB operations
        logger.info("Testing Knowledge Base operations")
        
        # Test attraction search
        logger.info("Testing attraction search")
        attractions = kb.search_attractions(query="pyramid", limit=5)
        logger.info(f"Found {len(attractions)} attractions matching 'pyramid'")
        
        if attractions:
            # Get the first attraction's ID
            attraction_id = attractions[0].get('id', None)
            if attraction_id:
                # Test get attraction by ID
                logger.info(f"Testing get attraction by ID: {attraction_id}")
                attraction = kb.get_attraction_by_id(attraction_id)
                if attraction:
                    logger.info(f"Successfully retrieved attraction: {attraction.get('name_en', 'Unknown')}")
                else:
                    logger.warning(f"Failed to retrieve attraction with ID: {attraction_id}")
        
        # Test restaurant search
        logger.info("Testing restaurant search")
        restaurants = kb.search_restaurants(limit=5)
        logger.info(f"Found {len(restaurants)} restaurants")
        
        # Test hotel search
        logger.info("Testing hotel search")
        hotels = kb.search_hotels(limit=5)
        logger.info(f"Found {len(hotels)} hotels")
        
        return True
    except Exception as e:
        logger.error(f"Knowledge Base verification failed: {str(e)}", exc_info=True)
        return False

def main():
    """Main verification function."""
    try:
        logger.info("Starting Knowledge Base verification")
        
        # Verify database
        db_result = verify_database_connection()
        logger.info(f"Database verification {'successful' if db_result else 'failed'}")
        
        # Verify Knowledge Base
        kb_result = verify_knowledge_base()
        logger.info(f"Knowledge Base verification {'successful' if kb_result else 'failed'}")
        
        if db_result and kb_result:
            logger.info("Knowledge Base connection verified successfully!")
            return 0
        else:
            logger.error("Knowledge Base verification failed")
            return 1
    except Exception as e:
        logger.error(f"Verification failed with exception: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 