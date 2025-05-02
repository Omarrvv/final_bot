#!/usr/bin/env python3
"""
Database Migration CLI

Command line interface for running database migrations using the MigrationManager.
Supports dry runs, validation, and selective table migration.
"""

import os
import sys
import argparse
import logging
from typing import List, Optional
from migration_manager import MigrationManager

def parse_args():
    parser = argparse.ArgumentParser(description="Migrate data between SQLite and PostgreSQL databases")
    parser.add_argument(
        "--sqlite-path",
        default=os.getenv("SQLITE_PATH", "./data/egypt_chatbot.db"),
        help="Path to SQLite database (default: ./data/egypt_chatbot.db)"
    )
    parser.add_argument(
        "--postgres-uri",
        default=os.getenv("POSTGRES_URI", "postgresql://localhost:5432/egypt_chatbot"),
        help="PostgreSQL connection URI"
    )
    parser.add_argument(
        "--tables",
        nargs="*",
        help="Specific tables to migrate (default: all tables)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of rows to migrate in each batch (default: 1000)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate migration without making changes"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing migration without migrating"
    )
    return parser.parse_args()

def get_tables(manager: MigrationManager) -> List[str]:
    """Get list of tables from SQLite database"""
    cursor = manager.sqlite_conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%'
    """)
    return [row[0] for row in cursor.fetchall()]

def main():
    args = parse_args()
    
    try:
        manager = MigrationManager(args.sqlite_path, args.postgres_uri)
        manager.connect()

        # Get list of tables to process
        all_tables = get_tables(manager)
        tables_to_migrate = args.tables if args.tables else all_tables

        if args.validate_only:
            # Only run validation
            for table in tables_to_migrate:
                manager.validate_migration(table)
            return

        # Perform migration
        for table in tables_to_migrate:
            if table not in all_tables:
                logging.warning(f"Table {table} not found in SQLite database - skipping")
                continue

            if args.dry_run:
                logging.info(f"Dry run - would migrate table: {table}")
                continue

            try:
                rows_migrated = manager.migrate_table(table, args.batch_size)
                logging.info(f"Successfully migrated {rows_migrated} rows from table {table}")
                
                # Validate after migration
                if manager.validate_migration(table):
                    logging.info(f"✅ Validation successful for table {table}")
                else:
                    logging.warning(f"⚠️ Validation failed for table {table}")
            
            except Exception as e:
                logging.error(f"Failed to migrate table {table}: {e}")
                raise

    except Exception as e:
        logging.error(f"Migration failed: {e}")
        sys.exit(1)
    
    finally:
        if 'manager' in locals():
            manager.cleanup()

if __name__ == "__main__":
    main()