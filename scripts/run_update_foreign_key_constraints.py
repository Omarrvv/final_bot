#!/usr/bin/env python3
"""
Run the Update Foreign Key Constraints migration script and verify the results.

This script:
1. Runs the migration script to update foreign key constraints
2. Verifies that the constraints were updated successfully
3. Tests constraint enforcement
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
    """Run the Update Foreign Key Constraints migration script"""
    postgres_uri = get_postgres_uri()
    migration_file = "migrations/20240615_update_foreign_key_constraints.sql"

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

        # Check foreign key constraints and their actions
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS referenced_table,
                    ccu.column_name AS referenced_column,
                    rc.delete_rule,
                    rc.update_rule
                FROM
                    information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    JOIN information_schema.referential_constraints AS rc
                        ON tc.constraint_name = rc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name IN ('attractions', 'accommodations', 'cities')
                ORDER BY tc.table_name, kcu.column_name;
            """)
            constraints = cursor.fetchall()

            # Check if constraints were updated correctly
            for constraint in constraints:
                table_name = constraint['table_name']
                column_name = constraint['column_name']
                delete_rule = constraint['delete_rule']
                update_rule = constraint['update_rule']

                if table_name == 'attractions' and column_name == 'type_id':
                    if delete_rule == 'RESTRICT':
                        logger.info(f"✅ attractions.type_id constraint updated correctly: ON DELETE {delete_rule}")
                    else:
                        logger.warning(f"⚠️ attractions.type_id constraint not updated correctly: ON DELETE {delete_rule} (expected RESTRICT)")

                elif table_name == 'accommodations' and column_name == 'type_id':
                    if delete_rule == 'RESTRICT':
                        logger.info(f"✅ accommodations.type_id constraint updated correctly: ON DELETE {delete_rule}")
                    else:
                        logger.warning(f"⚠️ accommodations.type_id constraint not updated correctly: ON DELETE {delete_rule} (expected RESTRICT)")

                elif table_name == 'cities' and column_name == 'user_id':
                    if update_rule == 'CASCADE':
                        logger.info(f"✅ cities.user_id constraint updated correctly: ON UPDATE {update_rule}")
                    else:
                        logger.warning(f"⚠️ cities.user_id constraint not updated correctly: ON UPDATE {update_rule} (expected CASCADE)")

        # Test constraint enforcement for attractions.type_id
        with conn.cursor() as cursor:
            try:
                # Try to delete an attraction type that is referenced by an attraction
                cursor.execute("DELETE FROM attraction_types WHERE type = 'historical';")
                logger.error("❌ Failed to enforce RESTRICT constraint on attractions.type_id")
            except psycopg2.errors.ForeignKeyViolation:
                logger.info("✅ RESTRICT constraint on attractions.type_id is enforced correctly")
            except Exception as e:
                logger.error(f"❌ Error testing RESTRICT constraint on attractions.type_id: {str(e)}")
            finally:
                # Make sure transaction is rolled back
                conn.rollback()

        # Test constraint enforcement for accommodations.type_id
        with conn.cursor() as cursor:
            try:
                # Try to delete an accommodation type that is referenced by an accommodation
                cursor.execute("DELETE FROM accommodation_types WHERE type = 'luxury_hotel';")
                logger.error("❌ Failed to enforce RESTRICT constraint on accommodations.type_id")
            except psycopg2.errors.ForeignKeyViolation:
                logger.info("✅ RESTRICT constraint on accommodations.type_id is enforced correctly")
            except Exception as e:
                logger.error(f"❌ Error testing RESTRICT constraint on accommodations.type_id: {str(e)}")
            finally:
                # Make sure transaction is rolled back
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
