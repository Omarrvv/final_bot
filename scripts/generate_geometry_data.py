#!/usr/bin/env python3
"""
Script to generate PostGIS geometry data from latitude and longitude values.
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

# Tables to update
TABLES = ["attractions", "restaurants", "accommodations", "destinations"]

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

def check_missing_geometry(table):
    """Check for rows with missing geometry data."""
    query = f"""
    SELECT 
        COUNT(*) as missing_geom
    FROM {table}
    WHERE geom IS NULL AND latitude IS NOT NULL AND longitude IS NOT NULL;
    """
    result = execute_query(query, fetchall=True)
    return result[0]['missing_geom']

def generate_geometry(table):
    """Generate geometry data from latitude and longitude values."""
    query = f"""
    UPDATE {table}
    SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    WHERE geom IS NULL AND latitude IS NOT NULL AND longitude IS NOT NULL;
    """
    rows_updated = execute_query(query, fetchall=False)
    logger.info(f"Updated {rows_updated} rows in {table}")
    return rows_updated

def main():
    """Main function to generate geometry data."""
    try:
        # Check for missing geometry data before fixing
        for table in TABLES:
            missing_geom = check_missing_geometry(table)
            logger.info(f"Found {missing_geom} rows with missing geometry in {table}")
        
        # Generate geometry data
        total_updated = 0
        for table in TABLES:
            rows_updated = generate_geometry(table)
            total_updated += rows_updated
        
        logger.info(f"Total rows updated: {total_updated}")
        
        # Verify the changes
        remaining_missing = 0
        for table in TABLES:
            missing_geom = check_missing_geometry(table)
            if missing_geom > 0:
                logger.warning(f"There are still {missing_geom} rows with missing geometry in {table}")
                remaining_missing += missing_geom
        
        if remaining_missing == 0:
            logger.info("All geometry data generated successfully!")
        
    except Exception as e:
        logger.error(f"Error generating geometry data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
