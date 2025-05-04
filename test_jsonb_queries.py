#!/usr/bin/env python3
"""
Test script to verify JSONB queries in the database
"""

import json
import logging
from src.utils.postgres_database import PostgresqlDatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_jsonb_query():
    """Test querying JSONB fields"""
    db = PostgresqlDatabaseManager()
    db.connect()

    # Query using JSONB operators
    query = """
    SELECT id, name, description
    FROM attractions
    WHERE name->>'en' LIKE '%Tower%'
    LIMIT 5
    """

    results = db.execute_query(query)

    logger.info(f"Found {len(results)} attractions with 'Tower' in name")
    for attraction in results:
        logger.info(f"ID: {attraction.get('id')}")
        logger.info(f"Name: {attraction.get('name')}")
        logger.info(f"Description: {attraction.get('description')}")
        logger.info("---")

    return len(results) > 0

def test_jsonb_update():
    """Test updating JSONB fields"""
    db = PostgresqlDatabaseManager()
    db.connect()

    # Get an attraction to update
    query = "SELECT id, name FROM attractions LIMIT 1"
    results = db.execute_query(query)

    if not results:
        logger.warning("No attractions found in database")
        return False

    attraction_id = results[0].get('id')
    current_name = results[0].get('name')
    logger.info(f"Updating attraction: {attraction_id}")
    logger.info(f"Current name: {current_name}")

    # Make a copy of the current name and modify it
    new_name = current_name.copy() if isinstance(current_name, dict) else {'en': 'Test Name', 'ar': 'اسم تجريبي'}
    new_name['test_field'] = 'This is a test field'

    # Update the name
    update_query = """
    UPDATE attractions
    SET name = %s::jsonb
    WHERE id = %s
    RETURNING id, name
    """

    update_results = db.execute_query(update_query, (json.dumps(new_name), attraction_id))

    if not update_results:
        logger.warning("Update failed")
        return False

    updated_name = update_results[0].get('name')
    logger.info(f"Updated name: {updated_name}")

    # Verify the update
    has_test_field = isinstance(updated_name, dict) and 'test_field' in updated_name
    logger.info(f"Has test field: {has_test_field}")

    # Restore the original name
    try:
        restore_query = """
        UPDATE attractions
        SET name = %s::jsonb
        WHERE id = %s
        """

        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(restore_query, (json.dumps(current_name), attraction_id))
                conn.commit()

        logger.info("Restored original name")
    except Exception as e:
        logger.error(f"Error restoring original name: {e}")

    return has_test_field

def main():
    """Run all tests"""
    logger.info("Testing JSONB queries...")
    query_works = test_jsonb_query()

    logger.info("\nTesting JSONB updates...")
    update_works = test_jsonb_update()

    # Print summary
    logger.info("\nTest Summary:")
    logger.info(f"JSONB queries work: {query_works}")
    logger.info(f"JSONB updates work: {update_works}")

    return query_works and update_works

if __name__ == "__main__":
    success = main()
    print(f"\nOverall test result: {'PASSED' if success else 'FAILED'}")
