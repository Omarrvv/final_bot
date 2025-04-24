#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script

This script migrates data from the SQLite database to PostgreSQL.
Features:
- Migrates all tables with proper schema conversion (JSON to JSONB, etc.)
- Validates data during migration
- Creates appropriate indexes
- Handles errors gracefully with proper logging
- Reports migration statistics
"""

import os
import sys
import json
import sqlite3
import psycopg2
import logging
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime
import argparse
from dotenv import load_dotenv
import time

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("migration")

def load_config():
    """Load configuration from .env file"""
    load_dotenv()
    
    # Get database URIs
    sqlite_uri = os.getenv("DATABASE_URI", "sqlite:///./data/egypt_chatbot.db")
    postgres_uri = os.getenv("POSTGRES_URI")

    logger.info(f"PostgreSQL URI from env: {postgres_uri}")
    
    if not sqlite_uri:
        logger.error("DATABASE_URI environment variable not set")
        sys.exit(1)
    
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable not set")
        sys.exit(1)
    
    # Extract the file path from the SQLite URI
    if sqlite_uri.startswith("sqlite:///"):
        sqlite_path = sqlite_uri.replace("sqlite:///", "")
    else:
        sqlite_path = sqlite_uri
    
    return {
        "sqlite_path": sqlite_path,
        "postgres_uri": postgres_uri
    }

def connect_to_sqlite(sqlite_path):
    """Connect to SQLite database"""
    try:
        connection = sqlite3.connect(sqlite_path)
        connection.row_factory = sqlite3.Row
        logger.info(f"Connected to SQLite database: {sqlite_path}")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to SQLite database: {e}")
        sys.exit(1)

def connect_to_postgres(postgres_uri):
    """Connect to PostgreSQL database"""
    try:
        connection = psycopg2.connect(postgres_uri)
        connection.autocommit = False  # We'll manage transactions manually
        logger.info(f"Connected to PostgreSQL database: {postgres_uri.split('@')[-1]}")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL database: {e}")
        sys.exit(1)

def get_sqlite_tables(sqlite_conn):
    """Get list of tables in SQLite database"""
    try:
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
    except Exception as e:
        logger.error(f"Failed to get SQLite tables: {e}")
        sys.exit(1)

def get_table_schema(sqlite_conn, table_name):
    """Get schema details for a SQLite table"""
    try:
        cursor = sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        cursor.close()
        
        schema = []
        for col in columns:
            schema.append({
                "name": col[1],
                "type": col[2],
                "is_pk": col[5] == 1
            })
        
        return schema
    except Exception as e:
        logger.error(f"Failed to get schema for table {table_name}: {e}")
        sys.exit(1)

def map_sqlite_to_postgres_type(sqlite_type, column_name):
    """Map SQLite data type to PostgreSQL data type"""
    # Remove any length specifiers, e.g., VARCHAR(255) -> VARCHAR
    base_type = sqlite_type.split('(')[0].upper() if sqlite_type else 'TEXT'
    
    # Map SQLite type to PostgreSQL type
    type_map = {
        'INTEGER': 'INTEGER',
        'INT': 'INTEGER',
        'BIGINT': 'BIGINT',
        'REAL': 'DOUBLE PRECISION',
        'FLOAT': 'DOUBLE PRECISION',
        'NUMERIC': 'NUMERIC',
        'TEXT': 'TEXT',
        'VARCHAR': 'TEXT',
        'CHAR': 'TEXT',
        'BOOLEAN': 'BOOLEAN',
        'BOOL': 'BOOLEAN',
        'BLOB': 'BYTEA',
        'DATE': 'DATE',
        'DATETIME': 'TIMESTAMP',
        'TIMESTAMP': 'TIMESTAMP WITH TIME ZONE',
        'JSON': 'JSONB'
    }
    
    # Special handling for columns likely to contain dates or JSON
    if 'date' in column_name.lower() or 'time' in column_name.lower():
        return 'TIMESTAMP WITH TIME ZONE'
    elif column_name.lower() == 'data':
        return 'JSONB'
    
    return type_map.get(base_type, 'TEXT')

def create_postgres_tables(postgres_conn, sqlite_conn, tables):
    """Create tables in PostgreSQL with appropriate schema"""
    try:
        cursor = postgres_conn.cursor()
        
        for table_name in tables:
            schema = get_table_schema(sqlite_conn, table_name)
            
            # Construct CREATE TABLE statement
            columns = []
            for col in schema:
                pg_type = map_sqlite_to_postgres_type(col['type'], col['name'])
                pk_suffix = " PRIMARY KEY" if col['is_pk'] else ""
                columns.append(f"{col['name']} {pg_type}{pk_suffix}")
            
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    " + ",\n    ".join(columns) + "\n)"
            logger.info(f"Creating table {table_name} in PostgreSQL...")
            logger.debug(f"SQL: {create_sql}")
            
            cursor.execute(create_sql)
        
        postgres_conn.commit()
        cursor.close()
        logger.info("All tables created in PostgreSQL")
    except Exception as e:
        postgres_conn.rollback()
        logger.error(f"Failed to create PostgreSQL tables: {e}")
        sys.exit(1)

def convert_value_for_postgres(value, pg_type):
    """Convert SQLite value to appropriate PostgreSQL format"""
    if value is None:
        return None
        
    try:
        if pg_type == 'JSONB':
            # If string, parse it first
            if isinstance(value, str):
                return Json(json.loads(value))
            return Json(value)
        elif pg_type.startswith('TIMESTAMP'):
            # Handle empty string
            if value == "":
                return None
                
            # Try to parse datetime string
            if isinstance(value, str):
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S.%f',
                    '%Y-%m-%d'
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                
                # If all formats fail, return the original value
                return value
            
            return value
        else:
            return value
    except Exception as e:
        logger.warning(f"Error converting value for PostgreSQL: {e} (value: {value}, type: {pg_type})")
        return value

def migrate_table(sqlite_conn, postgres_conn, table_name, batch_size=100):
    """Migrate data from SQLite to PostgreSQL for a single table"""
    try:
        logger.info(f"Migrating data for table {table_name}...")
        
        # Get table schema
        schema = get_table_schema(sqlite_conn, table_name)
        column_names = [col['name'] for col in schema]
        pg_types = [map_sqlite_to_postgres_type(col['type'], col['name']) for col in schema]
        
        # Get row count for progress tracking
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = sqlite_cursor.fetchone()[0]
        logger.info(f"Total rows to migrate for {table_name}: {total_rows}")
        
        # Create placeholders for prepared statement
        placeholders = ", ".join(["%s" for _ in column_names])
        insert_sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
        
        # Fetch data in batches and insert
        offset = 0
        rows_migrated = 0
        
        pg_cursor = postgres_conn.cursor()
        
        while True:
            sqlite_cursor.execute(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                break
            
            # Convert rows to list of tuples
            pg_rows = []
            for row in rows:
                pg_row = []
                for i, value in enumerate(row):
                    pg_value = convert_value_for_postgres(value, pg_types[i])
                    pg_row.append(pg_value)
                pg_rows.append(tuple(pg_row))
            
            # Insert rows in a single batch
            pg_cursor.executemany(insert_sql, pg_rows)
            
            rows_migrated += len(rows)
            offset += batch_size
            
            # Report progress
            progress = (rows_migrated / total_rows) * 100 if total_rows > 0 else 100
            logger.info(f"Migrated {rows_migrated}/{total_rows} rows ({progress:.2f}%) for table {table_name}")
        
        postgres_conn.commit()
        sqlite_cursor.close()
        pg_cursor.close()
        
        logger.info(f"Successfully migrated {rows_migrated} rows for table {table_name}")
        return rows_migrated
    except Exception as e:
        postgres_conn.rollback()
        logger.error(f"Failed to migrate data for table {table_name}: {e}")
        return 0

def create_postgres_indexes(postgres_conn, sqlite_conn, tables):
    """Create indexes in PostgreSQL based on SQLite indexes"""
    try:
        # Create standard indexes
        index_map = {
            'attractions': ['type', 'city', 'region'],
            'accommodations': ['type', 'city', 'category'],
            'restaurants': ['cuisine', 'city'],
            'sessions': ['expires_at'],
            'users': ['username', 'email'],
            'analytics': ['session_id', 'user_id', 'event_type', 'timestamp']
        }
        
        cursor = postgres_conn.cursor()
        
        for table, columns in index_map.items():
            if table in tables:
                for column in columns:
                    index_name = f"idx_{table}_{column}"
                    index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column})"
                    logger.info(f"Creating index {index_name}...")
                    cursor.execute(index_sql)
        
        # Create special indexes
        if 'attractions' in tables or 'accommodations' in tables or 'restaurants' in tables:
            logger.info("Creating spatial indexes...")
            # First check if PostGIS extension is available
            try:
                cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'postgis'")
                postgis_exists = cursor.fetchone() is not None
                
                if postgis_exists:
                    # Add spatial columns and indexes if PostGIS is available
                    for table in ['attractions', 'accommodations', 'restaurants']:
                        if table in tables:
                            # Add geometry column
                            cursor.execute(f"""
                                ALTER TABLE {table} 
                                ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326)
                            """)
                            
                            # Update geometry from latitude and longitude
                            cursor.execute(f"""
                                UPDATE {table} 
                                SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
                                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                                  AND geom IS NULL
                            """)
                            
                            # Create spatial index
                            cursor.execute(f"""
                                CREATE INDEX IF NOT EXISTS idx_{table}_geom 
                                ON {table} USING GIST (geom)
                            """)
                else:
                    logger.warning("PostGIS extension not found. Spatial indexes not created.")
            except Exception as e:
                logger.warning(f"Error creating spatial indexes: {e}")
        
        if 'attractions' in tables or 'restaurants' in tables or 'accommodations' in tables:
            logger.info("Creating JSONB indexes...")
            # Create JSONB indexes
            for table in ['attractions', 'restaurants', 'accommodations']:
                if table in tables:
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_{table}_data 
                        ON {table} USING GIN (data)
                    """)
        
        postgres_conn.commit()
        cursor.close()
        logger.info("All indexes created in PostgreSQL")
    except Exception as e:
        postgres_conn.rollback()
        logger.error(f"Failed to create PostgreSQL indexes: {e}")

def validate_migration(sqlite_conn, postgres_conn, tables):
    """Validate migration by comparing row counts between SQLite and PostgreSQL"""
    try:
        logger.info("Validating migration...")
        
        validation_results = {}
        all_valid = True
        
        for table in tables:
            # Get row count from SQLite
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cursor.fetchone()[0]
            sqlite_cursor.close()
            
            # Get row count from PostgreSQL
            pg_cursor = postgres_conn.cursor()
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            pg_count = pg_cursor.fetchone()[0]
            pg_cursor.close()
            
            # Compare counts
            is_valid = sqlite_count == pg_count
            percentage = (pg_count / sqlite_count * 100) if sqlite_count > 0 else 100
            
            validation_results[table] = {
                "sqlite_count": sqlite_count,
                "postgres_count": pg_count,
                "percentage": percentage,
                "is_valid": is_valid
            }
            
            if not is_valid:
                all_valid = False
        
        # Print validation results
        logger.info("Migration validation results:")
        for table, result in validation_results.items():
            status = "✅ VALID" if result["is_valid"] else "❌ INVALID"
            logger.info(f"{table}: {result['sqlite_count']} (SQLite) vs {result['postgres_count']} (PostgreSQL) - {result['percentage']:.2f}% migrated - {status}")
        
        return all_valid
    except Exception as e:
        logger.error(f"Failed to validate migration: {e}")
        return False

def main():
    """Main function for the migration script"""
    parser = argparse.ArgumentParser(description="Migrate data from SQLite to PostgreSQL")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for migration (default: 100)")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without actually migrating data")
    args = parser.parse_args()
    
    start_time = time.time()
    
    logger.info("Starting SQLite to PostgreSQL migration...")
    
    # Load configuration
    config = load_config()
    
    # Connect to databases
    sqlite_conn = connect_to_sqlite(config["sqlite_path"])
    postgres_conn = connect_to_postgres(config["postgres_uri"])
    
    # Get list of tables
    tables = get_sqlite_tables(sqlite_conn)
    logger.info(f"Found {len(tables)} tables in SQLite: {', '.join(tables)}")
    
    if args.dry_run:
        logger.info("Dry run mode: Only validating database connections and structures")
        create_postgres_tables(postgres_conn, sqlite_conn, tables)
        logger.info("Dry run completed successfully")
    else:
        # Create tables in PostgreSQL
        create_postgres_tables(postgres_conn, sqlite_conn, tables)
        
        # Migrate data for each table
        total_rows_migrated = 0
        for table in tables:
            rows_migrated = migrate_table(sqlite_conn, postgres_conn, table, args.batch_size)
            total_rows_migrated += rows_migrated
        
        # Create indexes in PostgreSQL
        create_postgres_indexes(postgres_conn, sqlite_conn, tables)
        
        # Validate migration
        is_valid = validate_migration(sqlite_conn, postgres_conn, tables)
        
        # Report migration summary
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("==== Migration Summary ====")
        logger.info(f"Total tables migrated: {len(tables)}")
        logger.info(f"Total rows migrated: {total_rows_migrated}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Validation status: {'✅ VALID' if is_valid else '❌ INVALID'}")
        
        if is_valid:
            logger.info("Migration completed successfully!")
        else:
            logger.warning("Migration completed with validation errors. Please check the logs.")
    
    # Close database connections
    sqlite_conn.close()
    postgres_conn.close()

if __name__ == "__main__":
    main()