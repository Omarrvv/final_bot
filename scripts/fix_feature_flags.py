#!/usr/bin/env python
"""
Feature Flag Configuration Update Script

This script enables the necessary feature flags to activate the advanced 
components of the Egypt Tourism Chatbot, specifically focusing on the
Knowledge Base connection to the database.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('feature_flag_updater')

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Feature flag default settings
FEATURE_FLAGS = {
    "USE_NEW_KB": True,        # Enable the new Knowledge Base implementation
    "USE_NEW_API": False,      # Keep using the current API implementation for now
    "USE_NEW_NLU": False,      # Keep using the current NLU implementation for now
    "USE_NEW_DIALOG": False,   # Keep using the current Dialog implementation for now
    "USE_POSTGRES": False,     # Keep using SQLite for now (can be changed to True if PostgreSQL is set up)
    "USE_REDIS": False,        # Keep using file-based sessions for now
    "USE_RAG": False,          # Keep the RAG pipeline disabled for now
    "USE_SERVICE_HUB": False   # Keep direct service calls for now
}

def update_env_file():
    """Update the .env file with the new feature flag settings."""
    env_path = os.path.join(project_root, '.env')
    
    try:
        # Read existing .env file if it exists
        existing_env = {}
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_env[key.strip()] = value.strip()
        
        # Update with our feature flags
        for flag, value in FEATURE_FLAGS.items():
            existing_env[flag] = str(value).lower()  # Convert to lowercase 'true' or 'false'
        
        # Write back to .env file
        with open(env_path, 'w') as f:
            for key, value in existing_env.items():
                f.write(f"{key}={value}\n")
        
        logger.info(f"✅ Updated feature flags in {env_path}")
        
        # Display the updated feature flags
        logger.info("Current feature flag settings:")
        for flag, value in FEATURE_FLAGS.items():
            logger.info(f"  {flag} = {value}")
    
    except Exception as e:
        logger.error(f"❌ Failed to update .env file: {str(e)}")

def update_config_json():
    """Update the config.json file with necessary settings."""
    config_path = os.path.join(project_root, 'configs', 'config.json')
    
    try:
        # Create configs directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Read existing config if it exists
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        # Update database configuration
        if 'database' not in config:
            config['database'] = {}
        
        # Ensure SQLite configuration is present and correct
        config['database']['sqlite'] = {
            'db_path': os.path.join(project_root, 'data', 'egypt_tourism.db')
        }
        
        # Ensure PostgreSQL configuration is present (but not activated yet)
        config['database']['postgres'] = {
            'host': 'localhost',
            'port': 5432,
            'user': 'postgres',
            'password': 'postgres',  # This should be changed in a production environment
            'database': 'egypt_tourism'
        }
        
        # Ensure knowledge base configuration
        if 'knowledge_base' not in config:
            config['knowledge_base'] = {}
        
        config['knowledge_base']['json_data_path'] = os.path.join(project_root, 'data')
        config['knowledge_base']['cache_enabled'] = True
        
        # Write the updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"✅ Updated configuration in {config_path}")
    
    except Exception as e:
        logger.error(f"❌ Failed to update config.json: {str(e)}")

def create_data_directory():
    """Ensure the data directory exists with correct permissions."""
    data_dir = os.path.join(project_root, 'data')
    try:
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"✅ Ensured data directory exists at {data_dir}")
    except Exception as e:
        logger.error(f"❌ Failed to create data directory: {str(e)}")

def verify_database_file():
    """Check if the SQLite database file exists, and if not, create a message about it."""
    db_path = os.path.join(project_root, 'data', 'egypt_tourism.db')
    
    if not os.path.exists(db_path):
        logger.warning(f"⚠️ SQLite database file not found at {db_path}")
        logger.info("Please run the database initialization script to create and populate the database.")
        logger.info("You can use the following command: python scripts/populate_attraction_data.py")
    else:
        logger.info(f"✅ SQLite database file found at {db_path}")

def run():
    """Run all configuration updates."""
    logger.info("Starting feature flag and configuration updates...")
    
    update_env_file()
    update_config_json()
    create_data_directory()
    verify_database_file()
    
    logger.info("\n=== Configuration Update Complete ===")
    logger.info("The new Knowledge Base implementation is now enabled.")
    logger.info("You can test the connection with: python scripts/test_kb_connection.py")
    
    # Special instructions for the next steps
    logger.info("\nNext steps:")
    logger.info("1. Run the database population script if needed: python scripts/populate_attraction_data.py")
    logger.info("2. Test the Knowledge Base connection: python scripts/test_kb_connection.py")
    logger.info("3. Restart the application to apply changes")

if __name__ == "__main__":
    run() 