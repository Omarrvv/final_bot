"""
Tests for database setup in test fixtures.
"""

import os
import pytest
import pytest_asyncio
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the database manager
from src.knowledge.database import DatabaseManager
from tests.setup_test_env import initialize_postgres_test_schema

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

async def test_db_manager_initialization(initialized_db_manager):
    """Test that the database manager is properly initialized."""
    # Check that the database manager is initialized
    assert initialized_db_manager is not None
    
    # Check that the connection pool is initialized
    assert initialized_db_manager.pg_pool is not None
    
    # Check that we can execute a simple query
    result = initialized_db_manager.execute_query("SELECT 1 as test")
    assert result is not None
    assert len(result) == 1
    assert result[0]['test'] == 1

async def test_tables_exist(initialized_db_manager):
    """Test that all required tables exist in the database."""
    # List of tables that should exist
    required_tables = [
        "users", "cities", "attractions", "restaurants", 
        "accommodations", "regions", "sessions"
    ]
    
    # Check each table
    for table in required_tables:
        result = initialized_db_manager.execute_query(
            f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table}')"
        )
        assert result[0]['exists'], f"Table {table} does not exist"

async def test_test_data_inserted(initialized_db_manager):
    """Test that test data is properly inserted."""
    # Check that test restaurant exists
    result = initialized_db_manager.execute_query(
        "SELECT * FROM restaurants WHERE id = 'test_restaurant_1'"
    )
    assert len(result) == 1
    assert result[0]['name_en'] == 'Test Restaurant'
    
    # Check that test hotel exists
    result = initialized_db_manager.execute_query(
        "SELECT * FROM accommodations WHERE id = 'test_hotel_1'"
    )
    assert len(result) == 1
    assert result[0]['name_en'] == 'Test Hotel'
    
    # Check that test attraction exists
    result = initialized_db_manager.execute_query(
        "SELECT * FROM attractions WHERE id = 'test_attraction_1'"
    )
    assert len(result) == 1
    assert result[0]['name_en'] == 'Test Attraction'
    
    # Check that test city exists
    result = initialized_db_manager.execute_query(
        "SELECT * FROM cities WHERE id = 'test_city_1'"
    )
    assert len(result) == 1
    assert result[0]['name_en'] == 'Test City'

async def test_schema_matches_code_expectations(initialized_db_manager):
    """Test that the database schema matches code expectations."""
    # Check that the restaurants table has the expected columns
    result = initialized_db_manager.execute_query("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'restaurants'
    """)
    
    # Convert to a dict for easier checking
    columns = {row['column_name']: row['data_type'] for row in result}
    
    # Check required columns
    assert 'id' in columns
    assert 'name_en' in columns
    assert 'name_ar' in columns
    assert 'description_en' in columns
    assert 'description_ar' in columns
    assert 'cuisine' in columns
    assert 'city' in columns
    assert 'region' in columns
    assert 'latitude' in columns
    assert 'longitude' in columns
    assert 'data' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns
    
    # Check data types
    assert columns['id'] == 'text'
    assert columns['name_en'] == 'text'
    assert columns['data'].lower() == 'jsonb'
    assert columns['latitude'] in ('double precision', 'real')
    assert columns['longitude'] in ('double precision', 'real')

async def test_geospatial_data(initialized_db_manager):
    """Test that geospatial data is properly set up."""
    # Skip if PostGIS is not enabled
    if not initialized_db_manager._check_postgis_enabled():
        pytest.skip("PostGIS is not enabled")
    
    # Check that the geom column exists and is properly set
    result = initialized_db_manager.execute_query("""
        SELECT ST_AsText(geom) as geom_text
        FROM restaurants
        WHERE id = 'test_restaurant_1'
    """)
    
    assert len(result) == 1
    assert result[0]['geom_text'] is not None
    assert 'POINT' in result[0]['geom_text']

async def test_database_crud_operations(initialized_db_manager):
    """Test basic CRUD operations on the database."""
    # Create a test user
    test_user = {
        'id': 'test_user_crud',
        'username': 'testuser_crud',
        'email': 'testuser_crud@example.com',
        'password_hash': 'hashed_password',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    try:
        # Insert the user
        initialized_db_manager.execute_query("""
            INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            test_user['id'], test_user['username'], test_user['email'],
            test_user['password_hash'], test_user['created_at'], test_user['updated_at']
        ))
        
        # Read the user
        result = initialized_db_manager.execute_query(
            "SELECT * FROM users WHERE id = %s", (test_user['id'],)
        )
        assert len(result) == 1
        assert result[0]['username'] == test_user['username']
        
        # Update the user
        initialized_db_manager.execute_query(
            "UPDATE users SET email = %s WHERE id = %s",
            ('updated_' + test_user['email'], test_user['id'])
        )
        
        # Verify the update
        result = initialized_db_manager.execute_query(
            "SELECT * FROM users WHERE id = %s", (test_user['id'],)
        )
        assert len(result) == 1
        assert result[0]['email'] == 'updated_' + test_user['email']
        
        # Delete the user
        initialized_db_manager.execute_query(
            "DELETE FROM users WHERE id = %s", (test_user['id'],)
        )
        
        # Verify the deletion
        result = initialized_db_manager.execute_query(
            "SELECT * FROM users WHERE id = %s", (test_user['id'],)
        )
        assert len(result) == 0
        
    finally:
        # Clean up in case the test fails
        initialized_db_manager.execute_query(
            "DELETE FROM users WHERE id = %s", (test_user['id'],)
        )
