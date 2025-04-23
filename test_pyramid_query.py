#!/usr/bin/env python3
"""
Test script to verify the chatbot's response to a query about the pyramids.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure the proper environment is set
os.environ['USE_NEW_KB'] = 'true'

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import chatbot
from src.chatbot import Chatbot
from src.utils.factory import component_factory
import asyncio

async def test_pyramid_query():
    """Test a query about the pyramids."""
    print("Initializing chatbot components...")
    
    # Initialize components
    component_factory.initialize()
    
    # Create chatbot
    chatbot = component_factory.create_chatbot()
    
    print("Chatbot components initialized.")
    
    # Create a test session ID
    session_id = "test_session_123"
    
    # Test queries
    test_queries = [
        "Tell me about the pyramids",
        "What are the pyramids of Giza?",
        "Information about pyramids",
        "Tell me about the Sphinx",
        "What's in Alexandria?"
    ]
    
    print("\nTesting queries with direct attraction handler...\n")
    
    for query in test_queries:
        print(f"\nQuery: \"{query}\"")
        # Use process_attraction_query directly instead of process_message to bypass session issues
        response = await chatbot.process_attraction_query(query, session_id, "en")
        
        # Print response
        print(f"Response: \"{response.get('text', 'No response text')}\"")
        print(f"Intent: {response.get('intent', 'unknown')}")
        print(f"Entities: {response.get('entities', {})}")
        
        # Validate response
        if "pyramid" in query.lower() and "pyramid" not in response.get('text', '').lower():
            print("ERROR: Query about pyramids but response doesn't mention pyramids!")
        elif "sphinx" in query.lower() and "sphinx" not in response.get('text', '').lower():
            print("ERROR: Query about sphinx but response doesn't mention sphinx!")
        elif "alexandria" in query.lower() and "alexandria" not in response.get('text', '').lower():
            print("ERROR: Query about Alexandria but response doesn't mention Alexandria!")
    
    print("\nTesting complete.")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_pyramid_query()) 