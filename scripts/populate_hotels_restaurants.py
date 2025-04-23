#!/usr/bin/env python3
"""
Script to populate hotels and restaurants tables in PostgreSQL database from JSON files.
"""

import os
import json
import logging
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv
import glob
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from .env file."""
    load_dotenv()
    
    # Get PostgreSQL URI from environment variables
    pg_uri = os.getenv('POSTGRES_URI', 'postgresql://omarmohamed@localhost:5432/postgres')
    logger.info(f"Using PostgreSQL URI: {pg_uri}")
    
    return {
        'pg_uri': pg_uri
    }

def connect_to_db(pg_uri):
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(pg_uri)
        logger.info(f"Connected to PostgreSQL database at {pg_uri.split('@')[1]}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL database: {e}")
        raise

def load_json_data(file_path):
    """Load data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load JSON file {file_path}: {e}")
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

def collect_restaurants(base_dir='data/restaurants'):
    """Collect restaurant data from JSON files."""
    restaurants = []
    restaurant_files = glob.glob(f"{base_dir}/**/*.json", recursive=True)
    
    logger.info(f"Found {len(restaurant_files)} restaurant JSON files")
    
    for file_path in restaurant_files:
        data = load_json_data(file_path)
        if data:
            if isinstance(data, list):
                restaurants.extend(data)
            else:
                restaurants.append(data)
    
    logger.info(f"Collected {len(restaurants)} restaurants")
    return restaurants

def populate_hotels(conn, hotels):
    """Populate hotels table with hotel data."""
    inserted = 0
    updated = 0
    errors = 0
    
    try:
        with conn.cursor() as cur:
            # First, check if the hotels table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'hotels'
                );
            """)
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                logger.info("Creating hotels table")
                cur.execute("""
                    CREATE TABLE hotels (
                        id TEXT PRIMARY KEY,
                        name JSONB NOT NULL,
                        type TEXT,
                        category TEXT,
                        location JSONB,
                        description JSONB,
                        price_min FLOAT,
                        price_max FLOAT,
                        currency TEXT,
                        rating FLOAT,
                        amenities JSONB,
                        room_types JSONB,
                        keywords JSONB,
                        metadata JSONB
                    );
                """)
                conn.commit()
            
            for hotel in hotels:
                try:
                    # Prepare hotel data for insertion
                    hotel_id = hotel.get('id')
                    if not hotel_id:
                        logger.warning(f"Skipping hotel without ID: {hotel}")
                        continue
                    
                    # Check if hotel already exists
                    cur.execute("SELECT 1 FROM hotels WHERE id = %s", (hotel_id,))
                    exists = cur.fetchone() is not None
                    
                    # Prepare JSONB fields
                    name = Json(hotel.get('name', {}))
                    location = Json(hotel.get('location', {}))
                    description = Json(hotel.get('description', {}))
                    amenities = Json(hotel.get('amenities', []))
                    room_types = Json(hotel.get('room_types', []))
                    keywords = Json(hotel.get('keywords', []))
                    metadata = Json(hotel.get('metadata', {}))
                    
                    if exists:
                        # Update existing hotel
                        cur.execute("""
                            UPDATE hotels 
                            SET name = %s, type = %s, category = %s, location = %s, 
                                description = %s, price_min = %s, price_max = %s, 
                                currency = %s, rating = %s, amenities = %s, 
                                room_types = %s, keywords = %s, metadata = %s
                            WHERE id = %s
                        """, (
                            name, hotel.get('type'), hotel.get('category'), location,
                            description, hotel.get('price_min'), hotel.get('price_max'),
                            hotel.get('currency'), hotel.get('rating'), amenities,
                            room_types, keywords, metadata, hotel_id
                        ))
                        updated += 1
                    else:
                        # Insert new hotel
                        cur.execute("""
                            INSERT INTO hotels (
                                id, name, type, category, location, description, 
                                price_min, price_max, currency, rating, amenities, 
                                room_types, keywords, metadata
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            hotel_id, name, hotel.get('type'), hotel.get('category'), 
                            location, description, hotel.get('price_min'), hotel.get('price_max'),
                            hotel.get('currency'), hotel.get('rating'), amenities,
                            room_types, keywords, metadata
                        ))
                        inserted += 1
                
                except Exception as e:
                    logger.error(f"Error processing hotel {hotel.get('id', 'unknown')}: {e}")
                    errors += 1
                    continue
            
            conn.commit()
    
    except Exception as e:
        logger.error(f"Failed to populate hotels table: {e}")
        conn.rollback()
        errors += 1
    
    logger.info(f"Hotels table population completed: {inserted} inserted, {updated} updated, {errors} errors")
    return inserted, updated, errors

def populate_restaurants(conn, restaurants):
    """Populate restaurants table with restaurant data."""
    inserted = 0
    updated = 0
    errors = 0
    
    try:
        with conn.cursor() as cur:
            # First, check if the restaurants table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'restaurants'
                );
            """)
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                logger.info("Creating restaurants table")
                cur.execute("""
                    CREATE TABLE restaurants (
                        id TEXT PRIMARY KEY,
                        name JSONB NOT NULL,
                        cuisine_type TEXT,
                        location JSONB,
                        description JSONB,
                        price_range TEXT,
                        rating FLOAT,
                        operating_hours JSONB,
                        menu_highlights JSONB,
                        keywords JSONB,
                        metadata JSONB
                    );
                """)
                conn.commit()
            
            for restaurant in restaurants:
                try:
                    # Prepare restaurant data for insertion
                    restaurant_id = restaurant.get('id')
                    if not restaurant_id:
                        logger.warning(f"Skipping restaurant without ID: {restaurant}")
                        continue
                    
                    # Check if restaurant already exists
                    cur.execute("SELECT 1 FROM restaurants WHERE id = %s", (restaurant_id,))
                    exists = cur.fetchone() is not None
                    
                    # Prepare JSONB fields
                    name = Json(restaurant.get('name', {}))
                    location = Json(restaurant.get('location', {}))
                    description = Json(restaurant.get('description', {}))
                    operating_hours = Json(restaurant.get('operating_hours', {}))
                    menu_highlights = Json(restaurant.get('menu_highlights', []))
                    keywords = Json(restaurant.get('keywords', []))
                    metadata = Json(restaurant.get('metadata', {}))
                    
                    if exists:
                        # Update existing restaurant
                        cur.execute("""
                            UPDATE restaurants 
                            SET name = %s, cuisine_type = %s, location = %s, 
                                description = %s, price_range = %s, rating = %s, 
                                operating_hours = %s, menu_highlights = %s, 
                                keywords = %s, metadata = %s
                            WHERE id = %s
                        """, (
                            name, restaurant.get('cuisine_type'), location,
                            description, restaurant.get('price_range'), restaurant.get('rating'),
                            operating_hours, menu_highlights, keywords, metadata, restaurant_id
                        ))
                        updated += 1
                    else:
                        # Insert new restaurant
                        cur.execute("""
                            INSERT INTO restaurants (
                                id, name, cuisine_type, location, description, 
                                price_range, rating, operating_hours, menu_highlights, 
                                keywords, metadata
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            restaurant_id, name, restaurant.get('cuisine_type'), location,
                            description, restaurant.get('price_range'), restaurant.get('rating'),
                            operating_hours, menu_highlights, keywords, metadata
                        ))
                        inserted += 1
                
                except Exception as e:
                    logger.error(f"Error processing restaurant {restaurant.get('id', 'unknown')}: {e}")
                    errors += 1
                    continue
            
            conn.commit()
    
    except Exception as e:
        logger.error(f"Failed to populate restaurants table: {e}")
        conn.rollback()
        errors += 1
    
    logger.info(f"Restaurants table population completed: {inserted} inserted, {updated} updated, {errors} errors")
    return inserted, updated, errors

def main():
    """Main function to populate hotels and restaurants tables."""
    config = load_config()
    conn = connect_to_db(config['pg_uri'])
    
    try:
        # Collect and populate hotels
        hotels = collect_hotels()
        if hotels:
            inserted, updated, errors = populate_hotels(conn, hotels)
            logger.info(f"Hotels population summary: {inserted} inserted, {updated} updated, {errors} errors")
        
        # Collect and populate restaurants
        restaurants = collect_restaurants()
        if restaurants:
            inserted, updated, errors = populate_restaurants(conn, restaurants)
            logger.info(f"Restaurants population summary: {inserted} inserted, {updated} updated, {errors} errors")
    
    finally:
        conn.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    main() 