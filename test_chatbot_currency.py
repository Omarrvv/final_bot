#!/usr/bin/env python3
"""
Test script to check if the chatbot can answer questions about currency.
This script tests the chatbot's ability to retrieve currency information from the database.
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary modules
from src.chatbot import Chatbot
from src.utils.container import container

async def test_chatbot_currency_query():
    """Test the chatbot's ability to answer questions about currency."""
    try:
        # Get the chatbot instance from the container
        chatbot = container.get("chatbot")
        if not chatbot:
            logger.error("❌ Chatbot not found in container")
            return
        
        logger.info("✅ Chatbot instance retrieved from container")
        
        # Define test questions about currency
        currency_questions = [
            "What is the currency used in Egypt?",
            "Tell me about Egyptian money",
            "What's the exchange rate for US dollars in Egypt?",
            "Do they accept credit cards in Egypt?",
            "How much should I tip in Egypt?",
            "Where can I exchange money in Egypt?",
            "Are there ATMs in Egypt?",
            "What denominations of Egyptian pounds are there?",
            "Should I bring cash to Egypt?",
            "Is it better to use cash or card in Egypt?"
        ]
        
        # Process each question and check the response
        for question in currency_questions:
            logger.info(f"\n--- Testing question: '{question}' ---")
            
            # Process the message
            response = await chatbot.process_message(
                user_message=question,
                session_id="test_session",
                language="en"
            )
            
            # Check if the response contains currency information
            response_text = response.get("text", "")
            source = response.get("source", "unknown")
            
            logger.info(f"Response source: {source}")
            logger.info(f"Response text (first 100 chars): {response_text[:100]}...")
            
            # Check if the response came from the database
            if source == "database" or "database" in source:
                logger.info("✅ Response came from database")
            else:
                logger.info("❌ Response did not come from database")
            
            # Check if the response contains currency-related keywords
            currency_keywords = ["pound", "EGP", "currency", "money", "exchange", "cash", "card", "ATM", "tip"]
            contains_currency_info = any(keyword.lower() in response_text.lower() for keyword in currency_keywords)
            
            if contains_currency_info:
                logger.info("✅ Response contains currency information")
            else:
                logger.info("❌ Response does not contain currency information")
            
            # Add a delay to avoid overwhelming the system
            await asyncio.sleep(1)
    
    except Exception as e:
        logger.error(f"❌ Error testing chatbot currency query: {str(e)}")

async def main():
    """Main function to run the test."""
    logger.info("Starting chatbot currency query test")
    
    # Initialize the container
    try:
        # Import the container initialization module
        from src.utils.container_init import initialize_container
        
        # Initialize the container
        initialize_container()
        logger.info("✅ Container initialized")
        
        # Test the chatbot's ability to answer questions about currency
        await test_chatbot_currency_query()
        
    except Exception as e:
        logger.error(f"❌ Error initializing container: {str(e)}")
    
    logger.info("Chatbot currency query test completed")

if __name__ == "__main__":
    asyncio.run(main())
