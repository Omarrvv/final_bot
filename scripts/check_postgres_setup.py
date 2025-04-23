#!/usr/bin/env python3
"""
PostgreSQL Setup Verification Script

This script verifies the PostgreSQL setup for the Egypt Chatbot application.
It checks:
1. PostgreSQL connection
2. Required extensions (pgvector, postgis)
3. Database schema
4. Vector column setup

Usage:
    python check_postgres_setup.py [--fix]

Options:
    --fix    Attempt to fix issues (install extensions, create vector columns)
"""

import os
import sys
import argparse
import logging
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Import project modules
from src.utils.logger import get_logger

# Configure logging
logger = get_logger("postgres_setup")

# Required extensions
REQUIRED_EXTENSIONS = [
    "pgvector",   # For vector operations
    "postgis"     # For geospatial operations
]

# Vector dimension (for BERT-based models)
VECTOR_DIMENSION = 768

def get_postgres_connection(postgres_uri):
    """
    Create a connection to the PostgreSQL database.
    
    Args:
        postgres_uri (str): URI for the PostgreSQL database
        
    Returns:
        psycopg2.connection: Connection to the PostgreSQL database or None on failure
    """
    try:
        conn = psycopg2.connect(postgres_uri)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Error connecting to PostgreSQL database: {e}")
        return None

def check_extension(conn, extension_name):
    """
    Check if an extension is installed and enabled.
    
    Args:
        conn (psycopg2.connection): PostgreSQL connection
        extension_name (str): Name of the extension
        
    Returns:
        bool: True if extension is enabled, False otherwise
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = %s)",
            (extension_name,)
        )
        result = cursor.fetchone()[0]
        cursor.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error checking extension {extension_name}: {e}")
        return False

def install_extension(conn, extension_name):
    """
    Install and enable an extension.
    
    Args:
        conn (psycopg2.connection): PostgreSQL connection
        extension_name (str): Name of the extension
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        cursor.execute(sql.SQL("CREATE EXTENSION IF NOT EXISTS {}").format(
            sql.Identifier(extension_name)
        ))
        conn.commit()
        cursor.close()
        return True
    except psycopg2.Error as e:
        logger.error(f"Error installing extension {extension_name}: {e}")
        conn.rollback()
        return False

def check_table_exists(conn, table_name):
    """
    Check if a table exists in the database.
    
    Args:
        conn (psycopg2.connection): PostgreSQL connection
        table_name (str): Name of the table
        
    Returns:
        bool: True if table exists, False otherwise
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
            (table_name,)
        )
        result = cursor.fetchone()[0]
        cursor.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error checking table {table_name}: {e}")
        return False

def check_vector_column(conn, table_name, column_name="embedding_vector"):
    """
    Check if a vector column exists in a table.
    
    Args:
        conn (psycopg2.connection): PostgreSQL connection
        table_name (str): Name of the table
        column_name (str): Name of the vector column
        
    Returns:
        bool: True if column exists, False otherwise
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT EXISTS(
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            )
            """,
            (table_name, column_name)
        )
        result = cursor.fetchone()[0]
        cursor.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error checking vector column for table {table_name}: {e}")
        return False

def add_vector_column(conn, table_name, column_name="embedding_vector", dimension=VECTOR_DIMENSION):
    """
    Add a vector column to a table.
    
    Args:
        conn (psycopg2.connection): PostgreSQL connection
        table_name (str): Name of the table
        column_name (str): Name of the vector column
        dimension (int): Vector dimension
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        # Check if pgvector extension is enabled
        if not check_extension(conn, "pgvector"):
            logger.error(f"Cannot add vector column to {table_name}: pgvector extension not enabled")
            return False
        
        # Add vector column
        cursor.execute(
            sql.SQL("ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} vector({})").format(
                sql.Identifier(table_name),
                sql.Identifier(column_name),
                sql.Literal(dimension)
            )
        )
        conn.commit()
        cursor.close()
        return True
    except psycopg2.Error as e:
        logger.error(f"Error adding vector column to table {table_name}: {e}")
        conn.rollback()
        return False

def check_vector_index(conn, table_name, column_name="embedding_vector", index_name=None):
    """
    Check if a vector index exists for a column.
    
    Args:
        conn (psycopg2.connection): PostgreSQL connection
        table_name (str): Name of the table
        column_name (str): Name of the vector column
        index_name (str): Name of the index (optional)
        
    Returns:
        bool: True if index exists, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        if index_name is None:
            index_name = f"idx_{table_name}_{column_name}"
        
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname = %s)",
            (index_name,)
        )
        result = cursor.fetchone()[0]
        cursor.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error checking vector index for table {table_name}: {e}")
        return False

def create_vector_index(conn, table_name, column_name="embedding_vector", index_name=None, index_method="ivfflat"):
    """
    Create a vector index for a column.
    
    Args:
        conn (psycopg2.connection): PostgreSQL connection
        table_name (str): Name of the table
        column_name (str): Name of the vector column
        index_name (str): Name of the index (optional)
        index_method (str): Index method (ivfflat or hnsw)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        if index_name is None:
            index_name = f"idx_{table_name}_{column_name}"
        
        # Choose index type based on method
        if index_method.lower() == "hnsw":
            index_operator = "vector_l2_ops"
            create_idx_sql = sql.SQL(
                "CREATE INDEX IF NOT EXISTS {} ON {} USING hnsw({} {})").format(
                sql.Identifier(index_name),
                sql.Identifier(table_name),
                sql.Identifier(column_name),
                sql.SQL(index_operator)
            )
        else:  # Default to ivfflat
            index_operator = "vector_l2_ops"
            create_idx_sql = sql.SQL(
                "CREATE INDEX IF NOT EXISTS {} ON {} USING ivfflat({} {})").format(
                sql.Identifier(index_name),
                sql.Identifier(table_name),
                sql.Identifier(column_name),
                sql.SQL(index_operator)
            )
        
        cursor.execute(create_idx_sql)
        conn.commit()
        cursor.close()
        return True
    except psycopg2.Error as e:
        logger.error(f"Error creating vector index for table {table_name}: {e}")
        conn.rollback()
        return False

def print_check_result(check_name, result):
    """
    Print a formatted check result.
    
    Args:
        check_name (str): Name of the check
        result (bool): Result of the check
    """
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{status} | {check_name}")

def main():
    """Main function to verify PostgreSQL setup."""
    parser = argparse.ArgumentParser(description="Verify PostgreSQL setup for Egypt Chatbot")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix issues")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Load environment variables
    load_dotenv()
    
    # Get database connection information
    postgres_uri = os.environ.get("POSTGRES_URI", "")
    
    if not postgres_uri:
        logger.error("PostgreSQL URI not set in environment variables")
        sys.exit(1)
    
    # Connect to PostgreSQL
    print("Connecting to PostgreSQL...")
    conn = get_postgres_connection(postgres_uri)
    
    if conn is None:
        print("❌ FAIL | PostgreSQL Connection")
        sys.exit(1)
    
    print("✅ PASS | PostgreSQL Connection\n")
    
    # Check extensions
    print("Checking required extensions:")
    all_extensions_ok = True
    
    for extension in REQUIRED_EXTENSIONS:
        extension_enabled = check_extension(conn, extension)
        print_check_result(f"Extension: {extension}", extension_enabled)
        
        if not extension_enabled and args.fix:
            print(f"  Attempting to install extension: {extension}...")
            if install_extension(conn, extension):
                print(f"  ✅ Successfully installed extension: {extension}")
            else:
                print(f"  ❌ Failed to install extension: {extension}")
                all_extensions_ok = False
        elif not extension_enabled:
            all_extensions_ok = False
    
    if not all_extensions_ok:
        print("\n⚠️  Some required extensions are not enabled.")
        if not args.fix:
            print("  Run with --fix option to attempt automatic installation.")
        print("  You may need to install these extensions manually using:")
        print("  CREATE EXTENSION IF NOT EXISTS <extension_name>;\n")
    
    # Check required tables
    print("\nChecking required tables:")
    required_tables = ["attractions", "accommodations", "restaurants", "cities"]
    all_tables_ok = True
    vector_tables = []
    
    for table in required_tables:
        table_exists = check_table_exists(conn, table)
        print_check_result(f"Table: {table}", table_exists)
        if table_exists:
            vector_tables.append(table)
        else:
            all_tables_ok = False
    
    if not all_tables_ok:
        print("\n⚠️  Some required tables are missing.")
        print("  Run the migration script first to create all required tables.")
    
    # Check vector columns
    if "pgvector" in REQUIRED_EXTENSIONS:
        print("\nChecking vector columns:")
        vector_column_name = "embedding_vector"
        all_vector_columns_ok = True
        
        for table in vector_tables:
            has_vector_column = check_vector_column(conn, table, vector_column_name)
            print_check_result(f"Vector column in {table}", has_vector_column)
            
            if not has_vector_column and args.fix:
                print(f"  Attempting to add vector column to {table}...")
                if add_vector_column(conn, table, vector_column_name, VECTOR_DIMENSION):
                    print(f"  ✅ Successfully added vector column to {table}")
                    has_vector_column = True
                else:
                    print(f"  ❌ Failed to add vector column to {table}")
                    all_vector_columns_ok = False
            elif not has_vector_column:
                all_vector_columns_ok = False
            
            # Check vector index if column exists
            if has_vector_column:
                has_vector_index = check_vector_index(conn, table, vector_column_name)
                print_check_result(f"Vector index in {table}", has_vector_index)
                
                if not has_vector_index and args.fix:
                    print(f"  Attempting to create vector index for {table}...")
                    if create_vector_index(conn, table, vector_column_name):
                        print(f"  ✅ Successfully created vector index for {table}")
                    else:
                        print(f"  ❌ Failed to create vector index for {table}")
        
        if not all_vector_columns_ok:
            print("\n⚠️  Some vector columns are missing.")
            if not args.fix:
                print("  Run with --fix option to add missing vector columns.")
            print("  Alternatively, run the create_vector_columns.py script.")
    
    # Close connection
    conn.close()
    
    print("\nSetup verification completed.")

if __name__ == "__main__":
    main() 