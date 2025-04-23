#!/usr/bin/env python3
"""
Test script to verify Knowledge Base functionality with PostgreSQL.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add the root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.knowledge.database import DatabaseManager, DatabaseType
from src.knowledge.knowledge_base import KnowledgeBase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("test_postgres_kb")

def test_attraction_query():
    """Test querying attractions from the Knowledge Base."""
    logger.info("Testing attraction query with PostgreSQL")
    
    # Load environment variables
    load_dotenv()
    
    # Verify PostgreSQL config
    logger.info(f"USE_POSTGRES: {os.environ.get('USE_POSTGRES')}")
    logger.info(f"POSTGRES_URI: {os.environ.get('POSTGRES_URI')}")
    logger.info(f"USE_NEW_KB: {os.environ.get('USE_NEW_KB')}")
    
    # Create DatabaseManager
    db = DatabaseManager()
    logger.info(f"Database type: {db.db_type}")
    
    # Create KnowledgeBase
    kb = KnowledgeBase(db)
    logger.info(f"Knowledge Base connected: {kb._db_available}")
    
    # Test getting attraction by ID
    attraction_id = "pyramids_of_giza"
    logger.info(f"Getting attraction by ID: {attraction_id}")
    attraction = kb.get_attraction_by_id(attraction_id)
    if attraction:
        logger.info(f"Found attraction: {attraction.get('name_en')}")
        logger.info(f"Description: {attraction.get('description_en', '')[:100]}...")
    else:
        logger.error(f"Attraction not found with ID: {attraction_id}")
    
    # Test search attractions with fixed query
    name_field = "name_en"
    search_text = "pyramid"
    logger.info(f"Searching attractions with query: {search_text}")
    
    # Use DatabaseManager directly
    query = {name_field: {"$like": f"%{search_text}%"}}
    results = db.search_attractions(query=query, limit=5)
    
    logger.info(f"Found {len(results)} attractions matching '{search_text}'")
    for result in results:
        logger.info(f"- {result.get('name_en')}")
    
    # Test find_nearby with PostGIS
    logger.info("Testing geospatial query with PostGIS")
    # Cairo coordinates
    lat, lng = 30.0131, 31.2089
    radius_km = 10
    
    nearby = db.find_nearby(
        table="attractions",
        latitude=lat,
        longitude=lng,
        radius_km=radius_km
    )
    
    logger.info(f"Found {len(nearby)} attractions within {radius_km}km of Cairo")
    for place in nearby:
        logger.info(f"- {place.get('name_en')}")
    
    logger.info("Tests completed")

if __name__ == "__main__":
    test_attraction_query() 