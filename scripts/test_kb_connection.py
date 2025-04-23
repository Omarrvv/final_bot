#!/usr/bin/env python
"""
Knowledge Base Connection Test

This script tests the connection to the Knowledge Base and its ability
to retrieve attraction data, specifically querying for the Pyramids of Giza.
It verifies that the Knowledge Base is properly configured and can access
the database.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('kb_connection_tester')

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import the Knowledge Base and Database Manager
try:
    from src.knowledge.knowledge_base import KnowledgeBase
    from src.utils.database import DatabaseManager
except ImportError as e:
    logger.error(f"❌ Failed to import required modules: {e}")
    logger.error("Make sure you're running this script from the project root directory")
    sys.exit(1)

def load_config():
    """Load database configuration."""
    try:
        config_path = os.path.join(project_root, 'configs', 'config.json')
        if not os.path.exists(config_path):
            logger.warning(f"⚠️ Config file not found at {config_path}")
            return {
                "database": {
                    "sqlite": {
                        "path": os.path.join(project_root, 'data', 'egypt_tourism.db')
                    }
                }
            }
            
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ Error loading configuration: {e}")
        return {}

def test_db_manager_connection(config):
    """Test the database manager connection."""
    logger.info("Testing DatabaseManager connection...")
    
    sqlite_path = config.get("database", {}).get("sqlite", {}).get("path")
    if not sqlite_path:
        sqlite_path = os.path.join(project_root, 'data', 'egypt_tourism.db')
        logger.warning(f"⚠️ SQLite path not found in config, using default: {sqlite_path}")
    
    if not os.path.exists(sqlite_path):
        logger.error(f"❌ SQLite database file not found at: {sqlite_path}")
        logger.error("Please run the populate_attraction_data.py script first")
        return None
    
    try:
        db_manager = DatabaseManager(sqlite_path)
        logger.info("✅ Successfully connected to the database")
        return db_manager
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        return None

def test_knowledge_base(db_manager):
    """Test the Knowledge Base functionality."""
    if not db_manager:
        logger.error("❌ Cannot test Knowledge Base without a valid DatabaseManager")
        return False
    
    logger.info("Initializing Knowledge Base...")
    try:
        kb = KnowledgeBase(db_manager)
        logger.info("✅ Knowledge Base initialized successfully")
        
        # Test attraction lookup
        logger.info("Testing attraction lookup for 'Pyramids of Giza'...")
        result = kb.lookup_attraction("Pyramids of Giza", "en")
        
        if result:
            logger.info("✅ Successfully retrieved information about the Pyramids of Giza:")
            logger.info(f"  - ID: {result.get('id')}")
            logger.info(f"  - Name: {result.get('name_en')}")
            logger.info(f"  - Type: {result.get('type')}")
            logger.info(f"  - Location: {result.get('city')}, {result.get('region')}")
            
            # Extract some data from the JSON
            data = json.loads(result.get('data', '{}'))
            if data:
                logger.info("  - Opening Hours: " + data.get('opening_hours', 'Not available'))
                logger.info("  - Best Time to Visit: " + data.get('best_time_to_visit', 'Not available'))
                
            return True
        else:
            logger.error("❌ Failed to retrieve information about the Pyramids of Giza")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing Knowledge Base: {e}")
        return False

def test_search_functionality(kb):
    """Test the search functionality of the Knowledge Base."""
    logger.info("\nTesting search functionality...")
    
    try:
        # Test searching for attractions
        search_term = "sphinx"
        logger.info(f"Searching for '{search_term}'...")
        results = kb.search_attractions(search_term, None, "en", 5)
        
        if results and len(results) > 0:
            logger.info(f"✅ Search returned {len(results)} results:")
            for i, result in enumerate(results, 1):
                logger.info(f"  {i}. {result.get('name_en')} ({result.get('id')})")
            return True
        else:
            logger.warning(f"⚠️ No results found for search term '{search_term}'")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing search functionality: {e}")
        return False

def run():
    """Run the Knowledge Base connection test."""
    logger.info("Starting Knowledge Base connection test...")
    
    # Load configuration
    config = load_config()
    
    # Test database connection
    db_manager = test_db_manager_connection(config)
    if not db_manager:
        logger.error("❌ Database connection test failed")
        return False
    
    # Initialize Knowledge Base
    kb = KnowledgeBase(db_manager)
    
    # Test attraction lookup
    lookup_success = test_knowledge_base(db_manager)
    
    # Test search functionality
    search_success = test_search_functionality(kb)
    
    # Print summary
    logger.info("\n=== Knowledge Base Connection Test Summary ===")
    logger.info(f"Database Connection: {'✅ PASSED' if db_manager else '❌ FAILED'}")
    logger.info(f"Attraction Lookup: {'✅ PASSED' if lookup_success else '❌ FAILED'}")
    logger.info(f"Search Functionality: {'✅ PASSED' if search_success else '❌ FAILED'}")
    
    overall_success = db_manager and lookup_success and search_success
    logger.info(f"\nOverall Test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
    
    if overall_success:
        logger.info("\n✅ The Knowledge Base is properly connected and functioning correctly.")
        logger.info("You can now enable USE_NEW_KB in your .env file to use the new Knowledge Base.")
    else:
        logger.error("\n❌ The Knowledge Base connection test failed.")
        logger.error("Please check the error messages above and fix the issues before enabling USE_NEW_KB.")
    
    return overall_success

if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1) 