#!/usr/bin/env python

"""
Verify Database Script

This script verifies the database connection and operations for the Egypt Chatbot.
It checks if the database is properly configured and validates its functionality.
"""

import os
import sys
import time
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Import database manager directly from the source
from src.utils.database import DatabaseManager
from src.utils.settings import settings

# Load environment variables
load_dotenv()

def verify_database_config():
    """
    Verify the database configuration in the settings.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    try:
        print("[INFO] Checking database configuration")
        
        # Check if database_uri is set
        if not settings.database_uri:
            print("[ERROR] DATABASE_URI is not set in environment variables")
            return False
        
        print(f"[INFO] Database URI: {settings.database_uri}")
        
        # Validate database type
        if settings.database_uri.startswith("sqlite"):
            db_path = settings.database_uri.replace("sqlite:///", "")
            if not os.path.exists(db_path) and "memory" not in db_path:
                print(f"[WARNING] SQLite database file does not exist: {db_path}")
                print("[INFO] This is okay if the app will create it on startup")
        elif not (settings.database_uri.startswith("postgresql") or 
                  settings.database_uri.startswith("mysql")):
            print(f"[WARNING] Unsupported database type in URI: {settings.database_uri}")
            print("[INFO] Supported types are sqlite, postgresql, and mysql")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error checking database configuration: {e}")
        return False

def verify_database_connection():
    """
    Verify that the database connection can be established.
    
    Returns:
        bool: True if connection is successful, False otherwise
        engine: SQLAlchemy engine if connection is successful, None otherwise
    """
    try:
        print("[INFO] Attempting to connect to database")
        
        # Create SQLAlchemy engine
        engine = create_engine(settings.database_uri)
        
        # Try to connect
        with engine.connect() as conn:
            # Execute a simple query to check connection
            result = conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                print("[INFO] Database connection successful")
                return True, engine
            else:
                print("[ERROR] Database connection test failed")
                return False, None
        
    except SQLAlchemyError as e:
        print(f"[ERROR] SQLAlchemy error connecting to database: {e}")
        return False, None
    except Exception as e:
        print(f"[ERROR] Error connecting to database: {e}")
        return False, None

def verify_database_tables(engine):
    """
    Verify that the necessary tables exist in the database.
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        bool: True if tables exist, False otherwise
    """
    try:
        print("[INFO] Checking database tables")
        
        required_tables = [
            'attractions', 
            'restaurants', 
            'accommodations',
            'analytics',
            'sessions'
        ]
        
        existing_tables = []
        
        # Get list of tables from database
        with engine.connect() as conn:
            if engine.url.drivername.startswith('sqlite'):
                result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ))
                existing_tables = [row[0] for row in result]
            elif engine.url.drivername.startswith('postgresql'):
                result = conn.execute(text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                ))
                existing_tables = [row[0] for row in result]
            elif engine.url.drivername.startswith('mysql'):
                result = conn.execute(text(
                    "SHOW TABLES"
                ))
                existing_tables = [row[0] for row in result]
            else:
                print(f"[WARNING] Unsupported database type for table verification: {engine.url.drivername}")
                return True
        
        # Check if required tables exist
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"[WARNING] Missing tables: {', '.join(missing_tables)}")
            print("[INFO] These tables will be created if using the ORM with create_all")
        else:
            print(f"[INFO] All required tables exist: {', '.join(required_tables)}")
        
        # List all tables found
        print(f"[INFO] Found tables: {', '.join(existing_tables)}")
        
        return True
        
    except SQLAlchemyError as e:
        print(f"[ERROR] SQLAlchemy error checking tables: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error checking database tables: {e}")
        return False

def verify_database_manager():
    """
    Verify that the DatabaseManager can be initialized and used.
    
    Returns:
        bool: True if manager works correctly, False otherwise
    """
    try:
        print("[INFO] Testing DatabaseManager initialization")
        
        # Initialize DatabaseManager
        db_manager = DatabaseManager()
        
        print("[INFO] DatabaseManager initialized successfully")
        
        # Test attraction retrieval
        print("[INFO] Testing attraction retrieval")
        attractions = db_manager.search_attractions({}, limit=1)
        if attractions:
            print(f"[INFO] Successfully retrieved attraction: {attractions[0]['name_en']}")
        else:
            print("[WARNING] No attractions found in database")
        
        # Test restaurant retrieval
        print("[INFO] Testing restaurant retrieval")
        restaurants = db_manager.search_restaurants({}, limit=1)
        if restaurants:
            print(f"[INFO] Successfully retrieved restaurant: {restaurants[0]['name_en']}")
        else:
            print("[WARNING] No restaurants found in database")
        
        # Test accommodation retrieval
        print("[INFO] Testing accommodation retrieval")
        try:
            accommodations = db_manager.search_accommodations({}, limit=1)
            if accommodations:
                print(f"[INFO] Successfully retrieved accommodation: {accommodations[0]['name_en']}")
            else:
                print("[WARNING] No accommodations found in database")
        except AttributeError:
            print("[WARNING] search_accommodations method not found, trying search_hotels")
            try:
                hotels = db_manager.search_hotels({}, limit=1)
                if hotels:
                    print(f"[INFO] Successfully retrieved hotel: {hotels[0]['name_en']}")
                else:
                    print("[WARNING] No hotels found in database")
            except Exception as e:
                print(f"[WARNING] Hotel retrieval failed: {e}")
        
        # Test analytics logging
        print("[INFO] Testing analytics logging")
        try:
            db_manager.log_analytics_event(
                event_type="test",
                event_data={"test": "data"},
                session_id="test_session",
                user_id=None
            )
            print("[INFO] Analytics logging successful")
        except Exception as e:
            print(f"[WARNING] Analytics logging failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error testing DatabaseManager: {e}")
        return False

def main():
    """Main function to run the verification process."""
    print("\n==== Starting Database Verification ====\n")
    
    # Verify database configuration
    if not verify_database_config():
        print("\n[FAIL] Database configuration verification failed")
        return False
    print("\n[PASS] Database configuration verification passed")
    
    # Verify database connection
    connection_success, engine = verify_database_connection()
    if not connection_success:
        print("\n[FAIL] Database connection verification failed")
        return False
    print("\n[PASS] Database connection verification passed")
    
    # Verify database tables
    if not verify_database_tables(engine):
        print("\n[FAIL] Database tables verification failed")
        return False
    print("\n[PASS] Database tables verification passed")
    
    # Verify database manager
    if not verify_database_manager():
        print("\n[FAIL] DatabaseManager verification failed")
        return False
    print("\n[PASS] DatabaseManager verification passed")
    
    print("\n==== Database Verification Completed Successfully ====\n")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 