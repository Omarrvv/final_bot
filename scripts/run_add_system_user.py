#!/usr/bin/env python3
"""
Run the Add System User migration script.

This script:
1. Runs the migration script to add a system user
2. Verifies that the system user was created successfully
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_postgres_uri():
    """Get PostgreSQL connection URI from environment or use default"""
    return os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")

def run_migration():
    """Run the Add System User migration script"""
    postgres_uri = get_postgres_uri()
    migration_file = "migrations/20240616_add_system_user.sql"
    
    try:
        # Connect to PostgreSQL
        logger.info(f"Connecting to PostgreSQL database")
        conn = psycopg2.connect(postgres_uri)
        conn.autocommit = True
        
        # Read migration file
        logger.info(f"Reading migration file: {migration_file}")
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        # Execute migration
        logger.info(f"Executing migration")
        with conn.cursor() as cursor:
            cursor.execute(sql)
        
        logger.info(f"Migration completed successfully")
        
        # Verify system user exists
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, username, role FROM users WHERE id = 'system'")
            system_user = cursor.fetchone()
            
            if system_user:
                logger.info(f"✅ System user exists: {system_user}")
                return True
            else:
                logger.error(f"❌ System user does not exist")
                return False
        
    except Exception as e:
        logger.error(f"Error running migration: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = run_migration()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
