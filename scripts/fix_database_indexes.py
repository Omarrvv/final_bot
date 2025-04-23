#!/usr/bin/env python3
"""
Script to fix database indexes, especially removing references to the non-existent "data" column
in PostgreSQL tables and creating appropriate indexes for the JSONB structure.
"""

import os
import logging
import psycopg2
from dotenv import load_dotenv

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

def get_existing_indexes(conn, table_name):
    """Get all existing indexes for a table."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = %s
            """, (table_name,))
            indexes = cur.fetchall()
            return {index[0]: index[1] for index in indexes}
    except Exception as e:
        logger.error(f"Error getting indexes for {table_name}: {e}")
        return {}

def drop_index(conn, index_name):
    """Drop an index."""
    try:
        with conn.cursor() as cur:
            cur.execute(f"DROP INDEX IF EXISTS {index_name}")
            logger.info(f"Dropped index {index_name}")
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error dropping index {index_name}: {e}")
        conn.rollback()
        return False

def create_index(conn, table, column, index_type=None, index_name=None):
    """Create an index on the specified column."""
    if index_name is None:
        index_name = f"idx_{table}_{column.replace('->', '_')}"
    
    index_type_clause = f"USING {index_type}" if index_type else ""
    
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} {index_type_clause} ({column})")
            logger.info(f"Created index {index_name}")
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error creating index: {e}")
        conn.rollback()
        return False

def create_jsonb_index(conn, table, jsonb_column, jsonb_path, index_name=None, index_type="gin"):
    """Create an index on a JSONB field."""
    if index_name is None:
        path_str = jsonb_path.replace("->", "_").replace("'", "").replace('"', "")
        index_name = f"idx_{table}_{jsonb_column}_{path_str}"
    
    try:
        with conn.cursor() as cur:
            if "->" in jsonb_path:
                # For nested JSONB fields
                cur.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} USING {index_type} (({jsonb_column}{jsonb_path}))")
            else:
                # For entire JSONB column
                cur.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} USING {index_type} ({jsonb_column})")
            logger.info(f"Created JSONB index {index_name}")
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error creating JSONB index: {e}")
        conn.rollback()
        return False

def fix_restaurant_indexes(conn):
    """Fix indexes for the restaurants table."""
    table_name = "restaurants"
    
    # Get existing indexes
    existing_indexes = get_existing_indexes(conn, table_name)
    logger.info(f"Found {len(existing_indexes)} existing indexes for {table_name}")
    
    # Drop problematic indexes
    for index_name, index_def in existing_indexes.items():
        if "data" in index_def:
            logger.info(f"Found problematic index referencing 'data' column: {index_name}")
            drop_index(conn, index_name)
    
    # Create appropriate indexes
    create_index(conn, table_name, "name_en")
    create_index(conn, table_name, "name_ar")
    create_index(conn, table_name, "cuisine_type")
    create_index(conn, table_name, "city")
    
    # Create JSONB indexes
    create_jsonb_index(conn, table_name, "name", "")
    create_jsonb_index(conn, table_name, "description", "")
    create_jsonb_index(conn, table_name, "name", "->>'en'", f"idx_{table_name}_name_en_jsonb")
    create_jsonb_index(conn, table_name, "name", "->>'ar'", f"idx_{table_name}_name_ar_jsonb")
    
    # Create or ensure GiST index for geospatial column
    found_geom_index = False
    for index_name, index_def in existing_indexes.items():
        if "geom" in index_def and "gist" in index_def.lower():
            found_geom_index = True
            break
    
    if not found_geom_index:
        create_index(conn, table_name, "geom", "gist", f"idx_{table_name}_geom")
    
    logger.info(f"Fixed indexes for {table_name}")
    return True

def fix_hotel_indexes(conn):
    """Fix indexes for the hotels table."""
    table_name = "hotels"
    
    # Get existing indexes
    existing_indexes = get_existing_indexes(conn, table_name)
    logger.info(f"Found {len(existing_indexes)} existing indexes for {table_name}")
    
    # Drop problematic indexes
    for index_name, index_def in existing_indexes.items():
        if "data" in index_def:
            logger.info(f"Found problematic index referencing 'data' column: {index_name}")
            drop_index(conn, index_name)
    
    # Create appropriate indexes
    create_index(conn, table_name, "name_en")
    create_index(conn, table_name, "name_ar")
    create_index(conn, table_name, "type")
    create_index(conn, table_name, "category")
    create_index(conn, table_name, "city")
    
    # Create JSONB indexes
    create_jsonb_index(conn, table_name, "name", "")
    create_jsonb_index(conn, table_name, "description", "")
    create_jsonb_index(conn, table_name, "name", "->>'en'", f"idx_{table_name}_name_en_jsonb")
    create_jsonb_index(conn, table_name, "name", "->>'ar'", f"idx_{table_name}_name_ar_jsonb")
    
    # Create or ensure GiST index for geospatial column
    found_geom_index = False
    for index_name, index_def in existing_indexes.items():
        if "geom" in index_def and "gist" in index_def.lower():
            found_geom_index = True
            break
    
    if not found_geom_index:
        create_index(conn, table_name, "geom", "gist", f"idx_{table_name}_geom")
    
    logger.info(f"Fixed indexes for {table_name}")
    return True

def fix_attraction_indexes(conn):
    """Fix indexes for the attractions table."""
    table_name = "attractions"
    
    # Get existing indexes
    existing_indexes = get_existing_indexes(conn, table_name)
    logger.info(f"Found {len(existing_indexes)} existing indexes for {table_name}")
    
    # Drop problematic indexes
    for index_name, index_def in existing_indexes.items():
        if "data" in index_def:
            logger.info(f"Found problematic index referencing 'data' column: {index_name}")
            drop_index(conn, index_name)
    
    # Create appropriate indexes
    create_index(conn, table_name, "name_en")
    create_index(conn, table_name, "name_ar")
    create_index(conn, table_name, "type")
    create_index(conn, table_name, "city_id")
    
    # Create JSONB indexes for attractions if they exist as JSONB
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'attractions' AND column_name = 'name'
            """)
            data_type = cur.fetchone()
            
            if data_type and data_type[0] == 'jsonb':
                create_jsonb_index(conn, table_name, "name", "")
                create_jsonb_index(conn, table_name, "description", "")
                create_jsonb_index(conn, table_name, "name", "->>'en'", f"idx_{table_name}_name_en_jsonb")
                create_jsonb_index(conn, table_name, "name", "->>'ar'", f"idx_{table_name}_name_ar_jsonb")
    except Exception as e:
        logger.error(f"Error checking JSONB columns for attractions: {e}")
    
    # Create or ensure GiST index for geospatial column
    found_geom_index = False
    for index_name, index_def in existing_indexes.items():
        if "geom" in index_def and "gist" in index_def.lower():
            found_geom_index = True
            break
    
    if not found_geom_index:
        create_index(conn, table_name, "geom", "gist", f"idx_{table_name}_geom")
    
    logger.info(f"Fixed indexes for {table_name}")
    return True

def main():
    """Main function to fix database indexes."""
    config = load_config()
    conn = connect_to_db(config['pg_uri'])
    
    try:
        # Fix indexes for each table
        fix_restaurant_indexes(conn)
        fix_hotel_indexes(conn)
        fix_attraction_indexes(conn)
        
        logger.info("Database indexes fixed successfully")
    
    finally:
        conn.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    main() 