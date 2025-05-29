#!/usr/bin/env python3
"""
Script to verify tourism data quality:
1. Check for duplicate FAQs
2. Check for missing embeddings
3. Check for test/generated destination names
4. Run test queries to verify functionality
"""

import os
import sys
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"tourism_data_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("tourism_data_verification")

# Load environment variables
load_dotenv()

# Database connection parameters
DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB", "egypt_chatbot"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432")
}

def connect_to_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = True
        logger.info("Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        sys.exit(1)

def check_duplicate_faqs(conn):
    """Check for duplicate FAQs"""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT question->>'en' as question_en, COUNT(*) as count
                FROM tourism_faqs
                GROUP BY question->>'en'
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()

            if duplicates:
                logger.error(f"Found {len(duplicates)} duplicate FAQs:")
                for dup in duplicates:
                    logger.error(f"  - '{dup['question_en']}' appears {dup['count']} times")
                return False
            else:
                logger.info("✅ No duplicate FAQs found")
                return True
    except Exception as e:
        logger.error(f"Error checking for duplicate FAQs: {e}")
        return False

def check_missing_embeddings(conn):
    """Check for missing embeddings"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM tourism_faqs
                WHERE embedding IS NULL
            """)
            missing_embeddings = cursor.fetchone()[0]

            if missing_embeddings > 0:
                logger.error(f"Found {missing_embeddings} FAQs with missing embeddings")
                return False
            else:
                logger.info("✅ All FAQs have embeddings")
                return True
    except Exception as e:
        logger.error(f"Error checking for missing embeddings: {e}")
        return False

def check_destination_names(conn):
    """Check for test/generated destination names"""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT id, name->>'en' as name_en
                FROM destinations
                WHERE (name->>'en' LIKE 'Desert%' OR name->>'en' LIKE 'Coastal%' OR
                      name->>'en' LIKE 'Southern%' OR name->>'en' LIKE 'Nile%' OR
                      name->>'en' LIKE 'Ancient%' OR name->>'en' LIKE 'Historic%')
                      -- Exclude legitimate "Valley of X" names
                      AND name->>'en' NOT IN ('Valley of the Kings', 'Valley of the Queens', 'Valley of the Nobles')
            """)
            test_names = cursor.fetchall()

            if test_names:
                logger.error(f"Found {len(test_names)} destinations with test/generated names:")
                for dest in test_names:
                    logger.error(f"  - ID: {dest['id']}, Name: '{dest['name_en']}'")
                return False
            else:
                logger.info("✅ All destination names look realistic")
                return True
    except Exception as e:
        logger.error(f"Error checking destination names: {e}")
        return False

def run_test_queries(conn):
    """Run test queries to verify functionality"""
    try:
        test_queries = [
            {
                "name": "Find cities in Upper Egypt",
                "query": """
                    SELECT id, name->>'en' as name_en
                    FROM destinations
                    WHERE parent_id = 'upper_egypt' AND type = 'city'
                    LIMIT 5
                """
            },
            {
                "name": "Find transportation routes between Cairo and Luxor",
                "query": """
                    SELECT id, name->>'en' as name_en, transportation_type, duration_minutes
                    FROM transportation_routes
                    WHERE origin_id = 'cairo' AND destination_id = 'luxor'
                    LIMIT 5
                """
            },
            {
                "name": "Find FAQs related to visa and immigration",
                "query": """
                    SELECT id, question->>'en' as question_en
                    FROM tourism_faqs
                    WHERE category_id = 'visa_immigration'
                    LIMIT 5
                """
            },
            {
                "name": "Find practical info about emergency contacts",
                "query": """
                    SELECT id, title->>'en' as title_en
                    FROM practical_info
                    WHERE category_id = 'emergency_contacts'
                    LIMIT 5
                """
            }
        ]

        all_passed = True

        for test in test_queries:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(test["query"])
                results = cursor.fetchall()

                if results:
                    logger.info(f"✅ Test query '{test['name']}' returned {len(results)} results")
                    # Print the first few results in a table format
                    if len(results) > 0:
                        table_data = []
                        headers = results[0].keys()
                        for row in results:
                            table_data.append([row[key] for key in headers])
                        logger.info(f"\n{tabulate(table_data, headers=headers)}")
                else:
                    logger.error(f"❌ Test query '{test['name']}' returned no results")
                    all_passed = False

        return all_passed
    except Exception as e:
        logger.error(f"Error running test queries: {e}")
        return False

def main():
    """Main function"""
    try:
        # Connect to database
        conn = connect_to_db()

        # Run checks
        checks = [
            ("No duplicate FAQs", check_duplicate_faqs(conn)),
            ("All FAQs have embeddings", check_missing_embeddings(conn)),
            ("All destination names are realistic", check_destination_names(conn)),
            ("All test queries return results", run_test_queries(conn))
        ]

        # Print summary
        logger.info("\n=== VERIFICATION SUMMARY ===")
        all_passed = True
        for check_name, result in checks:
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status}: {check_name}")
            all_passed = all_passed and result

        if all_passed:
            logger.info("\n🎉 All checks passed! Tourism data is ready for use.")
        else:
            logger.error("\n⚠️ Some checks failed. Please fix the issues before proceeding.")

        # Close connection
        conn.close()

        return 0 if all_passed else 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
