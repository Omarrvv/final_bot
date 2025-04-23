#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script

This script migrates data from SQLite to PostgreSQL for the Egypt Tourism Chatbot.
It handles schema creation, data transfer, and post-migration verification.
"""

import os
import sys
import json
import time
import logging
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from typing import Dict, List, Any, Tuple, Optional
from dotenv import load_dotenv
import argparse

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("migration")

# SQL scripts for schema creation
POSTGRES_SCHEMA_SQL = """
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgvector;

-- Create tables with appropriate data types

-- Attractions table
CREATE TABLE IF NOT EXISTS attractions (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name_en TEXT NOT NULL,
    name_ar TEXT,
    description_en TEXT,
    description_ar TEXT,
    location JSONB,
    metadata JSONB,
    images JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    embedding VECTOR(1536)
);

-- Cities table
CREATE TABLE IF NOT EXISTS cities (
    id TEXT PRIMARY KEY,
    name_en TEXT NOT NULL,
    name_ar TEXT,
    description_en TEXT,
    description_ar TEXT,
    location JSONB,
    metadata JSONB,
    images JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    embedding VECTOR(1536)
);

-- Accommodations table
CREATE TABLE IF NOT EXISTS accommodations (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name_en TEXT NOT NULL,
    name_ar TEXT,
    description_en TEXT,
    description_ar TEXT,
    location JSONB,
    price_range JSONB,
    amenities JSONB,
    metadata JSONB,
    images JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    embedding VECTOR(1536)
);

-- Restaurants table
CREATE TABLE IF NOT EXISTS restaurants (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name_en TEXT NOT NULL,
    name_ar TEXT,
    description_en TEXT,
    description_ar TEXT,
    location JSONB,
    cuisine_type JSONB,
    price_range JSONB,
    metadata JSONB,
    images JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    embedding VECTOR(1536)
);

-- Transportation table
CREATE TABLE IF NOT EXISTS transportation (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name_en TEXT NOT NULL,
    name_ar TEXT,
    description_en TEXT,
    description_ar TEXT,
    routes JSONB,
    schedule JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Practical info table
CREATE TABLE IF NOT EXISTS practical_info (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    title_en TEXT NOT NULL,
    title_ar TEXT,
    content_en TEXT,
    content_ar TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    preferences JSONB
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Analytics table
CREATE TABLE IF NOT EXISTS analytics (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    event_data JSONB,
    user_id TEXT,
    session_id TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for search performance
CREATE INDEX IF NOT EXISTS idx_attractions_name_en ON attractions USING GIN (to_tsvector('english', name_en));
CREATE INDEX IF NOT EXISTS idx_attractions_name_ar ON attractions USING GIN (to_tsvector('arabic', name_ar));
CREATE INDEX IF NOT EXISTS idx_attractions_type ON attractions(type);
CREATE INDEX IF NOT EXISTS idx_restaurants_name_en ON restaurants USING GIN (to_tsvector('english', name_en));
CREATE INDEX IF NOT EXISTS idx_accommodations_name_en ON accommodations USING GIN (to_tsvector('english', name_en));
CREATE INDEX IF NOT EXISTS idx_cities_name_en ON cities USING GIN (to_tsvector('english', name_en));

-- Add spatial indexes for location queries
"""

# Table names to migrate
TABLES_TO_MIGRATE = [
    "attractions",
    "cities",
    "accommodations",
    "restaurants",
    "transportation",
    "practical_info",
    "users",
    "sessions",
    "analytics"
]

def get_sqlite_connection(sqlite_db_path: str) -> sqlite3.Connection:
    """Connect to SQLite database."""
    try:
        conn = sqlite3.connect(sqlite_db_path)
        conn.row_factory = sqlite3.Row
        logger.info(f"Connected to SQLite database: {sqlite_db_path}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to SQLite database: {e}")
        raise

def get_postgres_connection(postgres_uri: str) -> psycopg2.extensions.connection:
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(postgres_uri)
        logger.info(f"Connected to PostgreSQL database: {postgres_uri.split('@')[-1]}")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Error connecting to PostgreSQL database: {e}")
        raise

def check_postgis_extension(pg_conn: psycopg2.extensions.connection) -> bool:
    """Check if PostGIS extension is enabled."""
    try:
        with pg_conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'postgis'")
            return cursor.fetchone() is not None
    except psycopg2.Error as e:
        logger.error(f"Error checking PostGIS extension: {e}")
        return False

def check_pgvector_extension(pg_conn: psycopg2.extensions.connection) -> bool:
    """Check if pgvector extension is enabled."""
    try:
        with pg_conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'pgvector'")
            return cursor.fetchone() is not None
    except psycopg2.Error as e:
        logger.error(f"Error checking pgvector extension: {e}")
        return False

def create_postgres_schema(pg_conn: psycopg2.extensions.connection) -> bool:
    """Create PostgreSQL schema."""
    try:
        with pg_conn.cursor() as cursor:
            cursor.execute(POSTGRES_SCHEMA_SQL)
        pg_conn.commit()
        logger.info("Created PostgreSQL schema")
        return True
    except psycopg2.Error as e:
        logger.error(f"Error creating PostgreSQL schema: {e}")
        pg_conn.rollback()
        return False

def get_table_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    """Get column names for a SQLite table."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row['name'] for row in cursor.fetchall()]
        return columns
    except sqlite3.Error as e:
        logger.error(f"Error getting columns for table {table_name}: {e}")
        return []

def get_table_data(conn: sqlite3.Connection, table_name: str) -> List[Dict[str, Any]]:
    """Get all data from a SQLite table."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        result = []
        
        for row in rows:
            # Convert sqlite3.Row to dict
            row_dict = {key: row[key] for key in row.keys()}
            # JSON-parse any string columns that look like JSON
            for key, value in row_dict.items():
                if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                    try:
                        row_dict[key] = json.loads(value)
                    except json.JSONDecodeError:
                        pass
            result.append(row_dict)
        
        return result
    except sqlite3.Error as e:
        logger.error(f"Error getting data from table {table_name}: {e}")
        return []

def check_table_exists(pg_conn: psycopg2.extensions.connection, table_name: str) -> bool:
    """Check if a table exists in PostgreSQL."""
    try:
        with pg_conn.cursor() as cursor:
        cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, (table_name,))
            return cursor.fetchone()[0]
    except psycopg2.Error as e:
        logger.error(f"Error checking if table {table_name} exists: {e}")
        return False

def migrate_table(sqlite_conn: sqlite3.Connection, pg_conn: psycopg2.extensions.connection, 
                 table_name: str, batch_size: int = 100) -> Tuple[int, int]:
    """Migrate data from SQLite to PostgreSQL for a specific table."""
    try:
        # Get columns and data from SQLite
        columns = get_table_columns(sqlite_conn, table_name)
        data = get_table_data(sqlite_conn, table_name)
        
        if not columns or not data:
            logger.warning(f"No columns or data found for table {table_name}")
            return 0, 0
            
        # Check if table exists in PostgreSQL
        if not check_table_exists(pg_conn, table_name):
            logger.warning(f"Table {table_name} does not exist in PostgreSQL")
            return 0, 0
            
        logger.info(f"Migrating table {table_name}: {len(data)} records")
        
        # For each record, insert into PostgreSQL
        inserted = 0
        errors = 0
        batches = [data[i:i+batch_size] for i in range(0, len(data), batch_size)]
        
        with pg_conn.cursor() as cursor:
            for batch in batches:
                # Create placeholders for values
                placeholders = ["%s" for _ in columns]
                placeholders_str = ", ".join(placeholders)
                
                # Create SQL for batch insert
                columns_str = ", ".join(columns)
                sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders_str}) ON CONFLICT (id) DO NOTHING"
                
                # Prepare batch data
                batch_data = []
                for row in batch:
                    # For each row, prepare values in same order as columns
                    row_values = []
                    for col in columns:
                        value = row.get(col)
                        # Convert dict to JSON string for JSONB columns
                        if isinstance(value, dict):
                            value = json.dumps(value)
                        row_values.append(value)
                    batch_data.append(row_values)
                
                try:
                    # Execute batch insert
                    execute_values(cursor, sql, batch_data, template=None, page_size=batch_size)
        pg_conn.commit()
                    inserted += len(batch)
                    logger.info(f"Inserted {len(batch)} records into {table_name}")
    except psycopg2.Error as e:
        pg_conn.rollback()
                    logger.error(f"Error inserting into {table_name}: {e}")
                    errors += len(batch)
        
        return inserted, errors
    except Exception as e:
        logger.error(f"Error migrating table {table_name}: {e}")
        return 0, 0

def update_geospatial_columns(pg_conn: psycopg2.extensions.connection) -> bool:
    """Update geospatial columns for tables with location data."""
    try:
        # Check if PostGIS is enabled
        if not check_postgis_extension(pg_conn):
            logger.error("PostGIS extension not enabled. Cannot update geospatial columns.")
            return False
            
        # Tables that have location data
        geo_tables = ["attractions", "cities", "accommodations", "restaurants"]
        
        with pg_conn.cursor() as cursor:
            for table in geo_tables:
            # Check if table exists
                if not check_table_exists(pg_conn, table):
                    logger.warning(f"Table {table} does not exist. Skipping geospatial update.")
                continue
            
                # Check if geometry column already exists
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                        AND column_name = 'geometry'
                    )
                """, (table,))
                column_exists = cursor.fetchone()[0]
                
                if column_exists:
                    logger.info(f"Geometry column already exists for table {table}")
                else:
                    # Add geometry column
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN geometry geometry(Point, 4326)")
                    logger.info(f"Added geometry column to table {table}")
                
                # Update geometry column based on location.coordinates in JSONB
                cursor.execute(f"""
                    UPDATE {table} 
                    SET geometry = ST_SetSRID(ST_MakePoint(
                        (location->>'longitude')::float,
                        (location->>'latitude')::float
                    ), 4326)
                    WHERE location ? 'longitude' AND location ? 'latitude'
                """)
                
                # Create spatial index
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_geometry ON {table} USING GIST (geometry)")
                
                pg_conn.commit()
                logger.info(f"Updated geospatial data for table {table}")
        
        return True
    except psycopg2.Error as e:
        logger.error(f"Error updating geospatial columns: {e}")
        pg_conn.rollback()
        return False

def migrate_json_files_to_postgres(pg_conn: psycopg2.extensions.connection, json_dir: str = None) -> Dict[str, int]:
    """Migrate JSON files from the data directory to PostgreSQL."""
    if json_dir is None:
        json_dir = os.path.join(project_root, 'data')
        
    if not os.path.exists(json_dir):
        logger.warning(f"JSON directory {json_dir} does not exist")
        return {}
        
    results = {}
    
    # Map of directories to table names
    dir_to_table = {
        'attractions': 'attractions',
        'cities': 'cities',
        'accommodations': 'accommodations',
        'restaurants': 'restaurants',
        'transportation': 'transportation',
        'practical_info': 'practical_info'
    }
    
    # Process JSON files in each directory
    for dir_name, table_name in dir_to_table.items():
        dir_path = os.path.join(json_dir, dir_name)
        if not os.path.exists(dir_path):
            logger.warning(f"Directory {dir_path} does not exist")
            continue
            
        # Check if table exists
        if not check_table_exists(pg_conn, table_name):
            logger.warning(f"Table {table_name} does not exist in PostgreSQL. Skipping.")
            continue
            
        # Find all JSON files in this directory
        json_files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
        if not json_files:
            logger.warning(f"No JSON files found in {dir_path}")
            continue
            
        logger.info(f"Processing {len(json_files)} JSON files from {dir_path}")
        
        # Track inserted records
        inserted_count = 0
        
        # Process each JSON file
        for json_file in json_files:
            file_path = os.path.join(dir_path, json_file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Handle both single objects and arrays of objects
                items = data if isinstance(data, list) else [data]
                
                # Insert each item into the database
                for item in items:
                    # Skip items without an ID
                    if 'id' not in item:
                        logger.warning(f"Item in {file_path} has no ID, skipping")
                        continue
                        
                    # Convert nested dictionaries to JSON strings
                    for key, value in item.items():
                        if isinstance(value, (dict, list)):
                            item[key] = json.dumps(value)
                    
                    # Prepare columns and values
                    columns = list(item.keys())
                    values = [item[col] for col in columns]
                    
                    # Insert into database
                    columns_str = ", ".join(columns)
                    placeholders_str = ", ".join(["%s" for _ in columns])
                    
                    with pg_conn.cursor() as cursor:
                        sql = f"""
                            INSERT INTO {table_name} ({columns_str})
                            VALUES ({placeholders_str})
                            ON CONFLICT (id) DO NOTHING
                        """
                        cursor.execute(sql, values)
                    
                    inserted_count += 1
                    
                # Commit after each file
                pg_conn.commit()
                logger.info(f"Processed {len(items)} items from {json_file}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON file {file_path}: {e}")
            except psycopg2.Error as e:
                pg_conn.rollback()
                logger.error(f"Database error while processing {file_path}: {e}")
                
        # Save results for this directory
        results[dir_name] = inserted_count
        
    return results

def print_migration_summary(results: Dict[str, Tuple[int, int]], json_results: Dict[str, int]) -> None:
    """Print summary of migration results."""
    print("\n=== Migration Summary ===\n")
    
    # Database migration results
    print("SQLite to PostgreSQL Migration:")
    for table, (inserted, errors) in results.items():
        status = "✅" if inserted > 0 and errors == 0 else "⚠️" if inserted > 0 else "❌"
        print(f"{status} {table}: {inserted} records inserted, {errors} errors")
    
    total_inserted = sum(inserted for inserted, _ in results.values())
    total_errors = sum(errors for _, errors in results.values())
    
    # JSON migration results
    if json_results:
        print("\nJSON Files Migration:")
        for dir_name, count in json_results.items():
            status = "✅" if count > 0 else "⚠️"
            print(f"{status} {dir_name}: {count} records inserted")
        
        json_total = sum(json_results.values())
        print(f"\nTotal from JSON: {json_total} records")
    
    # Overall summary
    print(f"\nOverall Database Migration: {total_inserted} records inserted, {total_errors} errors")
    
    if total_errors > 0:
        print("\n⚠️ Some errors occurred during migration. Check the log for details.")
    else:
        print("\n✅ Migration completed successfully!")

def main():
    """Main function to handle the migration process."""
    parser = argparse.ArgumentParser(
        description="Migrate data from SQLite to PostgreSQL for Egypt Tourism Chatbot."
    )
    parser.add_argument(
        "--sqlite-db",
        help="Path to SQLite database file (default: data/egypt_chatbot.db)"
    )
    parser.add_argument(
        "--json-dir",
        help="Directory containing JSON files to import (default: data/)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for inserts (default: 100)"
    )
    parser.add_argument(
        "--skip-json",
        action="store_true",
        help="Skip importing JSON files"
    )
    parser.add_argument(
        "--skip-sqlite",
        action="store_true",
        help="Skip importing from SQLite"
    )
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Get database paths
    sqlite_db_path = args.sqlite_db or os.path.join(project_root, 'data', 'egypt_chatbot.db')
    postgres_uri = os.environ.get("POSTGRES_URI")
    
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable not set")
        print("Error: POSTGRES_URI environment variable not set.")
        print("Run 'python scripts/configure_postgres.py' to set up PostgreSQL connection.")
        return False
    
    # Connect to databases
    try:
    pg_conn = get_postgres_connection(postgres_uri)
        
        # Check required extensions
        postgis_enabled = check_postgis_extension(pg_conn)
        pgvector_enabled = check_pgvector_extension(pg_conn)
        
        if not postgis_enabled or not pgvector_enabled:
            logger.error("Required PostgreSQL extensions not enabled")
            print("Error: Required PostgreSQL extensions not enabled.")
            print("Run 'python scripts/enable_postgres_extensions.py --enable' to enable them.")
            pg_conn.close()
            return False
        
        # Create schema
        if not create_postgres_schema(pg_conn):
            logger.error("Failed to create PostgreSQL schema")
            pg_conn.close()
            return False
        
        # Migrate from SQLite if not skipped
        results = {}
        if not args.skip_sqlite and os.path.exists(sqlite_db_path):
            sqlite_conn = get_sqlite_connection(sqlite_db_path)
    
    # Migrate each table
            for table in TABLES_TO_MIGRATE:
                results[table] = migrate_table(sqlite_conn, pg_conn, table, args.batch_size)
            
            # Update geospatial columns
            update_geospatial_columns(pg_conn)
            
            sqlite_conn.close()
        else:
            logger.info("Skipping SQLite migration")
        
        # Migrate JSON files if not skipped
        json_results = {}
        if not args.skip_json:
            json_results = migrate_json_files_to_postgres(pg_conn, args.json_dir)
        else:
            logger.info("Skipping JSON file migration")
    
        # Print summary
        print_migration_summary(results, json_results)
        
        # Close PostgreSQL connection
    pg_conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 