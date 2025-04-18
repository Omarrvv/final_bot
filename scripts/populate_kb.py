"""
Script to populate the SQLite Knowledge Base from JSON data files.
"""
import sqlite3
import json
import os
import logging
from pathlib import Path
from datetime import datetime, timezone

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

# --- Database Insertion Functions ---

def insert_attraction(cursor: sqlite3.Cursor, attraction_data: dict):
    """Inserts or replaces a single attraction record into the database."""
    try:
        attraction_id = attraction_data.get('id')
        if not attraction_id:
            logger.warning(f"Skipping attraction record due to missing ID: {attraction_data.get('name', {}).get('en', '(name missing)')}")
            return

        # Extract main fields
        name_en = get_localized_value(attraction_data, 'name', 'en')
        name_ar = get_localized_value(attraction_data, 'name', 'ar')
        attraction_type = get_nested_value(attraction_data, ['type'])
        city = get_nested_value(attraction_data, ['location', 'city'])
        region = get_nested_value(attraction_data, ['location', 'region'])
        latitude = get_nested_value(attraction_data, ['location', 'coordinates', 'latitude'])
        longitude = get_nested_value(attraction_data, ['location', 'coordinates', 'longitude'])
        description_en = get_localized_value(attraction_data, 'description', 'en')
        description_ar = get_localized_value(attraction_data, 'description', 'ar')

        # Prepare the rest of the data for the JSON blob
        # Create a deep copy to avoid modifying the original dict
        data_blob = json.loads(json.dumps(attraction_data))
        # Remove fields stored in dedicated columns to avoid duplication
        del data_blob['id']
        if 'name' in data_blob: del data_blob['name']
        if 'type' in data_blob: del data_blob['type']
        if 'location' in data_blob: del data_blob['location'] # Remove entire location block
        if 'description' in data_blob: del data_blob['description']

        data_json = json.dumps(data_blob, ensure_ascii=False)

        # Timestamps
        now = datetime.now(timezone.utc).isoformat()

        # Insert/Replace Data
        cursor.execute("""
            INSERT OR REPLACE INTO attractions
            (id, name_en, name_ar, type, city, region, latitude, longitude, description_en, description_ar, data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            attraction_id, name_en, name_ar, attraction_type, city, region,
            latitude, longitude, description_en, description_ar, data_json,
            now, now # Set created_at and updated_at to now on insert/replace
        ))
        logger.debug(f"Inserted/Replaced attraction: {attraction_id} ({name_en})")
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error inserting attraction {attraction_data.get('id', '(ID missing)')}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error processing attraction data {attraction_data.get('id', '(ID missing)')}: {e}", exc_info=True)
        return False

def insert_restaurant(cursor: sqlite3.Cursor, restaurant_data: dict):
    """Inserts or replaces a single restaurant record into the database."""
    try:
        restaurant_id = restaurant_data.get('id')
        if not restaurant_id:
            logger.warning(f"Skipping restaurant record due to missing ID: {restaurant_data.get('name', {}).get('en', '(name missing)')}")
            return

        # Extract main fields
        name_en = get_localized_value(restaurant_data, 'name', 'en')
        name_ar = get_localized_value(restaurant_data, 'name', 'ar')
        cuisine = restaurant_data.get('cuisine', '') # Assuming cuisine is a simple string
        city = get_nested_value(restaurant_data, ['location', 'city'])
        region = get_nested_value(restaurant_data, ['location', 'region'])
        latitude = get_nested_value(restaurant_data, ['location', 'coordinates', 'latitude'])
        longitude = get_nested_value(restaurant_data, ['location', 'coordinates', 'longitude'])
        description_en = get_localized_value(restaurant_data, 'description', 'en')
        description_ar = get_localized_value(restaurant_data, 'description', 'ar')
        price_range = restaurant_data.get('price_range', '') # Assuming price_range is a simple string

        # Prepare the rest of the data for the JSON blob
        data_blob = json.loads(json.dumps(restaurant_data))
        del data_blob['id']
        if 'name' in data_blob: del data_blob['name']
        if 'cuisine' in data_blob: del data_blob['cuisine']
        if 'location' in data_blob: del data_blob['location']
        if 'description' in data_blob: del data_blob['description']
        if 'price_range' in data_blob: del data_blob['price_range']

        data_json = json.dumps(data_blob, ensure_ascii=False)
        now = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO restaurants
            (id, name_en, name_ar, cuisine, city, region, latitude, longitude, description_en, description_ar, price_range, data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            restaurant_id, name_en, name_ar, cuisine, city, region,
            latitude, longitude, description_en, description_ar, price_range,
            data_json, now, now
        ))
        logger.debug(f"Inserted/Replaced restaurant: {restaurant_id} ({name_en})")
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error inserting restaurant {restaurant_data.get('id', '(ID missing)')}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error processing restaurant data {restaurant_data.get('id', '(ID missing)')}: {e}", exc_info=True)
        return False

def insert_accommodation(cursor: sqlite3.Cursor, accommodation_data: dict):
    """Inserts or replaces a single accommodation record into the database."""
    try:
        accommodation_id = accommodation_data.get('id')
        if not accommodation_id:
            logger.warning(f"Skipping accommodation record due to missing ID: {accommodation_data.get('name', {}).get('en', '(name missing)')}")
            return

        # Extract main fields
        name_en = get_localized_value(accommodation_data, 'name', 'en')
        name_ar = get_localized_value(accommodation_data, 'name', 'ar')
        accommodation_type = get_nested_value(accommodation_data, ['type'])
        category = get_nested_value(accommodation_data, ['category']) # e.g., 5-star, budget
        city = get_nested_value(accommodation_data, ['location', 'city'])
        region = get_nested_value(accommodation_data, ['location', 'region'])
        latitude = get_nested_value(accommodation_data, ['location', 'coordinates', 'latitude'])
        longitude = get_nested_value(accommodation_data, ['location', 'coordinates', 'longitude'])
        description_en = get_localized_value(accommodation_data, 'description', 'en')
        description_ar = get_localized_value(accommodation_data, 'description', 'ar')
        price_min = get_nested_value(accommodation_data, ['price_range', 'min'])
        price_max = get_nested_value(accommodation_data, ['price_range', 'max'])

        # Prepare the rest of the data for the JSON blob
        data_blob = json.loads(json.dumps(accommodation_data))
        del data_blob['id']
        if 'name' in data_blob: del data_blob['name']
        if 'type' in data_blob: del data_blob['type']
        if 'category' in data_blob: del data_blob['category']
        if 'location' in data_blob: del data_blob['location']
        if 'description' in data_blob: del data_blob['description']
        if 'price_range' in data_blob: del data_blob['price_range']

        data_json = json.dumps(data_blob, ensure_ascii=False)
        now = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO accommodations
            (id, name_en, name_ar, type, category, city, region, latitude, longitude, description_en, description_ar, price_min, price_max, data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            accommodation_id, name_en, name_ar, accommodation_type, category, city, region,
            latitude, longitude, description_en, description_ar, price_min, price_max,
            data_json, now, now
        ))
        logger.debug(f"Inserted/Replaced accommodation: {accommodation_id} ({name_en})")
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error inserting accommodation {accommodation_data.get('id', '(ID missing)')}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error processing accommodation data {accommodation_data.get('id', '(ID missing)')}: {e}", exc_info=True)
        return False

# --- Main Population Logic ---

def populate_database():
    """Connects to the database and populates tables from JSON files."""
    logger.info(f"Starting KB population from {DATA_SOURCE_DIR} into {DB_PATH}")

    if not DB_PATH.exists():
        logger.error(f"Database file not found at {DB_PATH}. Please run init_db.py first.")
        return

    conn = None
    inserted_counts = {"attractions": 0, "restaurants": 0, "accommodations": 0}
    processed_files = 0
    total_items = 0

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

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
                            if insert_attraction(cursor, item_data):
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
                         if isinstance(data, list): items = data
                         elif isinstance(data, dict): items = [data]
                         else: continue

                         for item_data in items:
                             total_items += 1
                             if insert_restaurant(cursor, item_data):
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
                         if isinstance(data, list): items = data
                         elif isinstance(data, dict): items = [data]
                         else: continue

                         for item_data in items:
                             total_items += 1
                             if insert_accommodation(cursor, item_data):
                                 inserted_counts["accommodations"] += 1
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON from {json_file.name}: {e}")
                except Exception as e:
                    logger.error(f"Error processing file {json_file.name}: {e}", exc_info=True)
        else:
            logger.warning(f"Accommodations directory not found: {accommodation_dir}")

        # Commit changes
        conn.commit()
        logger.info("Database population completed.")
        logger.info(f"Processed {processed_files} files, {total_items} total items found.")
        logger.info(f"Inserted/Replaced - Attractions: {inserted_counts['attractions']}, Restaurants: {inserted_counts['restaurants']}, Accommodations: {inserted_counts['accommodations']}")

    except sqlite3.Error as e:
        logger.error(f"Database error during population: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")

# --- Script Execution ---
if __name__ == "__main__":
    populate_database() 