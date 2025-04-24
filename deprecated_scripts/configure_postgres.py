#!/usr/bin/env python3
"""
PostgreSQL Configuration Script

This script helps configure the PostgreSQL connection settings and
environment variables for the Egypt Tourism Chatbot. It updates
the .env file with the appropriate PostgreSQL connection string.
"""

import os
import sys
import argparse
import logging
import getpass
from pathlib import Path
from dotenv import load_dotenv, set_key

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("postgres_config")

def get_current_config():
    """Get current configuration from .env file."""
    # Load existing .env file
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    
    # Get current PostgreSQL configuration
    postgres_uri = os.environ.get("POSTGRES_URI", "")
    use_postgres = os.environ.get("USE_POSTGRES", "false").lower() == "true"
    
    return {
        "postgres_uri": postgres_uri,
        "use_postgres": use_postgres
    }

def update_env_file(postgres_uri, use_postgres=True):
    """Update .env file with new PostgreSQL configuration."""
    env_path = os.path.join(project_root, '.env')
    
    # Create .env file if it doesn't exist
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write("# Egypt Tourism Chatbot Environment Variables\n\n")
    
    # Update environment variables in .env file
    set_key(env_path, "POSTGRES_URI", postgres_uri)
    set_key(env_path, "USE_POSTGRES", str(use_postgres).lower())
    
    logger.info(f"Updated .env file at {env_path}")
    logger.info(f"POSTGRES_URI set to: {postgres_uri}")
    logger.info(f"USE_POSTGRES set to: {str(use_postgres).lower()}")
    
    return True

def build_postgres_uri(host, port, database, user, password):
    """Build PostgreSQL URI from components."""
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

def test_connection(postgres_uri):
    """Test connection to PostgreSQL server."""
    try:
        import psycopg2
        conn = psycopg2.connect(postgres_uri)
        conn.close()
        logger.info("Successfully connected to PostgreSQL server")
        return True
    except ImportError:
        logger.error("psycopg2 module not installed. Cannot test connection.")
        return False
    except psycopg2.Error as e:
        logger.error(f"Failed to connect to PostgreSQL server: {e}")
        return False

def check_required_extensions(postgres_uri):
    """Check if required extensions are available in PostgreSQL."""
    required_extensions = ["pgvector", "postgis"]
    available_extensions = []
    
    try:
        import psycopg2
        conn = psycopg2.connect(postgres_uri)
        cursor = conn.cursor()
        
        # Check available extensions (not necessarily installed)
        cursor.execute("SELECT name FROM pg_available_extensions WHERE name = ANY(%s);", 
                      (required_extensions,))
        available_extensions = [row[0] for row in cursor.fetchall()]
        
        conn.close()
    except ImportError:
        logger.error("psycopg2 module not installed. Cannot check extensions.")
    except psycopg2.Error as e:
        logger.error(f"Error checking extensions: {e}")
    
    missing_extensions = set(required_extensions) - set(available_extensions)
    
    if missing_extensions:
        logger.warning(f"Missing required extensions: {', '.join(missing_extensions)}")
        logger.warning("You will need to install them on your PostgreSQL server")
    else:
        logger.info("All required extensions are available")
    
    return {
        "available": available_extensions,
        "missing": list(missing_extensions)
    }

def main():
    """Main function to configure PostgreSQL connection."""
    parser = argparse.ArgumentParser(
        description="Configure PostgreSQL connection for Egypt Tourism Chatbot."
    )
    
    # Add subparsers for different configuration methods
    subparsers = parser.add_subparsers(dest="command", help="Configuration method")
    
    # Interactive configuration
    interactive_parser = subparsers.add_parser("interactive", help="Interactive configuration")
    
    # Direct URI configuration
    uri_parser = subparsers.add_parser("uri", help="Configure using URI")
    uri_parser.add_argument("uri", help="PostgreSQL connection URI")
    
    # Component-based configuration
    component_parser = subparsers.add_parser("component", help="Configure using individual components")
    component_parser.add_argument("--host", default="localhost", help="PostgreSQL server hostname")
    component_parser.add_argument("--port", default="5432", help="PostgreSQL server port")
    component_parser.add_argument("--database", default="egypt_chatbot", help="PostgreSQL database name")
    component_parser.add_argument("--user", default="postgres", help="PostgreSQL username")
    component_parser.add_argument("--password", help="PostgreSQL password")
    
    # Common arguments
    parser.add_argument("--test", action="store_true", help="Test connection")
    parser.add_argument("--enable", action="store_true", help="Enable PostgreSQL (set USE_POSTGRES=true)")
    
    args = parser.parse_args()
    
    # Get current configuration
    current_config = get_current_config()
    
    # Determine new PostgreSQL URI based on command
    postgres_uri = None
    
    if args.command == "uri" and args.uri:
        postgres_uri = args.uri
    elif args.command == "component":
        # Get password if not provided
        password = args.password
        if password is None:
            password = getpass.getpass("PostgreSQL password: ")
        
        # Build URI from components
        postgres_uri = build_postgres_uri(
            args.host, args.port, args.database, args.user, password
        )
    elif args.command == "interactive" or not args.command:
        # Interactive configuration
        print("\n=== PostgreSQL Configuration ===\n")
        print("Current configuration:")
        print(f"POSTGRES_URI: {current_config['postgres_uri'] or 'Not set'}")
        print(f"USE_POSTGRES: {current_config['use_postgres']}")
        print("\nEnter new PostgreSQL connection details:")
        
        # Get connection details
        host = input("Host [localhost]: ") or "localhost"
        port = input("Port [5432]: ") or "5432"
        database = input("Database [egypt_chatbot]: ") or "egypt_chatbot"
        user = input("Username [postgres]: ") or "postgres"
        password = getpass.getpass("Password: ")
        
        # Build URI from components
        postgres_uri = build_postgres_uri(host, port, database, user, password)
    else:
        logger.error("No configuration method specified")
        parser.print_help()
        return False
    
    # If URI was determined, update configuration
    if postgres_uri:
        # Test connection if requested
        if args.test:
            connection_successful = test_connection(postgres_uri)
            if not connection_successful:
                logger.error("Connection test failed. Check PostgreSQL URI and try again.")
                return False
            
            # Check required extensions
            extension_status = check_required_extensions(postgres_uri)
            if extension_status["missing"]:
                print("\nWarning: Some required extensions are missing.")
                print("You will need to install them on your PostgreSQL server:")
                for ext in extension_status["missing"]:
                    print(f"  - {ext}")
        
        # Update .env file
        use_postgres = args.enable or current_config["use_postgres"]
        update_success = update_env_file(postgres_uri, use_postgres)
        
        if update_success:
            print("\n=== Configuration Summary ===\n")
            print(f"PostgreSQL URI: {postgres_uri}")
            print(f"USE_POSTGRES: {str(use_postgres).lower()}")
            
            if not use_postgres:
                print("\nNote: PostgreSQL is configured but not enabled.")
                print("To enable PostgreSQL, set USE_POSTGRES=true by running:")
                print("  python scripts/configure_postgres.py --enable")
            
            print("\nNext Steps:")
            print("1. Run scripts/enable_postgres_extensions.py to check and enable required extensions")
            print("2. Run scripts/test_postgres_connection.py to verify the connection")
            print("3. Run scripts/migrate_to_postgres.py to migrate data from SQLite")
            
            return True
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 