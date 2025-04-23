#!/usr/bin/env python3
"""
Script to verify PostgreSQL connection directly.
"""
import os
import sys
import psycopg2
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("postgres_verify")

def verify_postgres_connection():
    """Verify PostgreSQL connection directly."""
    # Load environment variables
    load_dotenv()
    
    # Get PostgreSQL URI from environment
    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        logger.error("POSTGRES_URI not set in environment variables")
        return False
    
    logger.info(f"Testing connection to PostgreSQL: {postgres_uri.split('@')[-1]}")
    
    try:
        # Connect to PostgreSQL
        connection = psycopg2.connect(postgres_uri)
        cursor = connection.cursor()
        
        # Test connection by getting version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"Connected to PostgreSQL: {version}")
        
        # Check for required tables
        required_tables = ['attractions', 'restaurants', 'accommodations']
        for table in required_tables:
            cursor.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}');")
            exists = cursor.fetchone()[0]
            if exists:
                # Get count of rows
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                logger.info(f"Table '{table}' exists with {count} rows")
            else:
                logger.warning(f"Table '{table}' does not exist")
        
        # Close connection
        cursor.close()
        connection.close()
        
        return True
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
        return False

if __name__ == "__main__":
    success = verify_postgres_connection()
    sys.exit(0 if success else 1) 