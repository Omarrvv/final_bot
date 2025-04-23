#!/usr/bin/env python3
"""
Verify and install PostgreSQL extensions required for the Egypt Tourism Chatbot.

This script checks for the required PostgreSQL extensions (pgvector and postgis)
and attempts to install them if they are not already available.

Usage:
    python3 verify_postgres_extensions.py [--install]

Options:
    --install   Attempt to install missing extensions (requires superuser privileges)
    --verbose   Enable verbose output
"""

import os
import sys
import argparse
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Required PostgreSQL extensions
REQUIRED_EXTENSIONS = ['vector', 'postgis']


def get_postgres_connection(postgres_uri):
    """
    Connect to PostgreSQL database.
    
    Args:
        postgres_uri (str): PostgreSQL connection URI
        
    Returns:
        connection: PostgreSQL connection object
    """
    try:
        conn = psycopg2.connect(postgres_uri)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        sys.exit(1)


def check_extension_exists(cursor, extension_name):
    """
    Check if a PostgreSQL extension exists.
    
    Args:
        cursor: PostgreSQL cursor
        extension_name (str): Name of the extension to check
        
    Returns:
        bool: True if extension exists, False otherwise
    """
    try:
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = %s)",
            (extension_name,)
        )
        return cursor.fetchone()[0]
    except psycopg2.Error as e:
        logger.error(f"Error checking for extension {extension_name}: {e}")
        return False


def check_extension_available(cursor, extension_name):
    """
    Check if a PostgreSQL extension is available to install.
    
    Args:
        cursor: PostgreSQL cursor
        extension_name (str): Name of the extension to check
        
    Returns:
        bool: True if extension is available, False otherwise
    """
    try:
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_available_extensions WHERE name = %s)",
            (extension_name,)
        )
        return cursor.fetchone()[0]
    except psycopg2.Error as e:
        logger.error(f"Error checking if extension {extension_name} is available: {e}")
        return False


def install_extension(cursor, extension_name):
    """
    Install a PostgreSQL extension.
    
    Args:
        cursor: PostgreSQL cursor
        extension_name (str): Name of the extension to install
        
    Returns:
        bool: True if extension was installed, False otherwise
    """
    try:
        cursor.execute(f"CREATE EXTENSION IF NOT EXISTS {extension_name}")
        logger.info(f"Extension {extension_name} installed successfully")
        return True
    except psycopg2.Error as e:
        logger.error(f"Failed to install extension {extension_name}: {e}")
        return False


def main():
    """Main function to verify and install PostgreSQL extensions."""
    parser = argparse.ArgumentParser(description='Verify and install PostgreSQL extensions')
    parser.add_argument('--install', action='store_true', help='Attempt to install missing extensions')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()

    # Set log level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Load environment variables
    load_dotenv()
    
    # Get PostgreSQL connection URI
    postgres_uri = os.getenv('POSTGRES_URI')
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable is not set")
        sys.exit(1)
    
    logger.info("Connecting to PostgreSQL database...")
    conn = get_postgres_connection(postgres_uri)
    cursor = conn.cursor()
    
    all_extensions_available = True
    missing_extensions = []
    
    for extension in REQUIRED_EXTENSIONS:
        if check_extension_exists(cursor, extension):
            logger.info(f"Extension {extension} is already installed")
        else:
            logger.warning(f"Extension {extension} is not installed")
            missing_extensions.append(extension)
            
            # Check if the extension is available
            if check_extension_available(cursor, extension):
                logger.info(f"Extension {extension} is available for installation")
            else:
                logger.error(f"Extension {extension} is not available. Please install it at the system level.")
                all_extensions_available = False
    
    if missing_extensions and args.install:
        logger.info("Attempting to install missing extensions...")
        
        for extension in missing_extensions:
            if check_extension_available(cursor, extension):
                logger.info(f"Installing extension {extension}...")
                if install_extension(cursor, extension):
                    logger.info(f"Extension {extension} installed successfully")
                else:
                    logger.error(f"Failed to install extension {extension}. May require superuser privileges.")
                    all_extensions_available = False
    
    conn.close()
    
    if not all_extensions_available:
        logger.error("Some required extensions are not available or could not be installed")
        sys.exit(1)
    
    if missing_extensions and not args.install:
        logger.warning("Some extensions are missing. Run with --install to attempt installation.")
        sys.exit(1)
    
    logger.info("All required PostgreSQL extensions are installed and available")
    sys.exit(0)


if __name__ == "__main__":
    main() 