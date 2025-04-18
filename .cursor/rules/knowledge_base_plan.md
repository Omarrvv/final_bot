# Knowledge Base Implementation Plan

## 1. Goal

Activate the sophisticated `src/` application path by:
1.  Populating the SQLite database (`data/egypt_chatbot.db`) with structured knowledge base data (attractions, accommodations, restaurants, etc.).
2.  Connecting the `src/knowledge/knowledge_base.py` component to the `src/knowledge/database.py::DatabaseManager` to retrieve and manage this data.

## 2. Target Data Structure (Example: Attractions)

Data will be stored in SQLite tables (`attractions`, `accommodations`, `restaurants`) as defined by `init_db.py`. The source data is currently in JSON files (partially, e.g., `data/attractions/*.json`).

**Mapping Example (Attraction):**

*   **JSON Source Field** -> **SQLite `attractions` Column** (`Data Type`) -> **Notes**
*   `id` -> `id` (`TEXT PK`) -> Unique identifier
*   `name.en` -> `name_en` (`TEXT`) -> Primary English name
*   `name.ar` -> `name_ar` (`TEXT`) -> Primary Arabic name
*   `type` -> `type` (`TEXT`) -> e.g., "temple", "museum"
*   `location.city` -> `city` (`TEXT`)
*   `location.region` -> `region` (`TEXT`)
*   `location.coordinates.latitude` -> `latitude` (`REAL`)
*   `location.coordinates.longitude` -> `longitude` (`REAL`)
*   `description.en` -> `description_en` (`TEXT`)
*   `description.ar` -> `description_ar` (`TEXT`)
*   *All other fields* (`history`, `practical_info`, `images`, `keywords`, nested location/name fields, etc.) -> `data` (`JSON Text`) -> Store remaining data as a JSON string.
*   *(Script Generated)* -> `created_at` (`TEXT`) -> ISO 8601 Timestamp
*   *(Script Generated)* -> `updated_at` (`TEXT`) -> ISO 8601 Timestamp

*(Similar mappings needed for `accommodations` and `restaurants` based on their JSON structure and DB schema)*

## 3. Data Ingestion (`scripts/populate_kb.py`)

A Python script needs to be created and run *after* `init_db.py`.

**Script Logic:**

1.  Import `sqlite3`, `json`, `os`, `pathlib`, `logging`, `datetime`.
2.  Define `DB_PATH = Path("data") / "egypt_chatbot.db"`.
3.  Define `DATA_SOURCE_DIR = Path("data")`.
4.  Implement helper function `get_nested_value(data, keys, default=None)` for safe dict access.
5.  Implement `insert_attraction(cursor, data)` function:
    *   Takes SQLite cursor and single attraction dict as input.
    *   Extracts fields matching the main table columns.
    *   Creates a copy of the input dict and removes the main fields to prepare the `data` JSON blob. Handle nested fields carefully.
    *   Generates `created_at`/`updated_at` timestamps.
    *   Executes `INSERT OR REPLACE INTO attractions ... VALUES (...)` using parameterized queries.
    *   Logs success or errors.
6.  **(TODO)** Implement `insert_restaurant(cursor, data)` and `insert_accommodation(cursor, data)` similarly based on their respective JSON structures and DB schemas.
7.  Implement `populate_database()` main function:
    *   Check if `DB_PATH` exists.
    *   Connect to SQLite DB.
    *   Create cursor.
    *   **Attractions:**
        *   Define `attraction_dir = DATA_SOURCE_DIR / "attractions"`.
        *   Iterate through `*.json` files in `attraction_dir`.
        *   Load JSON content (handle potential list vs dict structures within files).
        *   For each item, call `insert_attraction(cursor, item_data)`.
        *   Include error handling for JSON decoding and DB insertion.
    *   **(TODO)** Repeat iteration logic for `restaurants` and `accommodations` directories/files.
    *   Commit transaction.
    *   Close connection.
    *   Log completion.

**Execution:**

```bash
# First time or after schema changes
python init_db.py

# To load/update data from JSON files
python scripts/populate_kb.py

4. Connecting KnowledgeBase to DatabaseManager

Modify src/knowledge/knowledge_base.py and src/utils/factory.py.

Changes in src/utils/factory.py:

# (Inside ComponentFactory class)
    # Add factory for DatabaseManager
    def create_database_manager(self) -> Any:
        from src.knowledge.database import DatabaseManager
        return DatabaseManager(database_uri=self.env_vars["database_uri"])

    # Modify KB factory
    def create_knowledge_base(self) -> Any:
        from src.knowledge.knowledge_base import KnowledgeBase
        # Get DB Manager instance from container
        db_manager = container.get("database_manager") # Ensure name matches registration
        # Inject db_manager
        return KnowledgeBase(db_manager=db_manager,
                            database_uri=self.env_vars["database_uri"], # Pass URIs if needed
                            vector_db_uri=self.env_vars["vector_db_uri"],
                            content_path=self.env_vars["content_path"])

    def _register_services(self):
        # ... other registrations ...
        container.register_factory("database_manager", self.create_database_manager) # Add registration
        container.register_factory("knowledge_base", self.create_knowledge_base)
        # ... rest ...

   Changes in src/knowledge/knowledge_base.py:

   import logging
# Removed placeholder sample data

class KnowledgeBase:
    # Modified __init__
    def __init__(self, db_manager, database_uri=None, vector_db_uri=None, content_path=None):
        self.db_manager = db_manager
        if not self.db_manager:
             raise ValueError("DatabaseManager instance is required")
        # Store other args if needed...
        logging.info("KnowledgeBase initialized with DatabaseManager")

    # Example modification for get_attraction_by_id
    def get_attraction_by_id(self, attraction_id):
        logging.debug(f"KB: Getting attraction by ID via DB Manager: {attraction_id}")
        return self.db_manager.get_attraction(attraction_id) # Call DB Manager method

    # Example modification for search_attractions
    def search_attractions(self, query="", filters=None, language="en", limit=10):
         logging.debug(f"KB: Searching attractions via DB Manager: query='{query}', filters={filters}")
         # Convert filters/query to format expected by db_manager.search_attractions
         db_query_filters = filters if filters else {}
         if query:
             # Build a simple query structure, assuming db_manager handles SQLite syntax
             # This part needs refinement based on how db_manager implements search
             search_term = f'%{query}%'
             db_query_filters['$or'] = [
                 {'name_en': {'$like': search_term}}, # Need LIKE operator for SQLite
                 {'description_en': {'$like': search_term}}
                 # Add name_ar / description_ar if needed
             ]

         # Actual call might need adaptation depending on db_manager's search implementation
         # For example, DatabaseManager might need a different search method signature.
         # Let's assume it takes a query dictionary compatible with its logic:
         return self.db_manager.search_attractions(query=db_query_filters, limit=limit)

    # *** TODO: Repeat modification for ALL other methods: ***
    # lookup_location, lookup_attraction, search_restaurants, search_hotels,
    # get_practical_info, get_restaurant_by_id, get_hotel_by_id.
    # Each should call the corresponding method on `self.db_manager`.
    # Remove all mock return values and hardcoded sample lists.
    
         