#!/usr/bin/env python3
"""
Test script for the Egypt Tourism Chatbot with Anthropic integration.
This script tests the chatbot's ability to use Anthropic as a fallback.
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import the necessary components
from src.utils.factory import component_factory

async def test_chatbot_with_anthropic():
    """Test the chatbot with Anthropic fallback."""
    print("\n🧪 Testing Egypt Tourism Chatbot with Anthropic fallback...\n")
    
    # Initialize the component factory
    component_factory.initialize()
    
    # Create the chatbot
    chatbot = component_factory.create_chatbot()
    
    # Test queries that are likely to trigger the fallback mechanism
    test_queries = [
        "What's the best way to handle tipping in Egypt?",
        "Can you recommend some lesser-known historical sites near Aswan?",
        "What should I know about Egyptian wedding traditions?",
        "How has climate change affected tourism in Egypt?"
    ]
    
    # Create a session ID
    session_id = None
    
    for query in test_queries:
        print(f"📝 Query: {query}")
        
        # Process the message
        response = await chatbot.process_message(
            user_message=query,
            session_id=session_id,
            language="en"
        )
        
        # Get or update session ID
        if not session_id:
            session_id = response.get("session_id")
            print(f"Session created: {session_id}")
        
        # Print the response
        print(f"🤖 Response: {response.get('text', 'No response')[:300]}...\n")
        
        # Add a small delay to avoid rate limiting
        await asyncio.sleep(1)
    
    print("✅ Chatbot with Anthropic fallback test completed!")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_chatbot_with_anthropic())
