#!/usr/bin/env python3
"""
Simple SQLite to PostgreSQL Migration Script
"""
import os
import sys
import json
import sqlite3
import psycopg2
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database paths
SQLITE_PATH = "./data/egypt_chatbot.db"
PG_CONN_STRING = "dbname=egypt_chatbot"

def migrate_table(table_name, batch_size=100):
    """Migrate a single table from SQLite to PostgreSQL"""
    try:
        # Connect to databases
        sqlite_conn = sqlite3.connect(SQLITE_PATH)
        sqlite_conn.row_factory = sqlite3.Row
        pg_conn = psycopg2.connect(PG_CONN_STRING)
        
        # Get table schema from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in sqlite_cursor.fetchall()]
        
        # Create table in PostgreSQL if not exists
        pg_cursor = pg_conn.cursor()
        columns_sql = ", ".join([f"{col} TEXT" for col in columns])
        pg_cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})")
        pg_conn.commit()
        
        # Get row count for progress tracking
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = sqlite_cursor.fetchone()[0]
        logger.info(f"Migrating {total_rows} rows from {table_name}")
        
        # Migrate data in batches
        offset = 0
        migrated = 0
        
        while True:
            # Fetch batch from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                break
                
            # Insert into PostgreSQL
            placeholders = ", ".join(["%s"] * len(columns))
            for row in rows:
                row_data = tuple(row)
                try:
                    pg_cursor.execute(
                        f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})",
                        row_data
                    )
                except Exception as e:
                    logger.error(f"Error inserting row: {e}")
                    continue
            
            pg_conn.commit()
            
            migrated += len(rows)
            offset += batch_size
            logger.info(f"Migrated {migrated}/{total_rows} rows ({migrated/total_rows*100:.1f}%)")
        
        # Close connections
        sqlite_cursor.close()
        pg_cursor.close()
        sqlite_conn.close()
        pg_conn.close()
        
        logger.info(f"Successfully migrated {migrated} rows from {table_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to migrate table {table_name}: {e}")
        return False

def main():
    """Main migration function"""
    # Connect to SQLite to get table list
    try:
        sqlite_conn = sqlite3.connect(SQLITE_PATH)
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        sqlite_conn.close()
        
        logger.info(f"Found {len(tables)} tables to migrate: {', '.join(tables)}")
        
        # Migrate each table
        for table in tables:
            logger.info(f"Migrating table: {table}")
            success = migrate_table(table)
            if success:
                logger.info(f"Table {table} migrated successfully")
            else:
                logger.error(f"Failed to migrate table {table}")
        
        logger.info("Migration completed!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        
if __name__ == "__main__":
    main()
