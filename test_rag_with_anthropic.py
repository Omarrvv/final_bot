#!/usr/bin/env python3
"""
Test script for the RAG pipeline with Anthropic fallback in the Egypt Tourism Chatbot.
This script tests the RAG pipeline's ability to use Anthropic as a fallback.
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

async def test_rag_with_anthropic():
    """Test the RAG pipeline with Anthropic fallback."""
    print("\n🧪 Testing RAG Pipeline with Anthropic fallback...\n")
    
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
    
    # Test queries that are likely to trigger the fallback mechanism
    test_queries = [
        "What's the best way to handle tipping in Egypt?",
        "Can you recommend some lesser-known historical sites near Aswan?",
        "What should I know about Egyptian wedding traditions?",
        "How has climate change affected tourism in Egypt?"
    ]
    
    for query in test_queries:
        print(f"📝 Query: {query}")
        
        # Process the query through the general processing method
        # This will trigger the fallback since we have no vector DB or embedding model
        response = rag_pipeline._process_general_query(
            query=query,
            intent="general_query",
            context={},
            language="en"
        )
        
        # Print the response
        print(f"🤖 Response: {response.get('text', 'No response')[:300]}...\n")
        
        # Add a small delay to avoid rate limiting
        await asyncio.sleep(1)
    
    print("✅ RAG Pipeline with Anthropic fallback test completed!")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_rag_with_anthropic())
