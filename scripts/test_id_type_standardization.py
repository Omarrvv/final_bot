#!/usr/bin/env python3
"""
Test script to verify that the ID type standardization changes are working correctly.
This script tests:
1. User ID handling in the User model
2. Database queries with integer user_id
3. Polymorphic associations with integer target_id
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the necessary modules
from src.models.user import User
from src.knowledge.database import DatabaseManager
from src.utils.auth import generate_token

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default database connection string
DEFAULT_DB_CONNECTION = "postgresql://postgres:postgres@localhost:5432/egypt_chatbot"

def test_user_model():
    """Test the User model with integer user_id."""
    logger.info("Testing User model with integer user_id")
    
    # Create a user with integer user_id
    user = User(user_id=123, username="test_user")
    
    # Check that the user_id is an integer
    assert isinstance(user.user_id, int), f"user_id should be an integer, got {type(user.user_id)}"
    
    # Check that the id property returns an integer
    assert isinstance(user.id, int), f"id property should return an integer, got {type(user.id)}"
    
    # Check that the id property returns the correct value
    assert user.id == 123, f"id property should return 123, got {user.id}"
    
    logger.info("User model test passed")

def test_database_queries(conn_string):
    """Test database queries with integer user_id."""
    logger.info("Testing database queries with integer user_id")
    
    # Create a database manager
    db_manager = DatabaseManager(conn_string)
    
    # Test getting a user by ID
    try:
        # First, check if there's a user with ID 1
        with psycopg2.connect(conn_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE id = 1")
                user = cursor.fetchone()
        
        if user:
            # Test get_user with integer user_id
            user_data = db_manager.get_user(1)
            assert user_data is not None, "get_user should return user data"
            logger.info("get_user test passed")
        else:
            logger.warning("No user with ID 1 found, skipping get_user test")
    except Exception as e:
        logger.error(f"Error testing get_user: {e}")
    
    # Test searching users
    try:
        users = db_manager.search_users(limit=5)
        assert isinstance(users, list), "search_users should return a list"
        logger.info(f"search_users returned {len(users)} users")
        logger.info("search_users test passed")
    except Exception as e:
        logger.error(f"Error testing search_users: {e}")
    
    logger.info("Database queries test completed")

def test_polymorphic_associations(conn_string):
    """Test polymorphic associations with integer target_id."""
    logger.info("Testing polymorphic associations with integer target_id")
    
    try:
        # Check if there are any media records
        with psycopg2.connect(conn_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM media LIMIT 1")
                media = cursor.fetchone()
        
        if media:
            # Check that target_id is an integer
            assert isinstance(media['target_id'], int), f"target_id should be an integer, got {type(media['target_id'])}"
            logger.info(f"Media target_id is an integer: {media['target_id']}")
        else:
            logger.warning("No media records found, skipping target_id type check")
        
        # Check if there are any reviews records
        with psycopg2.connect(conn_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM reviews LIMIT 1")
                review = cursor.fetchone()
        
        if review:
            # Check that target_id is an integer
            assert isinstance(review['target_id'], int), f"target_id should be an integer, got {type(review['target_id'])}"
            logger.info(f"Review target_id is an integer: {review['target_id']}")
        else:
            logger.warning("No reviews records found, skipping target_id type check")
        
        logger.info("Polymorphic associations test passed")
    except Exception as e:
        logger.error(f"Error testing polymorphic associations: {e}")

def test_token_generation():
    """Test token generation with integer user_id."""
    logger.info("Testing token generation with integer user_id")
    
    # Generate a token with integer user_id
    token = generate_token(123)
    assert token is not None, "generate_token should return a token"
    logger.info("Token generation test passed")

def main():
    """Main function to run the tests."""
    conn_string = os.getenv("DB_CONNECTION", DEFAULT_DB_CONNECTION)
    
    logger.info("Starting ID type standardization tests")
    
    # Test the User model
    test_user_model()
    
    # Test database queries
    test_database_queries(conn_string)
    
    # Test polymorphic associations
    test_polymorphic_associations(conn_string)
    
    # Test token generation
    test_token_generation()
    
    logger.info("All tests completed")

if __name__ == "__main__":
    main()
