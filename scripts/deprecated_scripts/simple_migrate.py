#!/usr/bin/env python3
"""
Simple SQLite to PostgreSQL Data Migration Script

This script migrates data from the SQLite database to PostgreSQL.
It uses the tables that have already been created in PostgreSQL.
"""

import os
import sys
import json
import sqlite3
import psycopg2
import logging
import re
from psycopg2.extras import Json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"simple_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("migration")

# Database connection parameters
SQLITE_PATH = "./data/egypt_chatbot.db"
POSTGRES_URI = "postgresql://omarmohamed@localhost:5432/egypt_chatbot"

def connect_to_sqlite():
    """Connect to SQLite database"""
    try:
        connection = sqlite3.connect(SQLITE_PATH)
        connection.row_factory = sqlite3.Row
        logger.info(f"Connected to SQLite database: {SQLITE_PATH}")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to SQLite database: {e}")
        sys.exit(1)

def connect_to_postgres():
    """Connect to PostgreSQL database"""
    try:
        connection = psycopg2.connect(POSTGRES_URI)
        connection.autocommit = False  # We'll manage transactions manually
        logger.info(f"Connected to PostgreSQL database")
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

def get_column_names(sqlite_conn, table):
    """Get list of column names for a table"""
    try:
        cursor = sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        cursor.close()
        return columns
    except Exception as e:
        logger.error(f"Failed to get column names for table {table}: {e}")
        sys.exit(1)

def get_column_types(postgres_conn, table):
    """Get column types from PostgreSQL table"""
    try:
        cursor = postgres_conn.cursor()
        cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}'
        """)
        return {row[0]: row[1] for row in cursor.fetchall()}
    except Exception as e:
        logger.error(f"Failed to get column types for table {table}: {e}")
        return {}

def clean_price(price_str):
    """Remove currency symbols and convert to float"""
    if not price_str or not isinstance(price_str, str):
        return 0.0
    # Remove currency symbols and non-numeric chars except decimal point
    cleaned = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def migrate_table_data(sqlite_conn, postgres_conn, table, dry_run=False):
    """Migrate data from SQLite table to PostgreSQL"""
    try:
        # Get column names
        columns = get_column_names(sqlite_conn, table)
        
        # Check if table has data in SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = sqlite_cursor.fetchone()[0]
        
        if count == 0:
            logger.info(f"Table {table} has no data to migrate")
            return 0
        
        logger.info(f"Migrating {count} rows from {table}")
        
        # Skip tables we know don't exist or aren't compatible
        if table == 'analytics_events':
            logger.info(f"Skipping table {table} - not present in PostgreSQL schema")
            return 0
            
        # Get PostgreSQL column types for type conversion
        pg_column_types = get_column_types(postgres_conn, table)
        
        # Fetch data from SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        
        if dry_run:
            logger.info(f"[DRY RUN] Would migrate {len(rows)} rows to table {table}")
            return len(rows)
        
        # Prepare for PostgreSQL insert
        placeholders = ", ".join(["%s"] * len(columns))
        columns_str = ", ".join([f'"{col}"' for col in columns])
        insert_query = f'INSERT INTO {table} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'
        
        # Convert rows to list of tuples
        pg_rows = []
        for row in rows:
            row_dict = dict(row)
            
            # Handle data type conversions based on table and column
            for col in columns:
                col_type = pg_column_types.get(col, '')
                
                # Handle accommodations price field
                if table == 'accommodations' and col in ('price_per_night', 'price'):
                    if isinstance(row_dict[col], str) and ('$' in row_dict[col] or '£' in row_dict[col]):
                        row_dict[col] = clean_price(row_dict[col])
                
                # Handle analytics ID field
                if table == 'analytics' and col == 'id' and isinstance(row_dict[col], str):
                    # For UUID strings, create a numeric ID instead
                    row_dict[col] = hash(row_dict[col]) % 2147483647  # Max 32-bit int
                
                # Handle JSON data conversion
                if col in ('data', 'event_data') and row_dict[col]:
                    try:
                        if isinstance(row_dict[col], str):
                            row_dict[col] = Json(json.loads(row_dict[col]))
                        else:
                            row_dict[col] = Json(row_dict[col])
                    except:
                        pass
            
            pg_rows.append(tuple(row_dict[col] for col in columns))
        
        # Execute insert
        pg_cursor = postgres_conn.cursor()
        pg_cursor.executemany(insert_query, pg_rows)
        postgres_conn.commit()
        
        logger.info(f"Successfully migrated {len(pg_rows)} rows to table {table}")
        return len(pg_rows)
        
    except Exception as e:
        postgres_conn.rollback()
        logger.error(f"Failed to migrate table {table}: {e}")
        return 0

def validate_migration(sqlite_conn, postgres_conn, table):
    """Validate migration by comparing row counts"""
    try:
        # Skip tables that don't exist in PostgreSQL
        if table == 'analytics_events':
            logger.info(f"Skipping validation for table {table} - not present in PostgreSQL schema")
            return True
            
        # Get SQLite count
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = sqlite_cursor.fetchone()[0]
        
        # Get PostgreSQL count
        pg_cursor = postgres_conn.cursor()
        pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        pg_count = pg_cursor.fetchone()[0]
        
        match = sqlite_count == pg_count
        percentage = (pg_count / sqlite_count * 100) if sqlite_count > 0 else 100
        
        logger.info(f"Validation for {table}: {sqlite_count} rows (SQLite) vs {pg_count} rows (PostgreSQL) - {percentage:.2f}% migrated - {'✅' if match else '❌'}")
        
        return match
    except Exception as e:
        logger.error(f"Failed to validate migration for table {table}: {e}")
        return False

def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate data from SQLite to PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making changes")
    args = parser.parse_args()
    
    start_time = datetime.now()
    logger.info(f"Starting migration at {start_time}")
    
    # Connect to databases
    sqlite_conn = connect_to_sqlite()
    postgres_conn = connect_to_postgres()
    
    try:
        # Get tables
        tables = get_sqlite_tables(sqlite_conn)
        logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")
        
        # Migrate each table
        total_rows = 0
        for table in tables:
            try:
                rows = migrate_table_data(sqlite_conn, postgres_conn, table, args.dry_run)
                total_rows += rows
                
                if not args.dry_run:
                    validate_migration(sqlite_conn, postgres_conn, table)
            except Exception as e:
                logger.error(f"Error during migration of table {table}: {e}")
                postgres_conn.rollback()
        
        # Print summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Migration completed in {duration:.2f} seconds")
        logger.info(f"Total rows migrated: {total_rows}")
        
    finally:
        # Close connections
        sqlite_conn.close()
        postgres_conn.close()
        logger.info("Database connections closed")

if __name__ == "__main__":
    main() 