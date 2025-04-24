import logging
import json
import os
from typing import Dict, List, Any, Optional
from functools import lru_cache
from pathlib import Path

# Import TourismKnowledgeBase for fallback mechanism
from src.knowledge.data.tourism_kb import TourismKnowledgeBase

# --- Add Logger --- 
logger = logging.getLogger(__name__)

# --- Define paths relative to this file or a known root ---
# Assuming this script is in src/knowledge/, data is ../../data
# Adjust if the execution context is different.
BASE_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
CITIES_DATA_PATH = os.path.join(BASE_DATA_PATH, 'cities') # <<< Added path for cities

@lru_cache(maxsize=10) # Cache loaded JSON files
def _load_json_data(file_path: str) -> Optional[Dict]:
    """Helper function to load and cache JSON data from a file."""
    if not os.path.exists(file_path):
        logger.error(f"Data file not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Successfully loaded and cached: {os.path.basename(file_path)}")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

class KnowledgeBase:
    """Knowledge base for Egyptian tourism information.
       Acts as an interface layer over the DatabaseManager."""
    
    def __init__(self, db_manager: Any, vector_db_uri: Optional[str] = None, content_path: Optional[str] = None):
        """
        Initialize the knowledge base with a DatabaseManager instance.
        
        Args:
            db_manager: The DatabaseManager instance for database access
            vector_db_uri: Optional URI for vector database (for future use)
            content_path: Optional path to content files (no longer used)
        """
        if not db_manager:
             raise ValueError("DatabaseManager instance is required for KnowledgeBase")
        self.db_manager = db_manager
        # Store vector_db_uri for future use with RAG pipeline
        self.vector_db_uri = vector_db_uri 
        # content_path is no longer used as we exclusively use the database
        logger.info("KnowledgeBase initialized with DatabaseManager")
        
        # Initialize fallback TourismKnowledgeBase for when DB queries fail
        self.tourism_kb = TourismKnowledgeBase()
        
        # Check if database connection is available
        self._db_available = self._check_db_connection()
        if not self._db_available:
            logger.warning("Database connection unavailable. Using fallback data sources.")
    
    def _check_db_connection(self) -> bool:
        """Check if database connection is available."""
        try:
            if self.db_manager:
                # Simple test query to check connection
                return self.db_manager.connect()
            return False
        except Exception as e:
            logger.error(f"Database connection check failed: {str(e)}")
            return False
    
    def get_attraction_by_id(self, attraction_id: str) -> Optional[Dict]:
        """
        Retrieve information about an attraction by ID using the DatabaseManager.
        
        Args:
            attraction_id: The ID of the attraction to retrieve
            
        Returns:
            Dict containing attraction data if found, None otherwise
        """
        logger.debug(f"KB: Getting attraction by ID via DB Manager: {attraction_id}")
        try:
            attraction = self.db_manager.get_attraction(attraction_id)
            if attraction:
                logger.info(f"KB: Successfully retrieved attraction: {attraction_id}")
                return attraction
            else:
                logger.warning(f"KB: Attraction not found with ID: {attraction_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting attraction by ID {attraction_id} from DB Manager: {str(e)}", exc_info=True)
            return None

    def search_attractions(self, query: str = "", filters: Optional[Dict] = None, language: str = "en", limit: int = 10) -> List[Dict]:
        """
        Search for attractions based on query and filters.
        
        Args:
            query: Search query string
            filters: Additional filters to apply to the search
            language: Language code (en/ar)
            limit: Maximum number of results to return
            
        Returns:
            List of attraction dictionaries
        """
        logger.info(f"KnowledgeBase: Searching attractions with query '{query}', filters={filters}, language={language}")
        
        results = []
        
        try:
            # Try database first if available
            if self._db_available:
                try:
                    # If query is a string, use enhanced_search for text search
                    if isinstance(query, str) and query:
                        logger.info(f"Using enhanced_search for text query: {query}")
                        results = self.db_manager.enhanced_search(
                            table="attractions",
                            search_text=query,
                            limit=limit
                        )
                    # If query is a dictionary or filters are provided, use search_attractions
                    elif isinstance(query, dict):
                        logger.info(f"Using search_attractions for dictionary query: {query}")
                        results = self.db_manager.search_attractions(
                            query=query,
                            limit=limit
                        )
                    # If we have filters but no query
                    elif filters:
                        logger.info(f"Using search_attractions with filters: {filters}")
                        results = self.db_manager.search_attractions(
                            query=filters,
                            limit=limit
                        )
                    # No query or filters, just get all attractions up to limit
                    else:
                        logger.info(f"Getting all attractions up to limit: {limit}")
                        search_query = {}
                        if language == "ar":
                            search_query["name_ar"] = {"NOT": None}
                        else:
                            search_query["name_en"] = {"NOT": None}
                        results = self.db_manager.search_attractions(
                            query=search_query,
                            limit=limit
                        )
                    
                    # Check if we got any results
                    if not results:
                        logger.info(f"No attractions found in database for query '{query}'")
                    else:
                        logger.info(f"Found {len(results)} attractions in database for query '{query}'")
                    
                    return results
                    
                except Exception as db_error:
                    logger.error(f"Database search for attractions failed: {str(db_error)}")
                    # Return empty list for error case
                    return []
            
            # Fallback to hardcoded data
            logger.info(f"Falling back to hardcoded data for attraction search '{query}'")
            attractions_dict = self.tourism_kb.get_category("attractions")
            
            # Basic search on hardcoded data
            if not query or query == "":
                # Return all attractions up to limit
                for key, description in list(attractions_dict.items())[:limit]:
                    results.append({
                        "id": key,
                        "name": {"en": key.title(), "ar": key.title()},
                        "description": {"en": description, "ar": ""},
                        "location": {"coordinates": {"latitude": 0, "longitude": 0}},
                        "source": "hardcoded"
                    })
            else:
                # Search for query in keys and descriptions
                for key, description in attractions_dict.items():
                    if (query.lower() in key.lower() or 
                        query.lower() in description.lower()):
                        results.append({
                            "id": key,
                            "name": {"en": key.title(), "ar": key.title()},
                            "description": {"en": description, "ar": ""},
                            "location": {"coordinates": {"latitude": 0, "longitude": 0}},
                            "source": "hardcoded"
                        })
                        
                        if len(results) >= limit:
                            break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching attractions: {str(e)}")
            return []

    def lookup_location(self, location_name: str, language: str = "en") -> Optional[Dict]:
        """
        Look up information about a specific location (city/region) using the database.
        
        Args:
            location_name: The name of the location to look up
            language: Language code for localized search ("en" or "ar")
            
        Returns:
            Dictionary containing location data if found, None otherwise
        """
        logger.debug(f"KB: Looking up location '{location_name}' via DB Manager")
        
        try:
            # For simplicity, we'll search attractions with city or region matching the location name
            # In a more comprehensive system, we might have a dedicated cities/regions table
            
            name_field = "name_ar" if language == "ar" else "name_en"
            query = {
                "$or": [
                    {"city": {"$like": f"%{location_name}%"}},
                    {"region": {"$like": f"%{location_name}%"}},
                    {name_field: {"$like": f"%{location_name}%"}}
                ]
            }
            
            # Use enhanced search for better results
            results = self.db_manager.enhanced_search(
                table="attractions",
                filters=query,
                limit=5
            )
            
            if results:
                # Construct a location info object from the first result
                first_result = results[0]
                location_info = {
                    "name": first_result.get(name_field) or first_result.get("city") or first_result.get("region"),
                    "city": first_result.get("city"),
                    "region": first_result.get("region"),
                    "attractions": [r.get(name_field) for r in results if name_field in r],
                    "location": {
                        "latitude": first_result.get("latitude"),
                        "longitude": first_result.get("longitude")
                    }
                }
                
                logger.info(f"KB: Found location info for '{location_name}'")
                return location_info
                
            logger.warning(f"KB: Could not find location information for: {location_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error looking up location '{location_name}': {str(e)}", exc_info=True)
            return None

    def lookup_attraction(self, attraction_name: str, language: str = "en") -> Optional[Dict]:
        """
        Look up an attraction by its name.
        
        Args:
            attraction_name: Name of the attraction to look up
            language: Language code (en, ar)
            
        Returns:
            Attraction data if found, None otherwise
        """
        try:
            # Try to get from database first
            if self._db_available:
                result = None
                # Try the database query
                try:
                    # First try exact match
                    attractions = self.db_manager.search_attractions(
                        query={"name_en": attraction_name},
                        limit=1
                    )
                    
                    # If no exact match, try partial match using enhanced search
                    if not attractions or len(attractions) == 0:
                        logger.info(f"No exact match for '{attraction_name}', trying partial match")
                        attractions = self.db_manager.enhanced_search(
                table="attractions",
                search_text=attraction_name,
                limit=1
            )
            
                    if attractions and len(attractions) > 0:
                        attraction_id = attractions[0].get("id")
                        if attraction_id:
                            result = self.db_manager.get_attraction(attraction_id)
                except Exception as db_error:
                    logger.error(f"Database lookup for attraction '{attraction_name}' failed: {str(db_error)}")
                    
                if result:
                    logger.info(f"Found attraction '{attraction_name}' in database")
                    return result
            
            # Fallback to hardcoded data
            logger.info(f"Falling back to hardcoded data for attraction '{attraction_name}'")
            attractions_dict = self.tourism_kb.get_category("attractions")
            
            # Direct lookup if exact key exists
            if attraction_name.lower() in attractions_dict:
                return {
                    "id": attraction_name.lower(),
                    "name": {"en": attraction_name, "ar": attraction_name},
                    "description": {"en": attractions_dict[attraction_name.lower()], "ar": ""},
                    "location": {"coordinates": {"latitude": 0, "longitude": 0}},
                    "source": "hardcoded"
                }
                
            # Fuzzy search for name in hardcoded attraction descriptions
            for key, description in attractions_dict.items():
                if attraction_name.lower() in key.lower() or key.lower() in attraction_name.lower():
                    return {
                        "id": key,
                        "name": {"en": key.title(), "ar": key.title()},
                        "description": {"en": description, "ar": ""},
                        "location": {"coordinates": {"latitude": 0, "longitude": 0}},
                        "source": "hardcoded"
                    }
                    
            return None
        except Exception as e:
            logger.error(f"Error looking up attraction '{attraction_name}': {str(e)}")
            return None

    def search_restaurants(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """
        Search for restaurants based on query filters.
        
        Args:
            query: Search query string or structured query dictionary
            limit: Maximum number of results to return
            language: Language code for localized search ("en" or "ar")
            
        Returns:
            List of restaurant dictionaries matching the search criteria
        """
        logger.debug(f"KB: Searching restaurants with query: {query}, limit: {limit}")
        
        try:
            if isinstance(query, str) and query:
                # If query is a simple string, use enhanced search
                results = self.db_manager.enhanced_search(
                    table="restaurants",
                    search_text=query,
                    limit=limit
                )
                logger.info(f"KB: Found {len(results)} restaurants matching text query")
                return results
            elif isinstance(query, dict):
                # If query is a structured dict, use regular search
                results = self.db_manager.search_restaurants(query=query, limit=limit)
                logger.info(f"KB: Found {len(results)} restaurants matching structured query")
                return results
            else:
                # If no query, return all restaurants up to limit
                results = self.db_manager.get_all_restaurants(limit=limit)
                logger.info(f"KB: Retrieved {len(results)} restaurants (no query)")
                return results
            
        except Exception as e:
            logger.error(f"Error searching restaurants: {str(e)}", exc_info=True)
            return []

    def search_hotels(self, query: Dict = None, limit: int = 10, language: str = "en") -> List[Dict]:
        """
        Search for hotels/accommodations based on query filters.
        
        Args:
            query: Search query string or structured query dictionary
            limit: Maximum number of results to return
            language: Language code for localized search ("en" or "ar")
            
        Returns:
            List of hotel/accommodation dictionaries matching the search criteria
        """
        logger.debug(f"KB: Searching hotels with query: {query}, limit: {limit}")
        
        try:
            if isinstance(query, str) and query:
                # If query is a simple string, use enhanced search
                results = self.db_manager.enhanced_search(
                    table="accommodations",
                    search_text=query,
                    limit=limit
                )
                logger.info(f"KB: Found {len(results)} accommodations matching text query")
                return results
            elif isinstance(query, dict):
                # If query is a structured dict, use regular search
                results = self.db_manager.search_accommodations(query=query, limit=limit)
                logger.info(f"KB: Found {len(results)} accommodations matching structured query")
                return results
            else:
                # If no query, return all accommodations up to limit
                results = self.db_manager.get_all_accommodations(limit=limit)
                logger.info(f"KB: Retrieved {len(results)} accommodations (no query)")
                return results
            
        except Exception as e:
            logger.error(f"Error searching hotels: {str(e)}", exc_info=True)
            return []

    def get_practical_info(self, category: str, language: str = "en") -> Optional[Dict]:
        """
        Get practical information for a category.
        
        Args:
            category: Practical information category
            language: Language code (en, ar)
            
        Returns:
            Practical information data
        """
        try:
            # Try database first
            if self._db_available:
                try:
                    # Query practical_info table with category filter
                    logger.info(f"Searching for practical info with category: {category}")
                    results = self.db_manager.search_attractions(
                        query={"type": category},
                        limit=1
                    )
            
                    if results and len(results) > 0:
                        info = results[0]
                        # Format the result according to test expectations
                        name_field = "name_ar" if language == "ar" else "name_en"
                        desc_field = "description_ar" if language == "ar" else "description_en"
                        
                        result = {
                            "title": info.get(name_field, category),
                            "description": info.get(desc_field, ""),
                            "category": category,
                            "source": "database"
                        }
                        
                        # Add any additional data from the data field
                        if "data" in info and info["data"]:
                            if isinstance(info["data"], str):
                                try:
                                    data = json.loads(info["data"])
                                    result.update(data)
                                except json.JSONDecodeError:
                                    pass
                            elif isinstance(info["data"], dict):
                                result.update(info["data"])
                                
                        return result
                except Exception as db_error:
                    logger.error(f"Database query for practical info '{category}' failed: {str(db_error)}")
            
            # Fallback to JSON files
            try:
                json_path = os.path.join(self.vector_db_uri, "practical_info", f"{category}.json")
                if os.path.exists(json_path):
                    data = _load_json_data(json_path)
                    if data:
                        return data
                
                # Try general info file
                json_path = os.path.join(self.vector_db_uri, "practical_info_general.json")
                if os.path.exists(json_path):
                    data = _load_json_data(json_path)
                    if data and category in data:
                        return data[category]
            except Exception as json_error:
                logger.error(f"JSON lookup for practical info '{category}' failed: {str(json_error)}")
            
            # Final fallback to hardcoded data
            travel_tips = self.tourism_kb.get_category("travel_tips")
            if category in travel_tips:
                return {
                    "id": category,
                    "title": {"en": category.title(), "ar": category.title()},
                    "content": {"en": travel_tips[category], "ar": ""},
                    "source": "hardcoded"
                }
                
            # Try to fuzzy match the category
            for key, content in travel_tips.items():
                if category.lower() in key.lower() or key.lower() in category.lower():
                    return {
                        "id": key,
                        "title": {"en": key.title(), "ar": key.title()},
                        "content": {"en": content, "ar": ""},
                        "source": "hardcoded"
                    }
            
            return None
        except Exception as e:
            logger.error(f"Error getting practical info for '{category}': {str(e)}")
            return None

    def get_restaurant_by_id(self, restaurant_id: str) -> Optional[Dict]:
        """
        Retrieve information about a restaurant by ID using the DatabaseManager.
        
        Args:
            restaurant_id: The ID of the restaurant to retrieve
            
        Returns:
            Dictionary containing restaurant data if found, None otherwise
        """
        logger.debug(f"KB: Getting restaurant by ID via DB Manager: {restaurant_id}")
        try:
            restaurant = self.db_manager.get_restaurant(restaurant_id)
            if restaurant:
                logger.info(f"KB: Successfully retrieved restaurant: {restaurant_id}")
                return restaurant
            else:
                logger.warning(f"KB: Restaurant not found with ID: {restaurant_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting restaurant {restaurant_id} via DB Manager: {str(e)}", exc_info=True)
            return None

    def get_hotel_by_id(self, hotel_id: str) -> Optional[Dict]:
        """
        Retrieve information about a hotel/accommodation by ID using the DatabaseManager.
        
        Args:
            hotel_id: The ID of the hotel/accommodation to retrieve
            
        Returns:
            Dictionary containing hotel/accommodation data if found, None otherwise
        """
        logger.debug(f"KB: Getting hotel by ID via DB Manager: {hotel_id}")
        try:
            hotel = self.db_manager.get_accommodation(hotel_id)
            if hotel:
                logger.info(f"KB: Successfully retrieved accommodation: {hotel_id}")
                return hotel
            else:
                logger.warning(f"KB: Accommodation not found with ID: {hotel_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting accommodation {hotel_id} via DB Manager: {str(e)}", exc_info=True)
            return None

    def debug_entity(self, entity_name: str, entity_type: str = "attraction", language: str = "en") -> Dict:
        """
        Helper for debugging entity resolution.
        
        Args:
            entity_name: The name of the entity to debug
            entity_type: The type of entity ("attraction", "restaurant", "hotel", "location")
            language: Language code for localized search ("en" or "ar")
            
        Returns:
            Dictionary containing debug information
        """
        logger.debug(f"KB: Debug entity: {entity_name} (type: {entity_type}, language: {language})")
        
        try:
            result = {"entity_name": entity_name, "entity_type": entity_type, "language": language}
            entity = None
            
            # Define entity resolution strategies based on type
            if entity_type == "attraction":
                entity = self.lookup_attraction(entity_name, language)
                entity_label = "attraction"
            
            elif entity_type == "restaurant":
                # Try exact ID match first
                entity = self.get_restaurant_by_id(entity_name)
                if not entity:
                    # Try search by name
                    name_field = "name_ar" if language == "ar" else "name_en"
                    query = {name_field: {"$like": f"%{entity_name}%"}}
                    results = self.search_restaurants(query=query, limit=1, language=language)
                    entity = results[0] if results else None
                entity_label = "restaurant"
                
            elif entity_type in ["hotel", "accommodation"]:
                # Try exact ID match first
                entity = self.get_hotel_by_id(entity_name)
                if not entity:
                    # Try search by name
                    name_field = "name_ar" if language == "ar" else "name_en"
                    query = {name_field: {"$like": f"%{entity_name}%"}}
                    results = self.search_hotels(query=query, limit=1, language=language)
                    entity = results[0] if results else None
                entity_label = "hotel/accommodation" 
            
            elif entity_type in ["location", "city"]:
                entity = self.lookup_location(entity_name, language)
                entity_label = "location"
            
            else:
                result["found"] = False
                result["message"] = f"Unsupported entity type: {entity_type}"
                logger.info(f"KB: Debug entity results for {entity_name}: found=False (unsupported type)")
                return result
                
            # Process results
            if entity:
                result["found"] = True
                result["entity"] = entity
            else:
                result["found"] = False
                result["message"] = f"No {entity_label} found with name/id: {entity_name}"
                
            logger.info(f"KB: Debug entity results for {entity_name}: found={result.get('found')}")
            return result
            
        except Exception as e:
            logger.error(f"Error debugging entity '{entity_name}': {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "entity_name": entity_name,
                "entity_type": entity_type,
                "found": False,
                "language": language
            }

    def search_records(self, table_name, filters=None, limit=10, offset=0):
        """
        Generic method to search records in any table.
        This method is used by tests and wraps the specific table search methods.
        
        Args:
            table_name: Name of the table to search
            filters: Dictionary of filters to apply
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            List of matching records
        """
        logger.info(f"Searching {table_name} with filters {filters}")
        
        try:
            # Map table name to specific search method
            if table_name == "attractions":
                return self.db_manager.search_attractions(query=filters, limit=limit, offset=offset)
            elif table_name == "accommodations":
                return self.db_manager.search_hotels(query=filters, limit=limit, offset=offset)
            elif table_name == "restaurants":
                return self.db_manager.search_restaurants(query=filters, limit=limit, offset=offset)
            elif table_name == "cities":
                # Handle city search - may need to implement in DatabaseManager
                return self.db_manager.search_cities(query=filters, limit=limit, offset=offset) if hasattr(self.db_manager, "search_cities") else []
            else:
                logger.warning(f"Unknown table name: {table_name}")
                return []
        except Exception as e:
            logger.error(f"Error searching records in {table_name}: {str(e)}")
            return []
    
    def get_record_by_id(self, table_name, record_id):
        """
        Generic method to get a specific record by ID from any table.
        This method is used by tests and wraps the specific get methods.
        
        Args:
            table_name: Name of the table to query
            record_id: ID of the record to retrieve
            
        Returns:
            Record data if found, None otherwise
        """
        logger.info(f"Getting record from {table_name} with ID {record_id}")
        
        try:
            # Map table name to specific get method
            if table_name == "attractions":
                return self.db_manager.get_attraction(record_id)
            elif table_name == "accommodations":
                return self.db_manager.get_accommodation(record_id)
            elif table_name == "restaurants":
                return self.db_manager.get_restaurant(record_id)
            elif table_name == "cities":
                # Handle city lookup - may need to implement in DatabaseManager
                return self.db_manager.get_city(record_id) if hasattr(self.db_manager, "get_city") else None
            else:
                logger.warning(f"Unknown table name: {table_name}")
                return None
        except Exception as e:
            logger.error(f"Error getting record from {table_name} with ID {record_id}: {str(e)}")
            return None