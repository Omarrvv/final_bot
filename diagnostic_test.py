#!/usr/bin/env python3
"""
Diagnostic script to identify issues with the Egypt Tourism Chatbot database queries.
This script will:
1. Test the restaurant query handling to fix the 'str' object has no attribute 'get' error
2. Test the transportation query handling to fix the 'column "text" does not exist' error
3. Examine the cross-table query recognition to improve the 8.3% success rate
4. Check for missing data in tables
"""
import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the necessary components
from src.utils.factory import component_factory
from src.knowledge.database import DatabaseManager
from src.knowledge.knowledge_base import KnowledgeBase
from src.nlu.intent_classifier import AdvancedIntentClassifier
from src.chatbot import Chatbot

def test_restaurant_queries():
    """Test restaurant queries to diagnose the 'str' object has no attribute 'get' error."""
    logger.info("\n=== Testing Restaurant Queries ===")
    
    # Initialize the database manager
    db_manager = component_factory.create_database_manager()
    
    # Initialize the knowledge base
    kb = KnowledgeBase(db_manager=db_manager)
    
    # Test direct database query
    logger.info("Testing direct database query for restaurants...")
    try:
        restaurants = db_manager.search_restaurants(
            query={"text": "Cairo"},
            limit=3
        )
        logger.info(f"Found {len(restaurants)} restaurants matching 'Cairo'")
        
        # Examine the raw restaurant data
        for i, restaurant in enumerate(restaurants):
            logger.info(f"Restaurant {i+1} raw data: {type(restaurant)}")
            logger.info(f"Restaurant {i+1} keys: {restaurant.keys() if hasattr(restaurant, 'keys') else 'No keys method'}")
            
            # Test the name field specifically
            if 'name' in restaurant:
                logger.info(f"Restaurant {i+1} name type: {type(restaurant['name'])}")
                logger.info(f"Restaurant {i+1} name value: {restaurant['name']}")
    except Exception as e:
        logger.error(f"Error in direct database query: {str(e)}", exc_info=True)
    
    # Test knowledge base formatting
    logger.info("\nTesting knowledge base formatting for restaurants...")
    try:
        # Get restaurants through knowledge base
        kb_restaurants = kb.search_restaurants(
            query={"text": "Cairo"},
            limit=3
        )
        logger.info(f"Knowledge base found {len(kb_restaurants) if kb_restaurants else 0} restaurants")
        
        # If we got results, examine the first one
        if kb_restaurants and len(kb_restaurants) > 0:
            logger.info(f"First restaurant formatted data: {kb_restaurants[0]}")
    except Exception as e:
        logger.error(f"Error in knowledge base query: {str(e)}", exc_info=True)

def test_transportation_queries():
    """Test transportation queries to diagnose the 'column "text" does not exist' error."""
    logger.info("\n=== Testing Transportation Queries ===")
    
    # Initialize the database manager
    db_manager = component_factory.create_database_manager()
    
    # Initialize the knowledge base
    kb = KnowledgeBase(db_manager=db_manager)
    
    # Check the transportation_routes table schema
    logger.info("Checking transportation_routes table schema...")
    try:
        columns = db_manager._get_table_columns("transportation_routes")
        logger.info(f"Transportation_routes columns: {columns}")
    except Exception as e:
        logger.error(f"Error getting table columns: {str(e)}", exc_info=True)
    
    # Test enhanced search on transportation_routes
    logger.info("\nTesting enhanced_search on transportation_routes...")
    try:
        results = db_manager.enhanced_search(
            table="transportation_routes",
            search_text="Cairo",
            limit=3
        )
        logger.info(f"Enhanced search found {len(results)} transportation routes")
        if results and len(results) > 0:
            logger.info(f"First result: {results[0]}")
    except Exception as e:
        logger.error(f"Error in enhanced search: {str(e)}", exc_info=True)
    
    # Test knowledge base transportation search
    logger.info("\nTesting knowledge base transportation search...")
    try:
        kb_results = kb.search_transportation(
            query={"text": "Cairo to Luxor"},
            limit=3
        )
        logger.info(f"Knowledge base found {len(kb_results) if kb_results else 0} transportation options")
    except Exception as e:
        logger.error(f"Error in knowledge base transportation search: {str(e)}", exc_info=True)

def test_cross_table_queries():
    """Test cross-table queries to diagnose the low success rate."""
    logger.info("\n=== Testing Cross-Table Queries ===")
    
    # Initialize the database manager
    db_manager = component_factory.create_database_manager()
    
    # Initialize the knowledge base
    kb = KnowledgeBase(db_manager=db_manager)
    
    # Test intent recognition for cross-table queries
    logger.info("Testing intent recognition for cross-table queries...")
    try:
        # Initialize the intent classifier
        intent_classifier = AdvancedIntentClassifier()
        
        # Test some cross-table queries
        test_queries = [
            "What restaurants are near the Pyramids of Giza?",
            "Are there any hotels near the Sphinx?",
            "What events are happening near the Egyptian Museum?",
            "What attractions are included in the 7-day Egypt tour?"
        ]
        
        for query in test_queries:
            intent_result = intent_classifier.classify(query)
            logger.info(f"Query: '{query}'")
            logger.info(f"Intent: {intent_result.intent}")
            logger.info(f"Entities: {intent_result.entities}")
            logger.info(f"Confidence: {intent_result.confidence}")
            logger.info("")
    except Exception as e:
        logger.error(f"Error in intent recognition: {str(e)}", exc_info=True)
    
    # Test direct cross-table query methods
    logger.info("\nTesting direct cross-table query methods...")
    try:
        # Test find_restaurants_near_attraction
        restaurants = kb.find_restaurants_near_attraction(
            attraction_name="Pyramids of Giza",
            limit=3
        )
        logger.info(f"Found {len(restaurants) if restaurants else 0} restaurants near Pyramids of Giza")
        
        # Test find_hotels_near_attraction
        hotels = kb.find_hotels_near_attraction(
            attraction_name="Sphinx",
            limit=3
        )
        logger.info(f"Found {len(hotels) if hotels else 0} hotels near Sphinx")
    except Exception as e:
        logger.error(f"Error in direct cross-table query: {str(e)}", exc_info=True)

def check_table_data():
    """Check for missing data in tables."""
    logger.info("\n=== Checking Table Data ===")
    
    # Initialize the database manager
    db_manager = component_factory.create_database_manager()
    
    # List of tables to check
    tables = [
        "attractions",
        "restaurants",
        "accommodations",
        "transportation_routes",
        "events_festivals",
        "itineraries",
        "tour_packages",
        "practical_info",
        "tourism_faqs"
    ]
    
    # Check each table
    for table in tables:
        try:
            # Check if table exists
            if db_manager._table_exists(table):
                # Count rows
                sql = f"SELECT COUNT(*) as count FROM {table}"
                result = db_manager.execute_postgres_query(sql, fetchall=False)
                count = result.get('count', 0) if result else 0
                logger.info(f"Table '{table}' exists with {count} rows")
                
                # If table has data, show a sample
                if count > 0:
                    sample_sql = f"SELECT * FROM {table} LIMIT 1"
                    sample = db_manager.execute_postgres_query(sample_sql, fetchall=False)
                    if sample:
                        logger.info(f"Sample columns: {list(sample.keys())}")
            else:
                logger.warning(f"Table '{table}' does not exist")
        except Exception as e:
            logger.error(f"Error checking table '{table}': {str(e)}")

def main():
    """Run all diagnostic tests."""
    logger.info("Starting diagnostic tests for Egypt Tourism Chatbot...")
    
    # Test restaurant queries
    test_restaurant_queries()
    
    # Test transportation queries
    test_transportation_queries()
    
    # Test cross-table queries
    test_cross_table_queries()
    
    # Check table data
    check_table_data()
    
    logger.info("\nDiagnostic tests completed!")

if __name__ == "__main__":
    main()
