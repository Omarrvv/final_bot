#!/usr/bin/env python3
"""
Script to populate hotels and attractions tables in PostgreSQL database from JSON files.
This script ensures that data from JSON files is correctly loaded and indexes are created.
"""

import os
import json
import logging
import psycopg2
from psycopg2.extras import Json, DictCursor
from dotenv import load_dotenv
import glob
from pathlib import Path
import sys
import traceback

# Configure logging - make it more verbose
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose output
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Log to stdout
        logging.FileHandler('populate_data.log')  # Also log to file
    ]
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
        logger.error(traceback.format_exc())
        raise

def check_table(conn, table_name):
    """Check if a table exists and its structure."""
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Check if table exists
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                logger.error(f"{table_name} table does not exist!")
                return False, None
            
            # Get table columns
            cursor.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            column_names = [col['column_name'] for col in columns]
            
            logger.info(f"{table_name} table has {len(columns)} columns: {', '.join(column_names)}")
            
            # Check for specific columns based on table type
            has_city = 'city' in column_names
            has_type = 'type' in column_names
            
            return True, {
                'column_names': column_names,
                'has_city': has_city,
                'has_type': has_type
            }
    except Exception as e:
        logger.error(f"Error checking {table_name} table: {e}")
        logger.error(traceback.format_exc())
        return False, None

def create_indexes(conn, table_name, table_info):
    """Create necessary indexes on table."""
    try:
        with conn.cursor() as cursor:
            # Define indexes to create
            indexes = []
            
            if table_info['has_city']:
                indexes.append((f"idx_{table_name}_city", "city"))
            
            if table_info['has_type']:
                indexes.append((f"idx_{table_name}_type", "type"))
            
            # Add other common indexes
            if "name_en" in table_info['column_names']:
                indexes.append((f"idx_{table_name}_name_en", "name_en"))
            
            if "name_ar" in table_info['column_names']:
                indexes.append((f"idx_{table_name}_name_ar", "name_ar"))
            
            # Create regular indexes
            for index_name, column in indexes:
                logger.info(f"Creating index {index_name} on column {column}")
                try:
                    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column})"
                    cursor.execute(sql)
                except Exception as e:
                    logger.warning(f"Error creating index {index_name}: {e}")
            
            # Create JSONB indexes if needed
            if "name" in table_info['column_names']:
                try:
                    logger.info(f"Creating GIN index on name JSONB field for {table_name}")
                    sql = f"CREATE INDEX IF NOT EXISTS idx_{table_name}_name_gin ON {table_name} USING GIN (name)"
                    cursor.execute(sql)
                except Exception as e:
                    logger.warning(f"Error creating GIN index on name: {e}")
            
            if "description" in table_info['column_names']:
                try:
                    logger.info(f"Creating GIN index on description JSONB field for {table_name}")
                    sql = f"CREATE INDEX IF NOT EXISTS idx_{table_name}_description_gin ON {table_name} USING GIN (description)"
                    cursor.execute(sql)
                except Exception as e:
                    logger.warning(f"Error creating GIN index on description: {e}")
            
            conn.commit()
            logger.info(f"Indexes created successfully for {table_name}")
            return True
    
    except Exception as e:
        logger.error(f"Error creating indexes for {table_name}: {e}")
        logger.error(traceback.format_exc())
        conn.rollback()
        return False

def collect_hotels(base_dir='data/accommodations'):
    """Collect hotel data from JSON files."""
    hotels = []
    
    # List all files and directories in the base_dir to debug
    logger.debug(f"Current working directory: {os.getcwd()}")
    
    # Check if the directory exists
    if not os.path.exists(base_dir):
        logger.error(f"Directory {base_dir} does not exist!")
        # Try to list parent directory
        parent_dir = os.path.dirname(base_dir)
        if os.path.exists(parent_dir):
            logger.debug(f"Contents of parent directory {parent_dir}:")
            for item in os.listdir(parent_dir):
                logger.debug(f"  - {item}")
        return []
    
    # List all files in the directory to debug
    logger.debug(f"Contents of directory {base_dir}:")
    for item in os.listdir(base_dir):
        logger.debug(f"  - {item}")
    
    hotel_files = glob.glob(f"{base_dir}/**/*.json", recursive=True)
    
    logger.info(f"Found {len(hotel_files)} hotel JSON files")
    # List all found JSON files
    for file_path in hotel_files:
        logger.debug(f"  - {file_path}")
    
    for file_path in hotel_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                logger.debug(f"Reading {file_path}")
                data = json.load(f)
                if isinstance(data, list):
                    logger.debug(f"Found {len(data)} hotels in {file_path}")
                    hotels.extend(data)
                else:
                    logger.debug(f"Found 1 hotel in {file_path}")
                    hotels.append(data)
        except Exception as e:
            logger.error(f"Error loading hotel data from {file_path}: {e}")
            logger.error(traceback.format_exc())
    
    logger.info(f"Collected {len(hotels)} hotels")
    return hotels

def collect_attractions(base_dir='data/attractions'):
    """Collect attraction data from JSON files."""
    attractions = []
    
    # Check if the directory exists
    if not os.path.exists(base_dir):
        logger.error(f"Directory {base_dir} does not exist!")
        # Try to list parent directory
        parent_dir = os.path.dirname(base_dir)
        if os.path.exists(parent_dir):
            logger.debug(f"Contents of parent directory {parent_dir}:")
            for item in os.listdir(parent_dir):
                logger.debug(f"  - {item}")
        return []
    
    # List all files in the directory to debug
    logger.debug(f"Contents of directory {base_dir}:")
    for item in os.listdir(base_dir):
        logger.debug(f"  - {item}")
    
    attraction_files = glob.glob(f"{base_dir}/**/*.json", recursive=True)
    
    logger.info(f"Found {len(attraction_files)} attraction JSON files")
    # List all found JSON files
    for file_path in attraction_files:
        logger.debug(f"  - {file_path}")
    
    for file_path in attraction_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                logger.debug(f"Reading {file_path}")
                data = json.load(f)
                if isinstance(data, list):
                    logger.debug(f"Found {len(data)} attractions in {file_path}")
                    attractions.extend(data)
                else:
                    logger.debug(f"Found 1 attraction in {file_path}")
                    attractions.append(data)
        except Exception as e:
            logger.error(f"Error loading attraction data from {file_path}: {e}")
            logger.error(traceback.format_exc())
    
    logger.info(f"Collected {len(attractions)} attractions")
    return attractions

def update_hotels(conn, hotels):
    """Update hotels table from JSON files."""
    try:
        updated = 0
        inserted = 0
        errors = 0
        
        with conn.cursor() as cursor:
            for hotel in hotels:
                try:
                    hotel_id = hotel.get('id')
                    if not hotel_id:
                        logger.warning(f"Skipping hotel without ID")
                        continue
                    
                    # Check if hotel exists
                    cursor.execute("SELECT 1 FROM hotels WHERE id = %s", (hotel_id,))
                    exists = cursor.fetchone() is not None
                    
                    # Prepare data
                    name = Json(hotel.get('name', {}))
                    location = Json(hotel.get('location', {}))
                    description = Json(hotel.get('description', {}))
                    
                    # Get type and category if available
                    hotel_type = hotel.get('type')
                    category = hotel.get('category')
                    
                    # Get city from location if possible
                    city = None
                    if 'location' in hotel and 'city' in hotel['location']:
                        city = hotel['location']['city']
                    elif 'location' in hotel and 'district' in hotel['location']:
                        city = hotel['location']['district']
                    
                    # Extract English and Arabic names if they exist
                    name_en = None
                    name_ar = None
                    if isinstance(hotel.get('name'), dict):
                        name_en = hotel['name'].get('en')
                        name_ar = hotel['name'].get('ar')
                    
                    if exists:
                        # Update existing hotel
                        logger.debug(f"Updating existing hotel: {hotel_id}")
                        cursor.execute("""
                            UPDATE hotels
                            SET name = %s, type = %s, category = %s, location = %s, 
                                description = %s, city = %s, name_en = %s, name_ar = %s
                            WHERE id = %s
                        """, (
                            name, hotel_type, category, location, description, 
                            city, name_en, name_ar, hotel_id
                        ))
                        updated += 1
                    else:
                        # Insert new hotel
                        logger.debug(f"Inserting new hotel: {hotel_id}")
                        cursor.execute("""
                            INSERT INTO hotels (id, name, type, category, location, 
                                              description, city, name_en, name_ar)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            hotel_id, name, hotel_type, category, location, 
                            description, city, name_en, name_ar
                        ))
                        inserted += 1
                
                except Exception as e:
                    logger.error(f"Error processing hotel {hotel.get('id', 'unknown')}: {e}")
                    logger.error(traceback.format_exc())
                    errors += 1
                    continue
            
            conn.commit()
        
        logger.info(f"Hotels update completed: {inserted} inserted, {updated} updated, {errors} errors")
        return True
    
    except Exception as e:
        logger.error(f"Error updating hotels: {e}")
        logger.error(traceback.format_exc())
        conn.rollback()
        return False

def update_attractions(conn, attractions):
    """Update attractions table from JSON files."""
    try:
        updated = 0
        inserted = 0
        errors = 0
        
        with conn.cursor() as cursor:
            for attraction in attractions:
                try:
                    attraction_id = attraction.get('id')
                    if not attraction_id:
                        logger.warning(f"Skipping attraction without ID")
                        continue
                    
                    # Check if attraction exists
                    cursor.execute("SELECT 1 FROM attractions WHERE id = %s", (attraction_id,))
                    exists = cursor.fetchone() is not None
                    
                    # Prepare data
                    name = Json(attraction.get('name', {}))
                    location = Json(attraction.get('location', {}))
                    description = Json(attraction.get('description', {}))
                    
                    # Get type and subtype if available
                    attraction_type = attraction.get('type')
                    subtype = attraction.get('subtype')
                    
                    # Get city from location if possible
                    city = None
                    if 'location' in attraction and 'city' in attraction['location']:
                        city = attraction['location']['city']
                    elif 'location' in attraction and 'district' in attraction['location']:
                        city = attraction['location']['district']
                    
                    # Extract English and Arabic names if they exist
                    name_en = None
                    name_ar = None
                    if isinstance(attraction.get('name'), dict):
                        name_en = attraction['name'].get('en')
                        name_ar = attraction['name'].get('ar')
                    
                    # Extract coordinates if available
                    latitude = None
                    longitude = None
                    if 'location' in attraction and 'coordinates' in attraction['location']:
                        coords = attraction['location']['coordinates']
                        latitude = coords.get('latitude')
                        longitude = coords.get('longitude')
                    
                    if exists:
                        # Update existing attraction
                        logger.debug(f"Updating existing attraction: {attraction_id}")
                        cursor.execute("""
                            UPDATE attractions
                            SET name = %s, type = %s, subtype = %s, location = %s, 
                                description = %s, city = %s, name_en = %s, name_ar = %s,
                                latitude = %s, longitude = %s
                            WHERE id = %s
                        """, (
                            name, attraction_type, subtype, location, description, 
                            city, name_en, name_ar, latitude, longitude, attraction_id
                        ))
                        updated += 1
                    else:
                        # Insert new attraction
                        logger.debug(f"Inserting new attraction: {attraction_id}")
                        cursor.execute("""
                            INSERT INTO attractions (id, name, type, subtype, location, 
                                                   description, city, name_en, name_ar,
                                                   latitude, longitude)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            attraction_id, name, attraction_type, subtype, location, 
                            description, city, name_en, name_ar, latitude, longitude
                        ))
                        inserted += 1
                
                except Exception as e:
                    logger.error(f"Error processing attraction {attraction.get('id', 'unknown')}: {e}")
                    logger.error(traceback.format_exc())
                    errors += 1
                    continue
            
            conn.commit()
        
        logger.info(f"Attractions update completed: {inserted} inserted, {updated} updated, {errors} errors")
        return True
    
    except Exception as e:
        logger.error(f"Error updating attractions: {e}")
        logger.error(traceback.format_exc())
        conn.rollback()
        return False

def main():
    """Main function to populate hotels and attractions tables."""
    # List data directory contents first to diagnose
    data_dir = 'data'
    if os.path.exists(data_dir):
        logger.info(f"Contents of {data_dir} directory:")
        for item in os.listdir(data_dir):
            logger.info(f"  - {item}")
    else:
        logger.error(f"Data directory {data_dir} does not exist!")
    
    config = load_config()
    conn = connect_to_db(config['pg_uri'])
    
    try:
        # Process hotels
        logger.info("Processing hotels table")
        hotels_exist, hotels_info = check_table(conn, "hotels")
        if hotels_exist:
            # Create indexes for hotels
            create_indexes(conn, "hotels", hotels_info)
            
            # Update hotels from JSON files
            hotels = collect_hotels()
            if hotels:
                if not update_hotels(conn, hotels):
                    logger.error("Failed to update hotels from JSON files")
            else:
                logger.warning("No hotel data found in JSON files")
        else:
            logger.error("Cannot proceed with hotels - table does not exist")
        
        # Process attractions
        logger.info("Processing attractions table")
        attractions_exist, attractions_info = check_table(conn, "attractions")
        if attractions_exist:
            # Create indexes for attractions
            create_indexes(conn, "attractions", attractions_info)
            
            # Update attractions from JSON files
            attractions = collect_attractions()
            if attractions:
                if not update_attractions(conn, attractions):
                    logger.error("Failed to update attractions from JSON files")
            else:
                logger.warning("No attraction data found in JSON files")
        else:
            logger.error("Cannot proceed with attractions - table does not exist")
        
        logger.info("Population of hotels and attractions tables completed")
    
    finally:
        conn.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    main() 