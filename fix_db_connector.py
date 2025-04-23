#!/usr/bin/env python
"""
Database Connector Fix Script for Egypt Tourism Chatbot

This script patches any inconsistencies or missing methods in the DatabaseManager
and KnowledgeBase classes to ensure the connection between them works properly.
"""
import os
import sys
import logging
import importlib
import types
import inspect
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Load environment variables
logger.info("Loading environment variables")
load_dotenv()

def patch_database_manager():
    """Patch the DatabaseManager class with any missing methods."""
    try:
        # Import the database module
        from src.knowledge.database import DatabaseManager
        from src.utils.database import DatabaseManager as SQLiteDatabaseManager
        
        logger.info("Analyzing DatabaseManager classes")
        
        # Check if methods are missing or inconsistent
        issues_fixed = 0
        
        # Common method names that might have inconsistencies
        method_mappings = {
            # Search methods
            "search_attractions": "search_attractions",
            "search_accommodations": "search_hotels",
            "search_restaurants": "search_restaurants",
            "search_cities": "search_cities",
            
            # Get by ID methods
            "get_attraction_by_id": "get_attraction",
            "get_attraction": "get_attraction_by_id",
            "get_hotel_by_id": "get_accommodation",
            "get_accommodation_by_id": "get_hotel",
            "get_restaurant_by_id": "get_restaurant",
            "get_restaurant": "get_restaurant_by_id",
            "get_city_by_id": "get_city",
            "get_city": "get_city_by_id",
            
            # Get all methods
            "get_all_attractions": "get_attractions",
            "get_attractions": "get_all_attractions",
            "get_all_hotels": "get_all_accommodations",
            "get_all_accommodations": "get_all_hotels",
            "get_all_restaurants": "get_restaurants",
            "get_restaurants": "get_all_restaurants",
        }
        
        # Get all existing methods in DatabaseManager
        existing_methods = set(method[0] for method in inspect.getmembers(DatabaseManager, predicate=inspect.isfunction))
        
        # Check each mapping and patch if necessary
        for method_name, alias_name in method_mappings.items():
            if method_name not in existing_methods and alias_name in existing_methods:
                # Method is missing but alias exists, create an alias
                logger.info(f"Creating alias: {method_name} -> {alias_name}")
                
                # Get the original method
                original_method = getattr(DatabaseManager, alias_name)
                
                # Create a wrapper function that calls the original
                def create_method_wrapper(orig_method, orig_name):
                    def wrapper(self, *args, **kwargs):
                        logger.debug(f"Calling {orig_name} via wrapper")
                        return getattr(self, orig_name)(*args, **kwargs)
                    wrapper.__name__ = method_name
                    wrapper.__doc__ = f"Alias for {orig_name}. {original_method.__doc__}"
                    return wrapper
                
                # Add the method to the class
                setattr(DatabaseManager, method_name, 
                        create_method_wrapper(original_method, alias_name))
                
                issues_fixed += 1
        
        # Specifically check for search_accommodations which is often missing
        if "search_accommodations" not in existing_methods and "search_hotels" in existing_methods:
            logger.info("Adding search_accommodations alias for search_hotels")
            
            # Define a wrapper for search_accommodations
            def search_accommodations(self, query=None, limit=10, offset=0):
                """
                Search accommodations (alias for search_hotels).
                
                Args:
                    query: Search query or filters
                    limit: Maximum number of results
                    offset: Result offset for pagination
                    
                Returns:
                    List of accommodations matching the query
                """
                logger.debug("Redirecting search_accommodations to search_hotels")
                return self.search_hotels(query=query, limit=limit, offset=offset)
            
            # Add the method to the class
            setattr(DatabaseManager, "search_accommodations", search_accommodations)
            issues_fixed += 1
        
        logger.info(f"Fixed {issues_fixed} method inconsistencies in DatabaseManager")
        return issues_fixed > 0
        
    except ImportError as e:
        logger.error(f"Failed to import database modules: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error patching DatabaseManager: {str(e)}", exc_info=True)
        return False

def patch_knowledge_base():
    """Patch the KnowledgeBase class with any missing methods."""
    try:
        # Import the knowledge base module
        from src.knowledge.knowledge_base import KnowledgeBase
        
        logger.info("Analyzing KnowledgeBase class")
        
        # Check if methods are missing or inconsistent
        issues_fixed = 0
        
        # Common method names that might be inconsistent
        method_mappings = {
            "search_attractions": "lookup_attraction",
            "get_attraction_by_id": "lookup_attraction",
            "search_restaurants": "lookup_restaurant",
            "get_restaurant_by_id": "lookup_restaurant",
            "search_hotels": "lookup_hotel",
            "get_hotel_by_id": "lookup_hotel",
        }
        
        # Get all existing methods in KnowledgeBase
        existing_methods = set(method[0] for method in inspect.getmembers(KnowledgeBase, predicate=inspect.isfunction))
        
        # Add specific methods that are commonly missing
        if "_check_db_connection" not in existing_methods:
            logger.info("Adding _check_db_connection method to KnowledgeBase")
            
            def _check_db_connection(self):
                """Check if database connection is available."""
                try:
                    if hasattr(self, 'db_manager') and self.db_manager:
                        # Try a simple connection test
                        logger.debug("Testing database connection")
                        return self.db_manager.connect()
                    return False
                except Exception as e:
                    logger.error(f"Database connection check failed: {str(e)}")
                    return False
            
            setattr(KnowledgeBase, "_check_db_connection", _check_db_connection)
            issues_fixed += 1
        
        # Ensure the _db_available flag is set correctly in __init__
        original_init = KnowledgeBase.__init__
        
        def new_init(self, *args, **kwargs):
            """Patched __init__ method to ensure _db_available is set."""
            # Call the original __init__
            original_init(self, *args, **kwargs)
            
            # Ensure _db_available is set
            if not hasattr(self, '_db_available'):
                logger.info("Setting _db_available flag in KnowledgeBase")
                self._db_available = self._check_db_connection()
            
            # Double-check db_manager connectivity
            if hasattr(self, 'db_manager') and self.db_manager:
                if not self._db_available:
                    logger.warning("Database connection not available, attempting to connect...")
                    try:
                        self.db_manager.connect()
                        self._db_available = True
                        logger.info("Successfully connected to database")
                    except Exception as e:
                        logger.error(f"Failed to connect to database: {str(e)}")
        
        # Replace the __init__ method
        setattr(KnowledgeBase, "__init__", new_init)
        issues_fixed += 1
        
        logger.info(f"Fixed {issues_fixed} method inconsistencies in KnowledgeBase")
        return issues_fixed > 0
        
    except ImportError as e:
        logger.error(f"Failed to import knowledge base module: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error patching KnowledgeBase: {str(e)}", exc_info=True)
        return False

def verify_database_access():
    """Verify that database access works correctly."""
    try:
        # Import the necessary modules
        from src.utils.factory import component_factory
        
        logger.info("Initializing component factory")
        component_factory.initialize()
        
        logger.info("Creating database manager")
        db_manager = component_factory.create_database_manager()
        
        logger.info("Testing database connection")
        db_manager.connect()
        
        # Try a simple query
        logger.info("Testing simple database query")
        try:
            # Check if attractions table exists
            if db_manager._table_exists("attractions"):
                # Get all attractions
                attractions = db_manager.get_all_attractions(limit=5)
                logger.info(f"Successfully retrieved {len(attractions)} attractions")
                return True
            else:
                logger.warning("Attractions table does not exist")
                return False
        except Exception as e:
            logger.error(f"Database query failed: {str(e)}")
            return False
            
    except ImportError as e:
        logger.error(f"Failed to import necessary modules: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error verifying database access: {str(e)}", exc_info=True)
        return False

def main():
    """Main function to patch and verify database connectivity."""
    try:
        logger.info("Starting database connector fix script")
        
        # Patch DatabaseManager
        db_manager_fixed = patch_database_manager()
        logger.info(f"DatabaseManager patching {'successful' if db_manager_fixed else 'not needed'}")
        
        # Patch KnowledgeBase
        kb_fixed = patch_knowledge_base()
        logger.info(f"KnowledgeBase patching {'successful' if kb_fixed else 'not needed'}")
        
        # Verify database access
        db_access = verify_database_access()
        logger.info(f"Database access verification {'successful' if db_access else 'failed'}")
        
        if db_access:
            logger.info("Database connector fix script completed successfully")
            return 0
        else:
            logger.error("Database connector fix script completed with errors")
            return 1
            
    except Exception as e:
        logger.error(f"Error in database connector fix script: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 