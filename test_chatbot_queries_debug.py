#!/usr/bin/env python3
"""
Enhanced test script with additional debugging to identify database query issues.
This script tests the chatbot's ability to retrieve information from the database and
verifies whether responses come from the database or LLM fallback.
"""

import os
import sys
import logging
import asyncio
import time
import json
from collections import defaultdict
import traceback

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary modules
from src.chatbot import Chatbot
from src.knowledge.knowledge_base import KnowledgeBase

# Try to import optional modules
try:
    from src.nlu.intent_classifier import AdvancedIntentClassifier
except ImportError:
    logger.warning("Could not import AdvancedIntentClassifier")
    AdvancedIntentClassifier = None

try:
    from src.nlu.entity_extractor import EntityExtractor
except ImportError:
    logger.warning("Could not import EntityExtractor")
    EntityExtractor = None

try:
    from src.knowledge.cross_table_queries import CrossTableQueryManager
except ImportError:
    logger.warning("Could not import CrossTableQueryManager")
    CrossTableQueryManager = None

try:
    from src.utils.llm_fallback import LLMFallbackHandler
except ImportError:
    logger.warning("Could not import LLMFallbackHandler")
    LLMFallbackHandler = None

from src.knowledge.database import DatabaseManager

async def test_database_schema():
    """Test the database schema to identify column name issues."""
    logger.info("\n=== TESTING DATABASE SCHEMA ===")
    
    # Get database connection string from environment variable or use default
    db_uri = os.environ.get("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")
    logger.info(f"Using database URI: {db_uri}")
    
    # Create database manager
    db_manager = DatabaseManager(db_uri)
    if not db_manager.connect():
        logger.error("❌ Database connection failed")
        return None
    logger.info("✅ Database connection successful")
    
    # Test tables and columns
    tables_to_check = [
        "attractions", 
        "accommodations", 
        "restaurants", 
        "cities", 
        "regions", 
        "tourism_faqs", 
        "practical_info",
        "transportation_routes",
        "events_festivals",
        "tour_packages",
        "itineraries"
    ]
    
    for table in tables_to_check:
        try:
            # Check if table exists
            query = f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
            result = db_manager.execute_postgres_query(query)
            exists = result[0]['exists'] if result else False
            
            if exists:
                logger.info(f"✅ Table '{table}' exists")
                
                # Get columns
                query = f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'"
                columns = db_manager.execute_postgres_query(query)
                
                if columns:
                    logger.info(f"Columns in '{table}':")
                    for col in columns:
                        logger.info(f"  - {col['column_name']} ({col['data_type']})")
                    
                    # Check for specific columns that might be causing issues
                    name_columns = [col['column_name'] for col in columns if 'name' in col['column_name']]
                    logger.info(f"Name-related columns: {name_columns}")
                    
                    # Check for JSONB columns
                    jsonb_columns = [col['column_name'] for col in columns if col['data_type'] == 'jsonb']
                    logger.info(f"JSONB columns: {jsonb_columns}")
                    
                    # Test a simple query
                    try:
                        query = f"SELECT * FROM {table} LIMIT 1"
                        sample = db_manager.execute_postgres_query(query)
                        if sample:
                            logger.info(f"✅ Sample query successful for '{table}'")
                            logger.info(f"Sample data keys: {list(sample[0].keys())}")
                        else:
                            logger.warning(f"⚠️ No data in '{table}'")
                    except Exception as e:
                        logger.error(f"❌ Error querying '{table}': {str(e)}")
                else:
                    logger.warning(f"⚠️ No columns found for '{table}'")
            else:
                logger.warning(f"⚠️ Table '{table}' does not exist")
        except Exception as e:
            logger.error(f"❌ Error checking table '{table}': {str(e)}")
    
    return db_manager

async def test_specific_queries(db_manager):
    """Test specific queries that are failing in the main test."""
    logger.info("\n=== TESTING SPECIFIC QUERIES ===")
    
    # Test attractions query
    logger.info("\n--- Testing attractions query ---")
    try:
        # Test with name_en (failing in logs)
        query = "SELECT * FROM attractions WHERE 1=1 ORDER BY name_en LIMIT 3 OFFSET 0"
        logger.info(f"Executing query: {query}")
        result = db_manager.execute_postgres_query(query)
        logger.info(f"Result: {result is not None}")
    except Exception as e:
        logger.error(f"❌ Error with name_en query: {str(e)}")
        
        # Try with correct column name
        try:
            # Check if name is a JSONB column
            query = "SELECT * FROM attractions WHERE 1=1 ORDER BY name->>'en' LIMIT 3 OFFSET 0"
            logger.info(f"Trying JSONB query: {query}")
            result = db_manager.execute_postgres_query(query)
            if result:
                logger.info(f"✅ JSONB query successful: {len(result)} results")
                logger.info(f"First result keys: {list(result[0].keys())}")
            else:
                logger.warning("⚠️ No results from JSONB query")
        except Exception as jsonb_error:
            logger.error(f"❌ Error with JSONB query: {str(jsonb_error)}")
    
    # Test accommodations query
    logger.info("\n--- Testing accommodations query ---")
    try:
        # Test with name_en (failing in logs)
        query = "SELECT * FROM accommodations WHERE 1=1 ORDER BY name_en LIMIT 3 OFFSET 0"
        logger.info(f"Executing query: {query}")
        result = db_manager.execute_postgres_query(query)
        logger.info(f"Result: {result is not None}")
    except Exception as e:
        logger.error(f"❌ Error with name_en query: {str(e)}")
        
        # Try with correct column name
        try:
            # Check if name is a JSONB column
            query = "SELECT * FROM accommodations WHERE 1=1 ORDER BY name->>'en' LIMIT 3 OFFSET 0"
            logger.info(f"Trying JSONB query: {query}")
            result = db_manager.execute_postgres_query(query)
            if result:
                logger.info(f"✅ JSONB query successful: {len(result)} results")
                logger.info(f"First result keys: {list(result[0].keys())}")
            else:
                logger.warning("⚠️ No results from JSONB query")
        except Exception as jsonb_error:
            logger.error(f"❌ Error with JSONB query: {str(jsonb_error)}")
    
    # Test restaurants query
    logger.info("\n--- Testing restaurants query ---")
    try:
        query = "SELECT * FROM restaurants WHERE 1=1 ORDER BY name->>'en' LIMIT 3 OFFSET 0"
        logger.info(f"Executing query: {query}")
        result = db_manager.execute_postgres_query(query)
        if result:
            logger.info(f"✅ Query successful: {len(result)} results")
            logger.info(f"First result keys: {list(result[0].keys())}")
        else:
            logger.warning("⚠️ No results from query")
    except Exception as e:
        logger.error(f"❌ Error with query: {str(e)}")

async def main():
    """Main function to run the test."""
    logger.info("=== EGYPT TOURISM CHATBOT DATABASE DEBUGGING ===")
    logger.info("This test will diagnose database schema and query issues")
    
    # Test database schema
    db_manager = await test_database_schema()
    if not db_manager:
        logger.error("Cannot continue without database connection")
        return
    
    # Test specific queries
    await test_specific_queries(db_manager)
    
    logger.info("\nDatabase debugging completed")

if __name__ == "__main__":
    # Set up better logging format
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Run the test
    asyncio.run(main())
