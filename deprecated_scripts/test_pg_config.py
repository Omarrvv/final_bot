#!/usr/bin/env python3
import os
import psycopg2
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Test different connection configurations
def test_connections():
    """Test multiple PostgreSQL connection configurations."""
    
    # Connection strings to test
    connection_strings = [
        # Simple DSN
        "dbname=egypt_chatbot",
        
        # Full DSN with Docker default credentials
        "postgresql://user:password@localhost:5432/egypt_chatbot",
        
        # Full DSN with Docker hostname
        "postgresql://user:password@egypt_chatbot_postgres:5432/egypt_chatbot",
        
        # Using environment variable (if set)
        os.environ.get("POSTGRES_URI")
    ]
    
    # Filter out None values
    connection_strings = [cs for cs in connection_strings if cs]
    
    success = False
    
    for conn_str in connection_strings:
        logger.info(f"Testing connection with: {conn_str.replace('password', '****') if 'password' in conn_str else conn_str}")
        
        try:
            conn = psycopg2.connect(conn_str)
            cursor = conn.cursor()
            
            # Test a simple query
            cursor.execute("SELECT current_database(), current_user")
            db, user = cursor.fetchone()
            logger.info(f"✅ SUCCESS! Connected to database '{db}' as user '{user}'")
            
            # Get PostgreSQL version
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            logger.info(f"PostgreSQL version: {version}")
            
            # Check existing tables
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")
            
            conn.close()
            success = True
            logger.info(f"This connection string works: {conn_str.replace('password', '****') if 'password' in conn_str else conn_str}")
            break
            
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
    
    return success

if __name__ == "__main__":
    logger.info("Testing PostgreSQL connection configurations...")
    if test_connections():
        logger.info("At least one connection configuration works! Your PostgreSQL is correctly configured.")
        exit(0)
    else:
        logger.error("All connection configurations failed. Please check your PostgreSQL setup.")
        exit(1)
