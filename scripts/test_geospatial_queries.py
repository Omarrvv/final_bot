#!/usr/bin/env python3
"""
Script to test PostGIS geospatial queries for finding nearby attractions, restaurants, and hotels
"""

import os
import sys
import logging
import json
from dotenv import load_dotenv

# Add the project root to the path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.knowledge.database import DatabaseManager, DatabaseType

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def print_location_result(results, location_name, table):
    """Print the results of a location query in a readable format"""
    if not results:
        logger.info(f"No {table} found near {location_name}")
        return
    
    logger.info(f"Found {len(results)} {table} near {location_name}:")
    for i, result in enumerate(results, 1):
        name = result.get('name', 'Unknown')
        distance = result.get('distance_km', 'Unknown')
        logger.info(f"  {i}. {name} - {distance} km away")
        
        # Print additional details if available
        if 'address' in result:
            logger.info(f"     Address: {result['address']}")
        if 'description' in result and result['description']:
            desc = result['description']
            if isinstance(desc, dict) and 'en' in desc:
                desc = desc['en']
            logger.info(f"     Description: {desc[:100]}...")

def test_find_nearby(db_manager, latitude, longitude, radius_km, location_name, table):
    """Test finding items near a specific location"""
    logger.info(f"\n--- Testing find_nearby for {table} near {location_name} (radius: {radius_km}km) ---")
    
    try:
        results = db_manager.find_nearby(
            table=table,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            limit=5
        )
        print_location_result(results, location_name, table)
        return len(results)
    except Exception as e:
        logger.error(f"Error finding nearby {table}: {e}")
        return 0

def main():
    """Main function to run the geospatial tests"""
    # Load environment variables
    load_dotenv()
    
    # Initialize database manager
    pg_uri = os.getenv("POSTGRES_URI", "postgresql://omarmohamed@localhost:5432/postgres")
    logger.info(f"Connecting to database: {pg_uri}")
    
    db_manager = DatabaseManager(pg_uri)
    
    # Check if we're connected to PostgreSQL and if PostGIS is enabled
    if db_manager.db_type != DatabaseType.POSTGRES:
        logger.error("Not connected to PostgreSQL database. This script requires PostgreSQL with PostGIS.")
        return
    
    if not db_manager._check_postgis_enabled():
        logger.error("PostGIS is not enabled in the PostgreSQL database.")
        return
    
    logger.info("PostGIS is enabled. Starting geospatial tests...")
    
    # Test locations - famous Egyptian landmarks and their coordinates
    test_locations = [
        {"name": "Pyramids of Giza", "lat": 29.9773, "lng": 31.1325, "radius": 2},
        {"name": "Khan el-Khalili", "lat": 30.0478, "lng": 31.2623, "radius": 1},
        {"name": "Luxor Temple", "lat": 25.6995, "lng": 32.6368, "radius": 3},
        {"name": "Alexandria Library", "lat": 31.2089, "lng": 29.9092, "radius": 2}
    ]
    
    # Tables to test
    tables = ["attractions", "restaurants", "accommodations"]
    
    # Track results
    total_found = {table: 0 for table in tables}
    
    # Run tests for each location and table
    for location in test_locations:
        for table in tables:
            count = test_find_nearby(
                db_manager=db_manager,
                latitude=location["lat"],
                longitude=location["lng"],
                radius_km=location["radius"],
                location_name=location["name"],
                table=table
            )
            total_found[table] += count
    
    # Summary
    logger.info("\n--- Geospatial Query Test Summary ---")
    for table, count in total_found.items():
        logger.info(f"Total {table} found: {count}")
    
    # Close database connection
    db_manager.close()
    logger.info("Geospatial test completed.")

if __name__ == "__main__":
    main() 