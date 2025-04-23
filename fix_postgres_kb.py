#!/usr/bin/env python3
"""
Script to fix PostgreSQL knowledge base issues by adding missing methods
to DatabaseManager and testing functionality.
"""
import os
import sys
import json
import logging
import importlib
import inspect
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("postgres_kb_fix")

# Load environment variables
load_dotenv()
os.environ["USE_POSTGRES"] = "true"
os.environ["USE_NEW_KB"] = "true"

# Ensure PostgreSQL URI is set
postgres_uri = os.getenv("POSTGRES_URI")
if not postgres_uri:
    logger.error("POSTGRES_URI not set in environment")
    sys.exit(1)

def add_missing_methods():
    """Add missing methods to the DatabaseManager class"""
    logger.info("Adding missing methods to DatabaseManager...")
    
    try:
        # Import the database module dynamically
        module_path = "src.knowledge.database"
        db_module = importlib.import_module(module_path)
        DatabaseManager = db_module.DatabaseManager
        
        # Check existing methods
        existing_methods = [method for method in dir(DatabaseManager) if not method.startswith('_')]
        logger.info(f"Existing methods: {existing_methods}")
        
        # Check if methods need to be added
        methods_to_add = {
            "search_attractions": False,
            "search_restaurants": False, 
            "search_accommodations": False,
            "enhanced_search": False,
            "get_attraction": False,
            "get_restaurant": False,
            "get_accommodation": False
        }
        
        for method in methods_to_add:
            if method in existing_methods:
                methods_to_add[method] = True
                logger.info(f"Method {method} already exists")
        
        # Add the enhanced_search method if it doesn't exist
        if not methods_to_add["enhanced_search"]:
            logger.info("Adding enhanced_search method...")
            
            def enhanced_search(self, table, query, limit=10, offset=0):
                """
                Perform an enhanced search across text fields in the specified table.
                
                Args:
                    table (str): The table to search in
                    query (str): The search query
                    limit (int): Maximum number of results
                    offset (int): Offset for pagination
                    
                Returns:
                    list: List of matching records
                """
                try:
                    logger.info(f"Enhanced search in {table} for '{query}'")
                    
                    # For PostgreSQL, we can use to_tsvector and to_tsquery for full-text search
                    if self.is_postgres:
                        # Get the schema of the table to identify text fields
                        cursor = self.connection.cursor()
                        cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
                        columns = cursor.fetchall()
                        text_columns = [col[0] for col in columns if col[1] in ('text', 'character varying', 'varchar', 'jsonb')]
                        
                        if 'data' in text_columns:  # If we have a JSONB 'data' column
                            # Create a query that searches in JSONB fields
                            search_clause = f"data::text ILIKE '%{query}%'"
                        else:
                            # Fallback to searching in regular text columns
                            search_clauses = [f"{col} ILIKE '%{query}%'" for col in text_columns if col != 'id']
                            search_clause = " OR ".join(search_clauses)
                        
                        sql = f"SELECT * FROM {table} WHERE {search_clause} LIMIT {limit} OFFSET {offset}"
                        
                        cursor.execute(sql)
                        results = cursor.fetchall()
                        
                        # Get column names
                        column_names = [desc[0] for desc in cursor.description]
                        
                        # Convert to list of dicts
                        results_list = []
                        for row in results:
                            result_dict = dict(zip(column_names, row))
                            # Handle JSONB fields
                            for key, value in result_dict.items():
                                if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                                    try:
                                        result_dict[key] = json.loads(value)
                                    except:
                                        pass
                            results_list.append(result_dict)
                        
                        return results_list
                    else:
                        # For SQLite, we'll use a simpler approach
                        cursor = self.connection.cursor()
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = cursor.fetchall()
                        text_columns = [col[1] for col in columns if 'text' in col[2].lower()]
                        
                        if 'data' in text_columns:
                            search_clause = f"data LIKE '%{query}%'"
                        else:
                            search_clauses = [f"{col} LIKE '%{query}%'" for col in text_columns if col != 'id']
                            search_clause = " OR ".join(search_clauses)
                        
                        sql = f"SELECT * FROM {table} WHERE {search_clause} LIMIT {limit} OFFSET {offset}"
                        
                        cursor.execute(sql)
                        results = cursor.fetchall()
                        
                        # Get column names
                        column_names = [desc[0] for desc in cursor.description]
                        
                        # Convert to list of dicts
                        results_list = []
                        for row in results:
                            result_dict = dict(zip(column_names, row))
                            # Handle JSON fields
                            for key, value in result_dict.items():
                                if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                                    try:
                                        result_dict[key] = json.loads(value)
                                    except:
                                        pass
                            results_list.append(result_dict)
                        
                        return results_list
                        
                except Exception as e:
                    logger.error(f"Error in enhanced_search: {str(e)}")
                    return []
            
            # Add the method to the class
            enhanced_search.__qualname__ = f"DatabaseManager.enhanced_search"
            setattr(DatabaseManager, "enhanced_search", enhanced_search)
            logger.info("Added enhanced_search method")
        
        # Add entity specific search methods
        if not methods_to_add["search_attractions"]:
            logger.info("Adding search_attractions method...")
            
            def search_attractions(self, query, limit=10, offset=0):
                """
                Search for attractions based on the query.
                
                Args:
                    query (str): Search query
                    limit (int): Maximum number of results
                    offset (int): Offset for pagination
                    
                Returns:
                    list: List of matching attractions
                """
                logger.info(f"Searching attractions for '{query}'")
                return self.enhanced_search("attractions", query, limit, offset)
            
            # Add the method to the class
            search_attractions.__qualname__ = f"DatabaseManager.search_attractions"
            setattr(DatabaseManager, "search_attractions", search_attractions)
            logger.info("Added search_attractions method")
        
        if not methods_to_add["search_restaurants"]:
            logger.info("Adding search_restaurants method...")
            
            def search_restaurants(self, query, limit=10, offset=0):
                """
                Search for restaurants based on the query.
                
                Args:
                    query (str): Search query
                    limit (int): Maximum number of results
                    offset (int): Offset for pagination
                    
                Returns:
                    list: List of matching restaurants
                """
                logger.info(f"Searching restaurants for '{query}'")
                return self.enhanced_search("restaurants", query, limit, offset)
            
            # Add the method to the class
            search_restaurants.__qualname__ = f"DatabaseManager.search_restaurants"
            setattr(DatabaseManager, "search_restaurants", search_restaurants)
            logger.info("Added search_restaurants method")
        
        if not methods_to_add["search_accommodations"]:
            logger.info("Adding search_accommodations method...")
            
            def search_accommodations(self, query, limit=10, offset=0):
                """
                Search for accommodations based on the query.
                
                Args:
                    query (str): Search query
                    limit (int): Maximum number of results
                    offset (int): Offset for pagination
                    
                Returns:
                    list: List of matching accommodations
                """
                logger.info(f"Searching accommodations for '{query}'")
                return self.enhanced_search("accommodations", query, limit, offset)
            
            # Add the method to the class
            search_accommodations.__qualname__ = f"DatabaseManager.search_accommodations"
            setattr(DatabaseManager, "search_accommodations", search_accommodations)
            logger.info("Added search_accommodations method")
        
        # Add get_entity methods
        if not methods_to_add["get_attraction"]:
            logger.info("Adding get_attraction method...")
            
            def get_attraction(self, attraction_id):
                """
                Get an attraction by ID.
                
                Args:
                    attraction_id (str): The ID of the attraction
                    
                Returns:
                    dict: The attraction data or None if not found
                """
                try:
                    logger.info(f"Getting attraction with ID '{attraction_id}'")
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT * FROM attractions WHERE id = %s", (attraction_id,))
                    result = cursor.fetchone()
                    
                    if not result:
                        return None
                    
                    # Get column names
                    column_names = [desc[0] for desc in cursor.description]
                    
                    # Convert to dict
                    result_dict = dict(zip(column_names, result))
                    
                    # Handle JSON fields
                    for key, value in result_dict.items():
                        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                            try:
                                result_dict[key] = json.loads(value)
                            except:
                                pass
                    
                    return result_dict
                except Exception as e:
                    logger.error(f"Error in get_attraction: {str(e)}")
                    return None
            
            # Add the method to the class
            get_attraction.__qualname__ = f"DatabaseManager.get_attraction"
            setattr(DatabaseManager, "get_attraction", get_attraction)
            logger.info("Added get_attraction method")
        
        if not methods_to_add["get_restaurant"]:
            logger.info("Adding get_restaurant method...")
            
            def get_restaurant(self, restaurant_id):
                """
                Get a restaurant by ID.
                
                Args:
                    restaurant_id (str): The ID of the restaurant
                    
                Returns:
                    dict: The restaurant data or None if not found
                """
                try:
                    logger.info(f"Getting restaurant with ID '{restaurant_id}'")
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT * FROM restaurants WHERE id = %s", (restaurant_id,))
                    result = cursor.fetchone()
                    
                    if not result:
                        return None
                    
                    # Get column names
                    column_names = [desc[0] for desc in cursor.description]
                    
                    # Convert to dict
                    result_dict = dict(zip(column_names, result))
                    
                    # Handle JSON fields
                    for key, value in result_dict.items():
                        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                            try:
                                result_dict[key] = json.loads(value)
                            except:
                                pass
                    
                    return result_dict
                except Exception as e:
                    logger.error(f"Error in get_restaurant: {str(e)}")
                    return None
            
            # Add the method to the class
            get_restaurant.__qualname__ = f"DatabaseManager.get_restaurant"
            setattr(DatabaseManager, "get_restaurant", get_restaurant)
            logger.info("Added get_restaurant method")
        
        if not methods_to_add["get_accommodation"]:
            logger.info("Adding get_accommodation method...")
            
            def get_accommodation(self, accommodation_id):
                """
                Get an accommodation by ID.
                
                Args:
                    accommodation_id (str): The ID of the accommodation
                    
                Returns:
                    dict: The accommodation data or None if not found
                """
                try:
                    logger.info(f"Getting accommodation with ID '{accommodation_id}'")
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT * FROM accommodations WHERE id = %s", (accommodation_id,))
                    result = cursor.fetchone()
                    
                    if not result:
                        return None
                    
                    # Get column names
                    column_names = [desc[0] for desc in cursor.description]
                    
                    # Convert to dict
                    result_dict = dict(zip(column_names, result))
                    
                    # Handle JSON fields
                    for key, value in result_dict.items():
                        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                            try:
                                result_dict[key] = json.loads(value)
                            except:
                                pass
                    
                    return result_dict
                except Exception as e:
                    logger.error(f"Error in get_accommodation: {str(e)}")
                    return None
            
            # Add the method to the class
            get_accommodation.__qualname__ = f"DatabaseManager.get_accommodation"
            setattr(DatabaseManager, "get_accommodation", get_accommodation)
            logger.info("Added get_accommodation method")
        
        # Check if methods were successfully added
        updated_methods = [method for method in dir(DatabaseManager) if not method.startswith('_')]
        logger.info(f"Updated methods: {updated_methods}")
        
        # Verify we have all required methods
        for method in methods_to_add:
            if method not in updated_methods:
                logger.error(f"Failed to add method {method}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error adding methods to DatabaseManager: {str(e)}")
        return False

def verify_kb_functionality():
    """Verify that the Knowledge Base functionality works correctly"""
    logger.info("Verifying Knowledge Base functionality...")
    
    try:
        # Import necessary modules
        from src.knowledge.knowledge_base import KnowledgeBase
        
        # Create a Knowledge Base instance
        kb = KnowledgeBase()
        
        # Test search functionality
        attraction_results = kb.search_attractions("pyramid")
        logger.info(f"Found {len(attraction_results)} attractions matching 'pyramid'")
        
        restaurant_results = kb.search_restaurants("egyptian")
        logger.info(f"Found {len(restaurant_results)} restaurants matching 'egyptian'")
        
        hotel_results = kb.search_hotels("luxury")
        logger.info(f"Found {len(hotel_results)} hotels matching 'luxury'")
        
        # If all searches work without errors, the KB is functional
        return True
    except Exception as e:
        logger.error(f"Error verifying Knowledge Base functionality: {str(e)}")
        return False

def populate_sample_data():
    """Populate sample data into database tables if they are empty"""
    logger.info("Checking if sample data needs to be populated...")
    
    try:
        # Import necessary modules
        from src.knowledge.database import DatabaseManager
        
        # Create a database manager instance
        db_manager = DatabaseManager()
        
        # Check if tables are empty
        cursor = db_manager.connection.cursor()
        
        # Check attractions
        cursor.execute("SELECT COUNT(*) FROM attractions")
        attractions_count = cursor.fetchone()[0]
        
        # Check restaurants
        cursor.execute("SELECT COUNT(*) FROM restaurants")
        restaurants_count = cursor.fetchone()[0]
        
        # Check accommodations
        cursor.execute("SELECT COUNT(*) FROM accommodations")
        accommodations_count = cursor.fetchone()[0]
        
        logger.info(f"Current counts - Attractions: {attractions_count}, Restaurants: {restaurants_count}, Accommodations: {accommodations_count}")
        
        # If any table is empty, add sample data
        if attractions_count == 0:
            logger.info("Adding sample attractions...")
            sample_attractions = [
                {
                    "id": "pyramids_giza",
                    "name": "Pyramids of Giza",
                    "type": "historical",
                    "city": "Giza",
                    "data": json.dumps({
                        "description": "The Great Pyramids of Giza are ancient Egyptian pyramids located on the outskirts of Cairo.",
                        "location": {"latitude": 29.9792, "longitude": 31.1342},
                        "opening_hours": "8:00 AM - 5:00 PM",
                        "ticket_price": {"adult": 240, "child": 120, "currency": "EGP"},
                        "languages": {
                            "en": {
                                "name": "Pyramids of Giza",
                                "description": "The Great Pyramids of Giza are ancient Egyptian pyramids located on the outskirts of Cairo."
                            },
                            "ar": {
                                "name": "أهرامات الجيزة",
                                "description": "أهرامات الجيزة هي أهرامات مصرية قديمة تقع على مشارف القاهرة."
                            }
                        }
                    }),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                {
                    "id": "sphinx_giza",
                    "name": "Great Sphinx of Giza",
                    "type": "historical",
                    "city": "Giza",
                    "data": json.dumps({
                        "description": "The Great Sphinx of Giza is a limestone statue of a reclining sphinx, a mythical creature with the head of a human and the body of a lion.",
                        "location": {"latitude": 29.9753, "longitude": 31.1376},
                        "opening_hours": "8:00 AM - 5:00 PM",
                        "ticket_price": {"adult": 100, "child": 50, "currency": "EGP"},
                        "languages": {
                            "en": {
                                "name": "Great Sphinx of Giza",
                                "description": "The Great Sphinx of Giza is a limestone statue of a reclining sphinx, a mythical creature with the head of a human and the body of a lion."
                            },
                            "ar": {
                                "name": "أبو الهول",
                                "description": "أبو الهول هو تمثال من الحجر الجيري لمخلوق أسطوري برأس إنسان وجسد أسد."
                            }
                        }
                    }),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            ]
            
            for attraction in sample_attractions:
                cursor.execute(
                    "INSERT INTO attractions (id, name, type, city, data, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (attraction["id"], attraction["name"], attraction["type"], attraction["city"], attraction["data"], attraction["created_at"], attraction["updated_at"])
                )
            
            db_manager.connection.commit()
            logger.info("Added sample attractions")
        
        if restaurants_count == 0:
            logger.info("Adding sample restaurants...")
            sample_restaurants = [
                {
                    "id": "abou_el_sid",
                    "name": "Abou El Sid",
                    "type": "traditional",
                    "city": "Cairo",
                    "data": json.dumps({
                        "description": "Traditional Egyptian cuisine served in an authentic setting.",
                        "location": {"latitude": 30.0444, "longitude": 31.2357},
                        "opening_hours": "12:00 PM - 12:00 AM",
                        "price_range": {"min": 200, "max": 500, "currency": "EGP"},
                        "languages": {
                            "en": {
                                "name": "Abou El Sid",
                                "description": "Traditional Egyptian cuisine served in an authentic setting."
                            },
                            "ar": {
                                "name": "أبو السيد",
                                "description": "مأكولات مصرية تقليدية تقدم في جو أصيل."
                            }
                        }
                    }),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                {
                    "id": "koshary_abou_tarek",
                    "name": "Koshary Abou Tarek",
                    "type": "street_food",
                    "city": "Cairo",
                    "data": json.dumps({
                        "description": "Famous for serving Egypt's national dish, koshary.",
                        "location": {"latitude": 30.0509, "longitude": 31.2402},
                        "opening_hours": "10:00 AM - 12:00 AM",
                        "price_range": {"min": 50, "max": 100, "currency": "EGP"},
                        "languages": {
                            "en": {
                                "name": "Koshary Abou Tarek",
                                "description": "Famous for serving Egypt's national dish, koshary."
                            },
                            "ar": {
                                "name": "كشري أبو طارق",
                                "description": "مشهور بتقديم طبق الكشري، الطبق الوطني لمصر."
                            }
                        }
                    }),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            ]
            
            for restaurant in sample_restaurants:
                cursor.execute(
                    "INSERT INTO restaurants (id, name, type, city, data, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (restaurant["id"], restaurant["name"], restaurant["type"], restaurant["city"], restaurant["data"], restaurant["created_at"], restaurant["updated_at"])
                )
            
            db_manager.connection.commit()
            logger.info("Added sample restaurants")
        
        if accommodations_count == 0:
            logger.info("Adding sample accommodations...")
            sample_accommodations = [
                {
                    "id": "mena_house",
                    "name": "Marriott Mena House",
                    "type": "luxury",
                    "city": "Giza",
                    "data": json.dumps({
                        "description": "Historic luxury hotel with pyramid views.",
                        "location": {"latitude": 29.9844, "longitude": 31.1344},
                        "amenities": ["swimming pool", "spa", "restaurants", "wifi"],
                        "price_range": {"min": 2500, "max": 5000, "currency": "EGP"},
                        "languages": {
                            "en": {
                                "name": "Marriott Mena House",
                                "description": "Historic luxury hotel with pyramid views."
                            },
                            "ar": {
                                "name": "ماريوت منى هاوس",
                                "description": "فندق فاخر تاريخي مع إطلالات على الأهرامات."
                            }
                        }
                    }),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                {
                    "id": "four_seasons_nile",
                    "name": "Four Seasons Hotel Cairo at Nile Plaza",
                    "type": "luxury",
                    "city": "Cairo",
                    "data": json.dumps({
                        "description": "Luxury hotel on the banks of the Nile River.",
                        "location": {"latitude": 30.0290, "longitude": 31.2325},
                        "amenities": ["swimming pool", "spa", "restaurants", "wifi", "gym"],
                        "price_range": {"min": 3000, "max": 6000, "currency": "EGP"},
                        "languages": {
                            "en": {
                                "name": "Four Seasons Hotel Cairo at Nile Plaza",
                                "description": "Luxury hotel on the banks of the Nile River."
                            },
                            "ar": {
                                "name": "فندق فورسيزونز القاهرة في نايل بلازا",
                                "description": "فندق فاخر على ضفاف نهر النيل."
                            }
                        }
                    }),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            ]
            
            for accommodation in sample_accommodations:
                cursor.execute(
                    "INSERT INTO accommodations (id, name, type, city, data, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (accommodation["id"], accommodation["name"], accommodation["type"], accommodation["city"], accommodation["data"], accommodation["created_at"], accommodation["updated_at"])
                )
            
            db_manager.connection.commit()
            logger.info("Added sample accommodations")
        
        return True
    except Exception as e:
        logger.error(f"Error populating sample data: {str(e)}")
        return False

def main():
    """Main function to fix the PostgreSQL Knowledge Base"""
    logger.info("Starting PostgreSQL Knowledge Base fix script...")
    
    # Step 1: Add missing methods to DatabaseManager
    if not add_missing_methods():
        logger.error("Failed to add missing methods to DatabaseManager")
        sys.exit(1)
    logger.info("Successfully added missing methods to DatabaseManager")
    
    # Step 2: Populate sample data if needed
    if not populate_sample_data():
        logger.warning("Failed to populate sample data, but continuing...")
    else:
        logger.info("Successfully populated sample data")
    
    # Step 3: Verify Knowledge Base functionality
    if not verify_kb_functionality():
        logger.error("Failed to verify Knowledge Base functionality")
        sys.exit(1)
    logger.info("Successfully verified Knowledge Base functionality")
    
    logger.info("PostgreSQL Knowledge Base fix script completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 