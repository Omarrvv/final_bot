#!/usr/bin/env python3
"""
PostgreSQL Extensions Helper

This script checks for and enables required PostgreSQL extensions for
the Egypt Tourism Chatbot, specifically pgvector and PostGIS.
"""

import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv
import argparse

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("postgres_extensions")

# Required extensions
REQUIRED_EXTENSIONS = [
    "pgvector",  # For vector operations (embeddings)
    "postgis"    # For geospatial operations
]

def get_postgres_connection(postgres_uri):
    """
    Establish a connection to the PostgreSQL database.
    
    Args:
        postgres_uri (str): PostgreSQL connection URI
        
    Returns:
        Connection object or None if connection fails
    """
    try:
        conn = psycopg2.connect(postgres_uri)
        logger.info(f"Connected to PostgreSQL: {postgres_uri.split('@')[-1]}")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        return None

def check_extension(conn, extension_name):
    """
    Check if a PostgreSQL extension is already enabled.
    
    Args:
        conn: PostgreSQL connection
        extension_name (str): Name of the extension to check
        
    Returns:
        bool: True if extension is enabled, False otherwise
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = %s);",
            (extension_name,)
        )
        exists = cursor.fetchone()[0]
        cursor.close()
        
        return exists
    except psycopg2.Error as e:
        logger.error(f"Error checking extension {extension_name}: {e}")
        return False

def enable_extension(conn, extension_name):
    """
    Enable a PostgreSQL extension.
    
    Args:
        conn: PostgreSQL connection
        extension_name (str): Name of the extension to enable
        
    Returns:
        bool: True if extension was enabled successfully, False otherwise
    """
    try:
        cursor = conn.cursor()
        cursor.execute(f"CREATE EXTENSION IF NOT EXISTS {extension_name};")
        conn.commit()
        cursor.close()
        
        logger.info(f"Extension {extension_name} enabled successfully")
        return True
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Error enabling extension {extension_name}: {e}")
        return False

def check_superuser(conn):
    """
    Check if the current user has superuser privileges.
    
    Args:
        conn: PostgreSQL connection
        
    Returns:
        bool: True if user is superuser, False otherwise
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT usesuper FROM pg_user WHERE usename = CURRENT_USER;")
        result = cursor.fetchone()
        cursor.close()
        
        if result and result[0]:
            logger.info("Current user has superuser privileges")
            return True
        else:
            logger.warning("Current user does not have superuser privileges")
        return False
    except psycopg2.Error as e:
        logger.error(f"Error checking superuser privileges: {e}")
        return False

def check_extension_availability(conn, extension_name):
    """
    Check if an extension is available for installation.
    
    Args:
        conn: PostgreSQL connection
        extension_name (str): Name of the extension to check
        
    Returns:
        bool: True if extension is available, False otherwise
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_available_extensions WHERE name = %s);",
            (extension_name,)
        )
        available = cursor.fetchone()[0]
        cursor.close()
        
        return available
    except psycopg2.Error as e:
        logger.error(f"Error checking availability of extension {extension_name}: {e}")
        return False

def main():
    """Main function to check and enable required PostgreSQL extensions."""
    parser = argparse.ArgumentParser(description='Check and enable PostgreSQL extensions')
    parser.add_argument('--uri', help='PostgreSQL connection URI (overrides .env file)')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Get PostgreSQL URI
    postgres_uri = args.uri or os.environ.get("POSTGRES_URI")
    
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable not set")
        logger.error("Please set POSTGRES_URI in .env file or provide with --uri argument")
        return 1
    
    # Connect to PostgreSQL
    conn = get_postgres_connection(postgres_uri)
    if not conn:
        return 1
    
    # Check if user is superuser
    is_superuser = check_superuser(conn)
    if not is_superuser:
        logger.warning("Some operations may fail without superuser privileges")
    
    # Check and enable extensions
    extensions_status = {}
    
    for extension_name in REQUIRED_EXTENSIONS:
        # Check if extension is available
        is_available = check_extension_availability(conn, extension_name)
        
        if not is_available:
            logger.error(f"Extension {extension_name} is not available for installation")
            extensions_status[extension_name] = "Not available"
            continue
        
        # Check if extension is already enabled
        is_enabled = check_extension(conn, extension_name)
        
        if is_enabled:
            logger.info(f"Extension {extension_name} is already enabled")
            extensions_status[extension_name] = "Already enabled"
            continue
            
                # Try to enable the extension
        if enable_extension(conn, extension_name):
            extensions_status[extension_name] = "Enabled successfully"
                else:
            extensions_status[extension_name] = "Failed to enable"
    
    # Close connection
    conn.close()
    
    # Print summary
    print("\nPostgreSQL Extensions Status:")
    print("-----------------------------")
    for extension, status in extensions_status.items():
        print(f"{extension}: {status}")
    
    # Check if any required extensions are missing
    missing_extensions = [ext for ext, status in extensions_status.items() 
                         if status in ["Not available", "Failed to enable"]]
    
    if missing_extensions:
        logger.error("Some required extensions are missing or failed to enable")
        return 1
    
    logger.info("All required extensions are available and enabled")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 