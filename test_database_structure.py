#!/usr/bin/env python
"""
Test script for Database Structure Verification

This script verifies the current database structure to ensure:
1. JSONB columns exist and are properly indexed
2. Foreign key columns exist and are properly indexed
3. Foreign key constraints are properly configured
4. Data integrity is maintained
"""

import os
import sys
import logging
import json
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("db_structure_test")

# Database connection parameters
DB_NAME = os.environ.get("DB_NAME", "egypt_chatbot")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")

def get_postgres_uri():
    """Get PostgreSQL connection URI"""
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def connect_to_database():
    """Connect to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(get_postgres_uri())
        conn.autocommit = True
        logger.info(f"Connected to database: {DB_NAME}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def verify_jsonb_columns():
    """Verify JSONB columns exist and are properly indexed"""
    conn = connect_to_database()
    if not conn:
        return False
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Check tables that should have JSONB columns
            tables = ["attractions", "accommodations", "cities", "regions"]
            jsonb_columns = ["name", "description"]
            
            all_valid = True
            
            for table in tables:
                logger.info(f"Checking JSONB columns for table: {table}")
                
                # Check if JSONB columns exist
                for column in jsonb_columns:
                    cursor.execute(f"""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = %s
                    """, (table, column))
                    
                    result = cursor.fetchone()
                    if not result:
                        logger.error(f"❌ Column {column} does not exist in table {table}")
                        all_valid = False
                        continue
                        
                    if result["data_type"] != "jsonb":
                        logger.error(f"❌ Column {column} in table {table} is not JSONB type (found {result['data_type']})")
                        all_valid = False
                        continue
                        
                    logger.info(f"✅ Column {column} exists in table {table} with JSONB type")
                
                # Check if GIN indexes exist for JSONB columns
                for column in jsonb_columns:
                    cursor.execute(f"""
                        SELECT indexname, indexdef
                        FROM pg_indexes
                        WHERE tablename = %s AND indexdef LIKE %s
                    """, (table, f"%{column}%gin%"))
                    
                    result = cursor.fetchone()
                    if not result:
                        logger.error(f"❌ No GIN index found for {column} in table {table}")
                        all_valid = False
                        continue
                        
                    logger.info(f"✅ GIN index exists for {column} in table {table}: {result['indexname']}")
            
            return all_valid
            
    except Exception as e:
        logger.error(f"Error verifying JSONB columns: {e}")
        return False
    finally:
        conn.close()

def verify_foreign_keys():
    """Verify foreign key columns exist and are properly configured"""
    conn = connect_to_database()
    if not conn:
        return False
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Define expected foreign key relationships
            expected_fks = [
                {"table": "attractions", "column": "city_id", "ref_table": "cities", "ref_column": "id"},
                {"table": "attractions", "column": "region_id", "ref_table": "regions", "ref_column": "id"},
                {"table": "attractions", "column": "type_id", "ref_table": "attraction_types", "ref_column": "type"},
                {"table": "accommodations", "column": "city_id", "ref_table": "cities", "ref_column": "id"},
                {"table": "accommodations", "column": "region_id", "ref_table": "regions", "ref_column": "id"},
                {"table": "accommodations", "column": "type_id", "ref_table": "accommodation_types", "ref_column": "type"},
                {"table": "cities", "column": "region_id", "ref_table": "regions", "ref_column": "id"}
            ]
            
            all_valid = True
            
            # Check if foreign key columns exist
            for fk in expected_fks:
                logger.info(f"Checking foreign key: {fk['table']}.{fk['column']} -> {fk['ref_table']}.{fk['ref_column']}")
                
                # Check if column exists
                cursor.execute(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = %s AND column_name = %s
                """, (fk["table"], fk["column"]))
                
                if not cursor.fetchone():
                    logger.error(f"❌ Foreign key column {fk['column']} does not exist in table {fk['table']}")
                    all_valid = False
                    continue
                
                # Check if foreign key constraint exists
                cursor.execute(f"""
                    SELECT tc.constraint_name, tc.table_name, kcu.column_name, 
                           ccu.table_name AS foreign_table_name,
                           ccu.column_name AS foreign_column_name,
                           rc.update_rule, rc.delete_rule
                    FROM information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                    JOIN information_schema.referential_constraints AS rc
                      ON rc.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                      AND tc.table_name = %s
                      AND kcu.column_name = %s
                      AND ccu.table_name = %s
                      AND ccu.column_name = %s
                """, (fk["table"], fk["column"], fk["ref_table"], fk["ref_column"]))
                
                result = cursor.fetchone()
                if not result:
                    logger.error(f"❌ No foreign key constraint found for {fk['table']}.{fk['column']} -> {fk['ref_table']}.{fk['ref_column']}")
                    all_valid = False
                    continue
                
                logger.info(f"✅ Foreign key constraint exists: {result['constraint_name']}")
                logger.info(f"   ON UPDATE: {result['update_rule']}, ON DELETE: {result['delete_rule']}")
                
                # Check if index exists for foreign key column
                cursor.execute(f"""
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE tablename = %s AND indexdef LIKE %s
                """, (fk["table"], f"%{fk['column']}%"))
                
                if not cursor.fetchone():
                    logger.warning(f"⚠️ No index found for foreign key column {fk['table']}.{fk['column']}")
                else:
                    logger.info(f"✅ Index exists for foreign key column {fk['table']}.{fk['column']}")
            
            return all_valid
            
    except Exception as e:
        logger.error(f"Error verifying foreign keys: {e}")
        return False
    finally:
        conn.close()

def test_foreign_key_constraints():
    """Test foreign key constraints by attempting operations that should be restricted"""
    conn = connect_to_database()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            # Test 1: Try to insert a record with invalid foreign key
            logger.info("Testing foreign key constraint enforcement...")
            
            try:
                cursor.execute("""
                    INSERT INTO attractions (id, name, city_id, region_id, type_id)
                    VALUES ('test_attraction', '{"en": "Test Attraction"}', 'nonexistent_city', 'nonexistent_region', 'nonexistent_type')
                """)
                logger.error("❌ Foreign key constraint test failed: Inserted record with invalid foreign keys")
                return False
            except psycopg2.Error as e:
                logger.info(f"✅ Foreign key constraint properly prevented invalid insert: {e}")
            
            # Test 2: Try to delete a record that is referenced by other records
            try:
                # First, check if there are attractions for a city
                cursor.execute("""
                    SELECT c.id, COUNT(a.id) as attraction_count
                    FROM cities c
                    JOIN attractions a ON c.id = a.city_id
                    GROUP BY c.id
                    LIMIT 1
                """)
                
                result = cursor.fetchone()
                if result:
                    city_id = result[0]
                    attraction_count = result[1]
                    
                    logger.info(f"Found city {city_id} with {attraction_count} attractions")
                    
                    # Try to delete the city
                    try:
                        cursor.execute("DELETE FROM cities WHERE id = %s", (city_id,))
                        
                        # If we get here, either the constraint is SET NULL or there's no constraint
                        logger.info("City was deleted - checking if attractions were updated...")
                        
                        # Check if attractions were updated (SET NULL) or deleted (CASCADE)
                        cursor.execute("SELECT COUNT(*) FROM attractions WHERE city_id IS NULL AND city = %s", (city_id,))
                        null_count = cursor.fetchone()[0]
                        
                        if null_count > 0:
                            logger.info(f"✅ ON DELETE SET NULL constraint worked: {null_count} attractions have NULL city_id")
                        else:
                            cursor.execute("SELECT COUNT(*) FROM attractions WHERE city = %s", (city_id,))
                            remaining = cursor.fetchone()[0]
                            
                            if remaining == 0:
                                logger.info("✅ ON DELETE CASCADE constraint worked: all related attractions were deleted")
                            else:
                                logger.warning(f"⚠️ Constraint behavior unclear: {remaining} attractions still reference deleted city")
                        
                    except psycopg2.Error as e:
                        logger.info(f"✅ ON DELETE RESTRICT constraint prevented city deletion: {e}")
                else:
                    logger.info("No city with attractions found for constraint test")
            
            except Exception as e:
                logger.error(f"Error during constraint test: {e}")
            
            # Roll back any changes
            conn.rollback()
            
            return True
            
    except Exception as e:
        logger.error(f"Error testing foreign key constraints: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main test function"""
    logger.info("Starting database structure verification...")
    
    # Verify JSONB columns
    jsonb_valid = verify_jsonb_columns()
    
    # Verify foreign keys
    fk_valid = verify_foreign_keys()
    
    # Test foreign key constraints
    constraints_valid = test_foreign_key_constraints()
    
    # Print summary
    logger.info("\nVerification Summary:")
    logger.info(f"JSONB Columns: {'✅ PASS' if jsonb_valid else '❌ FAIL'}")
    logger.info(f"Foreign Keys: {'✅ PASS' if fk_valid else '❌ FAIL'}")
    logger.info(f"Constraint Tests: {'✅ PASS' if constraints_valid else '❌ FAIL'}")
    
    # Return success if all tests passed
    return jsonb_valid and fk_valid and constraints_valid

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
