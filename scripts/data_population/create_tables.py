#!/usr/bin/env python3
"""
Create database tables for Egypt Tourism Chatbot

This script creates the necessary tables for the Egypt Tourism Chatbot database.
"""
import sys
import time
from pathlib import Path

# Add the src directory to the Python path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.knowledge.database import DatabaseManager, DatabaseType

# Set up logging
logger = get_logger(__name__)

def main():
    """Main function to create database tables."""
    start_time = time.time()
    logger.info("Starting database table creation...")
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Ensure we're using PostgreSQL
    if db_manager.db_type != DatabaseType.POSTGRES:
        logger.error(f"PostgreSQL database not configured. Current type: {db_manager.db_type}")
        return
        
    logger.info("Connected to PostgreSQL database")
    
    # Create extension for vector support if it doesn't exist
    db_manager.execute_query("CREATE EXTENSION IF NOT EXISTS vector;", ())
    logger.info("Created vector extension")
    
    # Create cities table
    cities_table_query = """
    DROP TABLE IF EXISTS cities;
    CREATE TABLE cities (
        id TEXT PRIMARY KEY,
        name_en TEXT,
        name_ar TEXT,
        region TEXT,
        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
        data JSONB DEFAULT '{}',
        embedding VECTOR(1536),
        geom GEOMETRY(Point, 4326),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        user_id TEXT,
        region_id TEXT
    );
    """
    db_manager.execute_query(cities_table_query, ())
    logger.info("Created cities table")
    
    # Create attractions table
    attractions_table_query = """
    DROP TABLE IF EXISTS attractions;
    CREATE TABLE attractions (
        id TEXT PRIMARY KEY,
        name_en TEXT,
        name_ar TEXT,
        description_en TEXT,
        description_ar TEXT,
        city TEXT,
        region TEXT,
        type TEXT,
        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
        data JSONB DEFAULT '{}',
        embedding VECTOR(1536),
        geom GEOMETRY(Point, 4326),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        user_id TEXT,
        name JSONB,
        description JSONB
    );
    """
    db_manager.execute_query(attractions_table_query, ())
    logger.info("Created attractions table")
    
    # Create accommodations table
    accommodations_table_query = """
    DROP TABLE IF EXISTS accommodations;
    CREATE TABLE accommodations (
        id TEXT PRIMARY KEY,
        name_en TEXT,
        name_ar TEXT,
        description_en TEXT,
        description_ar TEXT,
        type TEXT,
        stars INTEGER,
        city TEXT,
        region TEXT,
        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
        data JSONB DEFAULT '{}',
        embedding VECTOR(1536),
        geom GEOMETRY(Point, 4326),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        user_id TEXT,
        name JSONB,
        description JSONB,
        price_min INTEGER,
        price_max INTEGER
    );
    """
    db_manager.execute_query(accommodations_table_query, ())
    logger.info("Created accommodations table")
    
    # Create restaurants table
    restaurants_table_query = """
    DROP TABLE IF EXISTS restaurants;
    CREATE TABLE restaurants (
        id TEXT PRIMARY KEY,
        name_en TEXT,
        name_ar TEXT,
        description_en TEXT,
        description_ar TEXT,
        cuisine TEXT,
        type TEXT,
        city TEXT,
        region TEXT,
        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
        data JSONB DEFAULT '{}',
        embedding VECTOR(1536),
        geom GEOMETRY(Point, 4326),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        user_id TEXT,
        name JSONB,
        description JSONB
    );
    """
    db_manager.execute_query(restaurants_table_query, ())
    logger.info("Created restaurants table")
    
    elapsed_time = time.time() - start_time
    logger.info(f"Database table creation completed in {elapsed_time:.2f} seconds")

if __name__ == '__main__':
    main()
