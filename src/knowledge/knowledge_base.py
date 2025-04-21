import logging
import json
import os
from typing import Dict, List, Any, Optional
from functools import lru_cache

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
        Search for attractions using the DatabaseManager.
        
        Args:
            query: Search query string or structured query dictionary
            filters: Additional filters to apply to the search
            language: Language code for localized search ("en" or "ar")
            limit: Maximum number of results to return
            
        Returns:
            List of attraction dictionaries matching the search criteria
        """
        logger.debug(f"KB: Searching attractions via DB Manager: query='{query}', filters={filters}, lang={language}, limit={limit}")
        
        # Prepare the filter dictionary for DatabaseManager
        db_query = filters if filters else {}
        
        try:
            # Handle text query
            if query and isinstance(query, str):
                # Use enhanced search for text queries
                logger.debug(f"KB: Using enhanced search for text query: {query}")
                results = self.db_manager.enhanced_search(
                    table="attractions", 
                    search_text=query,
                    filters=filters,
                    limit=limit
                )
                logger.info(f"KB: Found {len(results)} attractions matching text query")
                return results
            elif query and isinstance(query, dict):
                # If query is already a structured query dict, merge with filters
                if filters:
                    # If both query and filters are provided, combine them with AND logic
                    db_query = {"$and": [query, filters]} if filters else query
                else:
                    db_query = query
                
                logger.debug(f"KB: Using structured query: {db_query}")
                results = self.db_manager.search_attractions(query=db_query, limit=limit)
                logger.info(f"KB: Found {len(results)} attractions matching structured query")
                return results
            else:
                # If no query, just use filters (or empty dict for all)
                logger.debug(f"KB: No query provided, using only filters: {db_query}")
                results = self.db_manager.search_attractions(query=db_query, limit=limit)
                logger.info(f"KB: Found {len(results)} attractions with filter-only query")
                return results
        except Exception as e:
            logger.error(f"Error searching attractions via DB Manager: {str(e)}", exc_info=True)
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
        Look up a specific attraction by name.
        
        Args:
            attraction_name: The name of the attraction to look up
            language: Language code for localized search ("en" or "ar")
            
        Returns:
            Dictionary containing attraction data if found, None otherwise
        """
        logger.debug(f"KB: Looking up attraction by name: {attraction_name}")
        
        try:
            # Use enhanced search for better results with partial matches
            results = self.db_manager.enhanced_search(
                table="attractions",
                search_text=attraction_name,
                limit=1
            )
            
            if results:
                logger.info(f"KB: Found attraction match for '{attraction_name}'")
                return results[0]
                
            logger.warning(f"KB: Could not find attraction information for: {attraction_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error looking up attraction '{attraction_name}': {str(e)}", exc_info=True)
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
        Retrieve practical information from the database.
        
        Args:
            category: The category of practical information to retrieve
            language: Language code for localized search ("en" or "ar")
            
        Returns:
            Dictionary containing practical information if found, None otherwise
        """
        logger.debug(f"KB: Getting practical info for category: {category}")
        
        try:
            # Create a query to search for practical info with the specified category
            query = {"type": category}
            
            # In a fully implemented system, we would query a 'practical_info' table in the database
            # For now, we'll search for attractions with matching category/type as a placeholder
            
            results = self.db_manager.search_attractions(query=query, limit=1)
            
            if results:
                # Transform the results into a practical info format
                info = results[0]
                name_field = "name_ar" if language == "ar" else "name_en"
                desc_field = "description_ar" if language == "ar" else "description_en"
                
                practical_info = {
                    "title": info.get(name_field, category),
                    "description": info.get(desc_field, ""),
                    "category": category,
                    "source": "database"
                }
                
                # Add any additional fields from the data JSON if available
                if "data" in info and isinstance(info["data"], dict):
                    # Extract relevant data for this category
                    if "details" in info["data"]:
                        practical_info["details"] = info["data"]["details"]
                    if "tips" in info["data"]:
                        practical_info["tips"] = info["data"]["tips"]
                
                logger.info(f"KB: Found practical info for category: {category}")
                return practical_info
            
            logger.warning(f"KB: No practical info found in database for category: {category}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting practical info for category '{category}': {str(e)}", exc_info=True)
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