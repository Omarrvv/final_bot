#!/usr/bin/env python
"""
Database Restore Script for Egypt Tourism Chatbot

This script restores a PostgreSQL database from a backup file.
"""

import os
import sys
import logging
import subprocess
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('database_restore.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_NAME = os.environ.get("DB_NAME", "egypt_chatbot")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")

# Backup directory
BACKUP_DIR = os.environ.get("BACKUP_DIR", "backups")

def list_available_backups():
    """List all available backup files."""
    backup_path = Path(BACKUP_DIR)
    if not backup_path.exists():
        logger.error(f"Backup directory does not exist: {BACKUP_DIR}")
        return []
    
    # Find all backup files
    backups = list(backup_path.glob(f"{DB_NAME}_*.sql"))
    
    # Sort by modification time (newest first)
    backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return backups

def restore_database(backup_file, create_db=False):
    """Restore the PostgreSQL database from a backup file."""
    backup_path = Path(backup_file)
    if not backup_path.exists():
        logger.error(f"Backup file does not exist: {backup_file}")
        return False
    
    # Set environment variables for PostgreSQL commands
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD
    
    # Create the database if requested
    if create_db:
        logger.info(f"Creating database: {DB_NAME}")
        
        # Drop the database if it exists
        drop_cmd = [
            "dropdb",
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-U", DB_USER,
            "--if-exists",
            DB_NAME
        ]
        
        try:
            subprocess.run(
                drop_cmd,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"Dropped existing database: {DB_NAME}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Error dropping database: {e.stderr}")
        
        # Create the database
        create_cmd = [
            "createdb",
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-U", DB_USER,
            DB_NAME
        ]
        
        try:
            subprocess.run(
                create_cmd,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"Created database: {DB_NAME}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating database: {e.stderr}")
            return False
    
    # Build the pg_restore command
    restore_cmd = [
        "pg_restore",
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "-d", DB_NAME,
        "-v",       # Verbose
        str(backup_path)
    ]
    
    logger.info(f"Restoring database from backup: {backup_file}")
    
    try:
        # Execute the pg_restore command
        process = subprocess.run(
            restore_cmd,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"Database restored successfully from: {backup_file}")
        logger.debug(process.stdout)
        
        return True
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Restore failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during restore: {e}")
        return False

def verify_restore():
    """Verify the database restore by running a simple query."""
    # Set environment variables for psql
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD
    
    # Build the psql command to count tables
    verify_cmd = [
        "psql",
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "-d", DB_NAME,
        "-c", "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
    ]
    
    logger.info("Verifying database restore")
    
    try:
        # Execute the psql command
        process = subprocess.run(
            verify_cmd,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Check if we got a valid result
        output = process.stdout.strip()
        if "count" in output.lower():
            logger.info(f"Database restore verified: {output}")
            return True
        else:
            logger.error(f"Database verification failed: {output}")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Verification failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        return False

def main():
    """Main function to restore a database from backup."""
    parser = argparse.ArgumentParser(description="Restore PostgreSQL database from backup")
    parser.add_argument("--backup-file", help="Path to backup file")
    parser.add_argument("--create-db", action="store_true", help="Create the database if it doesn't exist")
    parser.add_argument("--list", action="store_true", help="List available backups")
    parser.add_argument("--latest", action="store_true", help="Restore from the latest backup")
    args = parser.parse_args()
    
    logger.info("Starting database restore process")
    
    # List available backups if requested
    if args.list:
        backups = list_available_backups()
        if backups:
            logger.info("Available backups:")
            for i, backup in enumerate(backups):
                size_mb = backup.stat().st_size / (1024 * 1024)
                logger.info(f"{i+1}. {backup.name} ({size_mb:.2f} MB)")
        else:
            logger.info("No backups found")
        return 0
    
    # Determine which backup file to use
    backup_file = None
    if args.backup_file:
        backup_file = args.backup_file
    elif args.latest:
        backups = list_available_backups()
        if backups:
            backup_file = str(backups[0])
            logger.info(f"Using latest backup: {backup_file}")
        else:
            logger.error("No backups found")
            return 1
    else:
        logger.error("No backup file specified. Use --backup-file or --latest")
        return 1
    
    # Restore the database
    if restore_database(backup_file, args.create_db):
        logger.info("Database restore completed successfully")
        
        # Verify the restore
        if verify_restore():
            logger.info("Database restore verified successfully")
            return 0
        else:
            logger.error("Database restore verification failed")
            return 1
    else:
        logger.error("Database restore failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
