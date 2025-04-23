#!/usr/bin/env python3
"""
Script to fix database schema issues by adding missing columns and fixing problematic indexes.
This script addresses:
1. Missing columns in entity tables
2. Problematic index definitions
3. Consistent schema across all tables
"""

import os
import sys
import logging
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Parse arguments
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Fix database schema issues")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL statements without executing them")
    parser.add_argument("--fix-columns", action="store_true", help="Fix missing columns")
    parser.add_argument("--fix-indexes", action="store_true", help="Fix problematic indexes")
    parser.add_argument("--all", action="store_true", help="Fix all issues")
    
    args = parser.parse_args()
    
    # If no specific flags are set, set --all to True
    if not (args.fix_columns or args.fix_indexes or args.all):
        args.all = True
    
    return args

# Load environment variables
def load_config():
    """Load configuration from .env file."""
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path)
    
    # Get PostgreSQL URI
    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable not set")
        sys.exit(1)
        
    logger.info(f"Using PostgreSQL URI: {postgres_uri}")
    return postgres_uri

# Connect to PostgreSQL
def connect_to_postgres(postgres_uri):
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(postgres_uri)
        logger.info("Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        sys.exit(1)

# Check if a column exists in a table
def column_exists(conn, table_name, column_name):
    """Check if a column exists in a table."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s 
                    AND column_name = %s
                )
            """, (table_name, column_name))
            return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error checking if column {column_name} exists in table {table_name}: {e}")
        return False

# Get problematic indexes
def get_problematic_indexes(conn, table_name):
    """Get all problematic indexes for a table."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = %s
            """, (table_name,))
            
            indexes = cursor.fetchall()
            problematic = []
            
            for index_name, index_def in indexes:
                if "data" in index_def:
                    problematic.append(index_name)
                
            return problematic
    except Exception as e:
        logger.error(f"Error getting problematic indexes for table {table_name}: {e}")
        return []

# Add missing columns
def add_missing_columns(conn, dry_run=False):
    """Add missing columns to tables."""
    # Define required columns for each entity type
    column_definitions = {
        'attractions': [
            ('name_en', 'TEXT'),
            ('name_ar', 'TEXT'),
            ('description_en', 'TEXT'),
            ('description_ar', 'TEXT'),
            ('type', 'TEXT'),
            ('city', 'TEXT')
        ],
        'restaurants': [
            ('name_en', 'TEXT'),
            ('name_ar', 'TEXT'),
            ('cuisine_type', 'TEXT'),
            ('city', 'TEXT'),
            ('price_range', 'TEXT')
        ],
        'hotels': [
            ('name_en', 'TEXT'),
            ('name_ar', 'TEXT'),
            ('type', 'TEXT'),
            ('category', 'TEXT'),
            ('city', 'TEXT'),
            ('price_range', 'TEXT')
        ],
        'cities': [
            ('name_en', 'TEXT'),
            ('name_ar', 'TEXT'),
            ('region', 'TEXT')
        ]
    }
    
    columns_added = 0
    
    for table, columns in column_definitions.items():
        for column_name, data_type in columns:
            if not column_exists(conn, table, column_name):
                try:
                    sql = f"ALTER TABLE {table} ADD COLUMN {column_name} {data_type}"
                    
                    if dry_run:
                        logger.info(f"[DRY RUN] Would execute: {sql}")
                    else:
                        with conn.cursor() as cursor:
                            cursor.execute(sql)
                            conn.commit()
                            logger.info(f"Added column {column_name} to table {table}")
                            columns_added += 1
                except Exception as e:
                    logger.error(f"Error adding column {column_name} to table {table}: {e}")
                    if not dry_run:
                        conn.rollback()
    
    logger.info(f"{'Would add' if dry_run else 'Added'} {columns_added} missing columns")
    return columns_added

# Fix problematic indexes
def fix_problematic_indexes(conn, dry_run=False):
    """Fix problematic indexes."""
    tables = ['attractions', 'restaurants', 'hotels', 'cities']
    indexes_fixed = 0
    
    for table in tables:
        problematic_indexes = get_problematic_indexes(conn, table)
        
        for index_name in problematic_indexes:
            try:
                sql = f"DROP INDEX IF EXISTS {index_name}"
                
                if dry_run:
                    logger.info(f"[DRY RUN] Would execute: {sql}")
                else:
                    with conn.cursor() as cursor:
                        cursor.execute(sql)
                        conn.commit()
                        logger.info(f"Dropped problematic index {index_name}")
                        indexes_fixed += 1
            except Exception as e:
                logger.error(f"Error dropping index {index_name}: {e}")
                if not dry_run:
                    conn.rollback()
    
    logger.info(f"{'Would fix' if dry_run else 'Fixed'} {indexes_fixed} problematic indexes")
    return indexes_fixed

# Create proper indexes
def create_proper_indexes(conn, dry_run=False):
    """Create proper indexes for all tables."""
    # Define proper indexes for each entity type
    index_definitions = {
        'attractions': [
            ('idx_attractions_name_en', 'name_en'),
            ('idx_attractions_name_ar', 'name_ar'),
            ('idx_attractions_type', 'type'),
            ('idx_attractions_city', 'city')
        ],
        'restaurants': [
            ('idx_restaurants_name_en', 'name_en'),
            ('idx_restaurants_name_ar', 'name_ar'),
            ('idx_restaurants_cuisine', 'cuisine_type'),
            ('idx_restaurants_city', 'city')
        ],
        'hotels': [
            ('idx_hotels_name_en', 'name_en'),
            ('idx_hotels_name_ar', 'name_ar'),
            ('idx_hotels_type', 'type'),
            ('idx_hotels_category', 'category'),
            ('idx_hotels_city', 'city')
        ],
        'cities': [
            ('idx_cities_name_en', 'name_en'),
            ('idx_cities_name_ar', 'name_ar'),
            ('idx_cities_region', 'region')
        ]
    }
    
    # Define JSONB indexes for each entity type
    jsonb_index_definitions = {
        'attractions': [
            ('idx_attractions_name_jsonb', 'name', 'jsonb_path_ops'),
            ('idx_attractions_description_jsonb', 'description', 'jsonb_path_ops')
        ],
        'restaurants': [
            ('idx_restaurants_name_jsonb', 'name', 'jsonb_path_ops'),
            ('idx_restaurants_description_jsonb', 'description', 'jsonb_path_ops')
        ],
        'hotels': [
            ('idx_hotels_name_jsonb', 'name', 'jsonb_path_ops'),
            ('idx_hotels_description_jsonb', 'description', 'jsonb_path_ops')
        ],
        'cities': [
            ('idx_cities_name_jsonb', 'name', 'jsonb_path_ops'),
            ('idx_cities_description_jsonb', 'description', 'jsonb_path_ops')
        ]
    }
    
    indexes_created = 0
    
    # Create regular indexes
    for table, indexes in index_definitions.items():
        for index_name, column_name in indexes:
            if column_exists(conn, table, column_name):
                try:
                    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column_name})"
                    
                    if dry_run:
                        logger.info(f"[DRY RUN] Would execute: {sql}")
                    else:
                        with conn.cursor() as cursor:
                            cursor.execute(sql)
                            conn.commit()
                            logger.info(f"Created index {index_name} on table {table}")
                            indexes_created += 1
                except Exception as e:
                    logger.error(f"Error creating index {index_name} on table {table}: {e}")
                    if not dry_run:
                        conn.rollback()
    
    # Create JSONB indexes
    for table, indexes in jsonb_index_definitions.items():
        for index_name, column_name, op_class in indexes:
            if column_exists(conn, table, column_name):
                try:
                    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} USING GIN ({column_name} {op_class})"
                    
                    if dry_run:
                        logger.info(f"[DRY RUN] Would execute: {sql}")
                    else:
                        with conn.cursor() as cursor:
                            cursor.execute(sql)
                            conn.commit()
                            logger.info(f"Created JSONB index {index_name} on table {table}")
                            indexes_created += 1
                except Exception as e:
                    logger.error(f"Error creating JSONB index {index_name} on table {table}: {e}")
                    if not dry_run:
                        conn.rollback()
    
    logger.info(f"{'Would create' if dry_run else 'Created'} {indexes_created} proper indexes")
    return indexes_created

# Update records from JSONB to dedicated columns
def update_records_from_jsonb(conn, dry_run=False):
    """Update records by copying data from JSONB columns to dedicated columns."""
    updates = {
        'attractions': [
            "UPDATE attractions SET name_en = name->>'en' WHERE name_en IS NULL AND name IS NOT NULL AND name->>'en' IS NOT NULL",
            "UPDATE attractions SET name_ar = name->>'ar' WHERE name_ar IS NULL AND name IS NOT NULL AND name->>'ar' IS NOT NULL",
            "UPDATE attractions SET description_en = description->>'en' WHERE description_en IS NULL AND description IS NOT NULL AND description->>'en' IS NOT NULL",
            "UPDATE attractions SET description_ar = description->>'ar' WHERE description_ar IS NULL AND description IS NOT NULL AND description->>'ar' IS NOT NULL"
        ],
        'restaurants': [
            "UPDATE restaurants SET name_en = name->>'en' WHERE name_en IS NULL AND name IS NOT NULL AND name->>'en' IS NOT NULL",
            "UPDATE restaurants SET name_ar = name->>'ar' WHERE name_ar IS NULL AND name IS NOT NULL AND name->>'ar' IS NOT NULL",
            "UPDATE restaurants SET cuisine_type = COALESCE(cuisine_type, (SELECT name->>'cuisine' FROM restaurants r WHERE r.id = restaurants.id))"
        ],
        'hotels': [
            "UPDATE hotels SET name_en = name->>'en' WHERE name_en IS NULL AND name IS NOT NULL AND name->>'en' IS NOT NULL",
            "UPDATE hotels SET name_ar = name->>'ar' WHERE name_ar IS NULL AND name IS NOT NULL AND name->>'ar' IS NOT NULL",
            "UPDATE hotels SET category = COALESCE(category, (SELECT name->>'category' FROM hotels h WHERE h.id = hotels.id))"
        ],
        'cities': [
            "UPDATE cities SET name_en = name->>'en' WHERE name_en IS NULL AND name IS NOT NULL AND name->>'en' IS NOT NULL",
            "UPDATE cities SET name_ar = name->>'ar' WHERE name_ar IS NULL AND name IS NOT NULL AND name->>'ar' IS NOT NULL",
            "UPDATE cities SET region = COALESCE(region, (SELECT name->>'region' FROM cities c WHERE c.id = cities.id))"
        ]
    }
    
    updates_executed = 0
    
    for table, sql_list in updates.items():
        for sql in sql_list:
            try:
                if dry_run:
                    logger.info(f"[DRY RUN] Would execute: {sql}")
                else:
                    with conn.cursor() as cursor:
                        cursor.execute(sql)
                        rows_affected = cursor.rowcount
                        conn.commit()
                        logger.info(f"Updated {rows_affected} rows in table {table}")
                        updates_executed += 1
            except Exception as e:
                logger.error(f"Error executing update on table {table}: {e}")
                if not dry_run:
                    conn.rollback()
    
    logger.info(f"{'Would execute' if dry_run else 'Executed'} {updates_executed} update operations")
    return updates_executed

# Main function
def main():
    """Main function to fix database schema issues."""
    args = parse_args()
    postgres_uri = load_config()
    conn = connect_to_postgres(postgres_uri)
    
    try:
        if args.all or args.fix_columns:
            logger.info("Fixing missing columns...")
            add_missing_columns(conn, args.dry_run)
            
            logger.info("Updating records from JSONB to dedicated columns...")
            update_records_from_jsonb(conn, args.dry_run)
        
        if args.all or args.fix_indexes:
            logger.info("Fixing problematic indexes...")
            fix_problematic_indexes(conn, args.dry_run)
            
            logger.info("Creating proper indexes...")
            create_proper_indexes(conn, args.dry_run)
        
        logger.info("Database schema fix completed successfully")
        
    except Exception as e:
        logger.error(f"Error in database schema fix: {e}")
    finally:
        conn.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    main() 