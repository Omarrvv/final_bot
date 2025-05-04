#!/usr/bin/env python3
"""
Test Environment Setup

This script sets up the environment for running tests.
It loads necessary environment variables and creates temporary test directories.
"""

import os
import tempfile
import shutil
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
import sys
import logging

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging for test setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_test_environment():
    """Set up the test environment with required variables."""
    logger.info("Setting up test environment")
    temp_dir = tempfile.mkdtemp(prefix="egypt_chatbot_test_")
    logger.info(f"Created temporary directory: {temp_dir}")

    # Set environment variables for testing
    os.environ["CONTENT_PATH"] = os.path.join(temp_dir, "data")
    os.environ["POSTGRES_URI"] = os.environ.get("TEST_POSTGRES_URI") or "postgresql://postgres:postgres@localhost:5432/egypt_chatbot_test"
    os.environ["SESSION_STORAGE_URI"] = f"file:///{os.path.join(temp_dir, 'sessions')}"
    os.environ["VECTOR_DB_URI"] = os.environ.get("TEST_VECTOR_DB_URI") or "postgresql://postgres:postgres@localhost:5432/egypt_chatbot_test"
    os.environ["TESTING"] = "true"
    os.environ["ENV"] = "test"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["USE_POSTGRES"] = "true"  # Always use PostgreSQL for tests
    os.environ["REDIS_URI"] = os.environ.get("TEST_REDIS_URI") or "redis://localhost:6379/1"

    # Create necessary directories
    os.makedirs(os.path.join(temp_dir, "data"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "data", "attractions"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "data", "restaurants"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "data", "accommodations"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "data", "cities"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "configs"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "sessions"), exist_ok=True)

    # Create test configs
    create_test_configs(temp_dir)

    # Initialize PostgreSQL test schema
    try:
        initialize_postgres_test_schema()
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL test schema: {str(e)}")
        logger.error("Tests requiring database access may fail")

    return temp_dir


def initialize_postgres_test_schema(conn=None):
    """
    Initialize the PostgreSQL test database schema.

    Args:
        conn: Optional existing database connection. If not provided, a new connection
             will be created using the POSTGRES_URI environment variable.

    Returns:
        bool: True if initialization was successful
    """
    db_uri = os.environ["POSTGRES_URI"]
    logger.info(f"Initializing test schema in: {db_uri}")

    # Track if we created a new connection that needs to be closed
    created_new_conn = False

    try:
        if conn is None:
            conn = psycopg2.connect(db_uri)
            created_new_conn = True

        with conn:
            with conn.cursor() as cursor:
                # Ensure required extensions
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

                # Create users table - was previously missing
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE,
                        password_hash TEXT,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMPTZ,
                        preferences JSONB,
                        role TEXT DEFAULT 'user'
                    )
                """)

                # Create core tables if they don't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS attractions (
                        id TEXT PRIMARY KEY,
                        name_en TEXT,
                        name_ar TEXT,
                        description_en TEXT,
                        description_ar TEXT,
                        city TEXT,
                        region TEXT,
                        type TEXT,
                        latitude FLOAT,
                        longitude FLOAT,
                        data JSONB,
                        embedding VECTOR(1536),
                        geom GEOMETRY(Point, 4326),
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        user_id TEXT REFERENCES users(id) ON DELETE SET NULL
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS restaurants (
                        id TEXT PRIMARY KEY,
                        name_en TEXT,
                        name_ar TEXT,
                        description_en TEXT,
                        description_ar TEXT,
                        cuisine TEXT,
                        type TEXT,
                        city TEXT,
                        region TEXT,
                        latitude FLOAT,
                        longitude FLOAT,
                        data JSONB,
                        embedding VECTOR(1536),
                        geom GEOMETRY(Point, 4326),
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        user_id TEXT REFERENCES users(id) ON DELETE SET NULL
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS accommodations (
                        id TEXT PRIMARY KEY,
                        name_en TEXT,
                        name_ar TEXT,
                        description_en TEXT,
                        description_ar TEXT,
                        type TEXT,
                        stars INTEGER,
                        city TEXT,
                        region TEXT,
                        latitude FLOAT,
                        longitude FLOAT,
                        data JSONB,
                        embedding VECTOR(1536),
                        geom GEOMETRY(Point, 4326),
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        user_id TEXT REFERENCES users(id) ON DELETE SET NULL
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cities (
                        id TEXT PRIMARY KEY,
                        name_en TEXT,
                        name_ar TEXT,
                        region TEXT,
                        latitude FLOAT,
                        longitude FLOAT,
                        data JSONB,
                        embedding VECTOR(1536),
                        geom GEOMETRY(Point, 4326),
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS regions (
                        id TEXT PRIMARY KEY,
                        name_en TEXT,
                        name_ar TEXT,
                        latitude FLOAT,
                        longitude FLOAT,
                        data JSONB,
                        embedding VECTOR(1536),
                        geom GEOMETRY(Point, 4326),
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create vector_search_metrics table for monitoring
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vector_search_metrics (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ DEFAULT NOW(),
                        table_name VARCHAR(255) NOT NULL,
                        query_time_ms FLOAT NOT NULL,
                        result_count INT NOT NULL,
                        vector_dimension INT,
                        query_type VARCHAR(50),
                        additional_info JSONB
                    )
                """)

                # Create vector_indexes table for index tracking
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vector_indexes (
                        id SERIAL PRIMARY KEY,
                        table_name VARCHAR(100) NOT NULL,
                        column_name VARCHAR(100) NOT NULL,
                        index_type VARCHAR(20) NOT NULL,
                        dimension INTEGER NOT NULL,
                        creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        duration_seconds FLOAT NOT NULL
                    )
                """)

                # Create analytics_events table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analytics_events (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ DEFAULT NOW(),
                        event_type VARCHAR(100) NOT NULL,
                        session_id TEXT,
                        user_id TEXT,
                        event_data JSONB
                    )
                """)

                # Create sessions table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        user_id TEXT,
                        data JSONB,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMPTZ,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """)

                # Create indexes for common query patterns
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_attractions_city ON attractions(city)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_attractions_type ON attractions(type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_city ON restaurants(city)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_cuisine ON restaurants(cuisine)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_accommodations_city ON accommodations(city)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_accommodations_type ON accommodations(type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cities_region ON cities(region)")

        logger.info("PostgreSQL test schema successfully initialized")
        return True

    except Exception as e:
        logger.error(f"Error initializing PostgreSQL schema: {str(e)}")
        raise
    finally:
        # Close the connection if we created it
        if created_new_conn and conn and not conn.closed:
            conn.close()


def create_test_configs(temp_dir):
    """Create minimal test configuration files."""
    # Only create essential configs needed for core functionality
    minimal_config = {
        "language_detection": {
            "supported_languages": ["en", "ar"],
            "default": "en"
        },
        "intent_classification": {
            "examples": {
                "greeting": ["hello", "hi"],
                "attraction_info": ["tell me about pyramids"]
            }
        },
        "models": {
            "language_detection": {
                "model_path": "lid.176.bin",
                "confidence_threshold": 0.8
            },
            "transformer_models": {
                "multilingual": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
            }
        }
    }

    with open(os.path.join(temp_dir, "configs", "test_config.json"), "w") as f:
        json.dump(minimal_config, f)

    logger.info("Created test configuration files")


def cleanup_test_environment(temp_dir):
    """Clean up the test environment."""
    # Remove temporary directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    # Reset environment variables
    for key in [
        "CONTENT_PATH", "DATABASE_URI", "SESSION_STORAGE_URI", "VECTOR_DB_URI",
        "FLASK_ENV", "TESTING", "JWT_SECRET", "LOG_LEVEL", "ENV", "FLASK_DEBUG",
        "API_HOST", "API_PORT", "FRONTEND_URL", "ANTHROPIC_API_KEY",
        "WEATHER_API_KEY", "TRANSLATION_API_KEY", "USE_NEW_KB", "USE_NEW_API",
        "USE_POSTGRES", "USE_REDIS", "USE_NEW_NLU", "USE_NEW_DIALOG", "USE_RAG",
        "USE_SERVICE_HUB"
    ]:
        if key in os.environ:
            del os.environ[key]

    logger.info("Test environment cleaned up")


if __name__ == "__main__":
    # This can be run directly to validate the test environment setup
    temp_dir = setup_test_environment()
    print(f"Test environment set up in: {temp_dir}")
    print("Environment variables set:")
    for key in sorted(os.environ.keys()):
        if key in [
            "CONTENT_PATH", "POSTGRES_URI", "SESSION_STORAGE_URI", "VECTOR_DB_URI",
            "FLASK_ENV", "TESTING", "JWT_SECRET", "LOG_LEVEL", "ENV", "FLASK_DEBUG",
            "API_HOST", "API_PORT", "FRONTEND_URL", "ANTHROPIC_API_KEY",
            "WEATHER_API_KEY", "TRANSLATION_API_KEY", "USE_NEW_KB", "USE_NEW_API",
            "USE_POSTGRES", "USE_REDIS", "USE_NEW_NLU", "USE_NEW_DIALOG", "USE_RAG",
            "USE_SERVICE_HUB"
        ]:
            # Hide sensitive values
            if key in ["JWT_SECRET", "ANTHROPIC_API_KEY", "WEATHER_API_KEY", "TRANSLATION_API_KEY"]:
                print(f"  {key}=***")
            else:
                print(f"  {key}={os.environ[key]}")

    input("Press Enter to clean up test environment...")
    cleanup_test_environment(temp_dir)
    print("Test environment cleaned up.")