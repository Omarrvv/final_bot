#!/usr/bin/env python3
"""
Test script to directly query the database and check what information is available.
This script bypasses the knowledge base and directly queries the database tables.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary modules
from src.knowledge.database import DatabaseManager

def connect_to_database():
    """Connect to the database."""
    try:
        # Get database connection string from environment variable or use default
        db_uri = os.environ.get("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")
        
        # Create database manager
        db_manager = DatabaseManager(db_uri)
        
        # Test connection
        if db_manager.connect():
            logger.info("✅ Database connection successful")
            return db_manager
        else:
            logger.error("❌ Database connection failed")
            return None
    except Exception as e:
        logger.error(f"❌ Error connecting to database: {str(e)}")
        return None

def list_tables(db_manager):
    """List all tables in the database."""
    try:
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        results = db_manager.execute_query(query)
        logger.info(f"Found {len(results)} tables in the database")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result['table_name']}")
        return results
    except Exception as e:
        logger.error(f"❌ Error listing tables: {str(e)}")
        return []

def count_records(db_manager, table_name):
    """Count the number of records in a table."""
    try:
        query = f"SELECT COUNT(*) FROM {table_name};"
        results = db_manager.execute_query(query)
        count = results[0]['count'] if results else 0
        logger.info(f"Table {table_name} has {count} records")
        return count
    except Exception as e:
        logger.error(f"❌ Error counting records in {table_name}: {str(e)}")
        return 0

def sample_records(db_manager, table_name, limit=3):
    """Get a sample of records from a table."""
    try:
        query = f"SELECT * FROM {table_name} LIMIT {limit};"
        results = db_manager.execute_query(query)
        logger.info(f"Sample of {len(results)} records from {table_name}")
        return results
    except Exception as e:
        logger.error(f"❌ Error getting sample records from {table_name}: {str(e)}")
        return []

def check_table_columns(db_manager, table_name):
    """Check the columns in a table."""
    try:
        query = f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position;
        """
        results = db_manager.execute_query(query)
        logger.info(f"Table {table_name} has {len(results)} columns")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result['column_name']} ({result['data_type']})")
        return results
    except Exception as e:
        logger.error(f"❌ Error checking columns in {table_name}: {str(e)}")
        return []

def test_currency_query(db_manager):
    """Test querying for currency information."""
    try:
        query = """
        SELECT * FROM practical_info 
        WHERE category_id = 'currency' 
        OR title->>'en' ILIKE '%currency%' 
        OR content->>'en' ILIKE '%currency%'
        LIMIT 3;
        """
        results = db_manager.execute_query(query)
        logger.info(f"Found {len(results)} currency-related records in practical_info")
        for i, result in enumerate(results):
            title = result.get('title', {})
            if isinstance(title, str):
                try:
                    title = json.loads(title)
                except:
                    title = {"en": title}
            logger.info(f"  {i+1}. {title.get('en', 'Unknown')}")
        return results
    except Exception as e:
        logger.error(f"❌ Error querying for currency information: {str(e)}")
        return []

def test_itinerary_query(db_manager):
    """Test querying for itinerary information."""
    try:
        query = """
        SELECT * FROM itineraries 
        LIMIT 3;
        """
        results = db_manager.execute_query(query)
        logger.info(f"Found {len(results)} itineraries")
        for i, result in enumerate(results):
            name = result.get('name', {})
            if isinstance(name, str):
                try:
                    name = json.loads(name)
                except:
                    name = {"en": name}
            logger.info(f"  {i+1}. {name.get('en', 'Unknown')}")
        return results
    except Exception as e:
        logger.error(f"❌ Error querying for itineraries: {str(e)}")
        return []

def test_faq_query(db_manager):
    """Test querying for FAQ information."""
    try:
        query = """
        SELECT * FROM tourism_faqs 
        LIMIT 3;
        """
        results = db_manager.execute_query(query)
        logger.info(f"Found {len(results)} FAQs")
        for i, result in enumerate(results):
            question = result.get('question', {})
            if isinstance(question, str):
                try:
                    question = json.loads(question)
                except:
                    question = {"en": question}
            logger.info(f"  {i+1}. {question.get('en', 'Unknown')}")
        return results
    except Exception as e:
        logger.error(f"❌ Error querying for FAQs: {str(e)}")
        return []

def test_event_query(db_manager):
    """Test querying for event information."""
    try:
        query = """
        SELECT * FROM events_festivals 
        LIMIT 3;
        """
        results = db_manager.execute_query(query)
        logger.info(f"Found {len(results)} events")
        for i, result in enumerate(results):
            name = result.get('name', {})
            if isinstance(name, str):
                try:
                    name = json.loads(name)
                except:
                    name = {"en": name}
            logger.info(f"  {i+1}. {name.get('en', 'Unknown')}")
        return results
    except Exception as e:
        logger.error(f"❌ Error querying for events: {str(e)}")
        return []

def main():
    """Main function to run all tests."""
    logger.info("Starting direct database query tests")
    
    # Connect to the database
    db_manager = connect_to_database()
    if not db_manager:
        logger.error("Cannot continue without database connection")
        return
    
    # List all tables
    logger.info("\n=== Listing all tables ===")
    tables = list_tables(db_manager)
    
    # Check record counts for key tables
    logger.info("\n=== Checking record counts ===")
    key_tables = [
        "attractions", "restaurants", "accommodations", 
        "tourism_faqs", "events_festivals", "itineraries", 
        "practical_info", "practical_info_categories"
    ]
    for table in key_tables:
        count_records(db_manager, table)
    
    # Test specific queries
    logger.info("\n=== Testing currency query ===")
    test_currency_query(db_manager)
    
    logger.info("\n=== Testing itinerary query ===")
    test_itinerary_query(db_manager)
    
    logger.info("\n=== Testing FAQ query ===")
    test_faq_query(db_manager)
    
    logger.info("\n=== Testing event query ===")
    test_event_query(db_manager)
    
    logger.info("\nAll direct database query tests completed")

if __name__ == "__main__":
    main()
