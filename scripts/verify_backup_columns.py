#!/usr/bin/env python3
"""
Script to verify that the data in the main columns matches the data in the backup columns.
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default database connection string
DEFAULT_DB_CONNECTION = "postgresql://postgres:postgres@localhost:5432/egypt_chatbot"

def verify_backup_columns(conn):
    """
    Verify that the data in the main columns matches the data in the backup columns.
    
    Args:
        conn: Database connection
    
    Returns:
        bool: True if all data matches, False otherwise
    """
    tables = ["attractions", "accommodations", "cities", "restaurants"]
    all_match = True
    
    for table in tables:
        logger.info(f"Verifying backup columns for table: {table}")
        
        # Check name and name_backup
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(f"""
                SELECT 
                    COUNT(*) AS total_rows,
                    COUNT(*) FILTER (WHERE name = name_backup) AS matching_name_rows,
                    COUNT(*) FILTER (WHERE name IS NOT NULL AND name_backup IS NOT NULL AND name != name_backup) AS mismatched_name_rows,
                    COUNT(*) FILTER (WHERE description = description_backup) AS matching_description_rows,
                    COUNT(*) FILTER (WHERE description IS NOT NULL AND description_backup IS NOT NULL AND description != description_backup) AS mismatched_description_rows
                FROM {table}
            """)
            result = cursor.fetchone()
            
            total_rows = result["total_rows"]
            matching_name_rows = result["matching_name_rows"]
            mismatched_name_rows = result["mismatched_name_rows"]
            matching_description_rows = result["matching_description_rows"]
            mismatched_description_rows = result["mismatched_description_rows"]
            
            logger.info(f"Table {table}:")
            logger.info(f"  Total rows: {total_rows}")
            logger.info(f"  Matching name rows: {matching_name_rows}")
            logger.info(f"  Mismatched name rows: {mismatched_name_rows}")
            logger.info(f"  Matching description rows: {matching_description_rows}")
            logger.info(f"  Mismatched description rows: {mismatched_description_rows}")
            
            if mismatched_name_rows > 0 or mismatched_description_rows > 0:
                all_match = False
                logger.warning(f"Data mismatch found in table {table}")
                
                # Show examples of mismatched rows
                cursor.execute(f"""
                    SELECT id, name, name_backup, description, description_backup
                    FROM {table}
                    WHERE (name IS NOT NULL AND name_backup IS NOT NULL AND name != name_backup)
                    OR (description IS NOT NULL AND description_backup IS NOT NULL AND description != description_backup)
                    LIMIT 5
                """)
                mismatched_rows = cursor.fetchall()
                
                for row in mismatched_rows:
                    logger.warning(f"Mismatched row ID: {row['id']}")
                    if row['name'] != row['name_backup']:
                        logger.warning(f"  name: {row['name']}")
                        logger.warning(f"  name_backup: {row['name_backup']}")
                    if row['description'] != row['description_backup']:
                        logger.warning(f"  description: {row['description']}")
                        logger.warning(f"  description_backup: {row['description_backup']}")
    
    return all_match

def main():
    """Main function to verify backup columns."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify backup columns in the database')
    parser.add_argument('--db-connection', type=str, default=DEFAULT_DB_CONNECTION,
                        help='Database connection string')
    args = parser.parse_args()
    
    # Connect to the database
    try:
        logger.info(f"Connecting to database: {args.db_connection}")
        conn = psycopg2.connect(args.db_connection)
        logger.info("Connected to database")
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return 1
    
    # Verify backup columns
    all_match = verify_backup_columns(conn)
    
    # Close database connection
    conn.close()
    
    if all_match:
        logger.info("All backup columns match their corresponding main columns")
        return 0
    else:
        logger.error("Some backup columns do not match their corresponding main columns")
        return 1

if __name__ == "__main__":
    sys.exit(main())
