#!/usr/bin/env python3
"""
Script to fix missing coordinates in the destinations table.
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

# Approximate coordinates for regions
REGION_COORDINATES = {
    "lower_egypt": {
        "latitude": 30.0444,   # Cairo area
        "longitude": 31.2357
    },
    "upper_egypt": {
        "latitude": 25.6872,   # Luxor area
        "longitude": 32.6396
    },
    "mediterranean_coast": {
        "latitude": 31.2001,   # Alexandria area
        "longitude": 29.9187
    }
}

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

def check_missing_coordinates():
    """Check for destinations with missing coordinates."""
    query = """
    SELECT 
        id, 
        name->>'en' as name_en
    FROM destinations
    WHERE latitude IS NULL OR longitude IS NULL;
    """
    results = execute_query(query, fetchall=True)
    return results

def fix_missing_coordinates():
    """Fix missing coordinates in the destinations table."""
    for region_id, coords in REGION_COORDINATES.items():
        query = """
        UPDATE destinations
        SET latitude = %s, longitude = %s
        WHERE id = %s AND (latitude IS NULL OR longitude IS NULL);
        """
        params = (coords["latitude"], coords["longitude"], region_id)
        rows_updated = execute_query(query, params=params, fetchall=False)
        logger.info(f"Updated {rows_updated} rows for region {region_id}")

def main():
    """Main function to fix missing coordinates."""
    try:
        # Check for missing coordinates before fixing
        missing_coords = check_missing_coordinates()
        logger.info(f"Found {len(missing_coords)} destinations with missing coordinates")
        for dest in missing_coords:
            logger.info(f"  - {dest['id']} ({dest['name_en']})")
        
        # Fix missing coordinates
        if missing_coords:
            fix_missing_coordinates()
        
        # Verify the changes
        missing_coords = check_missing_coordinates()
        if not missing_coords:
            logger.info("All missing coordinates fixed successfully!")
        else:
            logger.warning(f"There are still {len(missing_coords)} destinations with missing coordinates")
            for dest in missing_coords:
                logger.warning(f"  - {dest['id']} ({dest['name_en']})")
        
    except Exception as e:
        logger.error(f"Error fixing missing coordinates: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
