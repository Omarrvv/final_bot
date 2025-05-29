#!/usr/bin/env python
"""
Fix reference integrity issues in the Egypt Tourism Chatbot database.
This script fixes references to types that don't exist in the corresponding type tables.
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/reference_integrity.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_NAME = os.environ.get("DB_NAME", "egypt_chatbot_migration_test")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")

def get_connection():
    """Get a connection to the database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def check_reference_integrity():
    """Check for reference integrity issues."""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Check for attractions with invalid types
            cursor.execute("""
                SELECT a.id, a.type
                FROM attractions a
                LEFT JOIN attraction_types t ON a.type = t.type
                WHERE t.type IS NULL;
            """)
            invalid_attraction_types = cursor.fetchall()
            
            # Check for accommodations with invalid types
            cursor.execute("""
                SELECT a.id, a.type
                FROM accommodations a
                LEFT JOIN accommodation_types t ON a.type = t.type
                WHERE t.type IS NULL;
            """)
            invalid_accommodation_types = cursor.fetchall()
            
            return {
                "invalid_attraction_types": invalid_attraction_types,
                "invalid_accommodation_types": invalid_accommodation_types
            }
    except Exception as e:
        logger.error(f"Error checking reference integrity: {e}")
        return None
    finally:
        conn.close()

def fix_reference_integrity():
    """Fix reference integrity issues."""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            # Fix the attraction type for Bibliotheca Alexandrina
            cursor.execute("""
                UPDATE attractions
                SET type = 'cultural_center'
                WHERE id = 'bibliotheca_alexandrina' AND type = 'cultural';
            """)
            attraction_rows = cursor.rowcount
            
            # Fix the accommodation types
            cursor.execute("""
                UPDATE accommodations
                SET type = 'luxury_hotel'
                WHERE type = 'luxury';
            """)
            accommodation_rows = cursor.rowcount
            
            # Commit the changes
            conn.commit()
            
            logger.info(f"Fixed {attraction_rows} attraction types and {accommodation_rows} accommodation types")
            return True
    except Exception as e:
        logger.error(f"Error fixing reference integrity: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def verify_reference_integrity():
    """Verify that reference integrity issues have been fixed."""
    issues = check_reference_integrity()
    if not issues:
        return False
    
    if len(issues["invalid_attraction_types"]) == 0 and len(issues["invalid_accommodation_types"]) == 0:
        logger.info("All reference integrity issues have been fixed")
        return True
    else:
        logger.error(f"Reference integrity issues remain: {issues}")
        return False

def main():
    """Main function to fix reference integrity issues."""
    logger.info("Starting reference integrity fix")
    
    # Check for reference integrity issues
    issues = check_reference_integrity()
    if not issues:
        logger.error("Failed to check reference integrity")
        return 1
    
    # Log the issues found
    logger.info(f"Found {len(issues['invalid_attraction_types'])} invalid attraction types")
    for issue in issues["invalid_attraction_types"]:
        logger.info(f"  - Attraction {issue['id']} has invalid type '{issue['type']}'")
    
    logger.info(f"Found {len(issues['invalid_accommodation_types'])} invalid accommodation types")
    for issue in issues["invalid_accommodation_types"]:
        logger.info(f"  - Accommodation {issue['id']} has invalid type '{issue['type']}'")
    
    # Fix the issues
    if fix_reference_integrity():
        logger.info("Reference integrity issues fixed")
    else:
        logger.error("Failed to fix reference integrity issues")
        return 1
    
    # Verify the fixes
    if verify_reference_integrity():
        logger.info("Reference integrity verification passed")
        return 0
    else:
        logger.error("Reference integrity verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
