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
        """Initialize the knowledge base with a DatabaseManager instance."""
        if not db_manager:
             raise ValueError("DatabaseManager instance is required for KnowledgeBase")
        self.db_manager = db_manager
        # Store other args if needed by future methods (e.g., vector search)
        self.vector_db_uri = vector_db_uri 
        self.content_path = content_path
        logging.info("KnowledgeBase initialized with DatabaseManager")
    
    def get_attraction_by_id(self, attraction_id: str) -> Optional[Dict]:
        """Retrieve information about an attraction by ID using the DatabaseManager."""
        logging.debug(f"KB: Getting attraction by ID via DB Manager: {attraction_id}")
        try:
            return self.db_manager.get_attraction(attraction_id)
        except Exception as e:
            logging.error(f"Error getting attraction by ID {attraction_id} from DB Manager: {str(e)}", exc_info=True)
            return None

    def search_attractions(self, query: str = "", filters: Optional[Dict] = None, language: str = "en", limit: int = 10) -> List[Dict]:
        """Search for attractions using the DatabaseManager. Handles basic text search on name."""
        logging.debug(f"KB: Searching attractions via DB Manager: query='{query}', filters={filters}, lang={language}, limit={limit}")
        
        # Prepare the filter dictionary for DatabaseManager
        db_query = filters if filters else {}
        
        # Handle text query with simple LIKE on name fields
        if query:
            search_term = f'%{query}%' # Add wildcards for LIKE
            lang_suffix = "_ar" if language == "ar" else "_en"
            # Add LIKE condition for the name field in the specified language
            # NOTE: This assumes DatabaseManager._build_sqlite_query can handle a {'field': {'$like': 'value'}} structure
            #       or we might need to adjust DatabaseManager or pass a raw SQL fragment.
            #       For now, let's assume a convention or refine later.
            #       A safer initial bet might be to just filter by name_en or name_ar directly if LIKE isn't supported.
            #       Let's try passing a specific structure DatabaseManager might handle.
            db_query[f'name{lang_suffix}'] = {'$like': search_term} 
            # If we also want to search description:
            # db_query[f'description{lang_suffix}'] = {'$like': search_term} 
            # Handling OR between name and description might require changes in DatabaseManager._build_sqlite_query
            # For simplicity now, just search name.

        logging.debug(f"KB: Constructed DB query for search_attractions: {db_query}")
        
        try:
            # Pass the constructed dictionary directly to db_manager
            return self.db_manager.search_attractions(query=db_query, limit=limit)
        except Exception as e:
            logging.error(f"Error searching attractions via DB Manager: {str(e)}", exc_info=True)
            return []

    def lookup_location(self, location_name: str) -> Optional[Dict]:
        """(TODO) Look up information about a specific location (city/region)."""
        logger.debug(f"KB: Looking up location: {location_name}")

        # Normalize the location name (lowercase, underscores for spaces)
        # Basic normalization, might need more robust handling
        normalized_name = location_name.lower().replace(" ", "_")

        # 1. Try loading from data/cities/{normalized_name}.json
        city_file_path = os.path.join(CITIES_DATA_PATH, f"{normalized_name}.json")
        city_data = _load_json_data(city_file_path)
        if city_data:
            logger.info(f"Found location info in {os.path.basename(city_file_path)}")
            # Add a 'source' field to indicate where the data came from
            city_data['_source'] = f'cities/{normalized_name}.json' 
            return city_data

        # 2. If not found in cities/, try data/popular_destinations.json
        popular_dest_path = os.path.join(BASE_DATA_PATH, "popular_destinations.json")
        popular_dest_data = _load_json_data(popular_dest_path)

        if popular_dest_data and isinstance(popular_dest_data.get('destinations'), list):
            for destination in popular_dest_data['destinations']:
                # Match against name_en or name_ar (or other relevant fields)
                if isinstance(destination, dict) and (
                    destination.get('name_en', '').lower() == location_name.lower() or 
                    destination.get('name_ar') == location_name # Assuming Arabic name might be exact match
                ):
                    logger.info(f"Found location info for '{location_name}' in popular_destinations.json")
                    # Add a 'source' field
                    destination['_source'] = 'popular_destinations.json'
                    return destination
        
        logger.warning(f"Could not find location information for: {location_name}")
        return None

    def lookup_attraction(self, attraction_name: str) -> Optional[Dict]:
        """(TODO) Look up a specific attraction by name (might need better matching)."""
        # This currently searches using the name, which might need refinement
        # for fuzzy matching or entity resolution later.
        logger.debug(f"KB: Looking up attraction by name: {attraction_name}")
        # Use search_attractions with a LIKE query for the name
        results = self.search_attractions(query={'$like': {'name_en': attraction_name}}, limit=1)
        if results:
            logger.info(f"Found attraction match for '{attraction_name}' via search.")
            return results[0]
        
        # Maybe try Arabic name as well?
        results_ar = self.search_attractions(query={'$like': {'name_ar': attraction_name}}, limit=1)
        if results_ar:
             logger.info(f"Found attraction match for '{attraction_name}' via Arabic name search.")
             return results_ar[0]

        logger.warning(f"Could not find attraction information for: {attraction_name}")
        return None

    def search_restaurants(self, query: Dict, limit: int = 10, lang: str = 'en') -> List[Dict]:
        """Search for restaurants based on query filters."""
        logger.debug(f"KB: Searching restaurants with query: {query}, limit: {limit}")
        # Basic pass-through for now
        # TODO: Add language preference handling if needed
        results = self.db_manager.search_restaurants(query=query, limit=limit)
        logger.info(f"KB: Found {len(results)} restaurants matching query.")
        return results

    def search_hotels(self, query: Dict, limit: int = 10, lang: str = 'en') -> List[Dict]:
        """Search for hotels/accommodations based on query filters."""
        logger.debug(f"KB: Searching hotels with query: {query}, limit: {limit}")
        # Renamed from search_accommodations in DB manager for consistency?
        # Let's assume the method is search_accommodations in db_manager
        results = self.db_manager.search_accommodations(query=query, limit=limit)
        logger.info(f"KB: Found {len(results)} accommodations matching query.")
        return results

    def get_practical_info(self, category: str) -> Optional[Dict]:
        """Retrieve practical information (e.g., visa, transport) from JSON files."""
        logging.debug(f"KB: Getting practical info for category: {category}")

        # Map category to filename and potentially a sub-key within the file
        category_map = {
            "transportation": ("transportation.json", None), # Load the whole file
            "cultural_insights": ("cultural_insights.json", None), # Load the whole file
            "visa": ("practical_info_general.json", "visa"),
            "currency": ("practical_info_general.json", "currency"),
            "weather": ("practical_info_general.json", "weather"),
            "health_safety": ("practical_info_general.json", "health_safety"),
            "telecommunications": ("practical_info_general.json", "telecommunications"),
            "holidays_events": ("practical_info_general.json", "holidays_events")
            # Add more mappings as needed
        }

        # Normalize category (lowercase, replace spaces/underscores if needed)
        normalized_category = category.lower().replace(" ", "_")

        if normalized_category not in category_map:
            logging.warning(f"No mapping found for practical info category: {category}")
            return None

        filename, sub_key = category_map[normalized_category]
        # Construct the full path relative to the base data path
        file_path = os.path.join(BASE_DATA_PATH, filename) 
        
        # Load the data using the cached helper function
        data = _load_json_data(file_path)

        if data is None:
            return None # Error logged in helper

        if sub_key:
            # If a sub_key is specified, return that part of the dictionary
            return data.get(sub_key)
        else:
            # Otherwise, return the entire loaded dictionary
            return data

    def get_restaurant_by_id(self, restaurant_id: str) -> Optional[Dict]:
        """Retrieve information about a restaurant by ID using the DatabaseManager."""
        logging.debug(f"KB: Getting restaurant by ID via DB Manager: {restaurant_id}")
        try:
            return self.db_manager.get_restaurant(restaurant_id)
        except Exception as e:
            logging.error(f"Error getting restaurant {restaurant_id} via DB Manager: {str(e)}", exc_info=True)
            return None

    def get_hotel_by_id(self, hotel_id: str) -> Optional[Dict]:
        """Retrieve information about a hotel/accommodation by ID using the DatabaseManager."""
        logging.debug(f"KB: Getting hotel by ID via DB Manager: {hotel_id}")
        try:
            return self.db_manager.get_accommodation(hotel_id)
        except Exception as e:
            logging.error(f"Error getting accommodation {hotel_id} via DB Manager: {str(e)}", exc_info=True)
            return None

    def debug_entity(self, entity_name, entity_type="attraction", language="en"):
        """(TODO) Helper for debugging entity resolution."""
        logging.warning(f"debug_entity not implemented. Args: {entity_name}, {entity_type}, {language}")
        # TODO: Implement lookups based on entity_type using respective db_manager methods.
        return {"message": "debug_entity not implemented"}