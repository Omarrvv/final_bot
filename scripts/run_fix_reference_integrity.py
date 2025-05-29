#!/usr/bin/env python3
"""
Script to fix reference integrity issues in the attractions table.
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

# Database connection string
DB_CONNECTION_STRING = "postgresql://postgres:postgres@localhost:5432/egypt_chatbot"

def execute_query(query, params=None, fetchall=True):
    """Execute a query and return the results."""
    try:
        with psycopg2.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetchall:
                    return cursor.fetchall()
                else:
                    return cursor.rowcount
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise

def check_mismatches():
    """Check for mismatches between text fields and foreign key columns."""
    query = """
    SELECT 
        COUNT(*) as city_mismatches
    FROM attractions
    WHERE city IS NOT NULL 
      AND city_id IS NOT NULL 
      AND city != city_id;
    """
    city_result = execute_query(query, fetchall=True)
    city_mismatches = city_result[0]['city_mismatches']
    
    query = """
    SELECT 
        COUNT(*) as region_mismatches
    FROM attractions
    WHERE region IS NOT NULL 
      AND region_id IS NOT NULL 
      AND region != region_id;
    """
    region_result = execute_query(query, fetchall=True)
    region_mismatches = region_result[0]['region_mismatches']
    
    return city_mismatches, region_mismatches

def fix_city_mismatches():
    """Fix mismatches between city and city_id."""
    query = """
    UPDATE attractions
    SET city = city_id
    WHERE city IS NOT NULL 
      AND city_id IS NOT NULL 
      AND city != city_id;
    """
    rows_updated = execute_query(query, fetchall=False)
    logger.info(f"Updated {rows_updated} rows with city mismatches")
    return rows_updated

def fix_region_mismatches():
    """Fix mismatches between region and region_id."""
    query = """
    UPDATE attractions
    SET region = region_id
    WHERE region IS NOT NULL 
      AND region_id IS NOT NULL 
      AND region != region_id;
    """
    rows_updated = execute_query(query, fetchall=False)
    logger.info(f"Updated {rows_updated} rows with region mismatches")
    return rows_updated

def main():
    """Main function to fix reference integrity issues."""
    try:
        # Check for mismatches before fixing
        city_mismatches, region_mismatches = check_mismatches()
        logger.info(f"Found {city_mismatches} city mismatches and {region_mismatches} region mismatches")
        
        # Fix city mismatches
        if city_mismatches > 0:
            city_rows_updated = fix_city_mismatches()
            logger.info(f"Fixed {city_rows_updated} city mismatches")
        
        # Fix region mismatches
        if region_mismatches > 0:
            region_rows_updated = fix_region_mismatches()
            logger.info(f"Fixed {region_rows_updated} region mismatches")
        
        # Verify the changes
        city_mismatches, region_mismatches = check_mismatches()
        if city_mismatches == 0 and region_mismatches == 0:
            logger.info("All mismatches fixed successfully!")
        else:
            logger.warning(f"There are still {city_mismatches} city mismatches and {region_mismatches} region mismatches")
        
    except Exception as e:
        logger.error(f"Error fixing reference integrity issues: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
