#!/usr/bin/env python3
"""
Simple PostgreSQL connection test using a direct connection string.
"""

import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def test_connection():
    """Test direct connection to PostgreSQL database."""
    try:
        # Use a direct connection string without username/password
        conn = psycopg2.connect(dsn="dbname=egypt_chatbot")
        
        logger.info("Successfully connected to PostgreSQL!")
        
        # Test a simple query
        with conn.cursor() as cursor:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"Found tables: {', '.join(tables)}")
        
        conn.close()
        logger.info("Connection test successful and connection closed.")
        return True
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Testing PostgreSQL connection...")
    success = test_connection()
    exit(0 if success else 1)
