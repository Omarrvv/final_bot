#!/usr/bin/env python3
"""
Test script for the Anthropic integration in the Egypt Tourism Chatbot.
This script tests the fallback mechanism using the Anthropic API.
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
from src.services.anthropic_service import AnthropicService
from src.knowledge.rag_pipeline import RAGPipeline

async def test_anthropic_fallback():
    """Test the Anthropic fallback mechanism."""
    # Get the API key from environment variables
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key or api_key == "your-api-key-here":
        logger.error("No valid Anthropic API key found in .env file")
        print("\n⚠️ ERROR: No valid Anthropic API key found in .env file")
        print("Please add your Anthropic API key to the .env file:")
        print("ANTHROPIC_API_KEY=your-actual-api-key\n")
        return
    
    # Create the Anthropic service
    anthropic_service = AnthropicService({
        "anthropic_api_key": api_key,
        "claude_model": os.getenv("CLAUDE_MODEL", "claude-3-7-sonnet-20250219")
    })
    
    # Create a minimal RAG pipeline with just the Anthropic service
    rag_pipeline = RAGPipeline(
        knowledge_base=None,
        vector_db=None,
        embedding_model=None,
        llm_service=anthropic_service
    )
    
    # Test queries
    test_queries = [
        "What are the best times to visit the pyramids?",
        "Tell me about Egyptian cuisine",
        "What should I know about safety when traveling in Egypt?",
        "How do I get from Cairo to Luxor?"
    ]
    
    print("\n🧪 Testing Anthropic LLM fallback mechanism...\n")
    
    for query in test_queries:
        print(f"📝 Query: {query}")
        
        # Use the fallback response method directly
        response = rag_pipeline._get_fallback_response(
            language="en",
            query=query,
            session_data=None
        )
        
        # Print the response
        print(f"🤖 Response: {response.get('text', 'No response')[:200]}...\n")
        
        # Add a small delay to avoid rate limiting
        await asyncio.sleep(1)
    
    print("✅ Anthropic LLM fallback test completed!")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_anthropic_fallback())
