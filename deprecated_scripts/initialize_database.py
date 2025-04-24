#!/usr/bin/env python3
"""
Database Initialization and Verification Script.
This script ensures the SQLite database is properly initialized and populated.
"""

import os
import sys
import logging
import sqlite3
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import needed modules
from src.utils.init_db_tables import init_db_tables
from src.knowledge.database import DatabaseManager

def verify_db_exists():
    """Check if the database file exists."""
    db_path = Path(project_root) / "data" / "egypt_chatbot.db"
    if db_path.exists():
        logger.info(f"Database file exists at {db_path}")
        return True
    else:
        logger.warning(f"Database file not found at expected path: {db_path}")
        return False

def check_db_populated():
    """Check if the database contains data."""
    db_path = Path(project_root) / "data" / "egypt_chatbot.db"
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check key tables for data
        tables_to_check = ['attractions', 'restaurants', 'accommodations']
        empty_tables = []
        
        for table in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"Table '{table}' contains {count} records")
            if count == 0:
                empty_tables.append(table)
        
        conn.close()
        
        if empty_tables:
            logger.warning(f"The following tables are empty: {', '.join(empty_tables)}")
            return False
        else:
            logger.info("All tables contain data")
            return True
            
    except sqlite3.Error as e:
        logger.error(f"Error checking database population: {e}")
        return False

def initialize_db():
    """Initialize the database tables."""
    db_path = Path(project_root) / "data" / "egypt_chatbot.db"
    os.makedirs(db_path.parent, exist_ok=True)
    
    logger.info(f"Initializing database at {db_path}")
    success = init_db_tables(str(db_path))
    
    if success:
        logger.info("Database tables initialized successfully")
    else:
        logger.error("Failed to initialize database tables")
    
    return success

def run_populate_script():
    """Run the populate_kb.py script to load data into the database."""
    from importlib import import_module
    
    try:
        logger.info("Attempting to run populate_kb.py")
        # Import and run the populate_database function
        populate_module = import_module("scripts.populate_kb")
        populate_module.populate_database()
        logger.info("Database population complete")
        return True
    except Exception as e:
        logger.error(f"Error running populate_kb.py: {e}", exc_info=True)
        return False

def test_database_connection():
    """Test connection to the database through DatabaseManager."""
    try:
        logger.info("Testing database connection through DatabaseManager")
        db_manager = DatabaseManager()
        
        # Test a basic query
        attractions = db_manager.get_all_attractions(limit=5)
        if attractions:
            logger.info(f"Successfully retrieved {len(attractions)} attractions")
            for attr in attractions:
                logger.info(f"  - {attr.get('id')}: {attr.get('name_en')}")
        else:
            logger.warning("No attractions found in database")
        
        db_manager.close()
        return True
    except Exception as e:
        logger.error(f"Error testing database connection: {e}", exc_info=True)
        return False

def main():
    """Main function to initialize and verify the database."""
    logger.info("Starting database initialization and verification")
    
    # Step 1: Check if database file exists
    db_exists = verify_db_exists()
    
    # Step 2: Initialize database if needed
    if not db_exists:
        logger.info("Database file not found, initializing...")
        if not initialize_db():
            logger.error("Failed to initialize database. Aborting.")
            return False
    
    # Step 3: Check if database is populated
    is_populated = check_db_populated()
    
    # Step 4: Populate database if needed
    if not is_populated:
        logger.info("Database is empty, populating with data...")
        if not run_populate_script():
            logger.error("Failed to populate database. Aborting.")
            return False
    
    # Step 5: Test connection through DatabaseManager
    if not test_database_connection():
        logger.error("Failed to connect to database through DatabaseManager. Aborting.")
        return False
    
    logger.info("Database initialization and verification complete")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 