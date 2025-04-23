#!/usr/bin/env python3
"""
Fix Cities Table Schema

This script adds missing columns to the cities table in PostgreSQL.
"""

import os
import sys
import logging
import psycopg2
import sqlite3
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("fix_cities")

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

def get_sqlite_connection(sqlite_path):
    """
    Connect to SQLite database.
    
    Args:
        sqlite_path (str): Path to SQLite database
        
    Returns:
        connection: SQLite connection object
    """
    try:
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to SQLite database: {e}")
        sys.exit(1)

def get_sqlite_cities_columns(sqlite_conn):
    """
    Get column names from cities table in SQLite.
    
    Args:
        sqlite_conn: SQLite connection
        
    Returns:
        list: List of column names
    """
    try:
        cursor = sqlite_conn.cursor()
        cursor.execute("PRAGMA table_info(cities)")
        columns = [row['name'] for row in cursor.fetchall()]
        cursor.close()
        return columns
    except Exception as e:
        logger.error(f"Failed to get column names from SQLite cities table: {e}")
        return []

def get_postgres_cities_columns(pg_conn):
    """
    Get column names from cities table in PostgreSQL.
    
    Args:
        pg_conn: PostgreSQL connection
        
    Returns:
        list: List of column names
    """
    try:
        cursor = pg_conn.cursor()
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'cities'
        """)
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return columns
    except psycopg2.Error as e:
        logger.error(f"Failed to get column names from PostgreSQL cities table: {e}")
        return []

def add_missing_columns(pg_conn, missing_columns):
    """
    Add missing columns to cities table in PostgreSQL.
    
    Args:
        pg_conn: PostgreSQL connection
        missing_columns (list): List of column names to add
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cursor = pg_conn.cursor()
        
        for column in missing_columns:
            logger.info(f"Adding column {column} to cities table")
            cursor.execute(f"ALTER TABLE cities ADD COLUMN {column} TEXT")
            logger.info(f"Column {column} added to cities table successfully")
        
        cursor.close()
        return True
    except psycopg2.Error as e:
        logger.error(f"Failed to add columns to cities table: {e}")
        return False

def fix_cities_data(sqlite_conn, pg_conn):
    """
    Migrate cities data from SQLite to PostgreSQL.
    
    Args:
        sqlite_conn: SQLite connection
        pg_conn: PostgreSQL connection
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get cities data from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM cities")
        cities = sqlite_cursor.fetchall()
        
        if not cities:
            logger.info("No cities data in SQLite database")
            return True
        
        # Get column names
        columns = [k for k in cities[0].keys()]
        
        # Insert data into PostgreSQL
        pg_cursor = pg_conn.cursor()
        
        for city in cities:
            # Convert city to dict for easier access
            city_dict = dict(city)
            
            # Check if city already exists
            pg_cursor.execute("SELECT COUNT(*) FROM cities WHERE id = %s", (city_dict['id'],))
            count = pg_cursor.fetchone()[0]
            
            if count > 0:
                logger.info(f"City {city_dict['id']} already exists in PostgreSQL, updating...")
                
                # Build SET clause
                set_clauses = []
                params = []
                
                for column in columns:
                    set_clauses.append(f"{column} = %s")
                    params.append(city_dict[column])
                
                # Add id to params
                params.append(city_dict['id'])
                
                # Execute update
                update_query = f"UPDATE cities SET {', '.join(set_clauses)} WHERE id = %s"
                pg_cursor.execute(update_query, params)
            else:
                logger.info(f"Inserting city {city_dict['id']} into PostgreSQL...")
                
                # Build placeholders
                placeholders = ', '.join(['%s'] * len(columns))
                
                # Execute insert
                insert_query = f"INSERT INTO cities ({', '.join(columns)}) VALUES ({placeholders})"
                pg_cursor.execute(insert_query, [city_dict[column] for column in columns])
        
        pg_cursor.close()
        sqlite_cursor.close()
        
        logger.info("Cities data migrated successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to migrate cities data: {e}")
        return False

def main():
    """Main function to fix cities table."""
    # Load environment variables
    load_dotenv()
    
    # Get database URIs
    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable is not set")
        sys.exit(1)
    
    sqlite_path = "./data/egypt_chatbot.db"
    if not os.path.exists(sqlite_path):
        logger.error(f"SQLite database not found: {sqlite_path}")
        sys.exit(1)
    
    logger.info(f"Connecting to PostgreSQL database: {postgres_uri}")
    pg_conn = get_postgres_connection(postgres_uri)
    
    logger.info(f"Connecting to SQLite database: {sqlite_path}")
    sqlite_conn = get_sqlite_connection(sqlite_path)
    
    # Get column names from both databases
    sqlite_columns = get_sqlite_cities_columns(sqlite_conn)
    postgres_columns = get_postgres_cities_columns(pg_conn)
    
    # Determine missing columns
    missing_columns = [col for col in sqlite_columns if col not in postgres_columns]
    
    if not missing_columns:
        logger.info("No missing columns in PostgreSQL cities table")
    else:
        logger.info(f"Missing columns in PostgreSQL cities table: {', '.join(missing_columns)}")
        
        # Add missing columns
        if not add_missing_columns(pg_conn, missing_columns):
            logger.error("Failed to add missing columns to cities table")
            pg_conn.close()
            sqlite_conn.close()
            sys.exit(1)
    
    # Fix cities data
    if not fix_cities_data(sqlite_conn, pg_conn):
        logger.error("Failed to fix cities data")
        pg_conn.close()
        sqlite_conn.close()
        sys.exit(1)
    
    pg_conn.close()
    sqlite_conn.close()
    
    logger.info("Cities table fixed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 