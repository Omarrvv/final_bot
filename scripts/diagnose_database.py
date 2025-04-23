#!/usr/bin/env python3
"""
Diagnostic script for analyzing database schema issues in PostgreSQL.
This script checks for required columns, identifies missing columns,
and logs problematic indexes across all tables.
"""

import os
import sys
import logging
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from tabulate import tabulate
from pprint import pformat

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

# Get table information
def get_tables(conn):
    """Get all tables in the database."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")
            return tables
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        return []

# Get column information for a table
def get_table_columns(conn, table_name):
    """Get column information for a table."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            columns = [(row[0], row[1]) for row in cursor.fetchall()]
            return columns
    except Exception as e:
        logger.error(f"Error getting columns for table {table_name}: {e}")
        return []

# Get index information for a table
def get_table_indexes(conn, table_name):
    """Get index information for a table."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = %s
            """, (table_name,))
            indexes = [(row[0], row[1]) for row in cursor.fetchall()]
            return indexes
    except Exception as e:
        logger.error(f"Error getting indexes for table {table_name}: {e}")
        return []

# Check required columns for each entity type
def check_required_columns(table_name, columns):
    """Check if the table has all required columns."""
    # Define required columns for each entity type
    required_columns = {
        'attractions': ['id', 'name_en', 'name_ar', 'description_en', 'description_ar', 'type'],
        'restaurants': ['id', 'name_en', 'name_ar', 'cuisine_type', 'city'],
        'hotels': ['id', 'name_en', 'name_ar', 'type', 'category', 'city'],
        'cities': ['id', 'name_en', 'name_ar', 'region'],
    }
    
    if table_name not in required_columns:
        return None
    
    column_names = [col[0] for col in columns]
    missing_columns = []
    
    for required_col in required_columns[table_name]:
        if required_col not in column_names:
            missing_columns.append(required_col)
    
    return missing_columns

# Identify problematic indexes
def identify_problematic_indexes(indexes):
    """Identify problematic indexes."""
    problematic = []
    
    for index_name, index_def in indexes:
        # Check for non-existent columns
        if "data" in index_def:
            problematic.append((index_name, "References non-existent 'data' column"))
        if "USING GIN" in index_def and "jsonb_path_ops" not in index_def:
            problematic.append((index_name, "GIN index without jsonb_path_ops for JSONB column"))
    
    return problematic

# Report results in tabular format
def report_results(tables_info):
    """Print a report of the database schema issues."""
    print("\n" + "="*80)
    print("DATABASE SCHEMA DIAGNOSTIC REPORT")
    print("="*80)
    
    for table, info in tables_info.items():
        print(f"\nTABLE: {table}")
        print("-"*80)
        
        # Print columns
        column_data = [(col[0], col[1]) for col in info['columns']]
        print("COLUMNS:")
        print(tabulate(column_data, headers=["Column Name", "Data Type"], tablefmt="grid"))
        
        # Print missing columns
        if info['missing_columns']:
            print("\nMISSING REQUIRED COLUMNS:")
            print(", ".join(info['missing_columns']))
        
        # Print problematic indexes
        if info['problematic_indexes']:
            print("\nPROBLEMATIC INDEXES:")
            index_data = [(idx[0], idx[1]) for idx in info['problematic_indexes']]
            print(tabulate(index_data, headers=["Index Name", "Issue"], tablefmt="grid"))
        
        print("-"*80)
    
    # Print summary
    total_missing = sum(len(info['missing_columns']) for info in tables_info.values() if info['missing_columns'])
    total_problematic = sum(len(info['problematic_indexes']) for info in tables_info.values())
    
    print("\nSUMMARY:")
    print(f"Total missing columns: {total_missing}")
    print(f"Total problematic indexes: {total_problematic}")
    print("="*80)

# Main function
def main():
    """Main function for database schema diagnostics."""
    postgres_uri = load_config()
    conn = connect_to_postgres(postgres_uri)
    
    try:
        tables = get_tables(conn)
        tables_info = {}
        
        for table in tables:
            columns = get_table_columns(conn, table)
            indexes = get_table_indexes(conn, table)
            missing_columns = check_required_columns(table, columns)
            problematic_indexes = identify_problematic_indexes(indexes)
            
            tables_info[table] = {
                'columns': columns,
                'indexes': indexes,
                'missing_columns': missing_columns if missing_columns else [],
                'problematic_indexes': problematic_indexes
            }
        
        report_results(tables_info)
        
    except Exception as e:
        logger.error(f"Error in diagnostic script: {e}")
    finally:
        conn.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    main() 