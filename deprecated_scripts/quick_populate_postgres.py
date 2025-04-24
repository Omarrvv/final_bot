#!/usr/bin/env python3
"""
Quick script to populate the PostgreSQL database with data from JSON files in the data directory.
"""

import os
import sys
import json
import glob
import logging
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Ensure we can import from src package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def load_config():
    """Load configuration from .env file"""
    load_dotenv()
    
    # Get PostgreSQL URI from environment
    postgres_uri = os.getenv("POSTGRES_URI", "postgresql://omarmohamed@localhost:5432/postgres")
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable not set")
        sys.exit(1)
    
    # Hardcode the URI to make sure we're using the correct one
    postgres_uri = "postgresql://omarmohamed@localhost:5432/postgres"
    logger.info(f"Using PostgreSQL URI: {postgres_uri}")
    
    return {
        "postgres_uri": postgres_uri
    }

def connect_to_db(postgres_uri):
    """Connect to PostgreSQL database"""
    try:
        connection = psycopg2.connect(postgres_uri)
        connection.autocommit = True
        logger.info(f"Connected to PostgreSQL database: {postgres_uri.split('@')[-1]}")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL database: {e}")
        sys.exit(1)

def load_json_data(file_path):
    """Load data from a JSON file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load data from {file_path}: {e}")
        return None

def collect_attractions():
    """Collect attraction data from JSON files"""
    attractions = []
    
    # Root data directory
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    
    # Process main attractions directory
    attractions_dir = os.path.join(data_dir, "attractions")
    attraction_files = glob.glob(os.path.join(attractions_dir, "*.json"))
    
    # Also process subdirectories
    for subdir in ["historical", "cultural", "modern", "religious", "shopping"]:
        subdir_path = os.path.join(attractions_dir, subdir)
        if os.path.exists(subdir_path) and os.path.isdir(subdir_path):
            attraction_files.extend(glob.glob(os.path.join(subdir_path, "*.json")))
    
    logger.info(f"Found {len(attraction_files)} attraction JSON files")
    
    # Process each file
    for file_path in attraction_files:
        data = load_json_data(file_path)
        if data:
            # Some files might contain arrays, others might be single objects
            if isinstance(data, list):
                attractions.extend(data)
            else:
                # Single attraction - ensure it has an ID
                if "id" not in data:
                    # Use the filename (without extension) as the ID
                    data["id"] = os.path.splitext(os.path.basename(file_path))[0]
                attractions.append(data)
    
    logger.info(f"Collected {len(attractions)} attractions")
    return attractions

def populate_attractions(connection, attractions):
    """Populate attractions table with data"""
    inserted_count = 0
    updated_count = 0
    error_count = 0
    
    try:
        with connection.cursor() as cursor:
            timestamp = datetime.now().isoformat()
            
            for attraction in attractions:
                # Skip if no ID
                if "id" not in attraction:
                    logger.warning(f"Skipping attraction without ID: {attraction.get('name_en', 'Unknown')}")
                    continue
                
                try:
                    # Check if attraction already exists
                    cursor.execute(
                        "SELECT id FROM attractions WHERE id = %s",
                        (attraction["id"],)
                    )
                    
                    if cursor.fetchone():
                        # Update existing attraction
                        cursor.execute(
                            """
                            UPDATE attractions
                            SET 
                                name_en = %s,
                                name_ar = %s,
                                type = %s,
                                city = %s,
                                region = %s,
                                latitude = %s,
                                longitude = %s,
                                description_en = %s,
                                description_ar = %s,
                                data = %s,
                                updated_at = %s
                            WHERE id = %s
                            """,
                            (
                                attraction.get("name_en", ""),
                                attraction.get("name_ar", ""),
                                attraction.get("type", ""),
                                attraction.get("city", ""),
                                attraction.get("region", ""),
                                attraction.get("latitude"),
                                attraction.get("longitude"),
                                attraction.get("description_en", ""),
                                attraction.get("description_ar", ""),
                                json.dumps(attraction),
                                timestamp,
                                attraction["id"]
                            )
                        )
                        updated_count += 1
                    else:
                        # Insert new attraction
                        cursor.execute(
                            """
                            INSERT INTO attractions
                            (id, name_en, name_ar, type, city, region, latitude, longitude, 
                             description_en, description_ar, data, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                attraction["id"],
                                attraction.get("name_en", ""),
                                attraction.get("name_ar", ""),
                                attraction.get("type", ""),
                                attraction.get("city", ""),
                                attraction.get("region", ""),
                                attraction.get("latitude"),
                                attraction.get("longitude"),
                                attraction.get("description_en", ""),
                                attraction.get("description_ar", ""),
                                json.dumps(attraction),
                                timestamp,
                                timestamp
                            )
                        )
                        inserted_count += 1
                except Exception as e:
                    logger.error(f"Error processing attraction {attraction.get('id', 'Unknown')}: {e}")
                    error_count += 1
                    
        logger.info(f"Inserted {inserted_count} new attractions")
        logger.info(f"Updated {updated_count} existing attractions")
        logger.info(f"Encountered {error_count} errors")
        
    except Exception as e:
        logger.error(f"Failed to populate attractions table: {e}")
        sys.exit(1)

def main():
    # Load configuration
    config = load_config()
    
    # Connect to database
    connection = connect_to_db(config["postgres_uri"])
    
    # Collect attraction data
    attractions = collect_attractions()
    
    # Populate attractions table
    populate_attractions(connection, attractions)
    
    # Close connection
    connection.close()
    logger.info("Database population completed")

if __name__ == "__main__":
    main() 