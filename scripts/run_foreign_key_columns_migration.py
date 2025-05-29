#!/usr/bin/env python3
"""
Run the Foreign Key Columns migration script and verify the results.

This script:
1. Runs the migration script to add foreign key columns
2. Verifies that the columns were added successfully
3. Verifies that indexes were created
4. Reports the results
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
    """Run the Foreign Key Columns migration script"""
    postgres_uri = get_postgres_uri()
    migration_file = "migrations/20240611_add_foreign_key_columns.sql"
    
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
        
        # Check if foreign key columns exist
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT table_name, column_name 
                FROM information_schema.columns 
                WHERE table_name IN ('attractions', 'accommodations', 'cities') 
                AND column_name IN ('city_id', 'region_id', 'type_id')
                ORDER BY table_name, column_name;
            """)
            columns = cursor.fetchall()
            
            expected_columns = 7  # 3 for attractions, 3 for accommodations, 1 for cities
            if len(columns) == expected_columns:
                logger.info("✅ All foreign key columns were added successfully")
                for column in columns:
                    logger.info(f"  - {column['table_name']}.{column['column_name']}")
            else:
                logger.warning(f"⚠️ Only {len(columns)} of {expected_columns} expected foreign key columns were found")
                for column in columns:
                    logger.info(f"  - {column['table_name']}.{column['column_name']}")
        
        # Check if indexes exist
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT tablename, indexname 
                FROM pg_indexes 
                WHERE tablename IN ('attractions', 'accommodations', 'cities') 
                AND indexname LIKE 'idx_%_id'
                ORDER BY tablename, indexname;
            """)
            indexes = cursor.fetchall()
            
            expected_indexes = 7  # 3 for attractions, 3 for accommodations, 1 for cities
            if len(indexes) >= expected_indexes:
                logger.info("✅ All indexes were created successfully")
                for index in indexes:
                    logger.info(f"  - {index['tablename']}: {index['indexname']}")
            else:
                logger.warning(f"⚠️ Only {len(indexes)} of {expected_indexes} expected indexes were found")
                for index in indexes:
                    logger.info(f"  - {index['tablename']}: {index['indexname']}")
        
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
