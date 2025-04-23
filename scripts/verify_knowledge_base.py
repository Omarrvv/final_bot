#!/usr/bin/env python
"""
Verify Knowledge Base Script

This script verifies the SQLite database connection and data integrity for the Egypt Chatbot.
It checks for the existence of required tables, counts records, and tests the DatabaseManager's
ability to retrieve data.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.utils.settings import settings
from src.knowledge.database import DatabaseManager

# Load environment variables
load_dotenv()

def verify_sqlite_database(db_path):
    """
    Verify that the SQLite database exists and contains the required tables with data.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        bool: True if verification passes, False otherwise
    """
    print(f"Verifying SQLite database at: {db_path}")
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found at {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check required tables
        required_tables = ['attractions', 'restaurants', 'accommodations']
        all_tables_exist = True
        
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                print(f"[ERROR] Required table '{table}' not found in database")
                all_tables_exist = False
        
        if not all_tables_exist:
            conn.close()
            return False
        
        # Check record counts
        table_counts = {}
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_counts[table] = count
            print(f"[INFO] Table '{table}' contains {count} records")
            
        # Verify that at least one record exists across all tables
        if sum(table_counts.values()) == 0:
            print(f"[ERROR] No records found in any table")
            conn.close()
            return False
            
        # Close the connection
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"[ERROR] SQLite error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error verifying database: {e}")
        return False

def verify_database_manager():
    """
    Verify that the DatabaseManager can successfully connect to the database
    and retrieve data.
    
    Returns:
        bool: True if verification passes, False otherwise
    """
    print("Verifying DatabaseManager functionality...")
    
    try:
        # Initialize the database manager
        db_manager = DatabaseManager()
        
        # Test getting attractions
        attractions = db_manager.search_attractions({}, limit=5)
        if not attractions or len(attractions) == 0:
            print("[ERROR] Failed to retrieve attractions")
            return False
        print(f"[INFO] Successfully retrieved {len(attractions)} attractions")
        
        # Test getting restaurants
        restaurants = db_manager.search_restaurants({}, limit=5)
        if not restaurants or len(restaurants) == 0:
            print("[ERROR] Failed to retrieve restaurants")
            return False
        print(f"[INFO] Successfully retrieved {len(restaurants)} restaurants")
        
        # Test getting accommodations
        try:
            accommodations = db_manager.search_accommodations({}, limit=5)
            if not accommodations or len(accommodations) == 0:
                print("[WARNING] No accommodations found in the knowledge base")
            else:
                print(f"[INFO] Successfully retrieved {len(accommodations)} accommodations")
        except AttributeError:
            print("[WARNING] search_accommodations method not found, might be using search_hotels instead")
            try:
                accommodations = db_manager.search_hotels({}, limit=5)
                if not accommodations or len(accommodations) == 0:
                    print("[WARNING] No hotels found in the knowledge base")
                else:
                    print(f"[INFO] Successfully retrieved {len(accommodations)} hotels")
            except Exception as e:
                print(f"[WARNING] Could not retrieve accommodations: {e}")
        
        # Test keyword search
        search_results = db_manager.enhanced_search("attractions", search_text="pyramid", limit=5)
        print(f"[INFO] Keyword search returned {len(search_results)} results")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Database manager verification failed: {e}")
        return False

def main():
    """Main function to run the verification process."""
    print("\n==== Starting Knowledge Base Verification ====\n")
    
    # Get database path from settings
    db_uri = settings.database_uri
    
    # Extract file path from SQLite URI
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
        # Handle relative path
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)
    else:
        print(f"[ERROR] Unsupported database URI: {db_uri}")
        return False
    
    # Verify SQLite database
    if not verify_sqlite_database(db_path):
        print("\n[FAIL] SQLite database verification failed")
        return False
    print("\n[PASS] SQLite database verification passed")
    
    # Verify database manager
    if not verify_database_manager():
        print("\n[FAIL] Database manager verification failed")
        return False
    print("\n[PASS] Database manager verification passed")
    
    print("\n==== Knowledge Base Verification Completed Successfully ====\n")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 