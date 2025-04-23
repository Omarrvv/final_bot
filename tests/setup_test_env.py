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
import sqlite3
from pathlib import Path
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import DB initialization
from src.utils.init_db_tables import init_db_tables

def setup_test_environment():
    """Set up the test environment with required variables.

    Uses a temporary file-based SQLite database.
    """
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="egypt_chatbot_test_")
    db_file_path = os.path.join(temp_dir, "test_database.db")
    database_uri = f"sqlite:///{db_file_path}"

    # Initialize the file-based database BEFORE setting the env var
    # This ensures the app connects to an already initialized DB
    print(f"Initializing test database at: {db_file_path}")
    if not init_db_tables(db_file_path):
        raise RuntimeError(f"Failed to initialize test database at {db_file_path}")

    # Set environment variables for testing
    test_env_vars = {
        "CONTENT_PATH": os.path.join(temp_dir, "data"),
        "DATABASE_URI": database_uri, # Use the file-based URI
        "SESSION_STORAGE_URI": "memory://", # Use in-memory session storage
        "VECTOR_DB_URI": None, # Disable vector DB for tests
        "TESTING": "true", # Explicitly mark as testing environment
        "LOG_LEVEL": "INFO", # Use INFO to see more logs during testing if needed
        "ENV": "test",
        # Minimal required feature flags
        "USE_NEW_KB": "true",
        "USE_NEW_API": "true",
        "USE_POSTGRES": "false",
        "USE_REDIS": "false",
    }

    for key, value in test_env_vars.items():
        if value is not None: # Only set env vars that have a value
            os.environ[key] = str(value) # Convert all values to string

    # Create minimal required directories
    os.makedirs(os.path.join(temp_dir, "data"), exist_ok=True)

    # Create only essential test configurations
    create_test_configs(temp_dir)

    # Add test data to the database
    add_test_data_to_db(db_file_path)

    return temp_dir

def add_test_data_to_db(db_path):
    """Add minimal test data to the specified database file."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Add a test attraction
        cursor.execute('''
        INSERT OR REPLACE INTO attractions (id, name_en, name_ar, description_en, type, data)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'test_pyramids',
            'Pyramids of Giza',
            'أهرامات الجيزة',
            'The Pyramids of Giza are the only surviving ancient wonder.',
            'historical',
            json.dumps({
                "location": {"lat": 29.9792, "lng": 31.1342},
                "highlights": ["Great Pyramid", "Sphinx", "Khafre Pyramid"],
                "images": ["pyramids1.jpg", "pyramids2.jpg"]
            })
        ))

        # Add a test city
        cursor.execute('''
        INSERT OR REPLACE INTO cities (id, name_en, name_ar, description_en, region, data)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'cairo',
            'Cairo',
            'القاهرة',
            'Cairo is the capital of Egypt and largest city in the Arab world.',
            'Lower Egypt',
            json.dumps({
                "population": 9500000,
                "highlights": ["Khan el-Khalili", "Egyptian Museum", "Citadel"]
            })
        ))

        # Add a test hotel
        cursor.execute('''
        INSERT OR REPLACE INTO accommodations (id, name_en, name_ar, description_en, type, data)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'test_hotel',
            'Test Luxury Hotel',
            'فندق تيست الفاخر',
            'A luxury 5-star hotel with excellent amenities.',
            'hotel',
            json.dumps({
                "stars": 5,
                "amenities": ["pool", "spa", "restaurant"],
                "price_range": "high"
            })
        ))

        # Add a test restaurant
        cursor.execute('''
        INSERT OR REPLACE INTO restaurants (id, name_en, name_ar, description_en, cuisine, data)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'test_restaurant',
            'Test Egyptian Restaurant',
            'مطعم تيست المصري',
            'Traditional Egyptian cuisine in a modern setting.',
            'egyptian',
            json.dumps({
                "price_range": "medium",
                "highlights": ["koshari", "fattah", "kebab"],
                "rating": 4.5
            })
        ))

        # Add a test user
        cursor.execute('''
        INSERT OR REPLACE INTO users (id, username, email, password_hash, preferred_language)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            'test_user_1',
            'testuser',
            'test@example.com',
            'hashedpassword123', # Not a real hash, just for testing
            'en'
        ))

        # REMOVED outdated test analytics entry insert:
        # cursor.execute('''
        # INSERT INTO analytics (event_type, event_data, session_id)
        # VALUES (?, ?, ?)
        # ''', (
        #     'page_view',
        #     json.dumps({"page": "home"}),
        #     'test_session_1'
        # ))

        conn.commit()
        conn.close()
        print(f"Added test data to {db_path}")
        return True
    except Exception as e:
        print(f"Error adding test data to {db_path}: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
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
        }
    }
    
    os.makedirs(os.path.join(temp_dir, "configs"), exist_ok=True)
    with open(os.path.join(temp_dir, "configs", "test_config.json"), "w") as f:
        json.dump(minimal_config, f)

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

if __name__ == "__main__":
    # This can be run directly to validate the test environment setup
    temp_dir = setup_test_environment()
    print(f"Test environment set up in: {temp_dir}")
    print("Environment variables set:")
    for key in sorted(os.environ.keys()):
        if key in [
            "CONTENT_PATH", "DATABASE_URI", "SESSION_STORAGE_URI", "VECTOR_DB_URI",
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