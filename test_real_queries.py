#!/usr/bin/env python3
"""
Test script for verifying the chatbot responds correctly to real user queries.
This script tests various types of tourism-related queries in both English and Arabic.
"""
import os
import sys
import json
import asyncio
import uuid
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the chatbot components
from src.utils.factory import ComponentFactory
from src.chatbot import Chatbot

# Test queries in English and Arabic
TEST_QUERIES = {
    "en": [
        # Attraction queries
        "Tell me about the pyramids",
        "What can you tell me about the Sphinx?",
        "I want to visit Luxor Temple",
        "What are the best attractions in Egypt?",
        
        # Accommodation queries
        "Where can I stay in Cairo?",
        "Recommend a hotel near the pyramids",
        "I need a luxury hotel in Sharm El Sheikh",
        
        # Restaurant queries
        "Where can I eat in Cairo?",
        "What are some traditional Egyptian foods?",
        "Recommend a restaurant with a view of the Nile",
        
        # General tourism queries
        "What's the best time to visit Egypt?",
        "How do I get from Cairo to Luxor?",
        "Is it safe to travel to Egypt?",
        "What should I pack for Egypt?"
    ],
    "ar": [
        # Attraction queries in Arabic
        "أخبرني عن الأهرامات",
        "ماذا يمكنك أن تخبرني عن أبو الهول؟",
        "أريد زيارة معبد الأقصر",
        "ما هي أفضل المعالم السياحية في مصر؟",
        
        # Accommodation queries in Arabic
        "أين يمكنني الإقامة في القاهرة؟",
        "اقترح فندقًا بالقرب من الأهرامات",
        "أحتاج إلى فندق فاخر في شرم الشيخ"
    ]
}

async def test_real_queries():
    """Test the chatbot with real user queries."""
    logger.info("Testing chatbot with real user queries...")
    
    # Create the component factory and initialize it
    factory = ComponentFactory()
    factory.initialize()
    
    # Create the chatbot components
    knowledge_base = factory.create_knowledge_base()
    nlu_engine = factory.create_nlu_engine()
    dialog_manager = factory.create_dialog_manager()
    response_generator = factory.create_response_generator()
    service_hub = factory.create_service_hub()
    session_manager = factory.create_session_manager()
    db_manager = factory.create_database_manager()
    
    # Create the chatbot instance
    chatbot = Chatbot(
        knowledge_base=knowledge_base,
        nlu_engine=nlu_engine,
        dialog_manager=dialog_manager,
        response_generator=response_generator,
        service_hub=service_hub,
        session_manager=session_manager,
        db_manager=db_manager
    )
    
    # Test results
    results = {
        "en": {"success": 0, "total": len(TEST_QUERIES["en"])},
        "ar": {"success": 0, "total": len(TEST_QUERIES["ar"])}
    }
    
    # Test English queries
    logger.info("Testing English queries...")
    session_id = str(uuid.uuid4())
    
    for query in TEST_QUERIES["en"]:
        logger.info(f"Testing query: '{query}'")
        response = await chatbot.process_message(query, session_id, "en")
        
        # Check if response has text
        if response and "text" in response and response["text"]:
            logger.info(f"Response: '{response['text'][:100]}...'")
            results["en"]["success"] += 1
        else:
            logger.error(f"Failed to get response for query: '{query}'")
    
    # Test Arabic queries
    logger.info("Testing Arabic queries...")
    session_id = str(uuid.uuid4())
    
    for query in TEST_QUERIES["ar"]:
        logger.info(f"Testing query: '{query}'")
        response = await chatbot.process_message(query, session_id, "ar")
        
        # Check if response has text
        if response and "text" in response and response["text"]:
            logger.info(f"Response: '{response['text'][:100]}...'")
            results["ar"]["success"] += 1
        else:
            logger.error(f"Failed to get response for query: '{query}'")
    
    # Print summary
    logger.info("\n--- Test Results Summary ---")
    for language, result in results.items():
        success_rate = (result["success"] / result["total"]) * 100
        logger.info(f"{language.upper()} Queries: {result['success']}/{result['total']} ({success_rate:.1f}%)")
    
    # Overall success
    total_success = results["en"]["success"] + results["ar"]["success"]
    total_queries = results["en"]["total"] + results["ar"]["total"]
    overall_success_rate = (total_success / total_queries) * 100
    logger.info(f"Overall Success Rate: {total_success}/{total_queries} ({overall_success_rate:.1f}%)")
    
    return overall_success_rate >= 80  # Consider test successful if at least 80% of queries get responses

async def test_database_search():
    """Test the database search methods with real data."""
    logger.info("Testing database search methods with real data...")
    
    # Create the component factory and initialize it
    factory = ComponentFactory()
    factory.initialize()
    
    # Create the database manager
    db_manager = factory.create_database_manager()
    
    # Test results
    results = {
        "attractions": False,
        "hotels": False,
        "restaurants": False
    }
    
    # Test attraction search
    logger.info("Testing attraction search...")
    attractions = db_manager.search_attractions(query={"name": "pyramid"}, limit=5)
    if attractions and len(attractions) > 0:
        logger.info(f"Found {len(attractions)} attractions matching 'pyramid'")
        logger.info(f"First result: {attractions[0].get('name_en', 'Unknown')}")
        results["attractions"] = True
    else:
        logger.error("No attractions found matching 'pyramid'")
    
    # Test hotel search
    logger.info("Testing hotel search...")
    hotels = db_manager.search_hotels(query={"city": "Cairo"}, limit=5)
    if hotels and len(hotels) > 0:
        logger.info(f"Found {len(hotels)} hotels in Cairo")
        logger.info(f"First result: {hotels[0].get('name_en', 'Unknown')}")
        results["hotels"] = True
    else:
        logger.error("No hotels found in Cairo")
    
    # Test restaurant search
    logger.info("Testing restaurant search...")
    restaurants = db_manager.search_restaurants(query={"city": "Cairo"}, limit=5)
    if restaurants and len(restaurants) > 0:
        logger.info(f"Found {len(restaurants)} restaurants in Cairo")
        logger.info(f"First result: {restaurants[0].get('name_en', 'Unknown')}")
        results["restaurants"] = True
    else:
        logger.error("No restaurants found in Cairo")
    
    # Print summary
    logger.info("\n--- Database Search Test Results ---")
    for entity_type, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{entity_type.capitalize()}: {status}")
    
    # Overall success
    return all(results.values())

async def run_tests():
    """Run all tests."""
    logger.info("Starting comprehensive tests...")
    
    # Run the tests
    query_test_result = await test_real_queries()
    db_test_result = await test_database_search()
    
    # Print overall summary
    logger.info("\n--- Overall Test Results ---")
    logger.info(f"Real User Queries Test: {'✅ PASSED' if query_test_result else '❌ FAILED'}")
    logger.info(f"Database Search Test: {'✅ PASSED' if db_test_result else '❌ FAILED'}")
    
    # Return overall success
    return query_test_result and db_test_result

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_tests())
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
