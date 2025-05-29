#!/usr/bin/env python3
"""
Script to execute the migration from array columns to junction tables.
This script executes the migration scripts in the correct order.
"""

import os
import sys
import logging
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default database connection string
DEFAULT_DB_CONNECTION = "postgresql://postgres:postgres@localhost:5432/egypt_chatbot"

def execute_sql_file(conn, file_path):
    """
    Execute a SQL file.

    Args:
        conn: Database connection
        file_path: Path to the SQL file
    """
    logger.info(f"Executing SQL file: {file_path}")

    try:
        with open(file_path, 'r') as f:
            sql = f.read()

        with conn.cursor() as cursor:
            cursor.execute(sql)

        conn.commit()
        logger.info(f"Successfully executed SQL file: {file_path}")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error executing SQL file {file_path}: {str(e)}")
        return False

def main():
    """Main function to execute the migration."""
    parser = argparse.ArgumentParser(description='Execute array to junction table migration')
    parser.add_argument('--db-connection', type=str, default=DEFAULT_DB_CONNECTION,
                        help='Database connection string')
    parser.add_argument('--dry-run', action='store_true',
                        help='Dry run (do not execute SQL files)')
    args = parser.parse_args()

    # Migration files in the order they should be executed
    migration_files = [
        "migrations/20250715_migrate_array_data_to_junction_tables.sql",
        "migrations/20250715_fix_tourism_faq_destinations.sql",
        "migrations/20250715_update_functions_for_junction_tables.sql",
        "migrations/20250715_update_database_manager.sql",
        "migrations/20250715_drop_redundant_array_columns.sql"
    ]

    # Check if all migration files exist
    for file_path in migration_files:
        if not os.path.exists(file_path):
            logger.error(f"Migration file not found: {file_path}")
            return 1

    # Connect to the database
    try:
        logger.info(f"Connecting to database: {args.db_connection}")
        conn = psycopg2.connect(args.db_connection)
        logger.info("Connected to database")
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return 1

    # Execute migration files
    success = True
    for file_path in migration_files:
        logger.info(f"Processing migration file: {file_path}")

        if args.dry_run:
            logger.info(f"Dry run: would execute {file_path}")
        else:
            if not execute_sql_file(conn, file_path):
                success = False
                break

    # Close database connection
    conn.close()

    if success:
        logger.info("Migration completed successfully")
        return 0
    else:
        logger.error("Migration failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
