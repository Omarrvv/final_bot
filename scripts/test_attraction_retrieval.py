#!/usr/bin/env python3
"""
Test Attraction Retrieval Script

This script verifies that attraction data can be retrieved from the PostgreSQL database
through the Knowledge Base component.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set USE_NEW_KB to true to ensure we're using the database
os.environ["USE_NEW_KB"] = "true"
os.environ["USE_POSTGRES"] = "true"

# Import required components
from src.utils.factory import component_factory
from src.knowledge.knowledge_base import KnowledgeBase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Define test attractions
TEST_ATTRACTIONS = [
    "Pyramids of Giza",
    "Great Sphinx",
    "Valley of the Kings",
    "Karnak Temple",
    "Abu Simbel",
    # Add a test for a non-existent attraction
    "Non-existent Attraction"
]

def print_attraction_details(attraction):
    """Print detailed information about an attraction."""
    if not attraction:
        print("  No information found\n")
        return
        
    print(f"  ID: {attraction.get('id')}")
    print(f"  Name (EN): {attraction.get('name_en')}")
    print(f"  City: {attraction.get('city')}")
    
    # Extract descriptions with fallbacks
    description = attraction.get('description_en')
    if not description and 'description' in attraction:
        # Handle nested structure
        description = attraction.get('description', {}).get('en', 'No description available')
    
    print(f"  Description: {description[:100]}..." if len(description or '') > 100 else f"  Description: {description}")
    
    # Check data source
    source = attraction.get('source', 'database')
    print(f"  Source: {source}")
    
    # Print some additional data if available
    if 'data' in attraction and attraction['data']:
        data = attraction['data']
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                pass
                
        if isinstance(data, dict):
            if 'opening_hours' in data:
                print(f"  Opening Hours: {data.get('opening_hours')}")
            if 'entry_fee' in data:
                if isinstance(data['entry_fee'], dict):
                    print(f"  Entry Fee: {json.dumps(data['entry_fee'], indent=2)}")
                else:
                    print(f"  Entry Fee: {data.get('entry_fee')}")
    
    print("")  # Empty line for readability

def test_knowledge_base_retrieval():
    """Test retrieving attraction data from the Knowledge Base."""
    print("\n=== Testing Knowledge Base Attraction Retrieval ===\n")
    
    # Initialize the component factory
    component_factory.initialize()
    
    # Create knowledge base
    knowledge_base = component_factory.create_knowledge_base()
    
    if not knowledge_base:
        logger.error("Failed to create Knowledge Base instance")
        return False
        
    print(f"Knowledge Base type: {type(knowledge_base).__name__}")
        
    # Test attraction retrieval
    success_count = 0
    database_retrieval_count = 0
    
    for attraction_name in TEST_ATTRACTIONS:
        print(f"\nLooking up: '{attraction_name}'")
        
        # Try to retrieve the attraction
        attraction = knowledge_base.lookup_attraction(attraction_name)
        
        if attraction:
            print(f"Found attraction: {attraction_name}")
            print_attraction_details(attraction)
            success_count += 1
            
            # Check if this came from the database or hardcoded data
            if attraction.get('source') != 'hardcoded':
                database_retrieval_count += 1
                print("  ✓ Retrieved from database")
            else:
                print("  ✗ Retrieved from hardcoded fallback data")
        else:
            print(f"No information found for: {attraction_name}")
    
    # Print summary
    print("\n=== Summary ===")
    print(f"Total attractions tested: {len(TEST_ATTRACTIONS)}")
    print(f"Successfully retrieved: {success_count}")
    print(f"Retrieved from database: {database_retrieval_count}")
    print(f"Retrieved from hardcoded data: {success_count - database_retrieval_count}")
    print(f"Not found: {len(TEST_ATTRACTIONS) - success_count}")
    
    # Success if we retrieved at least one attraction from the database
    return database_retrieval_count > 0

if __name__ == "__main__":
    success = test_knowledge_base_retrieval()
    sys.exit(0 if success else 1) 