#!/usr/bin/env python3
"""
PostgreSQL Connection Test Script

This script tests the connection to the PostgreSQL database and verifies
basic database functionality. It ensures the database is properly configured
and accessible to the application.
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Try to import from the project modules
try:
    from src.utils.postgres_database import PostgresqlDatabaseManager
    from src.utils.database_factory import get_database_manager
except ImportError as e:
    print(f"Error importing project modules: {e}")
    print("Running in standalone mode with limited functionality.")
    HAS_PROJECT_MODULES = False
else:
    HAS_PROJECT_MODULES = True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("postgres_test")

def get_postgres_uri():
    """Get PostgreSQL URI from environment variables."""
    load_dotenv()
    postgres_uri = os.environ.get("POSTGRES_URI")
    
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable not set")
        return None
    
    return postgres_uri

def test_direct_connection(postgres_uri):
    """Test direct connection to PostgreSQL using psycopg2."""
    logger.info("Testing direct connection to PostgreSQL...")
    try:
        conn = psycopg2.connect(postgres_uri)
        
        # Get PostgreSQL version
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        
        # Check for required extensions
        cursor = conn.cursor()
        cursor.execute("SELECT extname FROM pg_extension;")
        extensions = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        conn.close()
        
        logger.info(f"Successfully connected to PostgreSQL: {postgres_uri.split('@')[-1]}")
        logger.info(f"PostgreSQL version: {version.split(',')[0]}")
        logger.info(f"Available extensions: {', '.join(extensions)}")
        
        # Check for essential extensions
        essential_extensions = {"pgvector", "postgis"}
        missing_extensions = essential_extensions - set(extensions)
        
        if missing_extensions:
            logger.warning(f"Missing essential extensions: {', '.join(missing_extensions)}")
            logger.warning("Run enable_postgres_extensions.py to enable them")
            return False, version, extensions
        
        return True, version, extensions
    except psycopg2.Error as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        return False, None, None

def test_database_manager(postgres_uri):
    """Test connection using the PostgresqlDatabaseManager."""
    if not HAS_PROJECT_MODULES:
        logger.warning("Cannot test DatabaseManager: required modules not found")
        return False
    
    logger.info("Testing connection using PostgresqlDatabaseManager...")
    
    try:
        # Temporarily set environment variable if needed
        if "USE_POSTGRES" not in os.environ:
            os.environ["USE_POSTGRES"] = "true"
        
        # Test using database factory
        logger.info("Testing connection via database_factory...")
        db_manager = get_database_manager()
        
        # Verify we got a PostgreSQL manager
        if not isinstance(db_manager, PostgresqlDatabaseManager):
            logger.error("Database factory did not return a PostgresqlDatabaseManager")
            return False
        
        # Test basic query
        test_query = "SELECT 1 as test"
        result = db_manager.execute_query(test_query)
        
        if result and len(result) > 0 and result[0].get('test') == 1:
            logger.info("Successfully executed test query via DatabaseManager")
            return True
        else:
            logger.error("Test query did not return expected result")
            return False
    except Exception as e:
        logger.error(f"Error testing DatabaseManager: {e}")
        return False

def test_table_existence(postgres_uri):
    """Test if the required tables exist in the database."""
    logger.info("Testing table existence...")
    
    required_tables = [
        "attractions", 
        "cities", 
        "restaurants", 
        "accommodations", 
        "users", 
        "sessions"
    ]
    
    try:
        conn = psycopg2.connect(postgres_uri)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        existing_tables = {row['table_name'] for row in cursor.fetchall()}
        cursor.close()
        conn.close()
        
        missing_tables = set(required_tables) - existing_tables
        
        if missing_tables:
            logger.warning(f"Missing tables: {', '.join(missing_tables)}")
            logger.warning("Database schema needs to be initialized")
            return False, existing_tables
        else:
            logger.info(f"All required tables exist: {', '.join(required_tables)}")
            return True, existing_tables
    except psycopg2.Error as e:
        logger.error(f"Error checking table existence: {e}")
        return False, set()

def test_query_attractions(postgres_uri):
    """Test querying the attractions table."""
    logger.info("Testing query for attractions table...")
    
    try:
        conn = psycopg2.connect(postgres_uri)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if attractions table exists and has data
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'attractions'
            );
        """)
        
        table_exists = cursor.fetchone()['exists']
        
        if not table_exists:
            logger.warning("Attractions table does not exist")
            cursor.close()
            conn.close()
            return False, 0, []
        
        # Count attractions
        cursor.execute("SELECT COUNT(*) FROM attractions")
        count = cursor.fetchone()['count']
        
        # If no attractions, report and return
        if count == 0:
            logger.warning("Attractions table exists but contains no data")
            cursor.close()
            conn.close()
            return True, 0, []
        
        # Get a sample of attractions
        cursor.execute("SELECT id, name_en, type FROM attractions LIMIT 5")
        attractions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Found {count} attractions in the database")
        for attraction in attractions:
            logger.info(f"  - {attraction['name_en']} ({attraction['type']})")
        
        return True, count, attractions
    except psycopg2.Error as e:
        logger.error(f"Error querying attractions: {e}")
        return False, 0, []

def check_vector_support(postgres_uri):
    """Check if vector embedding columns exist and are properly configured."""
    logger.info("Checking vector embedding support...")
    
    try:
        conn = psycopg2.connect(postgres_uri)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if pgvector extension is enabled
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_extension WHERE extname = 'pgvector'
            );
        """)
        
        pgvector_enabled = cursor.fetchone()['exists']
        
        if not pgvector_enabled:
            logger.warning("pgvector extension is not enabled")
            cursor.close()
            conn.close()
            return False
        
        # Check if attractions table has embedding column
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'attractions' AND column_name = 'embedding'
            );
        """)
        
        has_embedding_column = cursor.fetchone()['exists']
        
        cursor.close()
        conn.close()
        
        if has_embedding_column:
            logger.info("Vector embedding column exists in attractions table")
        else:
            logger.warning("Vector embedding column does not exist in attractions table")
        
        return has_embedding_column
    except psycopg2.Error as e:
        logger.error(f"Error checking vector support: {e}")
        return False

def main():
    """Main function to test PostgreSQL connection and functionality."""
    logger.info("Starting PostgreSQL connection test")
    
    # Get PostgreSQL URI
    postgres_uri = get_postgres_uri()
    if not postgres_uri:
        logger.error("Cannot proceed: PostgreSQL URI not available")
        return False
    
    # Test direct connection
    conn_success, version, extensions = test_direct_connection(postgres_uri)
    if not conn_success:
        logger.error("Direct connection test failed")
        return False
    
    # Check required extensions
    essential_extensions = {"pgvector", "postgis"}
    missing_extensions = essential_extensions - set(extensions)
    
    # Test table existence
    tables_exist, existing_tables = test_table_existence(postgres_uri)
    
    # Test query for attractions
    attractions_query_success, attractions_count, attractions = test_query_attractions(postgres_uri)
    
    # Check vector support
    vector_support = check_vector_support(postgres_uri)
    
    # Test using DatabaseManager
    db_manager_success = test_database_manager(postgres_uri)
    
    # Print summary
    print("\n=== PostgreSQL Connection Test Summary ===\n")
    print(f"Direct Connection:      {'✅ Success' if conn_success else '❌ Failed'}")
    print(f"PostgreSQL Version:     {version.split(',')[0] if version else 'N/A'}")
    print(f"Required Extensions:    {'✅ All installed' if not missing_extensions else f'❌ Missing: {", ".join(missing_extensions)}'}")
    print(f"Schema Initialization:  {'✅ Tables exist' if tables_exist else '❌ Missing tables'}")
    print(f"Data Population:        {'✅ Data present' if attractions_count > 0 else '❌ No attractions data'}")
    print(f"Vector Support:         {'✅ Enabled' if vector_support else '❌ Not configured'}")
    print(f"DatabaseManager Test:   {'✅ Success' if db_manager_success else '❌ Failed'}")
    
    # Overall status
    all_success = (
        conn_success and 
        not missing_extensions and 
        tables_exist and 
        attractions_count > 0 and 
        vector_support and 
        db_manager_success
    )
    
    print(f"\nOverall Status:         {'✅ READY FOR USE' if all_success else '❌ NEEDS CONFIGURATION'}")
    
    # Next steps
    if not all_success:
        print("\nRecommended Actions:")
        
        if missing_extensions:
            print("- Run scripts/enable_postgres_extensions.py --enable to install missing extensions")
        
        if not tables_exist:
            print("- Run scripts/migrate_to_postgres.py to create tables and migrate data")
        
        if tables_exist and attractions_count == 0:
            print("- Run scripts/migrate_to_postgres.py to migrate data from SQLite")
        
        if not vector_support:
            print("- Run scripts/setup_vector_embeddings.py to configure vector support")
    
    return all_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 