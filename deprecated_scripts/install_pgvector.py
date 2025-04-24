#!/usr/bin/env python3
"""
Install pgvector extension

This script provides instructions for installing the pgvector extension for PostgreSQL,
which is required for vector operations in the Egypt Tourism Chatbot.
"""

import os
import sys
import subprocess
import logging
import platform
import psycopg2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("pgvector_installer")

def get_os_type():
    """
    Determine the operating system type.
    
    Returns:
        str: Operating system type ('mac', 'linux', 'windows', or 'unknown')
    """
    system = platform.system().lower()
    if system == 'darwin':
        return 'mac'
    elif system == 'linux':
        return 'linux'
    elif system == 'windows':
        return 'windows'
    else:
        return 'unknown'

def get_postgres_version():
    """
    Get the PostgreSQL version.
    
    Returns:
        str: PostgreSQL version or None if not found
    """
    try:
        result = subprocess.run(
            ['psql', '--version'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Parse version from output like "psql (PostgreSQL) 14.2"
            version_line = result.stdout.strip()
            version_parts = version_line.split()
            
            for part in version_parts:
                if part[0].isdigit():
                    return part.split('.')[0]  # Return major version
            
            return None
        else:
            logger.error(f"Error getting PostgreSQL version: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Failed to get PostgreSQL version: {e}")
        return None

def print_installation_instructions():
    """
    Print pgvector installation instructions based on OS and PostgreSQL version.
    """
    os_type = get_os_type()
    pg_version = get_postgres_version()
    
    logger.info(f"Detected OS: {os_type}")
    logger.info(f"Detected PostgreSQL version: {pg_version}")
    
    if os_type == 'mac':
        logger.info("\nInstallation instructions for macOS:")
        logger.info("1. Install pgvector using Homebrew:")
        logger.info("   brew install pgvector")
        logger.info("\n2. Enable the extension in your PostgreSQL database:")
        logger.info("   psql -d egypt_chatbot -c 'CREATE EXTENSION IF NOT EXISTS vector;'")
    
    elif os_type == 'linux':
        logger.info("\nInstallation instructions for Linux:")
        logger.info("1. Install pgvector from source:")
        logger.info("   git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git")
        logger.info("   cd pgvector")
        logger.info("   make")
        logger.info("   sudo make install")
        logger.info("\n2. Enable the extension in your PostgreSQL database:")
        logger.info("   psql -d egypt_chatbot -c 'CREATE EXTENSION IF NOT EXISTS vector;'")
    
    elif os_type == 'windows':
        logger.info("\nInstallation instructions for Windows:")
        logger.info("1. Download the latest release from https://github.com/pgvector/pgvector/releases")
        logger.info("2. Extract the files to the PostgreSQL extensions directory")
        logger.info("3. Enable the extension in your PostgreSQL database:")
        logger.info("   psql -d egypt_chatbot -c 'CREATE EXTENSION IF NOT EXISTS vector;'")
    
    else:
        logger.info("\nGeneric installation instructions:")
        logger.info("1. Follow instructions at https://github.com/pgvector/pgvector")
        logger.info("2. Enable the extension in your PostgreSQL database:")
        logger.info("   psql -d egypt_chatbot -c 'CREATE EXTENSION IF NOT EXISTS vector;'")

def check_pgvector_availability(postgres_uri):
    """
    Check if pgvector extension is available in PostgreSQL.
    
    Args:
        postgres_uri (str): PostgreSQL connection URI
        
    Returns:
        bool: True if pgvector is available, False otherwise
    """
    try:
        conn = psycopg2.connect(postgres_uri)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_available_extensions WHERE name = 'vector')"
        )
        is_available = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return is_available
    except psycopg2.Error as e:
        logger.error(f"Error checking pgvector availability: {e}")
        return False

def main():
    """Main function to install pgvector extension."""
    # Load environment variables
    load_dotenv()
    
    # Get PostgreSQL connection URI
    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable is not set")
        sys.exit(1)
    
    # Check if pgvector is already available
    logger.info("Checking if pgvector extension is available...")
    is_available = check_pgvector_availability(postgres_uri)
    
    if is_available:
        logger.info("pgvector extension is available in PostgreSQL")
        logger.info("You can now enable it with:")
        logger.info("   psql -d egypt_chatbot -c 'CREATE EXTENSION IF NOT EXISTS vector;'")
        return 0
    
    logger.info("pgvector extension is not available in PostgreSQL")
    print_installation_instructions()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 