#!/usr/bin/env python3
"""
Run automated tests in the test environment.

This script:
1. Switches to the test environment
2. Runs a series of tests to verify database functionality
3. Tests JSONB queries, foreign key constraints, and other features
4. Reports test results
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import subprocess
import json
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test database connection parameters
TEST_DB_PARAMS = {
    'dbname': 'egypt_chatbot_migration_test',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

def switch_to_test_environment():
    """Switch to the test environment"""
    logger.info("Switching to test environment...")
    result = subprocess.run(
        ["./enhanced_switch_database.sh", "test"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    if result.returncode == 0:
        logger.info("Successfully switched to test environment")
        return True
    else:
        logger.error(f"Failed to switch to test environment: {result.stderr}")
        return False

def connect_to_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**TEST_DB_PARAMS)
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def test_database_connection():
    """Test database connection"""
    logger.info("Testing database connection...")
    conn = connect_to_db()
    if conn:
        logger.info("✅ Database connection successful")
        conn.close()
        return True
    else:
        logger.error("❌ Database connection failed")
        return False

def test_table_existence():
    """Test if required tables exist"""
    logger.info("Testing table existence...")
    conn = connect_to_db()
    if not conn:
        return False
    
    try:
        required_tables = [
            'cities', 'attractions', 'accommodations', 'regions',
            'users', 'attraction_types', 'accommodation_types'
        ]
        
        with conn.cursor() as cursor:
            for table in required_tables:
                cursor.execute(f"SELECT to_regclass('public.{table}')")
                result = cursor.fetchone()[0]
                
                if result:
                    logger.info(f"✅ Table exists: {table}")
                else:
                    logger.error(f"❌ Table does not exist: {table}")
                    return False
        
        return True
    except Exception as e:
        logger.error(f"Error testing table existence: {str(e)}")
        return False
    finally:
        conn.close()

def test_jsonb_queries():
    """Test JSONB queries"""
    logger.info("Testing JSONB queries...")
    conn = connect_to_db()
    if not conn:
        return False
    
    try:
        tests = [
            {
                'name': 'Simple JSONB equality',
                'query': "SELECT id FROM attractions WHERE name->>'en' = 'Pyramids of Giza' LIMIT 1",
                'expected_result': True  # Expect at least one result
            },
            {
                'name': 'JSONB path operator',
                'query': "SELECT id FROM attractions WHERE name @> '{\"en\": \"Pyramids of Giza\"}' LIMIT 1",
                'expected_result': True  # Expect at least one result
            },
            {
                'name': 'JSONB containment',
                'query': "SELECT id FROM attractions WHERE data ? 'year_built' LIMIT 1",
                'expected_result': True  # Expect at least one result
            },
            {
                'name': 'JSONB array elements',
                'query': "SELECT id FROM accommodations WHERE data->'amenities' ? 'WiFi' LIMIT 1",
                'expected_result': True  # Expect at least one result
            }
        ]
        
        all_passed = True
        
        with conn.cursor() as cursor:
            for test in tests:
                start_time = time.time()
                cursor.execute(test['query'])
                end_time = time.time()
                
                results = cursor.fetchall()
                has_results = len(results) > 0
                
                if has_results == test['expected_result']:
                    logger.info(f"✅ Test passed: {test['name']} ({end_time - start_time:.4f}s)")
                else:
                    logger.error(f"❌ Test failed: {test['name']}")
                    all_passed = False
        
        # Test JSONB index usage
        with conn.cursor() as cursor:
            cursor.execute("""
                EXPLAIN ANALYZE
                SELECT id FROM attractions WHERE name @> '{"en": "Pyramids of Giza"}'
            """)
            plan = cursor.fetchall()
            plan_text = "\n".join([row[0] for row in plan])
            
            if "idx_attractions_name_jsonb" in plan_text:
                logger.info("✅ JSONB index is being used")
            else:
                logger.warning("⚠️ JSONB index is not being used")
                logger.debug(f"Query plan:\n{plan_text}")
        
        return all_passed
    except Exception as e:
        logger.error(f"Error testing JSONB queries: {str(e)}")
        return False
    finally:
        conn.close()

def test_foreign_key_constraints():
    """Test foreign key constraints"""
    logger.info("Testing foreign key constraints...")
    conn = connect_to_db()
    if not conn:
        return False
    
    try:
        tests = [
            {
                'name': 'Attraction type RESTRICT constraint',
                'query': "DELETE FROM attraction_types WHERE type = 'historical'",
                'expected_error': True  # Expect a foreign key violation
            },
            {
                'name': 'Accommodation type RESTRICT constraint',
                'query': "DELETE FROM accommodation_types WHERE type = 'luxury_hotel'",
                'expected_error': True  # Expect a foreign key violation
            },
            {
                'name': 'Region CASCADE update',
                'query': """
                    BEGIN;
                    UPDATE regions SET id = 'test_region_update' WHERE id = 'lower_egypt';
                    SELECT COUNT(*) FROM attractions WHERE region_id = 'test_region_update';
                    ROLLBACK;
                """,
                'expected_error': False  # Should not error, CASCADE should work
            }
        ]
        
        all_passed = True
        
        for test in tests:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(test['query'])
                    
                    if test['expected_error']:
                        logger.error(f"❌ Test failed: {test['name']} (Expected error but none occurred)")
                        all_passed = False
                    else:
                        logger.info(f"✅ Test passed: {test['name']}")
                    
                    # Make sure we rollback any changes
                    conn.rollback()
            except psycopg2.errors.ForeignKeyViolation:
                if test['expected_error']:
                    logger.info(f"✅ Test passed: {test['name']} (Expected foreign key violation occurred)")
                else:
                    logger.error(f"❌ Test failed: {test['name']} (Unexpected foreign key violation)")
                    all_passed = False
                
                # Make sure we rollback any changes
                conn.rollback()
            except Exception as e:
                logger.error(f"❌ Test failed: {test['name']} (Unexpected error: {str(e)})")
                all_passed = False
                
                # Make sure we rollback any changes
                conn.rollback()
        
        return all_passed
    except Exception as e:
        logger.error(f"Error testing foreign key constraints: {str(e)}")
        return False
    finally:
        conn.close()

def run_tests():
    """Run all tests"""
    logger.info("Starting test environment tests...")
    
    # Switch to test environment
    if not switch_to_test_environment():
        return False
    
    # Run tests
    tests = [
        ('Database Connection', test_database_connection),
        ('Table Existence', test_table_existence),
        ('JSONB Queries', test_jsonb_queries),
        ('Foreign Key Constraints', test_foreign_key_constraints)
    ]
    
    results = {}
    all_passed = True
    
    for name, test_func in tests:
        logger.info(f"\n=== Running Test: {name} ===\n")
        start_time = time.time()
        passed = test_func()
        end_time = time.time()
        
        results[name] = {
            'passed': passed,
            'duration': end_time - start_time
        }
        
        if not passed:
            all_passed = False
    
    # Print summary
    print("\n=== Test Results Summary ===\n")
    print(f"Test Environment: {TEST_DB_PARAMS['dbname']}")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for name, result in results.items():
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        print(f"{name}: {status} ({result['duration']:.2f}s)")
    
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
