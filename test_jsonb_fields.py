#!/usr/bin/env python3
"""
Test script to verify JSONB fields in the database
"""

import json
import logging
from src.utils.postgres_database import PostgresqlDatabaseManager
from src.knowledge.knowledge_base import KnowledgeBase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection"""
    db = PostgresqlDatabaseManager()
    connected = db.test_connection()
    logger.info(f"Database connection: {connected}")
    return connected

def test_attraction_jsonb_fields():
    """Test JSONB fields in attractions table"""
    db = PostgresqlDatabaseManager()
    db.connect()
    
    # Get an attraction
    query = "SELECT id, name_en, name_ar, name, description_en, description_ar, description FROM attractions LIMIT 1"
    results = db.execute_query(query)
    
    if not results:
        logger.warning("No attractions found in database")
        return False
    
    attraction = results[0]
    logger.info(f"Attraction ID: {attraction.get('id')}")
    logger.info(f"name_en: {attraction.get('name_en')}")
    logger.info(f"name_ar: {attraction.get('name_ar')}")
    logger.info(f"name (JSONB): {attraction.get('name')}")
    logger.info(f"description_en: {attraction.get('description_en')}")
    logger.info(f"description_ar: {attraction.get('description_ar')}")
    logger.info(f"description (JSONB): {attraction.get('description')}")
    
    # Check if JSONB fields exist
    has_name_jsonb = attraction.get('name') is not None
    has_description_jsonb = attraction.get('description') is not None
    
    logger.info(f"Has name JSONB: {has_name_jsonb}")
    logger.info(f"Has description JSONB: {has_description_jsonb}")
    
    return has_name_jsonb and has_description_jsonb

def test_knowledge_base_formatters():
    """Test KnowledgeBase formatters with JSONB fields"""
    db = PostgresqlDatabaseManager()
    kb = KnowledgeBase(db)
    
    # Search for attractions
    attractions = kb.search_attractions(limit=1)
    if not attractions:
        logger.warning("No attractions found")
        return False
    
    attraction = attractions[0]
    logger.info(f"Formatted attraction: {json.dumps(attraction, indent=2, default=str)}")
    
    # Check if the name and description are properly formatted
    has_name = isinstance(attraction.get('name'), dict) and 'en' in attraction.get('name', {})
    has_description = isinstance(attraction.get('description'), dict) and 'en' in attraction.get('description', {})
    
    logger.info(f"Has formatted name: {has_name}")
    logger.info(f"Has formatted description: {has_description}")
    
    return has_name and has_description

def main():
    """Run all tests"""
    logger.info("Testing database connection...")
    if not test_database_connection():
        logger.error("Database connection failed")
        return False
    
    logger.info("\nTesting JSONB fields in attractions table...")
    jsonb_fields_exist = test_attraction_jsonb_fields()
    
    logger.info("\nTesting KnowledgeBase formatters...")
    formatters_working = test_knowledge_base_formatters()
    
    # Print summary
    logger.info("\nTest Summary:")
    logger.info(f"JSONB fields exist: {jsonb_fields_exist}")
    logger.info(f"KnowledgeBase formatters working: {formatters_working}")
    
    return jsonb_fields_exist and formatters_working

if __name__ == "__main__":
    success = main()
    print(f"\nOverall test result: {'PASSED' if success else 'FAILED'}")
