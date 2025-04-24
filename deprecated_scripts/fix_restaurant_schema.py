#!/usr/bin/env python3
"""
Script to fix the restaurant table schema in PostgreSQL.
This script checks if the restaurant table has proper name columns,
adds them if missing, and updates the name values from restaurant JSON files.
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import configparser

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """Load database configuration from .env or config file."""
    # Default to environment variables
    pg_uri = os.environ.get('POSTGRES_URI', 'postgresql://omarmohamed@localhost:5432/postgres')
    
    # Try loading from config.ini if it exists
    config = configparser.ConfigParser()
    if os.path.exists('config.ini'):
        config.read('config.ini')
        if 'database' in config and 'postgres_uri' in config['database']:
            pg_uri = config['database']['postgres_uri']
    
    logger.info(f"Using PostgreSQL URI: {pg_uri}")
    return pg_uri

def connect_to_db(pg_uri):
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(pg_uri)
        logger.info("Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        sys.exit(1)

def check_table_exists(conn, table_name):
    """Check if the table exists in the database."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (table_name,))
        return cur.fetchone()[0]

def get_table_columns(conn, table_name):
    """Get the columns of a table."""
    columns = []
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s;
        """, (table_name,))
        
        for col in cur.fetchall():
            columns.append((col[0], col[1]))
            logger.info(f"- {col[0]}: {col[1]}")
    
    return columns

def ensure_name_columns(conn, columns):
    """Ensure the name_en and name_ar columns exist, add them if not."""
    required_columns = {
        'name_en': 'text',
        'name_ar': 'text'
    }
    
    existing_cols = {col[0]: col[1] for col in columns}
    
    for col_name, col_type in required_columns.items():
        if col_name not in existing_cols:
            with conn.cursor() as cur:
                try:
                    cur.execute(f"ALTER TABLE restaurants ADD COLUMN {col_name} {col_type};")
                    conn.commit()
                    logger.info(f"Added column '{col_name}' with type '{col_type}' to restaurants table")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Error adding column '{col_name}': {e}")
        else:
            logger.info(f"'{col_name}' column already exists in restaurants table")

def load_restaurant_data():
    """Load restaurant data from JSON files."""
    restaurants = []
    data_dir = os.path.join('data', 'restaurants')
    
    if not os.path.exists(data_dir):
        logger.error(f"Restaurant data directory not found: {data_dir}")
        return restaurants
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(data_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    restaurant = json.load(f)
                    restaurant_id = os.path.splitext(filename)[0]
                    restaurant['id'] = restaurant_id
                    restaurants.append(restaurant)
            except Exception as e:
                logger.error(f"Error loading restaurant file {filename}: {e}")
    
    logger.info(f"Loaded {len(restaurants)} restaurants from JSON files")
    return restaurants

def update_restaurant_names(conn, restaurants):
    """Update restaurant names based on the loaded JSON data."""
    with conn.cursor() as cur:
        for restaurant in restaurants:
            try:
                # Extract names from JSON
                name_en = None
                name_ar = None
                
                # Check different possible locations for name data
                if 'name' in restaurant:
                    if isinstance(restaurant['name'], dict):
                        name_en = restaurant['name'].get('en')
                        name_ar = restaurant['name'].get('ar')
                    elif isinstance(restaurant['name'], str):
                        name_en = restaurant['name']
                
                # Fallback checks for other name formats
                if name_en is None and 'name_en' in restaurant:
                    name_en = restaurant['name_en']
                if name_ar is None and 'name_ar' in restaurant:
                    name_ar = restaurant['name_ar']
                
                if name_en or name_ar:
                    restaurant_id = restaurant['id']
                    update_query = """
                        UPDATE restaurants
                        SET name_en = %s, 
                            name_ar = %s
                        WHERE id = %s;
                    """
                    cur.execute(update_query, (name_en, name_ar, restaurant_id))
                    conn.commit()
                    logger.info(f"Updated names for restaurant {restaurant_id}")
                else:
                    logger.warning(f"Could not find name for restaurant {restaurant['id']}")
            except Exception as e:
                conn.rollback()
                logger.error(f"Error updating restaurant {restaurant.get('id', 'unknown')}: {e}")

def update_jsonb_name_column(conn):
    """Update the JSONB 'name' column structure if needed."""
    with conn.cursor() as cur:
        try:
            # Check if any rows have NULL or invalid name column
            cur.execute("""
                SELECT COUNT(*) FROM restaurants
                WHERE name IS NULL OR NOT jsonb_typeof(name) = 'object';
            """)
            null_count = cur.fetchone()[0]
            
            if null_count > 0:
                logger.info(f"Found {null_count} restaurants with missing or invalid JSONB name structure")
                
                # Update the JSONB name column using name_en and name_ar
                cur.execute("""
                    UPDATE restaurants
                    SET name = jsonb_build_object('en', name_en, 'ar', name_ar)
                    WHERE name IS NULL OR NOT jsonb_typeof(name) = 'object';
                """)
                conn.commit()
                logger.info("Updated JSONB name column with values from name_en and name_ar")
            else:
                logger.info("All restaurants have proper JSONB name structure")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating JSONB name column: {e}")

def print_restaurant_summary(conn):
    """Print a summary of restaurant data."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, name_en, name_ar FROM restaurants
                ORDER BY id LIMIT 10;
            """)
            
            restaurants = cur.fetchall()
            logger.info(f"Restaurant summary (showing {len(restaurants)} of {len(restaurants)} records):")
            
            for r in restaurants:
                logger.info(f"ID: {r['id']}, Name (EN): {r['name_en']}, Name (AR): {r['name_ar']}")
    except Exception as e:
        logger.error(f"Error printing restaurant summary: {e}")

def main():
    """Main function to fix restaurant schema."""
    # Load configuration
    pg_uri = load_config()
    
    # Connect to database
    conn = None
    try:
        conn = connect_to_db(pg_uri)
        
        # Check if restaurant table exists
        if not check_table_exists(conn, 'restaurants'):
            logger.error("Restaurants table does not exist in the database")
            return
        
        # Get current columns
        logger.info("Current columns in restaurants table:")
        columns = get_table_columns(conn, 'restaurants')
        
        # Ensure name columns exist
        ensure_name_columns(conn, columns)
        
        # Load restaurant data from JSON files
        restaurants = load_restaurant_data()
        
        # Update restaurant names
        update_restaurant_names(conn, restaurants)
        
        # Update JSONB name column structure
        update_jsonb_name_column(conn)
        
        # Print summary of restaurant data
        print_restaurant_summary(conn)
        
        logger.info("Restaurant schema fix completed")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main() 