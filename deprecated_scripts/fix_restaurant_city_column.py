#!/usr/bin/env python3
"""
Script to fix the restaurant table schema by adding a missing 'city' column
and populating it from the 'location' JSONB field.
"""

import os
import logging
import psycopg2
import psycopg2.extras
import json
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from .env file."""
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(dotenv_path)
    
    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable not set")
        exit(1)
        
    logger.info(f"Using PostgreSQL URI: {postgres_uri}")
    return postgres_uri

def connect_to_postgres(postgres_uri):
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(postgres_uri)
        logger.info("Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        exit(1)

def check_column_exists(conn, table, column):
    """Check if a column exists in a table."""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        """, (table, column))
        return cursor.fetchone() is not None

def add_city_column(conn):
    """Add the city column to the restaurants table."""
    try:
        with conn.cursor() as cursor:
            # Check if city column already exists
            if check_column_exists(conn, 'restaurants', 'city'):
                logger.info("City column already exists in restaurants table")
                return
                
            # Add city column
            cursor.execute("""
                ALTER TABLE restaurants
                ADD COLUMN city TEXT
            """)
            conn.commit()
            logger.info("Added city column to restaurants table")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding city column: {e}")
        raise

def populate_city_from_location(conn):
    """Populate the city column from the location JSONB field."""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # Get all restaurants with location data
            cursor.execute("""
                SELECT id, location 
                FROM restaurants 
                WHERE location IS NOT NULL
            """)
            restaurants = cursor.fetchall()
            
            logger.info(f"Found {len(restaurants)} restaurants with location data")
            
            updated_count = 0
            for restaurant in restaurants:
                try:
                    location = restaurant['location']
                    if isinstance(location, str):
                        location = json.loads(location)
                        
                    # Try different possible fields for city
                    city = None
                    if isinstance(location, dict):
                        if 'city' in location:
                            city = location['city']
                        elif 'address' in location and 'city' in location['address']:
                            city = location['address']['city']
                        elif 'address' in location and isinstance(location['address'], str) and ',' in location['address']:
                            # Try to extract city from comma-separated address
                            parts = location['address'].split(',')
                            if len(parts) >= 2:
                                city = parts[1].strip()
                    
                    if city:
                        with conn.cursor() as update_cursor:
                            update_cursor.execute("""
                                UPDATE restaurants 
                                SET city = %s 
                                WHERE id = %s
                            """, (city, restaurant['id']))
                            updated_count += 1
                except Exception as e:
                    logger.warning(f"Error processing restaurant {restaurant['id']}: {e}")
                    continue
            
            conn.commit()
            logger.info(f"Updated city for {updated_count} restaurants")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error populating city from location: {e}")
        raise

def create_city_index(conn):
    """Create the index on the city column."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_restaurants_city 
                ON restaurants (city)
            """)
            conn.commit()
            logger.info("Created index on city column in restaurants table")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating city index: {e}")
        raise

def main():
    """Main entry point for the script."""
    logger.info("Starting restaurant table fix")
    
    postgres_uri = load_config()
    conn = connect_to_postgres(postgres_uri)
    
    try:
        # Add city column if it doesn't exist
        add_city_column(conn)
        
        # Populate city column from location data
        populate_city_from_location(conn)
        
        # Create index on city column
        create_city_index(conn)
        
        logger.info("Restaurant table fix completed successfully")
    except Exception as e:
        logger.error(f"Error fixing restaurant table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main() 