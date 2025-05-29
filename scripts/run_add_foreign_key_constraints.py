#!/usr/bin/env python3
"""
Run the Add Foreign Key Constraints migration script and verify the results.

This script:
1. Runs the migration script to add foreign key constraints
2. Verifies that the constraints were added successfully
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
    """Run the Add Foreign Key Constraints migration script"""
    postgres_uri = get_postgres_uri()
    migration_file = "migrations/20240613_add_foreign_key_constraints.sql"
    
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
        
        # Check if foreign key constraints exist
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    tc.table_schema, 
                    tc.constraint_name, 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name IN ('attractions', 'accommodations', 'cities')
                ORDER BY tc.table_name, kcu.column_name;
            """)
            constraints = cursor.fetchall()
            
            expected_constraints = 7  # 3 for attractions, 3 for accommodations, 1 for cities
            if len(constraints) == expected_constraints:
                logger.info("✅ All foreign key constraints were added successfully")
                for constraint in constraints:
                    logger.info(f"  - {constraint['table_name']}.{constraint['column_name']} -> {constraint['foreign_table_name']}.{constraint['foreign_column_name']}")
            else:
                logger.warning(f"⚠️ Only {len(constraints)} of {expected_constraints} expected foreign key constraints were found")
                for constraint in constraints:
                    logger.info(f"  - {constraint['table_name']}.{constraint['column_name']} -> {constraint['foreign_table_name']}.{constraint['foreign_column_name']}")
        
        # Test constraint enforcement
        with conn.cursor() as cursor:
            try:
                # Try to insert a record with an invalid foreign key
                cursor.execute("""
                    INSERT INTO attractions (id, name_en, city_id)
                    VALUES ('test_attraction', 'Test Attraction', 'nonexistent_city');
                """)
                logger.warning("⚠️ Foreign key constraint not enforced for attractions.city_id")
            except psycopg2.errors.ForeignKeyViolation:
                logger.info("✅ Foreign key constraint enforced for attractions.city_id")
            except Exception as e:
                logger.error(f"Error testing constraint: {str(e)}")
            finally:
                # Rollback the transaction
                conn.rollback()
        
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
