#!/usr/bin/env python3
"""
Fix PostgreSQL Schema Mismatches

This script fixes the schema mismatches between the code and the database:
1. Adds missing 'name' column to restaurants table as JSONB
2. Populates the 'name' column with data from name_en and name_ar
3. Makes similar fixes for description column
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("fix_schema")

def get_postgres_connection(postgres_uri):
    """
    Connect to PostgreSQL database.
    
    Args:
        postgres_uri (str): PostgreSQL connection URI
        
    Returns:
        connection: PostgreSQL connection object
    """
    try:
        conn = psycopg2.connect(postgres_uri)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        sys.exit(1)

def column_exists(cursor, table, column):
    """
    Check if a column exists in a table.
    
    Args:
        cursor: PostgreSQL cursor
        table: Table name
        column: Column name
        
    Returns:
        bool: True if column exists, False otherwise
    """
    cursor.execute(
        "SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s)",
        (table, column)
    )
    return cursor.fetchone()[0]

def fix_restaurants_schema(cursor):
    """
    Fix restaurants table schema by adding 'name' column as JSONB.
    
    Args:
        cursor: PostgreSQL cursor
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if the table exists
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'restaurants')")
        if not cursor.fetchone()[0]:
            logger.warning("Restaurants table does not exist. Skipping.")
            return True
        
        # Check if name column already exists
        if column_exists(cursor, "restaurants", "name"):
            logger.info("'name' column already exists in restaurants table. Skipping addition.")
        else:
            # Add name column as JSONB
            logger.info("Adding 'name' column to restaurants table as JSONB")
            cursor.execute("ALTER TABLE restaurants ADD COLUMN name JSONB")
            logger.info("'name' column added to restaurants table successfully")
            
            # Update the name column with data from name_en and name_ar
            logger.info("Populating 'name' column with data from name_en and name_ar")
            cursor.execute("""
                UPDATE restaurants 
                SET name = jsonb_build_object('en', name_en, 'ar', name_ar)
                WHERE name IS NULL AND name_en IS NOT NULL
            """)
            logger.info("'name' column populated successfully")
        
        # Check if description column already exists
        if column_exists(cursor, "restaurants", "description"):
            logger.info("'description' column already exists in restaurants table. Skipping addition.")
        else:
            # Add description column as JSONB
            logger.info("Adding 'description' column to restaurants table as JSONB")
            cursor.execute("ALTER TABLE restaurants ADD COLUMN description JSONB")
            logger.info("'description' column added to restaurants table successfully")
            
            # Update the description column with data from description_en and description_ar
            logger.info("Populating 'description' column with data from description_en and description_ar")
            cursor.execute("""
                UPDATE restaurants 
                SET description = jsonb_build_object('en', description_en, 'ar', description_ar)
                WHERE description IS NULL AND description_en IS NOT NULL
            """)
            logger.info("'description' column populated successfully")
            
        return True
    except psycopg2.Error as e:
        logger.error(f"Failed to fix restaurants schema: {e}")
        return False

def fix_cities_schema(cursor):
    """
    Fix cities table schema by adding 'name' column as JSONB if needed.
    
    Args:
        cursor: PostgreSQL cursor
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if the table exists
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'cities')")
        if not cursor.fetchone()[0]:
            logger.warning("Cities table does not exist. Skipping.")
            return True
        
        # Check if name column already exists
        if column_exists(cursor, "cities", "name"):
            logger.info("'name' column already exists in cities table. Skipping addition.")
        else:
            # Add name column as JSONB
            logger.info("Adding 'name' column to cities table as JSONB")
            cursor.execute("ALTER TABLE cities ADD COLUMN name JSONB")
            logger.info("'name' column added to cities table successfully")
            
            # Update the name column with data from name_en and name_ar
            logger.info("Populating 'name' column with data from name_en and name_ar")
            cursor.execute("""
                UPDATE cities 
                SET name = jsonb_build_object('en', name_en, 'ar', name_ar)
                WHERE name IS NULL AND name_en IS NOT NULL
            """)
            logger.info("'name' column populated successfully")
        
        # Check if description column already exists
        if column_exists(cursor, "cities", "description"):
            logger.info("'description' column already exists in cities table. Skipping addition.")
        else:
            # Add description column as JSONB
            logger.info("Adding 'description' column to cities table as JSONB")
            cursor.execute("ALTER TABLE cities ADD COLUMN description JSONB")
            logger.info("'description' column added to cities table successfully")
            
            # Update the description column with data from description_en and description_ar
            logger.info("Populating 'description' column with data from description_en and description_ar")
            cursor.execute("""
                UPDATE cities 
                SET description = jsonb_build_object('en', description_en, 'ar', description_ar)
                WHERE description IS NULL AND description_en IS NOT NULL
            """)
            logger.info("'description' column populated successfully")
            
        return True
    except psycopg2.Error as e:
        logger.error(f"Failed to fix cities schema: {e}")
        return False

def main():
    """Main function to fix schema mismatches."""
    # Load environment variables
    load_dotenv()
    
    # Get PostgreSQL connection URI
    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable is not set")
        sys.exit(1)
    
    logger.info(f"Connecting to PostgreSQL database: {postgres_uri}")
    conn = get_postgres_connection(postgres_uri)
    cursor = conn.cursor()
    
    # Fix restaurants schema
    logger.info("Fixing restaurants schema...")
    success_restaurants = fix_restaurants_schema(cursor)
    if success_restaurants:
        logger.info("Restaurants schema fixed successfully")
    
    # Fix cities schema
    logger.info("Fixing cities schema...")
    success_cities = fix_cities_schema(cursor)
    if success_cities:
        logger.info("Cities schema fixed successfully")
    
    cursor.close()
    conn.close()
    logger.info("Database connection closed")
    
    if success_restaurants and success_cities:
        logger.info("Schema mismatches fixed successfully")
        return 0
    else:
        logger.error("Failed to fix all schema mismatches")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 