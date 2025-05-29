#!/usr/bin/env python3
"""
Run the Add JSONB Helper Functions migration script and test the functions.

This script:
1. Runs the migration script to add JSONB helper functions
2. Tests each function to verify it works correctly
3. Measures performance of JSONB queries with and without helper functions
4. Reports the results
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import json
from tabulate import tabulate

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
    """Run the Add JSONB Helper Functions migration script"""
    postgres_uri = get_postgres_uri()
    migration_file = "migrations/20240617_add_jsonb_helper_functions.sql"

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
        return conn

    except Exception as e:
        logger.error(f"Error running migration: {str(e)}")
        return None

def test_get_text_by_language(conn):
    """Test the get_text_by_language function"""
    logger.info("Testing get_text_by_language function...")

    try:
        with conn.cursor() as cursor:
            # Test with English
            cursor.execute("SELECT get_text_by_language('{\"en\": \"Hello\", \"ar\": \"مرحبا\"}'::jsonb, 'en')")
            result = cursor.fetchone()[0]
            assert result == "Hello", f"Expected 'Hello', got '{result}'"

            # Test with Arabic
            cursor.execute("SELECT get_text_by_language('{\"en\": \"Hello\", \"ar\": \"مرحبا\"}'::jsonb, 'ar')")
            result = cursor.fetchone()[0]
            assert result == "مرحبا", f"Expected 'مرحبا', got '{result}'"

            # Test with fallback to English
            cursor.execute("SELECT get_text_by_language('{\"en\": \"Hello\", \"ar\": \"مرحبا\"}'::jsonb, 'fr')")
            result = cursor.fetchone()[0]
            assert result == "Hello", f"Expected 'Hello', got '{result}'"

            logger.info("✅ get_text_by_language function works correctly")
            return True
    except Exception as e:
        logger.error(f"❌ Error testing get_text_by_language function: {str(e)}")
        return False

def test_search_jsonb_text(conn):
    """Test the search_jsonb_text function"""
    logger.info("Testing search_jsonb_text function...")

    try:
        with conn.cursor() as cursor:
            # Test with exact match
            cursor.execute("SELECT search_jsonb_text('{\"en\": \"Pyramids of Giza\", \"ar\": \"أهرامات الجيزة\"}'::jsonb, 'Pyramids', 'en')")
            result = cursor.fetchone()[0]
            assert result is True, f"Expected True, got {result}"

            # Test with case insensitive match
            cursor.execute("SELECT search_jsonb_text('{\"en\": \"Pyramids of Giza\", \"ar\": \"أهرامات الجيزة\"}'::jsonb, 'pyramids', 'en')")
            result = cursor.fetchone()[0]
            assert result is True, f"Expected True, got {result}"

            # Test with no match
            cursor.execute("SELECT search_jsonb_text('{\"en\": \"Pyramids of Giza\", \"ar\": \"أهرامات الجيزة\"}'::jsonb, 'Sphinx', 'en')")
            result = cursor.fetchone()[0]
            assert result is False, f"Expected False, got {result}"

            logger.info("✅ search_jsonb_text function works correctly")
            return True
    except Exception as e:
        logger.error(f"❌ Error testing search_jsonb_text function: {str(e)}")
        return False

def test_get_attraction_by_name(conn):
    """Test the get_attraction_by_name function"""
    logger.info("Testing get_attraction_by_name function...")

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Test with English name
            cursor.execute("SELECT * FROM get_attraction_by_name('Pyramid', 'en')")
            results = cursor.fetchall()
            assert len(results) > 0, "Expected at least one result"

            # Print results
            logger.info(f"Found {len(results)} attractions matching 'Pyramid':")
            for i, result in enumerate(results[:3]):  # Show first 3 results
                # Handle the name which could be a string or already parsed JSON
                if isinstance(result['name'], str):
                    name_data = json.loads(result['name'])
                else:
                    name_data = result['name']
                name_en = name_data.get('en', 'Unknown')
                logger.info(f"  {i+1}. {name_en}")

            logger.info("✅ get_attraction_by_name function works correctly")
            return True
    except Exception as e:
        logger.error(f"❌ Error testing get_attraction_by_name function: {str(e)}")
        return False

def benchmark_jsonb_queries(conn):
    """Benchmark JSONB queries with and without helper functions"""
    logger.info("Benchmarking JSONB queries...")

    try:
        results = []

        # Test 1: Standard JSONB query
        query1 = """
            SELECT id, name->>'en' as name_en
            FROM attractions
            WHERE name->>'en' ILIKE '%pyramid%'
            LIMIT 5
        """

        # Test 2: Using helper function
        query2 = """
            SELECT id, get_text_by_language(name, 'en') as name_en
            FROM attractions
            WHERE search_jsonb_text(name, 'pyramid', 'en') = TRUE
            LIMIT 5
        """

        # Test 3: Complex standard JSONB query
        query3 = """
            SELECT a.id, a.name->>'en' as name_en, c.name->>'en' as city_en
            FROM attractions a
            JOIN cities c ON a.city_id = c.id
            WHERE a.name->>'en' ILIKE '%temple%'
            AND c.name->>'en' ILIKE '%luxor%'
            LIMIT 5
        """

        # Test 4: Using helper function for complex query
        query4 = """
            SELECT * FROM get_attraction_by_name('temple', 'en')
            WHERE city ILIKE '%luxor%'
            LIMIT 5
        """

        # Run each query 10 times and average the results
        iterations = 10

        with conn.cursor() as cursor:
            # Test 1
            total_time = 0
            for i in range(iterations):
                start_time = time.time()
                cursor.execute(query1)
                end_time = time.time()
                total_time += (end_time - start_time)
            avg_time1 = total_time / iterations
            results.append(["Standard JSONB query", avg_time1, 1.0])

            # Test 2
            total_time = 0
            for i in range(iterations):
                start_time = time.time()
                cursor.execute(query2)
                end_time = time.time()
                total_time += (end_time - start_time)
            avg_time2 = total_time / iterations
            results.append(["Helper function query", avg_time2, avg_time1 / avg_time2])

            # Test 3
            total_time = 0
            for i in range(iterations):
                start_time = time.time()
                cursor.execute(query3)
                end_time = time.time()
                total_time += (end_time - start_time)
            avg_time3 = total_time / iterations
            results.append(["Complex standard JSONB query", avg_time3, 1.0])

            # Test 4
            total_time = 0
            for i in range(iterations):
                start_time = time.time()
                cursor.execute(query4)
                end_time = time.time()
                total_time += (end_time - start_time)
            avg_time4 = total_time / iterations
            results.append(["Complex helper function query", avg_time4, avg_time3 / avg_time4])

        # Print results
        print("\n=== JSONB Query Performance Benchmark ===\n")
        print(tabulate(
            results,
            headers=["Query Type", "Average Time (s)", "Speedup Factor"],
            tablefmt="grid",
            floatfmt=".6f"
        ))

        return True
    except Exception as e:
        logger.error(f"❌ Error benchmarking JSONB queries: {str(e)}")
        return False

def main():
    """Main function"""
    # Run migration
    conn = run_migration()
    if not conn:
        logger.error("Migration failed, exiting")
        sys.exit(1)

    try:
        # Test functions
        tests = [
            ("get_text_by_language", test_get_text_by_language),
            ("search_jsonb_text", test_search_jsonb_text),
            ("get_attraction_by_name", test_get_attraction_by_name)
        ]

        all_passed = True
        for name, test_func in tests:
            if not test_func(conn):
                all_passed = False

        # Benchmark queries
        benchmark_jsonb_queries(conn)

        if all_passed:
            logger.info("✅ All tests passed")
            return True
        else:
            logger.error("❌ Some tests failed")
            return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
