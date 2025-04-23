#!/usr/bin/env python3
"""
Fix the hotels table structure to match the database model requirements.
This script drops the existing hotels table, creates a new one with the correct
structure, and populates it from the JSON files in data/accommodations/.
"""

import os
import sys
import glob
import json
import logging
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("fix_hotels_table")

def load_config():
    """Load configuration from .env file."""
    load_dotenv()
    pg_uri = os.getenv("POSTGRES_URI", "postgresql://omarmohamed@localhost:5432/postgres")
    logger.info(f"Using PostgreSQL URI: {pg_uri}")
    
    return {
        "pg_uri": pg_uri
    }

def connect_to_db(pg_uri):
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(pg_uri)
        logger.info(f"Connected to PostgreSQL database at {pg_uri.split('@')[1]}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL database: {e}")
        sys.exit(1)

def load_json_data(file_path):
    """Load data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON from {file_path}: {e}")
        return None

def collect_hotels(base_dir='data/accommodations'):
    """Collect hotel data from JSON files."""
    hotels = []
    hotel_files = glob.glob(f"{base_dir}/**/*.json", recursive=True)
    
    logger.info(f"Found {len(hotel_files)} hotel JSON files")
    
    for file_path in hotel_files:
        data = load_json_data(file_path)
        if data:
            if isinstance(data, list):
                hotels.extend(data)
            else:
                hotels.append(data)
    
    logger.info(f"Collected {len(hotels)} hotels")
    return hotels

def fix_hotels_table(conn, hotels):
    """Drop and recreate the hotels table with the correct structure, then populate it."""
    inserted = 0
    errors = 0
    
    try:
        with conn.cursor() as cur:
            # First, drop the existing hotels table if it exists
            cur.execute("""
                DROP TABLE IF EXISTS hotels;
            """)
            conn.commit()
            logger.info("Dropped existing hotels table")
            
            # Create the hotels table with the correct structure
            cur.execute("""
                CREATE TABLE hotels (
                    id TEXT PRIMARY KEY,
                    name_en TEXT NOT NULL,
                    name_ar TEXT,
                    category TEXT,
                    star_rating INTEGER,
                    city TEXT,
                    region TEXT,
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    description_en TEXT,
                    description_ar TEXT,
                    price_range_min DOUBLE PRECISION,
                    price_range_max DOUBLE PRECISION,
                    currency TEXT,
                    data JSONB,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create necessary indices
            cur.execute("CREATE INDEX idx_hotels_category ON hotels(category);")
            cur.execute("CREATE INDEX idx_hotels_city ON hotels(city);")
            cur.execute("CREATE INDEX idx_hotels_star_rating ON hotels(star_rating);")
            cur.execute("CREATE INDEX idx_hotels_data ON hotels USING GIN(data);")
            
            # Add PostGIS support
            cur.execute("ALTER TABLE hotels ADD COLUMN geom GEOMETRY(Point, 4326);")
            cur.execute("CREATE INDEX idx_hotels_geom ON hotels USING GIST(geom);")
            
            conn.commit()
            logger.info("Created new hotels table with correct structure")
            
            # Populate the hotels table
            for hotel in hotels:
                try:
                    hotel_id = hotel.get('id')
                    if not hotel_id:
                        logger.warning(f"Skipping hotel without ID: {hotel}")
                        continue
                    
                    # Extract nested values for flattened columns
                    name = hotel.get('name', {})
                    name_en = name.get('en', '')
                    name_ar = name.get('ar', '')
                    
                    description = hotel.get('description', {})
                    description_en = description.get('en', '')
                    description_ar = description.get('ar', '')
                    
                    # Extract location data
                    location = hotel.get('location', {})
                    coordinates = location.get('coordinates', {})
                    latitude = coordinates.get('latitude')
                    longitude = coordinates.get('longitude')
                    
                    # Extract other fields
                    category = hotel.get('category', '')
                    star_rating = hotel.get('star_rating')
                    price_min = hotel.get('price_min')
                    price_max = hotel.get('price_max')
                    currency = hotel.get('currency', 'EGP')
                    
                    # Region/city data
                    city = location.get('city', '')
                    district = location.get('district', '')
                    
                    # Store the entire hotel data as JSONB
                    data = Json(hotel)
                    
                    # Insert the hotel
                    cur.execute("""
                        INSERT INTO hotels (
                            id, name_en, name_ar, category, star_rating, city, region,
                            latitude, longitude, description_en, description_ar,
                            price_range_min, price_range_max, currency, data, geom
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            CASE WHEN %s IS NOT NULL AND %s IS NOT NULL 
                                THEN ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                                ELSE NULL
                            END
                        )
                    """, (
                        hotel_id, name_en, name_ar, category, star_rating, city, district,
                        latitude, longitude, description_en, description_ar,
                        price_min, price_max, currency, data,
                        longitude, latitude, longitude, latitude
                    ))
                    
                    inserted += 1
                except Exception as e:
                    logger.error(f"Error processing hotel {hotel.get('id', 'unknown')}: {e}")
                    errors += 1
                    continue
            
            conn.commit()
    
    except Exception as e:
        logger.error(f"Failed to fix and populate hotels table: {e}")
        conn.rollback()
        errors += 1
    
    logger.info(f"Hotels table fix completed: {inserted} inserted, {errors} errors")
    return inserted, errors

def main():
    """Main function to fix the hotels table."""
    config = load_config()
    conn = connect_to_db(config['pg_uri'])
    
    try:
        # Collect and populate hotels
        hotels = collect_hotels()
        if hotels:
            inserted, errors = fix_hotels_table(conn, hotels)
            logger.info(f"Hotels fix summary: {inserted} inserted, {errors} errors")
        else:
            logger.error("No hotel data found")
    
    finally:
        conn.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    main() 