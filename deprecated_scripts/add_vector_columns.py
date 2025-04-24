#!/usr/bin/env python3
"""
Add vector columns to the existing PostgreSQL database.

This script adds vector columns for embeddings to the attractions,
accommodations, restaurants, and cities tables. It requires the pgvector
extension to be installed.
"""

import os
import sys
import argparse
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# SQL commands to add vector columns
SQL_COMMANDS = [
    # Add vector columns
    """
    ALTER TABLE attractions
    ADD COLUMN IF NOT EXISTS embedding vector(1536);
    """,
    
    """
    ALTER TABLE accommodations
    ADD COLUMN IF NOT EXISTS embedding vector(1536);
    """,
    
    """
    ALTER TABLE restaurants
    ADD COLUMN IF NOT EXISTS embedding vector(1536);
    """,
    
    """
    ALTER TABLE cities
    ADD COLUMN IF NOT EXISTS embedding vector(1536);
    """,
    
    # Create indexes
    """
    CREATE INDEX IF NOT EXISTS attractions_embedding_idx ON attractions USING hnsw (embedding vector_l2_ops);
    """,
    
    """
    CREATE INDEX IF NOT EXISTS accommodations_embedding_idx ON accommodations USING hnsw (embedding vector_l2_ops);
    """,
    
    """
    CREATE INDEX IF NOT EXISTS restaurants_embedding_idx ON restaurants USING hnsw (embedding vector_l2_ops);
    """,
    
    """
    CREATE INDEX IF NOT EXISTS cities_embedding_idx ON cities USING hnsw (embedding vector_l2_ops);
    """
]


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


def check_extensions(cursor):
    """
    Check if required PostgreSQL extensions are installed.
    
    Args:
        cursor: PostgreSQL cursor
        
    Returns:
        bool: True if all required extensions are installed, False otherwise
    """
    required_extensions = ['vector', 'postgis']
    
    for extension in required_extensions:
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = %s)",
            (extension,)
        )
        if not cursor.fetchone()[0]:
            logger.error(f"Required extension {extension} is not installed")
            logger.error(f"Please run: CREATE EXTENSION IF NOT EXISTS {extension};")
            return False
    
    return True


def execute_sql_commands(cursor, dry_run=False):
    """
    Execute SQL commands to add vector columns.
    
    Args:
        cursor: PostgreSQL cursor
        dry_run (bool): If True, print SQL commands without executing them
        
    Returns:
        bool: True if all commands executed successfully, False otherwise
    """
    for i, command in enumerate(SQL_COMMANDS, 1):
        logger.info(f"Executing SQL command {i}/{len(SQL_COMMANDS)}")
        
        if dry_run:
            logger.info(f"SQL command (dry run):\n{command}")
            continue
        
        try:
            cursor.execute(command)
            logger.info(f"SQL command {i}/{len(SQL_COMMANDS)} executed successfully")
        except psycopg2.Error as e:
            logger.error(f"Failed to execute SQL command {i}/{len(SQL_COMMANDS)}: {e}")
            logger.error(f"SQL command:\n{command}")
            return False
    
    return True


def main():
    """Main function to add vector columns to PostgreSQL database."""
    parser = argparse.ArgumentParser(description='Add vector columns to PostgreSQL database')
    parser.add_argument('--dry-run', action='store_true', help='Print SQL commands without executing them')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Get PostgreSQL connection URI
    postgres_uri = os.getenv('POSTGRES_URI')
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable is not set")
        sys.exit(1)
    
    logger.info("Connecting to PostgreSQL database...")
    conn = get_postgres_connection(postgres_uri)
    cursor = conn.cursor()
    
    # Check if required extensions are installed
    logger.info("Checking for required PostgreSQL extensions...")
    if not check_extensions(cursor):
        logger.error("Required PostgreSQL extensions are not installed")
        logger.error("Please enable extensions first")
        conn.close()
        sys.exit(1)
    
    # Execute SQL commands
    logger.info("Adding vector columns to PostgreSQL database...")
    success = execute_sql_commands(cursor, args.dry_run)
    
    conn.close()
    
    if not success and not args.dry_run:
        logger.error("Failed to add vector columns to PostgreSQL database")
        sys.exit(1)
    
    if args.dry_run:
        logger.info("Dry run completed. Use without --dry-run to execute SQL commands.")
    else:
        logger.info("Vector columns added to PostgreSQL database successfully")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 