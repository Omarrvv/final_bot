#!/usr/bin/env python3
"""
Script to populate the PostgreSQL database with sample data.
This script populates the attractions table in the PostgreSQL database
with sample data from a JSON file.
"""

import sys
import os
import json
import psycopg2
import logging
import argparse
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
    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable not set")
        sys.exit(1)
    
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

def load_sample_data(file_path):
    """Load sample data from JSON file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} items from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Failed to load sample data from {file_path}: {e}")
        sys.exit(1)

def populate_attractions(connection, attractions):
    """Populate attractions table with sample data"""
    inserted_count = 0
    updated_count = 0
    
    try:
        with connection.cursor() as cursor:
            timestamp = datetime.now().isoformat()
            
            for attraction in attractions:
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
                    
        logger.info(f"Inserted {inserted_count} new attractions")
        logger.info(f"Updated {updated_count} existing attractions")
        
    except Exception as e:
        logger.error(f"Failed to populate attractions table: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Populate PostgreSQL database with sample data")
    parser.add_argument(
        "--data-file", 
        default="data/attractions.json", 
        help="Path to the JSON file containing attractions data"
    )
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Connect to database
    connection = connect_to_db(config["postgres_uri"])
    
    # Load sample data
    data_file = args.data_file
    attractions = load_sample_data(data_file)
    
    # Populate attractions table
    populate_attractions(connection, attractions)
    
    # Close connection
    connection.close()
    logger.info("Database population completed")

if __name__ == "__main__":
    main() 