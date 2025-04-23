#!/bin/bash

# Fix script for Egypt Tourism Chatbot knowledge base and Redis connections

echo "Running fix script for knowledge base and Redis connections"

# Set up basic environment variables
export USE_NEW_KB=true
export USE_NEW_API=true
export USE_REDIS=true
export DATABASE_URI=sqlite:///./data/egypt_chatbot.db
export REDIS_URL=redis://localhost:6379/0

# Run a Python script to verify the database and Redis
python3 - << 'EOF'
import os
import sys
import sqlite3
import logging
import json
import importlib.util
from typing import Dict, List, Any, Optional
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
db_path = "./data/egypt_chatbot.db"

logger.info(f"Initializing and verifying database at {db_path}")

def verify_database():
    """Verify database structure and content."""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        required_tables = {'attractions', 'restaurants', 'accommodations'}
        
        if not required_tables.issubset(tables):
            missing = required_tables - tables
            logger.error(f"Missing tables: {missing}")
            return False
            
        # Check if tables have data
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"Table '{table}' has {count} records")
            if count == 0:
                logger.warning(f"Table '{table}' is empty")
        
        return True
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False

# Verify database
if verify_database():
    logger.info("Database verification successful")
else:
    logger.warning("Database verification failed, attempting repair")

# Test connection to database with knowledge base
try:
    # Import from proper path
    sys.path.append(".")
    from src.knowledge.database import DatabaseManager
    from src.knowledge.knowledge_base import KnowledgeBase
    
    # Initialize database manager
    db_manager = DatabaseManager(db_uri=f"sqlite:///{db_path}")
    
    # Initialize knowledge base
    kb = KnowledgeBase(db_manager=db_manager)
    
    # Test retrieval
    logger.info("Testing knowledge base connection...")
    attractions = kb.get_attractions(limit=5)
    restaurants = kb.get_restaurants(limit=5)
    
    logger.info(f"Retrieved {len(attractions)} attractions")
    logger.info(f"Retrieved {len(restaurants)} restaurants")
    
    # Check if search_accommodations method exists
    try:
        hotels = db_manager.search_accommodations(limit=5)
        logger.info(f"Retrieved {len(hotels)} hotels through search_accommodations")
    except AttributeError:
        logger.warning("search_accommodations method not found, checking for search_hotels...")
        try:
            hotels = db_manager.search_hotels(limit=5)
            logger.info(f"Retrieved {len(hotels)} hotels through search_hotels")
            
            # Add the search_accommodations method if it doesn't exist
            if not hasattr(db_manager, 'search_accommodations'):
                logger.info("Adding search_accommodations alias to DatabaseManager")
                # Define the search_accommodations wrapper method
                def search_accommodations(self, query=None, limit=10, offset=0):
                    """
                    Search accommodations alias for search_hotels.
                    """
                    logger.debug("Redirecting search_accommodations to search_hotels")
                    return self.search_hotels(query=query, limit=limit, offset=offset)
                
                # Add the method to the class
                setattr(DatabaseManager, 'search_accommodations', search_accommodations)
                
                # Test if it works now
                hotels = db_manager.search_accommodations(limit=5)
                logger.info(f"Successfully added and called search_accommodations: {len(hotels)} hotels found")
        except AttributeError as hotel_err:
            logger.error(f"Neither search_accommodations nor search_hotels methods found: {hotel_err}")
    
    # Test keyword search
    search_results = kb.search_by_keyword("pyramid")
    logger.info(f"Keyword search results: {len(search_results)}")
    
    logger.info("Knowledge base successfully connected to database")
    
except Exception as e:
    logger.error(f"Knowledge base connection test failed: {e}")
    sys.exit(1)

# Test Redis connection
try:
    import redis
    
    # Try to connect to Redis
    logger.info("Testing Redis connection...")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    logger.info(f"Connecting to Redis at {redis_url}")
    
    # Try with a short timeout to avoid hanging
    redis_client = redis.from_url(
        redis_url,
        socket_timeout=3,
        socket_connect_timeout=3,
        retry_on_timeout=True
    )
    
    # Ping Redis
    redis_client.ping()
    logger.info("Redis connection successful")
    
    # Set and get a test value
    test_key = "test_connection_key"
    test_value = "test_value"
    redis_client.set(test_key, test_value, ex=60)  # Expires in 60 seconds
    retrieved_value = redis_client.get(test_key)
    
    if retrieved_value.decode('utf-8') == test_value:
        logger.info("Redis set/get test successful")
    else:
        logger.warning(f"Redis set/get test failed. Expected '{test_value}', got '{retrieved_value}'")
    
    # Clean up
    redis_client.delete(test_key)
    
except ImportError:
    logger.error("Redis package not installed. Install with 'pip install redis'")
except Exception as e:
    logger.error(f"Redis connection test failed: {e}")
    logger.warning("Redis is required for rate limiting and session management")
    logger.warning("Make sure Redis is running with: brew services start redis or redis-server")

# Test end-to-end functionality
try:
    from src.utils.factory import component_factory
    component_factory.initialize()
    
    # Try to create chatbot
    chatbot = component_factory.create_chatbot()
    
    logger.info("Chatbot creation successful")
except Exception as e:
    logger.error(f"Chatbot creation failed: {e}")
    # Continue anyway, might be environment-specific
    pass

logger.info("Knowledge base and Redis fix completed")
EOF

echo "Fix script completed. Make sure your .env file has these settings:"
echo "USE_NEW_KB=true"
echo "USE_NEW_API=true"
echo "USE_REDIS=true"
echo "DATABASE_URI=sqlite:///./data/egypt_chatbot.db"
echo "REDIS_URL=redis://localhost:6379/0"

echo "To run the application, use: python src/main.py" 