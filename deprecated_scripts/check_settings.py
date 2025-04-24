#!/usr/bin/env python3
"""
Settings Validator

This script loads and displays the application settings from the .env file
and environment variables. It helps verify that settings are correctly loaded.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to sys.path to allow importing from src
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Explicitly load the .env file first
dotenv_path = os.path.join(parent_dir, '.env')
print(f"Loading .env file from: {dotenv_path}")
load_dotenv(dotenv_path=dotenv_path)

# Print the USE_NEW_KB environment variable value
print(f"USE_NEW_KB environment variable value: {os.getenv('USE_NEW_KB')}")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function that loads and displays settings."""
    try:
        # Import settings
        from src.utils.settings import settings
        
        print("\n==== Egypt Tourism Chatbot Settings ====\n")
        
        # Display settings groups
        print("Environment:")
        print("------------")
        print(f"Environment: {settings.env}")
        print(f"Debug Mode: {settings.debug}")
        print(f"Log Level: {settings.log_level}")
        print()
        
        print("Database:")
        print("---------")
        print(f"Database URI: {settings.database_uri}")
        print(f"Vector DB URI: {settings.vector_db_uri}")
        print(f"Content Path: {settings.content_path}")
        print()
        
        print("Session Storage:")
        print("---------------")
        print(f"Session Storage URI: {settings.session_storage_uri}")
        print(f"Redis URL: {settings.redis_url}")
        print()
        
        print("API Configuration:")
        print("-----------------")
        print(f"API Host: {settings.api_host}")
        print(f"API Port: {settings.api_port}")
        print(f"Frontend URL: {settings.frontend_url}")
        print(f"Allowed Origins: {settings.allowed_origins}")
        print()
        
        print("Security:")
        print("---------")
        print(f"JWT Algorithm: {settings.jwt_algorithm}")
        print(f"JWT Expiration: {settings.jwt_expiration} seconds")
        # Don't display the JWT secret
        print()
        
        print("API Keys (presence check only):")
        print("------------------------------")
        print(f"Anthropic API Key: {'Set' if settings.anthropic_api_key.get_secret_value() else 'Not Set'}")
        print(f"Weather API Key: {'Set' if settings.weather_api_key.get_secret_value() else 'Not Set'}")
        print(f"Translation API Key: {'Set' if settings.translation_api_key.get_secret_value() else 'Not Set'}")
        print()
        
        print("Feature Flags:")
        print("-------------")
        for field_name, field_value in settings.feature_flags.model_dump().items():
            status = "ENABLED" if field_value else "DISABLED"
            print(f"{field_name:15} : {status}")
        print()
        
        print("Path Validation:")
        print("---------------")
        paths_to_check = [
            ('Content Path', settings.content_path),
            ('Models Config', settings.models_config),
            ('Flows Config', settings.flows_config),
            ('Services Config', settings.services_config),
            ('Templates Path', settings.templates_path)
        ]
        
        for name, path in paths_to_check:
            exists = Path(path).exists()
            status = "✅ Exists" if exists else "❌ Missing"
            print(f"{name:15} : {path} ({status})")
        
        print("\n=========================================\n")
        
        # Return success if validation passes
        return 0
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure the settings module is correctly implemented.")
        return 1
    except Exception as e:
        logger.error(f"Error validating settings: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 