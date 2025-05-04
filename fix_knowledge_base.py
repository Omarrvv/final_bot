#!/usr/bin/env python3
"""
Fix script for KnowledgeBase methods to match PostgresqlDatabaseManager parameter names
"""

import logging
from src.knowledge.knowledge_base import KnowledgeBase
from src.utils.postgres_database import PostgresqlDatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_search_restaurants_method():
    """Fix the search_restaurants method in KnowledgeBase"""
    logger.info("Fixing search_restaurants method in KnowledgeBase")
    
    # Create a subclass of KnowledgeBase with fixed methods
    class FixedKnowledgeBase(KnowledgeBase):
        def search_restaurants(self, query=None, limit=10, language="en"):
            """
            Fixed search_restaurants method that matches PostgresqlDatabaseManager parameter names
            """
            logger.debug(f"KB: Searching restaurants with query: {query}, limit: {limit}")

            try:
                raw_results = []
                if isinstance(query, str) and query:
                    # If query is a simple string, use enhanced search
                    raw_results = self.db_manager.enhanced_search(
                        table="restaurants",
                        search_text=query,
                        limit=limit
                    )
                    logger.info(f"KB: Found {len(raw_results)} restaurants matching text query")
                elif isinstance(query, dict):
                    # If query is a structured dict, use regular search with filters parameter
                    raw_results = self.db_manager.search_restaurants(filters=query, limit=limit)
                    logger.info(f"KB: Found {len(raw_results)} restaurants matching structured query")
                else:
                    # If no query, return all restaurants up to limit
                    try:
                        # Try to get all restaurants
                        raw_results = self.db_manager.search_restaurants(filters={}, limit=limit)
                    except Exception as e:
                        logger.error(f"Error getting all restaurants: {e}")
                        raw_results = []
                    logger.info(f"KB: Retrieved {len(raw_results)} restaurants (no query)")

                # Format the results using our formatter
                formatted_results = []
                for restaurant in raw_results:
                    formatted_results.append(self._format_restaurant_data(restaurant, language))

                return formatted_results

            except Exception as e:
                logger.error(f"Error searching restaurants: {str(e)}", exc_info=True)
                return []
        
        def search_hotels(self, query=None, limit=10, language="en"):
            """
            Fixed search_hotels method that matches PostgresqlDatabaseManager parameter names
            """
            logger.debug(f"KB: Searching hotels with query: {query}, limit: {limit}")

            try:
                raw_results = []
                if isinstance(query, str) and query:
                    # If query is a simple string, use enhanced search
                    raw_results = self.db_manager.enhanced_search(
                        table="accommodations",
                        search_text=query,
                        limit=limit
                    )
                    logger.info(f"KB: Found {len(raw_results)} accommodations matching text query")
                elif isinstance(query, dict):
                    # If query is a structured dict, use regular search with filters parameter
                    raw_results = self.db_manager.search_hotels(filters=query, limit=limit)
                    logger.info(f"KB: Found {len(raw_results)} accommodations matching structured query")
                else:
                    # If no query, return all accommodations up to limit
                    try:
                        # Try to get all accommodations
                        raw_results = self.db_manager.search_hotels(filters={}, limit=limit)
                    except Exception as e:
                        logger.error(f"Error getting all accommodations: {e}")
                        raw_results = []
                    logger.info(f"KB: Retrieved {len(raw_results)} accommodations (no query)")

                # Format the results using our formatter
                formatted_results = []
                for hotel in raw_results:
                    formatted_results.append(self._format_accommodation_data(hotel, language))

                return formatted_results

            except Exception as e:
                logger.error(f"Error searching hotels: {str(e)}", exc_info=True)
                return []
    
    # Return the fixed class
    return FixedKnowledgeBase

def test_fixed_methods():
    """Test the fixed methods"""
    logger.info("Testing fixed methods")
    
    # Get the fixed class
    FixedKnowledgeBase = fix_search_restaurants_method()
    
    # Create instances
    db = PostgresqlDatabaseManager()
    kb = FixedKnowledgeBase(db)
    
    # Test search_restaurants
    logger.info("Testing search_restaurants")
    restaurants = kb.search_restaurants(limit=5)
    logger.info(f"Found {len(restaurants)} restaurants")
    
    # Test search_hotels
    logger.info("Testing search_hotels")
    hotels = kb.search_hotels(limit=5)
    logger.info(f"Found {len(hotels)} hotels")
    
    return len(restaurants) > 0 or len(hotels) > 0

if __name__ == "__main__":
    success = test_fixed_methods()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")
    
    if success:
        print("\nTo fix the KnowledgeBase methods, update the following methods in src/knowledge/knowledge_base.py:")
        print("1. search_restaurants - Change 'query=query' to 'filters=query'")
        print("2. search_hotels - Change 'query=query' to 'filters=query'")
    else:
        print("\nFix not successful. Please check the logs for details.")
