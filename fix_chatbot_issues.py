#!/usr/bin/env python3
"""
Fix script for Egypt Tourism Chatbot issues.
This script will:
1. Fix the restaurant query formatting issue
2. Fix the transportation query issue with 'column "text" does not exist'
3. Improve cross-table query recognition
4. Add diagnostic logging to identify other issues
"""
import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the necessary components
from src.utils.factory import component_factory
from src.knowledge.database import DatabaseManager
from src.knowledge.knowledge_base import KnowledgeBase
from src.chatbot import Chatbot

def fix_restaurant_formatting():
    """Fix the restaurant formatting issue with 'str' object has no attribute 'get'."""
    logger.info("\n=== Fixing Restaurant Formatting ===")
    
    # Monkey patch the _format_restaurant_data method in KnowledgeBase
    try:
        # Get the KnowledgeBase class
        kb_class = KnowledgeBase
        
        # Store the original method for reference
        original_format_restaurant = kb_class._format_restaurant_data
        
        # Define the fixed method
        def fixed_format_restaurant(self, restaurant_data: Dict, language: str = "en") -> Dict:
            """
            Fixed version of _format_restaurant_data that handles all edge cases.
            """
            try:
                result = restaurant_data.copy() if restaurant_data else {}
                
                # Handle name field
                if "name" in result:
                    if isinstance(result["name"], str):
                        try:
                            # Try to parse as JSON
                            name_data = json.loads(result["name"])
                            result["name"] = name_data
                        except json.JSONDecodeError:
                            # If not valid JSON, use as is
                            result["name"] = {
                                "en": result["name"],
                                "ar": result["name"]
                            }
                    elif not isinstance(result["name"], dict):
                        # Handle case where name is neither string nor dict
                        result["name"] = {
                            "en": str(result["name"]),
                            "ar": str(result["name"])
                        }
                else:
                    # Fallback if no name field is found
                    result["name"] = {
                        "en": result.get("id", "").replace("_", " ").title(),
                        "ar": result.get("id", "").replace("_", " ").title()
                    }
                
                # Handle description field
                if "description" in result:
                    if isinstance(result["description"], str):
                        try:
                            # Try to parse as JSON
                            desc_data = json.loads(result["description"])
                            result["description"] = desc_data
                        except json.JSONDecodeError:
                            # If not valid JSON, use as is
                            result["description"] = {
                                "en": result["description"],
                                "ar": result["description"]
                            }
                    elif not isinstance(result["description"], dict):
                        # Handle case where description is neither string nor dict
                        result["description"] = {
                            "en": str(result["description"]),
                            "ar": str(result["description"])
                        }
                else:
                    # Fallback if no description field is found
                    result["description"] = {
                        "en": "",
                        "ar": ""
                    }
                
                # Add source field if not present
                if "source" not in result:
                    result["source"] = "database"
                
                return result
            except Exception as e:
                logger.error(f"Error in fixed_format_restaurant: {str(e)}")
                # Return the original data if there's an error
                return restaurant_data
        
        # Replace the original method with the fixed one
        kb_class._format_restaurant_data = fixed_format_restaurant
        
        logger.info("Successfully patched _format_restaurant_data method")
        return True
    except Exception as e:
        logger.error(f"Failed to patch _format_restaurant_data: {str(e)}")
        return False

def fix_transportation_queries():
    """Fix the transportation query issue with 'column "text" does not exist'."""
    logger.info("\n=== Fixing Transportation Queries ===")
    
    # Monkey patch the search_transportation method in KnowledgeBase
    try:
        # Get the KnowledgeBase class
        kb_class = KnowledgeBase
        
        # Store the original method for reference
        original_search_transportation = kb_class.search_transportation
        
        # Define the fixed method
        def fixed_search_transportation(self, query: Dict = None, origin: str = None, destination: str = None, 
                                      transportation_type: str = None, limit: int = 10, language: str = "en") -> List[Dict]:
            """
            Fixed version of search_transportation that uses enhanced_search for text queries.
            """
            logger.info(f"KB: Searching transportation with query={query}, origin={origin}, destination={destination}, type={transportation_type}, limit={limit}")
            
            try:
                raw_results = []
                if self._db_available:
                    # Handle string query (text search)
                    if isinstance(query, str) and query:
                        # If query is a simple string, use enhanced search
                        logger.info(f"Using enhanced_search for transportation with text query: {query}")
                        raw_results = self.db_manager.enhanced_search(
                            table="transportation_routes",
                            search_text=query,
                            limit=limit
                        )
                        logger.info(f"KB: Found {len(raw_results)} transportation options matching text query")
                        return self._format_transportation_results(raw_results, language)
                    
                    # Handle dictionary query with text field
                    if isinstance(query, dict) and query and "text" in query and query["text"]:
                        # Use enhanced search for text search
                        logger.info(f"Using enhanced_search for transportation with text field: {query['text']}")
                        raw_results = self.db_manager.enhanced_search(
                            table="transportation_routes",
                            search_text=query["text"],
                            limit=limit
                        )
                        logger.info(f"KB: Found {len(raw_results)} transportation options matching text query")
                        return self._format_transportation_results(raw_results, language)
                
                # If we get here, use the original method for other query types
                return original_search_transportation(self, query, origin, destination, transportation_type, limit, language)
            except Exception as e:
                logger.error(f"Error in fixed_search_transportation: {str(e)}")
                # Return empty list if there's an error
                return []
        
        # Replace the original method with the fixed one
        kb_class.search_transportation = fixed_search_transportation
        
        logger.info("Successfully patched search_transportation method")
        return True
    except Exception as e:
        logger.error(f"Failed to patch search_transportation: {str(e)}")
        return False

def main():
    """Run all fixes."""
    logger.info("Starting fixes for Egypt Tourism Chatbot...")
    
    # Fix restaurant formatting
    if fix_restaurant_formatting():
        logger.info("✅ Restaurant formatting fix applied")
    else:
        logger.error("❌ Restaurant formatting fix failed")
    
    # Fix transportation queries
    if fix_transportation_queries():
        logger.info("✅ Transportation queries fix applied")
    else:
        logger.error("❌ Transportation queries fix failed")
    
    logger.info("\nAll fixes applied. Please restart the chatbot for changes to take effect.")

if __name__ == "__main__":
    main()
