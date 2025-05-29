#!/usr/bin/env python3
"""
Run the Populate Foreign Key Columns migration script and verify the results.

This script:
1. Runs the migration script to populate foreign key columns
2. Verifies that the columns were populated successfully
3. Reports the results
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
    """Run the Populate Foreign Key Columns migration script"""
    postgres_uri = get_postgres_uri()
    migration_file = "migrations/20240612_populate_foreign_key_columns.sql"
    
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
        return True
        
    except Exception as e:
        logger.error(f"Error running migration: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def verify_migration():
    """Verify that the migration was successful"""
    postgres_uri = get_postgres_uri()
    
    try:
        # Connect to PostgreSQL
        logger.info(f"Connecting to PostgreSQL database to verify migration")
        conn = psycopg2.connect(postgres_uri)
        conn.autocommit = True
        
        # Check if regions were created
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM regions")
            result = cursor.fetchone()
            if result['count'] >= 3:
                logger.info(f"✅ Regions table has {result['count']} rows")
            else:
                logger.warning(f"⚠️ Regions table has only {result['count']} rows (expected at least 3)")
        
        # Check if cities.region_id is populated
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as total, 
                       COUNT(region_id) as populated
                FROM cities
            """)
            result = cursor.fetchone()
            if result['populated'] == result['total']:
                logger.info(f"✅ All {result['total']} cities have region_id populated")
            else:
                logger.warning(f"⚠️ Only {result['populated']} of {result['total']} cities have region_id populated")
        
        # Check if attractions foreign keys are populated
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as total, 
                       COUNT(city_id) as city_populated,
                       COUNT(region_id) as region_populated,
                       COUNT(type_id) as type_populated
                FROM attractions
            """)
            result = cursor.fetchone()
            if result['city_populated'] == result['total']:
                logger.info(f"✅ All {result['total']} attractions have city_id populated")
            else:
                logger.warning(f"⚠️ Only {result['city_populated']} of {result['total']} attractions have city_id populated")
            
            if result['region_populated'] == result['total']:
                logger.info(f"✅ All {result['total']} attractions have region_id populated")
            else:
                logger.warning(f"⚠️ Only {result['region_populated']} of {result['total']} attractions have region_id populated")
            
            if result['type_populated'] == result['total']:
                logger.info(f"✅ All {result['total']} attractions have type_id populated")
            else:
                logger.warning(f"⚠️ Only {result['type_populated']} of {result['total']} attractions have type_id populated")
        
        # Check if accommodations foreign keys are populated
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as total, 
                       COUNT(city_id) as city_populated,
                       COUNT(region_id) as region_populated,
                       COUNT(type_id) as type_populated
                FROM accommodations
            """)
            result = cursor.fetchone()
            if result['city_populated'] == result['total']:
                logger.info(f"✅ All {result['total']} accommodations have city_id populated")
            else:
                logger.warning(f"⚠️ Only {result['city_populated']} of {result['total']} accommodations have city_id populated")
            
            if result['region_populated'] == result['total']:
                logger.info(f"✅ All {result['total']} accommodations have region_id populated")
            else:
                logger.warning(f"⚠️ Only {result['region_populated']} of {result['total']} accommodations have region_id populated")
            
            if result['type_populated'] == result['total']:
                logger.info(f"✅ All {result['total']} accommodations have type_id populated")
            else:
                logger.warning(f"⚠️ Only {result['type_populated']} of {result['total']} accommodations have type_id populated")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying migration: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Run migration
    success = run_migration()
    
    if success:
        # Verify migration
        verify_migration()
    else:
        logger.error("Migration failed, skipping verification")
        sys.exit(1)
