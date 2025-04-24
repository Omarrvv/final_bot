"""
Script to populate the SQLite Knowledge Base from JSON data files.
Uses the DatabaseManager for interaction.
"""
import json
import os
import logging
from pathlib import Path
from datetime import datetime, timezone

# --- Import DatabaseManager ---
from src.knowledge.database import DatabaseManager 
# Ensure src is in the Python path when running, or adjust import

# --- Configuration ---
# Ensure paths are relative to the project root where the script is expected to be run from
DB_PATH = Path("data") / "egypt_chatbot.db"
DATA_SOURCE_DIR = Path("data")
LOG_LEVEL = logging.INFO

# --- Logging Setup ---
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Helper Functions ---
def get_nested_value(data: dict, keys: list, default=None):
    """Safely retrieve a nested value from a dictionary using a list of keys."""
    temp_data = data
    for key in keys:
        if isinstance(temp_data, dict) and key in temp_data:
            temp_data = temp_data[key]
        else:
            return default
    return temp_data

def get_localized_value(data: dict, base_key: str, lang: str = 'en', fallback_lang: str = 'en'):
    """Get localized value (e.g., name.en or name.ar), falling back to English."""
    return get_nested_value(data, [base_key, lang], default=get_nested_value(data, [base_key, fallback_lang]))

# --- Database Interaction Functions (Use DatabaseManager) ---

def save_attraction(db_manager: DatabaseManager, attraction_data: dict) -> bool:
    """Saves a single attraction record using the DatabaseManager."""
    try:
        if not attraction_data.get('id'):
            logger.warning(f"Skipping attraction record due to missing ID: {get_localized_value(attraction_data, 'name', 'en')}")
            return False
        
        success = db_manager.save_attraction(attraction_data)
        if success:
            logger.debug(f"Saved attraction via DB Manager: {attraction_data['id']} ({get_localized_value(attraction_data, 'name', 'en')})")
        else:
            logger.warning(f"Failed to save attraction via DB Manager: {attraction_data['id']}")
        return success
    except Exception as e:
        logger.error(f"Error saving attraction {attraction_data.get('id', '(ID missing)')} via DB Manager: {e}", exc_info=True)
        return False

def save_restaurant(db_manager: DatabaseManager, restaurant_data: dict) -> bool:
    """Saves a single restaurant record using the DatabaseManager."""
    try:
        if not restaurant_data.get('id'):
            logger.warning(f"Skipping restaurant record due to missing ID: {get_localized_value(restaurant_data, 'name', 'en')}")
            return False
        
        success = db_manager.save_restaurant(restaurant_data)
        if success:
            logger.debug(f"Saved restaurant via DB Manager: {restaurant_data['id']} ({get_localized_value(restaurant_data, 'name', 'en')})")
        else:
            logger.warning(f"Failed to save restaurant via DB Manager: {restaurant_data['id']}")
        return success
    except Exception as e:
        logger.error(f"Error saving restaurant {restaurant_data.get('id', '(ID missing)')} via DB Manager: {e}", exc_info=True)
        return False

def save_accommodation(db_manager: DatabaseManager, accommodation_data: dict) -> bool:
    """Saves a single accommodation record using the DatabaseManager."""
    try:
        if not accommodation_data.get('id'):
            logger.warning(f"Skipping accommodation record due to missing ID: {get_localized_value(accommodation_data, 'name', 'en')}")
            return False
        
        success = db_manager.save_accommodation(accommodation_data)
        if success:
            logger.debug(f"Saved accommodation via DB Manager: {accommodation_data['id']} ({get_localized_value(accommodation_data, 'name', 'en')})")
        else:
            logger.warning(f"Failed to save accommodation via DB Manager: {accommodation_data['id']}")
        return success
    except Exception as e:
        logger.error(f"Error saving accommodation {accommodation_data.get('id', '(ID missing)')} via DB Manager: {e}", exc_info=True)
        return False

# --- Main Population Logic ---

def populate_database():
    """Initializes DatabaseManager and populates tables from JSON files."""
    logger.info(f"Starting KB population from {DATA_SOURCE_DIR} into DB specified by DatabaseManager")

    # --- Initialize DatabaseManager --- 
    # It will read DATABASE_URI from env or use default
    # It also handles table creation if needed.
    db_manager = None
    try:
        db_manager = DatabaseManager() # Assumes DATABASE_URI is set or default is okay
        if not db_manager.connection: # Check if SQLite connection succeeded
             logger.error("DatabaseManager failed to initialize SQLite connection. Aborting population.")
             return
        logger.info("DatabaseManager initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize DatabaseManager: {e}. Aborting population.", exc_info=True)
        return

    # --- Keep track of counts --- 
    inserted_counts = {"attractions": 0, "restaurants": 0, "accommodations": 0}
    processed_files = 0
    total_items = 0

    try:
        # --- Process Attractions ---
        attraction_dir = DATA_SOURCE_DIR / "attractions"
        if attraction_dir.is_dir():
            logger.info(f"Processing attractions from {attraction_dir}...")
            for json_file in attraction_dir.glob('*.json'):
                processed_files += 1
                logger.debug(f"Processing file: {json_file.name}")
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Handle files containing a single object or a list of objects
                        if isinstance(data, list):
                            items = data
                        elif isinstance(data, dict):
                            items = [data]
                        else:
                            logger.warning(f"Skipping file {json_file.name}: Unexpected JSON structure (not list or dict).")
                            continue

                        for item_data in items:
                            total_items += 1
                            # --- Use db_manager method --- 
                            if save_attraction(db_manager, item_data):
                                inserted_counts["attractions"] += 1
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON from {json_file.name}: {e}")
                except Exception as e:
                    logger.error(f"Error processing file {json_file.name}: {e}", exc_info=True)
        else:
            logger.warning(f"Attractions directory not found: {attraction_dir}")

        # --- Process Restaurants ---
        restaurant_dir = DATA_SOURCE_DIR / "restaurants"
        if restaurant_dir.is_dir():
            logger.info(f"Processing restaurants from {restaurant_dir}...")
            for json_file in restaurant_dir.glob('*.json'):
                processed_files += 1
                logger.debug(f"Processing file: {json_file.name}")
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            items = data
                        elif isinstance(data, dict):
                            items = [data]
                        else:
                            logger.warning(f"Skipping file {json_file.name}: Unexpected JSON structure.")
                            continue

                        for item_data in items:
                            total_items += 1
                            # --- Use db_manager method --- 
                            if save_restaurant(db_manager, item_data):
                                inserted_counts["restaurants"] += 1
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON from {json_file.name}: {e}")
                except Exception as e:
                    logger.error(f"Error processing file {json_file.name}: {e}", exc_info=True)
        else:
            logger.warning(f"Restaurants directory not found: {restaurant_dir}")

        # --- Process Accommodations ---
        accommodation_dir = DATA_SOURCE_DIR / "accommodations"
        if accommodation_dir.is_dir():
            logger.info(f"Processing accommodations from {accommodation_dir}...")
            for json_file in accommodation_dir.glob('*.json'):
                processed_files += 1
                logger.debug(f"Processing file: {json_file.name}")
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            items = data
                        elif isinstance(data, dict):
                            items = [data]
                        else:
                            logger.warning(f"Skipping file {json_file.name}: Unexpected JSON structure.")
                            continue

                        for item_data in items:
                            total_items += 1
                            # --- Use db_manager method --- 
                            if save_accommodation(db_manager, item_data):
                                inserted_counts["accommodations"] += 1
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON from {json_file.name}: {e}")
                except Exception as e:
                    logger.error(f"Error processing file {json_file.name}: {e}", exc_info=True)
        else:
            logger.warning(f"Accommodations directory not found: {accommodation_dir}")

        # --- Commit and Log Summary --- 
        # Commit is handled within db_manager save methods for SQLite if needed,
        # or by autocommit if using PostgreSQL.
        # No explicit commit needed here.

        logger.info("--- Population Summary ---")
        logger.info(f"Processed {processed_files} files.")
        logger.info(f"Attempted to process {total_items} items.")
        logger.info(f"Successfully saved {inserted_counts['attractions']} attractions.")
        logger.info(f"Successfully saved {inserted_counts['restaurants']} restaurants.")
        logger.info(f"Successfully saved {inserted_counts['accommodations']} accommodations.")
        logger.info("-------------------------")

    except Exception as e:
        logger.critical(f"An unexpected error occurred during population: {e}", exc_info=True)
        # Attempt to rollback if needed? Transaction management is complex here.
        # Relying on DB Manager's handling for now.
    finally:
        # --- Close connection via DatabaseManager --- 
        if db_manager:
            db_manager.close()
            logger.info("Database connection closed by DatabaseManager.")

# --- Script Execution ---
if __name__ == "__main__":
    # Adjust path for running script directly if needed
    # This assumes the script is run from the project root
    # If run from scripts/, need to adjust path or ensure src is in PYTHONPATH
    import sys
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    populate_database() 