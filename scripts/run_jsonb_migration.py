#!/usr/bin/env python3
"""
Run the JSONB migration script and verify the results.

This script:
1. Runs the migration script to migrate data from text fields to JSONB columns
2. Verifies that the migration was successful
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
    """Run the JSONB migration script"""
    postgres_uri = get_postgres_uri()
    migration_file = "migrations/20240610_migrate_data_to_jsonb.sql"
    
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
        
        # Check if JSONB columns exist
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name IN ('attractions', 'accommodations', 'cities')
                AND column_name IN ('name', 'description')
                AND data_type = 'jsonb'
            """)
            columns = cursor.fetchall()
            
            expected_columns = 6  # 2 columns for each of 3 tables
            if len(columns) == expected_columns:
                logger.info("✅ All JSONB columns were created successfully")
                for column in columns:
                    logger.info(f"  - {column['table_name']}.{column['column_name']} ({column['data_type']})")
            else:
                logger.warning(f"⚠️ Only {len(columns)} of {expected_columns} expected JSONB columns were found")
                for column in columns:
                    logger.info(f"  - {column['table_name']}.{column['column_name']} ({column['data_type']})")
        
        # Check if data was migrated
        tables = ['attractions', 'accommodations', 'cities']
        for table in tables:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(f"""
                    SELECT COUNT(*) as total,
                           COUNT(name) as with_name,
                           COUNT(CASE WHEN name IS NOT NULL THEN 1 END) as with_name_jsonb
                    FROM {table}
                """)
                result = cursor.fetchone()
                logger.info(f"✅ {table}: {result['with_name_jsonb']} of {result['total']} rows have data in the name JSONB column")
        
        # Check if reference integrity issues were fixed
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT a.id, a.type 
                FROM attractions a 
                LEFT JOIN attraction_types t ON a.type = t.type 
                WHERE t.type IS NULL
            """)
            attractions_with_issues = cursor.fetchall()
            
            if not attractions_with_issues:
                logger.info("✅ All attractions have valid types")
            else:
                logger.warning(f"⚠️ {len(attractions_with_issues)} attractions still have invalid types")
                for attraction in attractions_with_issues:
                    logger.warning(f"  - {attraction['id']}: {attraction['type']}")
            
            cursor.execute("""
                SELECT a.id, a.type 
                FROM accommodations a 
                LEFT JOIN accommodation_types t ON a.type = t.type 
                WHERE t.type IS NULL
            """)
            accommodations_with_issues = cursor.fetchall()
            
            if not accommodations_with_issues:
                logger.info("✅ All accommodations have valid types")
            else:
                logger.warning(f"⚠️ {len(accommodations_with_issues)} accommodations still have invalid types")
                for accommodation in accommodations_with_issues:
                    logger.warning(f"  - {accommodation['id']}: {accommodation['type']}")
        
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
