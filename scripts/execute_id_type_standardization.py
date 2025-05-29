#!/usr/bin/env python3
"""
Script to execute the ID type standardization migrations.
This script executes the migration scripts in the correct order.
"""

import os
import sys
import logging
import argparse
import psycopg2
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

def backup_database(conn, backup_file):
    """
    Create a backup of the database.

    Args:
        conn: Database connection
        backup_file: Path to the backup file
    """
    logger.info(f"Creating database backup: {backup_file}")

    try:
        # Get database connection parameters
        db_params = conn.get_dsn_parameters()

        # Create backup using pg_dump
        os.system(f"pg_dump -h {db_params['host']} -U {db_params['user']} -d {db_params['dbname']} -f {backup_file}")

        logger.info(f"Successfully created database backup: {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Error creating database backup: {str(e)}")
        return False

def main():
    """Main function to execute the migration."""
    parser = argparse.ArgumentParser(description='Execute ID type standardization migrations')
    parser.add_argument('--db-connection', type=str, default=DEFAULT_DB_CONNECTION,
                        help='Database connection string')
    parser.add_argument('--dry-run', action='store_true',
                        help='Dry run (do not execute SQL files)')
    parser.add_argument('--skip-backup', action='store_true',
                        help='Skip database backup')
    args = parser.parse_args()

    # Migration files in the order they should be executed
    migration_files = [
        "migrations/20250720_fix_user_id_inconsistency.sql",
        "migrations/20250720_fix_polymorphic_associations.sql",
        "migrations/20250720_fix_remaining_user_id.sql"
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

    # Create a backup of the database
    if not args.skip_backup and not args.dry_run:
        backup_file = f"egypt_chatbot_backup_before_id_standardization_{Path(__file__).stem}.sql"
        if not backup_database(conn, backup_file):
            logger.error("Failed to create database backup. Aborting migration.")
            conn.close()
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
