#!/usr/bin/env python
"""
Database Backup Script for Egypt Tourism Chatbot

This script creates a backup of the PostgreSQL database and stores it in a secure location.
It also verifies the backup was created successfully.
"""

import os
import sys
import logging
import subprocess
import datetime
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('database_backup.log')
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
BACKUP_RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "7"))

def create_backup_directory():
    """Create the backup directory if it doesn't exist."""
    backup_path = Path(BACKUP_DIR)
    if not backup_path.exists():
        logger.info(f"Creating backup directory: {BACKUP_DIR}")
        backup_path.mkdir(parents=True)
    return backup_path

def generate_backup_filename():
    """Generate a timestamped backup filename."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{DB_NAME}_{timestamp}.sql"

def create_database_backup():
    """Create a backup of the PostgreSQL database."""
    backup_path = create_backup_directory()
    backup_file = backup_path / generate_backup_filename()
    
    # Set environment variables for pg_dump
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD
    
    # Build the pg_dump command
    cmd = [
        "pg_dump",
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "-F", "c",  # Custom format (compressed)
        "-b",       # Include large objects
        "-v",       # Verbose
        "-f", str(backup_file),
        DB_NAME
    ]
    
    logger.info(f"Creating backup: {backup_file}")
    
    try:
        # Execute the pg_dump command
        process = subprocess.run(
            cmd,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"Backup created successfully: {backup_file}")
        logger.debug(process.stdout)
        
        # Verify the backup file exists and has content
        if backup_file.exists() and backup_file.stat().st_size > 0:
            logger.info(f"Backup verified: {backup_file} ({backup_file.stat().st_size} bytes)")
            return str(backup_file)
        else:
            logger.error(f"Backup verification failed: {backup_file} does not exist or is empty")
            return None
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during backup: {e}")
        return None

def cleanup_old_backups():
    """Remove backups older than BACKUP_RETENTION_DAYS."""
    backup_path = Path(BACKUP_DIR)
    if not backup_path.exists():
        return
    
    # Calculate the cutoff date
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=BACKUP_RETENTION_DAYS)
    
    # Find and remove old backups
    for backup_file in backup_path.glob(f"{DB_NAME}_*.sql"):
        try:
            # Get the file's modification time
            mod_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            # Remove if older than the cutoff date
            if mod_time < cutoff_date:
                logger.info(f"Removing old backup: {backup_file}")
                backup_file.unlink()
        except Exception as e:
            logger.error(f"Error cleaning up old backup {backup_file}: {e}")

def main():
    """Main function to create a database backup."""
    logger.info("Starting database backup process")
    
    # Create the backup
    backup_file = create_database_backup()
    
    if backup_file:
        logger.info(f"Database backup completed successfully: {backup_file}")
        
        # Clean up old backups
        cleanup_old_backups()
        
        return 0
    else:
        logger.error("Database backup failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
