#!/usr/bin/env python3
"""
Test script to check database queries for different types of information in the Egypt Tourism Chatbot.
This script tests the knowledge base's ability to retrieve information from the database.
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
from src.knowledge.knowledge_base import KnowledgeBase
from src.knowledge.database import DatabaseManager

def test_database_connection():
    """Test the database connection."""
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

def test_knowledge_base(db_manager):
    """Test the knowledge base with the database manager."""
    try:
        # Create knowledge base
        kb = KnowledgeBase(db_manager)
        logger.info("✅ Knowledge base created successfully")
        return kb
    except Exception as e:
        logger.error(f"❌ Error creating knowledge base: {str(e)}")
        return None

def test_search_attractions(kb, query_text=None):
    """Test searching for attractions."""
    logger.info(f"Testing search_attractions with query: {query_text}")
    try:
        query = {"text": query_text} if query_text else {}
        results = kb.search_attractions(query=query, limit=3)
        logger.info(f"Found {len(results)} attractions")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result.get('name', {}).get('en', 'Unknown')}")
        return results
    except Exception as e:
        logger.error(f"❌ Error searching attractions: {str(e)}")
        return []

def test_search_restaurants(kb, query_text=None):
    """Test searching for restaurants."""
    logger.info(f"Testing search_restaurants with query: {query_text}")
    try:
        query = {"text": query_text} if query_text else {}
        results = kb.search_restaurants(query=query, limit=3)
        logger.info(f"Found {len(results)} restaurants")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result.get('name', {}).get('en', 'Unknown')}")
        return results
    except Exception as e:
        logger.error(f"❌ Error searching restaurants: {str(e)}")
        return []

def test_search_hotels(kb, query_text=None):
    """Test searching for hotels."""
    logger.info(f"Testing search_hotels with query: {query_text}")
    try:
        query = {"text": query_text} if query_text else {}
        results = kb.search_hotels(query=query, limit=3)
        logger.info(f"Found {len(results)} hotels")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result.get('name', {}).get('en', 'Unknown')}")
        return results
    except Exception as e:
        logger.error(f"❌ Error searching hotels: {str(e)}")
        return []

def test_search_faqs(kb, query_text=None):
    """Test searching for FAQs."""
    logger.info(f"Testing search_faqs with query: {query_text}")
    try:
        query = {"text": query_text} if query_text else {}
        results = kb.search_faqs(query=query, limit=3)
        logger.info(f"Found {len(results)} FAQs")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result.get('question', {}).get('en', 'Unknown')}")
        return results
    except Exception as e:
        logger.error(f"❌ Error searching FAQs: {str(e)}")
        return []

def test_search_events(kb, query_text=None):
    """Test searching for events."""
    logger.info(f"Testing search_events with query: {query_text}")
    try:
        query = {"text": query_text} if query_text else {}
        results = kb.search_events(query=query, limit=3)
        logger.info(f"Found {len(results)} events")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result.get('name', {}).get('en', 'Unknown')}")
        return results
    except Exception as e:
        logger.error(f"❌ Error searching events: {str(e)}")
        return []

def test_search_itineraries(kb, query_text=None):
    """Test searching for itineraries."""
    logger.info(f"Testing search_itineraries with query: {query_text}")
    try:
        query = {"text": query_text} if query_text else {}
        results = kb.search_itineraries(query=query, limit=3)
        logger.info(f"Found {len(results)} itineraries")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result.get('name', {}).get('en', 'Unknown')}")
        return results
    except Exception as e:
        logger.error(f"❌ Error searching itineraries: {str(e)}")
        return []

def test_search_practical_info(kb, query_text=None, category=None):
    """Test searching for practical info."""
    logger.info(f"Testing search_practical_info with query: {query_text}, category: {category}")
    try:
        query = {}
        if query_text:
            query["text"] = query_text
        if category:
            query["category_id"] = category
        
        results = kb.search_practical_info(query=query, limit=3)
        logger.info(f"Found {len(results)} practical info items")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result.get('title', {}).get('en', 'Unknown')}")
        return results
    except Exception as e:
        logger.error(f"❌ Error searching practical info: {str(e)}")
        return []

def main():
    """Main function to run all tests."""
    logger.info("Starting database query tests")
    
    # Test database connection
    db_manager = test_database_connection()
    if not db_manager:
        logger.error("Cannot continue without database connection")
        return
    
    # Test knowledge base
    kb = test_knowledge_base(db_manager)
    if not kb:
        logger.error("Cannot continue without knowledge base")
        return
    
    # Test all query types
    logger.info("\n=== Testing all query types ===")
    
    # Test attractions
    logger.info("\n--- Testing Attractions ---")
    test_search_attractions(kb)
    test_search_attractions(kb, "pyramid")
    
    # Test restaurants
    logger.info("\n--- Testing Restaurants ---")
    test_search_restaurants(kb)
    test_search_restaurants(kb, "seafood")
    
    # Test hotels
    logger.info("\n--- Testing Hotels ---")
    test_search_hotels(kb)
    test_search_hotels(kb, "luxury")
    
    # Test FAQs
    logger.info("\n--- Testing FAQs ---")
    test_search_faqs(kb)
    test_search_faqs(kb, "visa")
    
    # Test events
    logger.info("\n--- Testing Events ---")
    test_search_events(kb)
    test_search_events(kb, "festival")
    
    # Test itineraries
    logger.info("\n--- Testing Itineraries ---")
    test_search_itineraries(kb)
    test_search_itineraries(kb, "adventure")
    
    # Test practical info
    logger.info("\n--- Testing Practical Info ---")
    test_search_practical_info(kb)
    test_search_practical_info(kb, "currency")
    test_search_practical_info(kb, None, "safety")
    
    logger.info("\nAll tests completed")

if __name__ == "__main__":
    main()
