#!/usr/bin/env python3
"""
Database Migration CLI Script

Provides a command-line interface for running database migrations using the MigrationManager.
"""

import os
import sys
import argparse
import logging
from typing import List, Optional
from migration_manager import MigrationManager, logger

def get_tables_to_migrate(manager: MigrationManager, tables: Optional[List[str]] = None) -> List[str]:
    """Get list of tables to migrate, either specified or all tables"""
    if tables:
        return tables
    
    cursor = manager.sqlite_conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%'
    """)
    return [row[0] for row in cursor.fetchall()]

def main():
    parser = argparse.ArgumentParser(description="Migrate data from SQLite to PostgreSQL")
    parser.add_argument(
        "--sqlite-path",
        default=os.getenv("SQLITE_PATH", "./data/egypt_chatbot.db"),
        help="Path to SQLite database"
    )
    parser.add_argument(
        "--postgres-uri",
        default=os.getenv("POSTGRES_URI", "postgresql://localhost:5432/egypt_chatbot"),
        help="PostgreSQL connection URI"
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        help="Specific tables to migrate (defaults to all tables)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of rows to migrate in each batch"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate migration after completion"
    )
    args = parser.parse_args()

    # Initialize migration manager
    manager = MigrationManager(args.sqlite_path, args.postgres_uri)
    
    try:
        # Connect to databases
        manager.connect()
        
        # Get tables to migrate
        tables = get_tables_to_migrate(manager, args.tables)
        logger.info(f"Preparing to migrate {len(tables)} tables: {', '.join(tables)}")
        
        # Migrate each table
        total_rows = 0
        for table in tables:
            try:
                logger.info(f"Migrating table: {table}")
                rows = manager.migrate_table(table, args.batch_size)
                total_rows += rows
                
                if args.validate:
                    manager.validate_migration(table)
                    
            except Exception as e:
                logger.error(f"Failed to migrate table {table}: {e}")
                if input(f"Continue with remaining tables? (y/n): ").lower() != 'y':
                    break
        
        logger.info(f"Migration complete. Total rows migrated: {total_rows}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
        
    finally:
        manager.cleanup()

if __name__ == "__main__":
    main()