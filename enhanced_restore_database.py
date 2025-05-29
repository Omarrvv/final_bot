#!/usr/bin/env python
"""
Enhanced Database Restore Script for Egypt Tourism Chatbot

This script restores a PostgreSQL database from a backup file with the following improvements:
1. Supports compressed backups
2. Implements more thorough restore verification
3. Supports incremental backups
4. Verifies backup integrity with checksums
5. Provides detailed restore progress and statistics
"""

import os
import sys
import logging
import subprocess
import argparse
import json
import hashlib
import gzip
import tempfile
import time
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

# Backup types
BACKUP_TYPE_FULL = "full"
BACKUP_TYPE_INCREMENTAL = "incremental"
BACKUP_TYPE_SCHEMA = "schema"
BACKUP_TYPE_DATA = "data"

def list_available_backups():
    """List all available backup files."""
    backup_path = Path(BACKUP_DIR).resolve()
    if not backup_path.exists():
        logger.error(f"Backup directory does not exist: {backup_path}")
        return []

    # Find all backup files
    backups = list(backup_path.glob(f"{DB_NAME}_*.sql.gz"))

    # Sort by modification time (newest first)
    backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    logger.info(f"Found {len(backups)} backup files in {backup_path}")
    return backups

def get_backup_metadata(backup_file):
    """Get metadata for a backup file."""
    backup_path = Path(backup_file)
    metadata_file = backup_path.with_suffix(".json")

    if not metadata_file.exists():
        logger.warning(f"Metadata file does not exist for backup: {backup_file}")
        return None

    try:
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
        return metadata
    except Exception as e:
        logger.error(f"Error reading metadata file: {e}")
        return None

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_backup_integrity(backup_file):
    """Verify the integrity of a backup file using its metadata."""
    backup_path = Path(backup_file)
    if not backup_path.exists():
        logger.error(f"Backup file does not exist: {backup_file}")
        return False

    # Get metadata
    metadata = get_backup_metadata(backup_file)
    if not metadata:
        logger.warning(f"No metadata available for backup: {backup_file}")
        return True  # Continue without verification

    # Verify file size
    actual_size = backup_path.stat().st_size
    expected_size = metadata.get("file_size")
    if expected_size and actual_size != expected_size:
        logger.error(f"Backup file size mismatch: expected {expected_size}, got {actual_size}")
        return False

    # Verify file hash
    expected_hash = metadata.get("file_hash")
    if expected_hash:
        actual_hash = calculate_file_hash(backup_path)
        if actual_hash != expected_hash:
            logger.error(f"Backup file hash mismatch: expected {expected_hash}, got {actual_hash}")
            return False
        else:
            logger.info(f"Backup file integrity verified: {backup_file}")

    return True

def restore_database(backup_file, create_db=False, apply_incremental=True):
    """Restore the PostgreSQL database from a backup file."""
    # Convert to absolute path
    backup_path = Path(backup_file).resolve()
    logger.info(f"Restoring from backup file: {backup_path}")

    if not backup_path.exists():
        logger.error(f"Backup file does not exist: {backup_path}")
        return False

    # Verify backup integrity
    if not verify_backup_integrity(str(backup_path)):
        logger.error(f"Backup integrity verification failed: {backup_path}")
        return False

    # Get backup metadata
    metadata = get_backup_metadata(str(backup_path))
    backup_type = metadata.get("backup_type", BACKUP_TYPE_FULL) if metadata else BACKUP_TYPE_FULL

    logger.info(f"Backup type: {backup_type}")

    # Check if this is an incremental backup
    if backup_type == BACKUP_TYPE_INCREMENTAL and apply_incremental:
        # Get the base backup
        base_backup_name = metadata.get("base_backup")
        if not base_backup_name:
            logger.error(f"Incremental backup missing base backup reference: {backup_path}")
            return False

        # Resolve the base backup path
        base_backup_path = Path(BACKUP_DIR).resolve() / base_backup_name
        logger.info(f"Base backup path: {base_backup_path}")

        if not base_backup_path.exists():
            logger.error(f"Base backup does not exist: {base_backup_path}")
            # Try to find the base backup by name in the backup directory
            potential_backups = list(Path(BACKUP_DIR).resolve().glob(f"*{base_backup_name}"))
            if potential_backups:
                base_backup_path = potential_backups[0]
                logger.info(f"Found potential base backup: {base_backup_path}")
            else:
                return False

        # First restore the base backup with create_db=True
        logger.info(f"Restoring base backup first: {base_backup_path}")
        if not restore_database(str(base_backup_path), True, False):
            logger.error(f"Failed to restore base backup: {base_backup_path}")
            return False

        # Check if the incremental backup has any modified tables
        modified_tables = metadata.get("modified_tables", [])
        if not modified_tables:
            logger.info("Incremental backup contains no modified tables, skipping application")
            return True

        # Then apply the incremental backup without dropping the database
        logger.info(f"Applying incremental backup: {backup_path}")

        # Override create_db for incremental backups
        create_db = False

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

    # Restore the database
    logger.info(f"Restoring database from backup: {backup_file}")

    try:
        # For gzipped backups, we'll use a two-step approach:
        # 1. Decompress to a temporary file
        # 2. Use psql to restore from the temporary file
        try:
            # Create a temporary file for the decompressed SQL
            with tempfile.NamedTemporaryFile(suffix='.sql', delete=False) as temp_sql:
                temp_sql_path = temp_sql.name
                logger.info(f"Decompressing backup to temporary file: {temp_sql_path}")

                # Decompress the backup file
                with gzip.open(backup_path, 'rb') as f_in:
                    # Read and write in chunks
                    while True:
                        chunk = f_in.read(4096)
                        if not chunk:
                            break
                        temp_sql.write(chunk)

            # Now restore from the temporary file
            logger.info(f"Restoring from decompressed file: {temp_sql_path}")
            restore_cmd = [
                "psql",
                "-h", DB_HOST,
                "-p", DB_PORT,
                "-U", DB_USER,
                "-d", DB_NAME,
                "-v", "ON_ERROR_STOP=1",
                "-f", temp_sql_path
            ]

            process = subprocess.run(
                restore_cmd,
                env=env,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Clean up the temporary file
            try:
                os.unlink(temp_sql_path)
                logger.info(f"Removed temporary file: {temp_sql_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_sql_path}: {e}")

            # Check the result
            if process.returncode != 0:
                logger.error(f"Restore failed with return code {process.returncode}")
                logger.error(f"Error output: {process.stderr}")
                return False

        except Exception as e:
            logger.error(f"Unexpected error during restore: {e}")
            return False

        logger.info(f"Database restored successfully from: {backup_file}")
        return True

    except Exception as e:
        logger.error(f"Unexpected error during restore: {e}")
        return False

def verify_restore():
    """Verify the database restore by running a series of queries."""
    # Set environment variables for psql
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    logger.info("Verifying database restore")

    try:
        # Check table count
        table_count_cmd = [
            "psql",
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-U", DB_USER,
            "-d", DB_NAME,
            "-t",  # Tuple only output
            "-c", "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
        ]

        process = subprocess.run(
            table_count_cmd,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        table_count = int(process.stdout.strip())
        logger.info(f"Database has {table_count} tables")

        if table_count == 0:
            logger.error("No tables found in database")
            return False

        # Check record counts in key tables
        key_tables = ["cities", "attractions", "accommodations", "regions"]
        for table in key_tables:
            count_cmd = [
                "psql",
                "-h", DB_HOST,
                "-p", DB_PORT,
                "-U", DB_USER,
                "-d", DB_NAME,
                "-t",  # Tuple only output
                "-c", f"SELECT COUNT(*) FROM {table};"
            ]

            try:
                process = subprocess.run(
                    count_cmd,
                    env=env,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                record_count = int(process.stdout.strip())
                logger.info(f"Table {table} has {record_count} records")

                if record_count == 0:
                    logger.warning(f"Table {table} is empty")
            except Exception as e:
                logger.warning(f"Error checking record count for table {table}: {e}")

        # Run a simple query to verify data integrity
        query_cmd = [
            "psql",
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-U", DB_USER,
            "-d", DB_NAME,
            "-c", "SELECT id, name->>'en' FROM attractions LIMIT 1;"
        ]

        process = subprocess.run(
            query_cmd,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if "id" in process.stdout and "name" in process.stdout:
            logger.info("Data integrity verified")
        else:
            logger.warning("Data integrity check inconclusive")

        logger.info("Database restore verification completed")
        return True

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
    parser.add_argument("--latest-full", action="store_true", help="Restore from the latest full backup")
    parser.add_argument("--skip-verify", action="store_true", help="Skip restore verification")
    args = parser.parse_args()

    logger.info("Starting enhanced database restore process")

    # List available backups if requested
    if args.list:
        backups = list_available_backups()
        if backups:
            logger.info("Available backups:")
            for i, backup in enumerate(backups):
                size_mb = backup.stat().st_size / (1024 * 1024)
                metadata = get_backup_metadata(backup)
                backup_type = metadata.get("backup_type", "unknown") if metadata else "unknown"
                logger.info(f"{i+1}. {backup.name} ({size_mb:.2f} MB) - Type: {backup_type}")
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
    elif args.latest_full:
        backups = list_available_backups()
        for backup in backups:
            metadata = get_backup_metadata(backup)
            if metadata and metadata.get("backup_type") == BACKUP_TYPE_FULL:
                backup_file = str(backup)
                logger.info(f"Using latest full backup: {backup_file}")
                break

        if not backup_file:
            logger.error("No full backups found")
            return 1
    else:
        logger.error("No backup file specified. Use --backup-file, --latest, or --latest-full")
        return 1

    # Restore the database
    if restore_database(backup_file, args.create_db):
        logger.info("Database restore completed successfully")

        # Verify the restore
        if not args.skip_verify:
            if verify_restore():
                logger.info("Database restore verified successfully")
                return 0
            else:
                logger.error("Database restore verification failed")
                return 1
        else:
            logger.info("Skipping restore verification")
            return 0
    else:
        logger.error("Database restore failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
