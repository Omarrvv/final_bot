#!/usr/bin/env python
"""
Script to properly enable and configure the Knowledge Base component.
This script fixes the disconnection issue by ensuring the Knowledge Base is properly connected
to either the SQLite or PostgreSQL database and sets the appropriate feature flags.
"""

import os
import sys
import logging
import dotenv
from typing import Dict, Any

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from src.knowledge.knowledge_base import KnowledgeBase
from src.utils.database import DatabaseManager
from src.utils.postgres_database import PostgresqlDatabaseManager
from src.settings import settings, update_settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('enable_knowledge_base')

def test_database_connection():
    """Test the database connection to ensure it's working properly."""
    try:
        if settings.use_postgres:
            db_manager = PostgresqlDatabaseManager()
            db_type = "PostgreSQL"
        else:
            db_manager = DatabaseManager()
            db_type = "SQLite"
        
        logger.info(f"Testing connection to {db_type} database...")
        db_manager.connect()
        
        # Test a simple query
        result = db_manager.execute_query("SELECT 1")
        if result:
            logger.info(f"{db_type} database connection successful")
            
            # Test attractions table
            attractions = db_manager.execute_query(
                "SELECT COUNT(*) as count FROM attractions"
            )
            if attractions:
                count = attractions[0]['count'] if isinstance(attractions[0], dict) else attractions[0][0]
                logger.info(f"Found {count} attractions in the database")
            else:
                logger.warning("Could not retrieve attractions count")
                
            db_manager.disconnect()
            return True
        else:
            logger.error(f"{db_type} database connection test failed")
            db_manager.disconnect()
            return False
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return False

def test_knowledge_base():
    """Test the Knowledge Base component to ensure it's correctly connected to the database."""
    try:
        logger.info("Testing Knowledge Base component...")
        # Initialize Knowledge Base with appropriate database manager
        if settings.use_postgres:
            db_manager = PostgresqlDatabaseManager()
        else:
            db_manager = DatabaseManager()
            
        kb = KnowledgeBase(db_manager)
        
        # Test attraction lookup
        attraction = kb.lookup_attraction("Pyramids of Giza", "en")
        if attraction:
            logger.info("Knowledge Base successfully retrieved 'Pyramids of Giza'")
            logger.info(f"Attraction data: {attraction['name_en']}")
            return True
        else:
            logger.warning("Knowledge Base failed to retrieve 'Pyramids of Giza'")
            
            # Try a search instead
            attractions = kb.search_attractions("pyramid", None, "en", 1)
            if attractions and len(attractions) > 0:
                logger.info(f"Search found: {attractions[0]['name_en']}")
                return True
            else:
                logger.error("Knowledge Base search also failed")
                return False
    except Exception as e:
        logger.error(f"Knowledge Base test error: {str(e)}")
        return False

def update_env_file():
    """Update the .env file to enable the Knowledge Base feature flag."""
    try:
        logger.info("Updating .env file to enable Knowledge Base...")
        
        # Load current .env file
        dotenv_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if os.path.exists(dotenv_file):
            # Load existing variables
            dotenv.load_dotenv(dotenv_file)
            
        # Update the USE_NEW_KB flag
        os.environ["USE_NEW_KB"] = "true"
        
        # Write changes back to .env file
        with open(dotenv_file, 'w') as f:
            for key, value in os.environ.items():
                if key in ["USE_NEW_KB", "USE_POSTGRES", "USE_NEW_NLU", "USE_NEW_DIALOG", 
                           "USE_REDIS", "USE_RAG", "USE_SERVICE_HUB", "USE_NEW_API"]:
                    f.write(f"{key}={value}\n")
        
        logger.info("Updated .env file successfully")
        return True
    except Exception as e:
        logger.error(f"Error updating .env file: {str(e)}")
        return False

def update_runtime_settings():
    """Update the runtime settings to enable the Knowledge Base feature flag."""
    try:
        logger.info("Updating runtime settings...")
        update_settings({"use_new_kb": True})
        logger.info(f"Runtime settings updated. USE_NEW_KB is now: {settings.use_new_kb}")
        return True
    except Exception as e:
        logger.error(f"Error updating runtime settings: {str(e)}")
        return False

def verify_json_fallback():
    """Verify that the JSON fallback mechanism in the Knowledge Base is working."""
    try:
        logger.info("Verifying JSON fallback mechanism...")
        # Initialize Knowledge Base without a database manager to force JSON fallback
        kb = KnowledgeBase(None)
        
        # Test attraction lookup with JSON fallback
        attraction = kb.lookup_attraction("Pyramids of Giza", "en")
        if attraction:
            logger.info("JSON fallback successfully retrieved 'Pyramids of Giza'")
            return True
        else:
            logger.warning("JSON fallback failed to retrieve 'Pyramids of Giza'")
            return False
    except Exception as e:
        logger.error(f"JSON fallback verification error: {str(e)}")
        return False

def summarize_status():
    """Summarize the current status of the Knowledge Base and related components."""
    status = {
        "Database": "Connected" if test_database_connection() else "Disconnected",
        "Knowledge Base": "Functioning" if test_knowledge_base() else "Not functioning",
        "JSON Fallback": "Available" if verify_json_fallback() else "Not available",
        "USE_NEW_KB": "Enabled" if settings.use_new_kb else "Disabled",
        "USE_POSTGRES": "Enabled" if settings.use_postgres else "Disabled"
    }
    
    logger.info("Current System Status:")
    for component, state in status.items():
        logger.info(f"  - {component}: {state}")
    
    if status["Knowledge Base"] == "Functioning":
        logger.info("✅ Knowledge Base is properly connected and functioning!")
    else:
        logger.error("❌ Knowledge Base is not functioning correctly. Check the logs for details.")
    
    return status

def main():
    """Main function to enable and configure the Knowledge Base."""
    logger.info("Starting Knowledge Base configuration...")
    
    # Step 1: Test database connection
    if not test_database_connection():
        logger.error("Database connection failed. Cannot proceed.")
        return False
    
    # Step 2: Update settings to enable Knowledge Base
    update_runtime_settings()
    update_env_file()
    
    # Step 3: Test Knowledge Base functionality
    if not test_knowledge_base():
        logger.warning("Knowledge Base test failed. It may not be correctly connected.")
    
    # Step 4: Verify JSON fallback
    verify_json_fallback()
    
    # Step 5: Summarize status
    status = summarize_status()
    
    return status["Knowledge Base"] == "Functioning"

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Knowledge Base configuration completed successfully!")
        sys.exit(0)
    else:
        logger.error("Knowledge Base configuration encountered issues. Check the logs.")
        sys.exit(1) 