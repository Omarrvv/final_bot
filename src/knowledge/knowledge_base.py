import logging
from typing import Dict, List, Any, Optional

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
        """Search for attractions using the DatabaseManager."""
        logging.debug(f"KB: Searching attractions via DB Manager: query='{query}', filters={filters}, lang={language}, limit={limit}")
        try:
            # --- Query Translation --- 
            db_filters = filters if filters else {}
            search_conditions = []
            if query:
                search_term = f'%{query}%'
                lang_suffix = "_ar" if language == "ar" else "_en"
                search_conditions.append({'$or': [
                    {f'name{lang_suffix}': {'$like': search_term}},
                    {f'description{lang_suffix}': {'$like': search_term}}
                ]})
            for key, value in db_filters.items():
                 search_conditions.append({key: {'$eq': value}})
            final_query = {}
            if len(search_conditions) > 1:
                 final_query['$and'] = search_conditions
            elif len(search_conditions) == 1:
                final_query = search_conditions[0]
            logging.debug(f"KB: Translated DB query for search_attractions: {final_query}")
            # --- Call DB Manager --- 
            return self.db_manager.search_attractions(query=final_query, limit=limit)
        except Exception as e:
            logging.error(f"Error searching attractions via DB Manager: {str(e)}", exc_info=True)
            return []

    def lookup_location(self, location_name, language="en", *args):
        """(TODO) Look up information about a location."""
        logging.warning(f"lookup_location not fully implemented. Args: {location_name}, {language}, {args}")
        # TODO: Implement using db_manager.search_attractions/restaurants/accommodations by city/region?
        # Requires deciding how to define/store distinct locations.
        return {
            "location": location_name,
            "canonical_name": location_name,
            "description": f"Lookup for location '{location_name}' not implemented yet."
        }

    def lookup_attraction(self, attraction_name, language="en", *args):
        """(TODO) Look up information about a specific attraction by name."""
        logging.warning(f"lookup_attraction not fully implemented. Args: {attraction_name}, {language}, {args}")
        # Simple implementation using search
        results = self.search_attractions(query=attraction_name, language=language, limit=1)
        if results:
            return results[0]
        return {
            "attraction": attraction_name,
            "canonical_name": attraction_name,
            "description": f"Lookup for attraction '{attraction_name}' not implemented yet or not found."
        }

    def search_restaurants(self, query: str = "", filters: Optional[Dict] = None, language: str = "en", limit: int = 5) -> List[Dict]:
        """Search for restaurants using the DatabaseManager."""
        logging.debug(f"KB: Searching restaurants via DB Manager: query='{query}', filters={filters}, lang={language}, limit={limit}")
        try:
            # --- Query Translation --- 
            db_filters = filters if filters else {}
            search_conditions = []
            if query:
                search_term = f'%{query}%'
                lang_suffix = "_ar" if language == "ar" else "_en"
                search_conditions.append({'$or': [
                    {f'name{lang_suffix}': {'$like': search_term}},
                    {f'description{lang_suffix}': {'$like': search_term}},
                    {'cuisine': {'$like': search_term}}
                ]})
            for key, value in db_filters.items():
                 search_conditions.append({key: {'$eq': value}})
            final_query = {}
            if len(search_conditions) > 1:
                final_query['$and'] = search_conditions
            elif len(search_conditions) == 1:
                final_query = search_conditions[0]
            logging.debug(f"KB: Translated DB query for search_restaurants: {final_query}")
            # --- Call DB Manager --- 
            return self.db_manager.search_restaurants(query=final_query, limit=limit)
        except Exception as e:
            logging.error(f"Error searching restaurants via DB Manager: {str(e)}", exc_info=True)
            return []

    def search_hotels(self, query: str = "", filters: Optional[Dict] = None, language: str = "en", limit: int = 5) -> List[Dict]:
        """Search for hotels/accommodations using the DatabaseManager."""
        logging.debug(f"KB: Searching hotels via DB Manager: query='{query}', filters={filters}, lang={language}, limit={limit}")
        try:
            # --- Query Translation --- 
            db_filters = filters if filters else {}
            search_conditions = []
            if query:
                search_term = f'%{query}%'
                lang_suffix = "_ar" if language == "ar" else "_en"
                search_conditions.append({'$or': [
                    {f'name{lang_suffix}': {'$like': search_term}},
                    {f'description{lang_suffix}': {'$like': search_term}},
                    {'type': {'$like': search_term}},
                    {'category': {'$like': search_term}}
                ]})
            for key, value in db_filters.items():
                 search_conditions.append({key: {'$eq': value}})
            final_query = {}
            if len(search_conditions) > 1:
                final_query['$and'] = search_conditions
            elif len(search_conditions) == 1:
                final_query = search_conditions[0]
            logging.debug(f"KB: Translated DB query for search_accommodations: {final_query}")
            # --- Call DB Manager --- 
            return self.db_manager.search_accommodations(query=final_query, limit=limit)
        except Exception as e:
            logging.error(f"Error searching accommodations via DB Manager: {str(e)}", exc_info=True)
            return []

    def get_practical_info(self, category):
        """(TODO) Retrieve practical information (e.g., visa, transport)."""
        logging.warning(f"get_practical_info not implemented. Args: {category}")
        # TODO: Decide how practical info is stored (dedicated table? JSON blob in another table?)
        # Implement retrieval logic once storage is defined.
        return {
            "category": category,
            "info": f"Practical info for '{category}' not implemented yet."
        }

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