#!/usr/bin/env python3
"""
Script to fix the restaurants table structure and data in PostgreSQL.
This script ensures that cuisine data from JSON files is correctly
populated into the cuisine column, and adds necessary indexes.
"""

import os
import json
import logging
import psycopg2
from psycopg2.extras import Json, DictCursor
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

def check_restaurants_table(conn):
    """Check if restaurants table exists and its structure."""
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'restaurants'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                logger.error("Restaurants table does not exist!")
                return False, None
            
            # Get table columns
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'restaurants'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            column_names = [col['column_name'] for col in columns]
            
            logger.info(f"Restaurants table has {len(columns)} columns: {', '.join(column_names)}")
            
            # Check for specific columns we're interested in
            has_cuisine = 'cuisine' in column_names
            has_cuisine_type = 'cuisine_type' in column_names
            has_city = 'city' in column_names
            
            if has_cuisine and has_cuisine_type:
                logger.info("Table has both 'cuisine' and 'cuisine_type' columns - will consolidate")
            elif has_cuisine:
                logger.info("Table has 'cuisine' column")
            elif has_cuisine_type:
                logger.info("Table has 'cuisine_type' column - will rename to 'cuisine'")
            else:
                logger.warning("Neither 'cuisine' nor 'cuisine_type' column exists - will add 'cuisine' column")
                
            return True, {
                'column_names': column_names,
                'has_cuisine': has_cuisine,
                'has_cuisine_type': has_cuisine_type,
                'has_city': has_city
            }
    except Exception as e:
        logger.error(f"Error checking restaurants table: {e}")
        return False, None

def fix_restaurants_table_structure(conn, table_info):
    """Fix restaurants table structure."""
    try:
        with conn.cursor() as cursor:
            # Add missing columns
            if not table_info['has_cuisine'] and not table_info['has_cuisine_type']:
                logger.info("Adding 'cuisine' column to restaurants table")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN cuisine TEXT;")
                table_info['has_cuisine'] = True
            
            # Add city column if missing
            if not table_info['has_city']:
                logger.info("Adding 'city' column to restaurants table")
                cursor.execute("ALTER TABLE restaurants ADD COLUMN city TEXT;")
                table_info['has_city'] = True
            
            # Rename cuisine_type to cuisine if cuisine doesn't exist
            if not table_info['has_cuisine'] and table_info['has_cuisine_type']:
                logger.info("Renaming 'cuisine_type' column to 'cuisine'")
                cursor.execute("ALTER TABLE restaurants RENAME COLUMN cuisine_type TO cuisine;")
                table_info['has_cuisine'] = True
                table_info['has_cuisine_type'] = False
            
            conn.commit()
            logger.info("Table structure fixed successfully")
            return True
    
    except Exception as e:
        logger.error(f"Error fixing restaurants table structure: {e}")
        conn.rollback()
        return False

def update_restaurants_data(conn, table_info):
    """Update restaurants data from JSONB fields."""
    try:
        with conn.cursor() as cursor:
            updates_made = 0
            
            # If both cuisine and cuisine_type exist, migrate data
            if table_info['has_cuisine'] and table_info['has_cuisine_type']:
                logger.info("Migrating data from cuisine_type to cuisine where cuisine is NULL")
                cursor.execute("""
                    UPDATE restaurants 
                    SET cuisine = cuisine_type 
                    WHERE cuisine IS NULL AND cuisine_type IS NOT NULL;
                """)
                updates_made += cursor.rowcount
            
            # Update cuisine from the JSONB fields if applicable
            if table_info['has_cuisine']:
                logger.info("Updating cuisine from JSONB name->>'cuisine' field where applicable")
                cursor.execute("""
                    UPDATE restaurants 
                    SET cuisine = name->>'cuisine' 
                    WHERE cuisine IS NULL AND name IS NOT NULL AND name->>'cuisine' IS NOT NULL;
                """)
                updates_made += cursor.rowcount
                
                # Also try to get cuisine from the 'type' field if it exists and cuisine is still NULL
                cursor.execute("""
                    UPDATE restaurants 
                    SET cuisine = type 
                    WHERE cuisine IS NULL AND type IS NOT NULL;
                """)
                updates_made += cursor.rowcount
            
            # Update city from location JSONB if applicable and city is NULL
            if table_info['has_city']:
                logger.info("Updating city from location->>'district' field where applicable")
                cursor.execute("""
                    UPDATE restaurants 
                    SET city = location->>'district' 
                    WHERE city IS NULL AND location IS NOT NULL AND location->>'district' IS NOT NULL;
                """)
                updates_made += cursor.rowcount
            
            conn.commit()
            logger.info(f"Data updated successfully with {updates_made} changes")
            return True
    
    except Exception as e:
        logger.error(f"Error updating restaurants data: {e}")
        conn.rollback()
        return False

def create_restaurants_indexes(conn, table_info):
    """Create necessary indexes on restaurants table."""
    try:
        with conn.cursor() as cursor:
            # Define indexes to create
            indexes = []
            
            if table_info['has_cuisine']:
                indexes.append(("idx_restaurants_cuisine", "cuisine"))
            
            if table_info['has_city']:
                indexes.append(("idx_restaurants_city", "city"))
            
            # Add other common indexes
            if "name_en" in table_info['column_names']:
                indexes.append(("idx_restaurants_name_en", "name_en"))
            
            if "name_ar" in table_info['column_names']:
                indexes.append(("idx_restaurants_name_ar", "name_ar"))
            
            # Create regular indexes
            for index_name, column in indexes:
                logger.info(f"Creating index {index_name} on column {column}")
                try:
                    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON restaurants ({column})"
                    cursor.execute(sql)
                except Exception as e:
                    logger.warning(f"Error creating index {index_name}: {e}")
            
            # Create JSONB indexes if needed
            if "name" in table_info['column_names']:
                try:
                    logger.info("Creating GIN index on name JSONB field")
                    sql = "CREATE INDEX IF NOT EXISTS idx_restaurants_name_gin ON restaurants USING GIN (name)"
                    cursor.execute(sql)
                except Exception as e:
                    logger.warning(f"Error creating GIN index on name: {e}")
            
            if "description" in table_info['column_names']:
                try:
                    logger.info("Creating GIN index on description JSONB field")
                    sql = "CREATE INDEX IF NOT EXISTS idx_restaurants_description_gin ON restaurants USING GIN (description)"
                    cursor.execute(sql)
                except Exception as e:
                    logger.warning(f"Error creating GIN index on description: {e}")
            
            conn.commit()
            logger.info("Indexes created successfully")
            return True
    
    except Exception as e:
        logger.error(f"Error creating restaurants indexes: {e}")
        conn.rollback()
        return False

def collect_restaurants(base_dir='data/restaurants'):
    """Collect restaurant data from JSON files."""
    restaurants = []
    restaurant_files = glob.glob(f"{base_dir}/**/*.json", recursive=True)
    
    logger.info(f"Found {len(restaurant_files)} restaurant JSON files")
    
    for file_path in restaurant_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    restaurants.extend(data)
                else:
                    restaurants.append(data)
        except Exception as e:
            logger.error(f"Error loading restaurant data from {file_path}: {e}")
    
    logger.info(f"Collected {len(restaurants)} restaurants")
    return restaurants

def update_from_json_files(conn, restaurants):
    """Update restaurants table from JSON files."""
    try:
        updated = 0
        inserted = 0
        errors = 0
        
        with conn.cursor() as cursor:
            for restaurant in restaurants:
                try:
                    restaurant_id = restaurant.get('id')
                    if not restaurant_id:
                        logger.warning(f"Skipping restaurant without ID")
                        continue
                    
                    # Check if restaurant exists
                    cursor.execute("SELECT 1 FROM restaurants WHERE id = %s", (restaurant_id,))
                    exists = cursor.fetchone() is not None
                    
                    # Prepare data
                    name = Json(restaurant.get('name', {}))
                    location = Json(restaurant.get('location', {}))
                    description = Json(restaurant.get('description', {}))
                    cuisine = restaurant.get('cuisine', restaurant.get('type'))
                    
                    # Get city from location if possible
                    city = None
                    if 'location' in restaurant and 'district' in restaurant['location']:
                        city = restaurant['location']['district']
                    
                    if exists:
                        # Update existing restaurant
                        cursor.execute("""
                            UPDATE restaurants
                            SET name = %s, location = %s, description = %s, cuisine = %s, city = %s
                            WHERE id = %s
                        """, (
                            name, location, description, cuisine, city, restaurant_id
                        ))
                        updated += 1
                    else:
                        # Insert new restaurant
                        cursor.execute("""
                            INSERT INTO restaurants (id, name, location, description, cuisine, city)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            restaurant_id, name, location, description, cuisine, city
                        ))
                        inserted += 1
                
                except Exception as e:
                    logger.error(f"Error processing restaurant {restaurant.get('id', 'unknown')}: {e}")
                    errors += 1
                    continue
            
            conn.commit()
        
        logger.info(f"JSON update completed: {inserted} inserted, {updated} updated, {errors} errors")
        return True
    
    except Exception as e:
        logger.error(f"Error updating from JSON files: {e}")
        conn.rollback()
        return False

def main():
    """Main function to fix restaurants table."""
    config = load_config()
    conn = connect_to_db(config['pg_uri'])
    
    try:
        # Check restaurants table
        table_exists, table_info = check_restaurants_table(conn)
        if not table_exists:
            logger.error("Cannot proceed without restaurants table")
            return
        
        # Fix table structure
        if not fix_restaurants_table_structure(conn, table_info):
            logger.error("Failed to fix table structure, aborting")
            return
        
        # Update restaurants data from existing fields
        if not update_restaurants_data(conn, table_info):
            logger.error("Failed to update restaurant data, aborting")
            return
        
        # Create necessary indexes
        if not create_restaurants_indexes(conn, table_info):
            logger.error("Failed to create indexes, aborting")
            return
        
        # Update from JSON files if needed
        restaurants = collect_restaurants()
        if restaurants:
            if not update_from_json_files(conn, restaurants):
                logger.error("Failed to update from JSON files")
        
        logger.info("Restaurants table fixed successfully")
    
    finally:
        conn.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    main() 