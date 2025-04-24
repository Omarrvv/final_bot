#!/usr/bin/env python3
"""
Fix PostgreSQL Migration Issues

This script fixes the issues identified in the migration logs:
1. Fixes the accommodations table price columns to accept string prices
2. Adds the missing 'country' column to the cities table
"""

import os
import sys
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
logger = logging.getLogger("fix_migration")

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

def fix_accommodations_table(cursor):
    """
    Fix accommodations table price columns to accept string prices.
    
    Args:
        cursor: PostgreSQL cursor
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if the table exists
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'accommodations')")
        if not cursor.fetchone()[0]:
            logger.warning("Accommodations table does not exist. Skipping.")
            return True
        
        # Check column types
        cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'accommodations' AND column_name IN ('price_per_night', 'price')")
        columns = cursor.fetchall()
        
        # Alter columns to TEXT if they're numeric
        for column_name, data_type in columns:
            if data_type in ('double precision', 'numeric', 'integer'):
                logger.info(f"Converting column {column_name} from {data_type} to TEXT")
                cursor.execute(f"ALTER TABLE accommodations ALTER COLUMN {column_name} TYPE TEXT")
                logger.info(f"Column {column_name} converted to TEXT successfully")
            else:
                logger.info(f"Column {column_name} is already type {data_type}. No change needed.")
        
        return True
    except psycopg2.Error as e:
        logger.error(f"Failed to fix accommodations table: {e}")
        return False

def add_cities_country_column(cursor):
    """
    Add missing 'country' column to cities table.
    
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
        
        # Check if country column already exists
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'cities' AND column_name = 'country')")
        if cursor.fetchone()[0]:
            logger.info("Country column already exists in cities table. No change needed.")
            return True
        
        # Add country column
        logger.info("Adding 'country' column to cities table")
        cursor.execute("ALTER TABLE cities ADD COLUMN country TEXT")
        logger.info("Country column added to cities table successfully")
        
        # Set default value for existing rows
        cursor.execute("UPDATE cities SET country = 'Egypt' WHERE country IS NULL")
        logger.info("Set default country value for existing rows to 'Egypt'")
        
        return True
    except psycopg2.Error as e:
        logger.error(f"Failed to add country column to cities table: {e}")
        return False

def main():
    """Main function to fix migration issues."""
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
    
    # Fix accommodations table
    logger.info("Fixing accommodations table price columns...")
    success_accom = fix_accommodations_table(cursor)
    if success_accom:
        logger.info("Accommodations table fixed successfully")
    
    # Add cities country column
    logger.info("Adding missing country column to cities table...")
    success_cities = add_cities_country_column(cursor)
    if success_cities:
        logger.info("Cities table fixed successfully")
    
    conn.close()
    logger.info("Database connection closed")
    
    if success_accom and success_cities:
        logger.info("Migration issues fixed successfully")
        return 0
    else:
        logger.error("Failed to fix all migration issues")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 