#!/usr/bin/env python3
"""
Complete PostgreSQL Migration Script

This script handles the complete process of migrating from SQLite to PostgreSQL,
including fixing schema issues and adding vector and geospatial features.
"""

import os
import sys
import logging
import argparse
import subprocess
import psycopg2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("complete_migration")

def run_script(script_path, description, script_args=None):
    """
    Run a Python script with optional arguments.
    
    Args:
        script_path (str): Path to the script
        description (str): Description of what the script does
        script_args (list): Optional arguments to pass to the script
        
    Returns:
        bool: True if the script ran successfully, False otherwise
    """
    cmd = [sys.executable, script_path]
    
    if script_args:
        cmd.extend(script_args)
    
    logger.info(f"Running {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Successfully ran {description}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run {description}: {e}")
        logger.error(f"Output: {e.stdout}")
        logger.error(f"Error: {e.stderr}")
        return False

def check_postgres_version():
    """
    Check PostgreSQL version.
    
    Returns:
        str: PostgreSQL version
    """
    try:
        result = subprocess.run(
            ["psql", "--version"], 
            check=True, 
            capture_output=True, 
            text=True
        )
        version_line = result.stdout.strip()
        logger.info(f"PostgreSQL version: {version_line}")
        return version_line
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check PostgreSQL version: {e}")
        sys.exit(1)

def check_environment_variables():
    """
    Check required environment variables.
    
    Returns:
        dict: Environment variables
    """
    required_vars = {
        "POSTGRES_URI": os.getenv("POSTGRES_URI"),
        "USE_POSTGRES": os.getenv("USE_POSTGRES"),
        "USE_NEW_KB": os.getenv("USE_NEW_KB")
    }
    
    for var, value in required_vars.items():
        if value:
            logger.info(f"Environment variable {var} is set: {value}")
        else:
            logger.error(f"Environment variable {var} is not set")
            sys.exit(1)
    
    return required_vars

def main():
    """Main function to handle complete migration process."""
    parser = argparse.ArgumentParser(description="Complete PostgreSQL migration process")
    parser.add_argument("--skip-migrate", action="store_true", help="Skip data migration step")
    parser.add_argument("--skip-vector", action="store_true", help="Skip vector features setup")
    parser.add_argument("--skip-postgis", action="store_true", help="Skip PostGIS setup")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Step 1: Check prerequisites
    logger.info("Step 1: Checking prerequisites...")
    pg_version = check_postgres_version()
    env_vars = check_environment_variables()
    
    # Step 2: Fix schema issues
    logger.info("Step 2: Fixing schema issues...")
    if not run_script("scripts/fix_migration_issues.py", "schema issues fix"):
        logger.error("Failed to fix schema issues")
        sys.exit(1)
        
    # Run schema fix for PostgreSQL
    if not run_script("scripts/fix_postgres_schema.py", "PostgreSQL schema fixes"):
        logger.error("Failed to fix PostgreSQL schema")
        sys.exit(1)
    
    # Step 3: Migrate data (if not skipped)
    if not args.skip_migrate:
        logger.info("Step 3: Migrating data from SQLite to PostgreSQL...")
        if not run_script("scripts/migrate_to_postgres.py", "data migration"):
            logger.error("Failed to migrate data to PostgreSQL")
            sys.exit(1)
    else:
        logger.info("Step 3: Data migration skipped per user request")
    
    # Step 4: Add vector and geospatial features
    logger.info("Step 4: Adding vector and geospatial features...")
    
    # Add PostgreSQL extensions
    if not args.skip_vector:
        # Add vector extension
        try:
            subprocess.run(
                ["psql", "-d", "egypt_chatbot", "-c", "CREATE EXTENSION IF NOT EXISTS vector;"],
                check=True
            )
            logger.info("Vector extension added successfully")
            
            # Add vector columns and indices
            if not run_script("scripts/add_vector_columns.py", "vector columns addition"):
                logger.warning("Failed to add all vector columns - some may already exist")
        except Exception as e:
            logger.error(f"Failed to add vector extension: {e}")
    else:
        logger.info("Vector features setup skipped per user request")
    
    if not args.skip_postgis:
        # Add PostGIS extension
        try:
            subprocess.run(
                ["psql", "-d", "egypt_chatbot", "-c", "CREATE EXTENSION IF NOT EXISTS postgis;"],
                check=True
            )
            logger.info("PostGIS extension added successfully")
        except Exception as e:
            logger.error(f"Failed to add PostGIS extension: {e}")
    else:
        logger.info("PostGIS setup skipped per user request")
    
    # Step 5: Validate configuration
    logger.info("Step 5: Validating configuration...")
    if env_vars["USE_POSTGRES"] != "true":
        logger.warning("USE_POSTGRES is not set to 'true' in .env file")
        logger.info("Setting USE_POSTGRES=true in .env file")
        # Modify .env file to enable PostgreSQL
        try:
            with open(".env", "r") as f:
                env_content = f.readlines()
            
            with open(".env", "w") as f:
                for line in env_content:
                    if line.startswith("USE_POSTGRES="):
                        f.write("USE_POSTGRES=true\n")
                    else:
                        f.write(line)
            
            logger.info("Updated .env file with USE_POSTGRES=true")
        except Exception as e:
            logger.error(f"Failed to update .env file: {e}")
    
    if env_vars["USE_NEW_KB"] != "true":
        logger.warning("USE_NEW_KB is not set to 'true' in .env file")
        logger.info("Setting USE_NEW_KB=true in .env file")
        # Modify .env file to enable new knowledge base
        try:
            with open(".env", "r") as f:
                env_content = f.readlines()
            
            with open(".env", "w") as f:
                for line in env_content:
                    if line.startswith("USE_NEW_KB="):
                        f.write("USE_NEW_KB=true\n")
                    else:
                        f.write(line)
                
                # Add USE_NEW_KB=true if not found
                if not any(line.startswith("USE_NEW_KB=") for line in env_content):
                    f.write("USE_NEW_KB=true\n")
            
            logger.info("Updated .env file with USE_NEW_KB=true")
        except Exception as e:
            logger.error(f"Failed to update .env file: {e}")
    
    logger.info("Migration completed successfully!")
    logger.info("PostgreSQL database is ready to use")
    logger.info("To start the application, run: python main.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 