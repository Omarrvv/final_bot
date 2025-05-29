#!/usr/bin/env python3
"""
Run the Add Missing JSONB Indexes migration script and verify the results.

This script:
1. Runs the migration script to add missing GIN indexes for JSONB columns
2. Verifies that the indexes were created successfully
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
    """Run the Add Missing JSONB Indexes migration script"""
    postgres_uri = get_postgres_uri()
    migration_file = "migrations/20240614_add_missing_jsonb_indexes.sql"
    
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
        
        # Check if GIN indexes exist for JSONB columns
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT tablename, indexname, indexdef
                FROM pg_indexes
                WHERE tablename IN ('attractions', 'accommodations', 'cities')
                AND indexname LIKE 'idx_%_jsonb'
                ORDER BY tablename, indexname;
            """)
            indexes = cursor.fetchall()
            
            expected_indexes = 6  # 2 for attractions, 2 for accommodations, 2 for cities
            if len(indexes) == expected_indexes:
                logger.info("✅ All GIN indexes for JSONB columns were created successfully")
                for index in indexes:
                    logger.info(f"  - {index['tablename']}: {index['indexname']}")
            else:
                logger.warning(f"⚠️ Only {len(indexes)} of {expected_indexes} expected GIN indexes were found")
                for index in indexes:
                    logger.info(f"  - {index['tablename']}: {index['indexname']}")
        
        # Test JSONB query performance
        with conn.cursor() as cursor:
            # Get query plan for a JSONB query
            cursor.execute("""
                EXPLAIN ANALYZE
                SELECT * FROM attractions
                WHERE name @> '{"en": "Pyramids of Giza"}';
            """)
            plan = cursor.fetchall()
            
            # Check if the query plan uses the GIN index
            plan_text = "\n".join([row[0] for row in plan])
            if "idx_attractions_name_jsonb" in plan_text:
                logger.info("✅ Query plan uses the GIN index for JSONB columns")
            else:
                logger.warning("⚠️ Query plan does not use the GIN index for JSONB columns")
                logger.info(f"Query plan:\n{plan_text}")
        
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
