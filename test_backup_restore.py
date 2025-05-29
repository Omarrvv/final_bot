#!/usr/bin/env python
"""
Test script for database backup and restore functionality.

This script:
1. Creates a full backup
2. Creates an incremental backup
3. Restores to a test database
4. Verifies the restore
5. Measures performance and compression ratio
"""

import os
import sys
import logging
import subprocess
import argparse
import time
import tempfile
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backup_restore_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection parameters
PROD_DB_NAME = os.environ.get("DB_NAME", "egypt_chatbot")
TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "egypt_chatbot_backup_test")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")

# Backup directory
BACKUP_DIR = os.environ.get("BACKUP_DIR", "backups")
TEST_BACKUP_DIR = os.environ.get("TEST_BACKUP_DIR", "test_backups")

def setup_test_environment():
    """Set up the test environment."""
    # Create test backup directory with absolute path
    test_backup_path = Path(TEST_BACKUP_DIR).resolve()
    if test_backup_path.exists():
        shutil.rmtree(test_backup_path)
    test_backup_path.mkdir(parents=True)

    # Set environment variables for the test with absolute path
    os.environ["BACKUP_DIR"] = str(test_backup_path)
    os.environ["DB_NAME"] = PROD_DB_NAME

    logger.info(f"Created test backup directory: {test_backup_path}")
    return test_backup_path

def cleanup_test_environment():
    """Clean up the test environment."""
    # Remove test backup directory
    test_backup_path = Path(TEST_BACKUP_DIR).resolve()
    if test_backup_path.exists():
        logger.info(f"Removing test backup directory: {test_backup_path}")
        shutil.rmtree(test_backup_path)

    # Reset environment variables
    os.environ["BACKUP_DIR"] = BACKUP_DIR
    os.environ["DB_NAME"] = PROD_DB_NAME

    # Drop test database if it exists
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    drop_cmd = [
        "dropdb",
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "--if-exists",
        TEST_DB_NAME
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
        logger.info(f"Dropped test database: {TEST_DB_NAME}")
    except Exception as e:
        logger.warning(f"Error dropping test database: {e}")

def create_full_backup():
    """Create a full backup."""
    logger.info("Creating full backup")

    start_time = time.time()

    # Run the enhanced backup script
    cmd = [
        "python", "enhanced_backup_database.py",
        "--type", "full"
    ]

    process = subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    end_time = time.time()
    duration = end_time - start_time

    logger.info(f"Full backup created in {duration:.2f} seconds")
    logger.debug(process.stdout)

    # Find the backup file
    backup_path = Path(TEST_BACKUP_DIR).resolve()
    backup_files = list(backup_path.glob(f"{PROD_DB_NAME}_full_*.sql.gz"))

    if not backup_files:
        logger.error("No full backup file found")
        return None

    # Get the latest backup file
    backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    backup_file = backup_files[0]

    logger.info(f"Full backup file: {backup_file}")
    return str(backup_file)

def create_incremental_backup():
    """Create an incremental backup."""
    logger.info("Creating incremental backup")

    start_time = time.time()

    # Run the enhanced backup script
    cmd = [
        "python", "enhanced_backup_database.py",
        "--type", "incremental"
    ]

    process = subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    end_time = time.time()
    duration = end_time - start_time

    logger.info(f"Incremental backup created in {duration:.2f} seconds")
    logger.debug(process.stdout)

    # Find the backup file
    backup_path = Path(TEST_BACKUP_DIR).resolve()
    backup_files = list(backup_path.glob(f"{PROD_DB_NAME}_incremental_*.sql.gz"))

    if not backup_files:
        logger.error("No incremental backup file found")
        return None

    # Get the latest backup file
    backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    backup_file = backup_files[0]

    logger.info(f"Incremental backup file: {backup_file}")
    return str(backup_file)

def restore_backup(backup_file):
    """Restore a backup to the test database."""
    # Convert to absolute path if not already
    backup_path = Path(backup_file).resolve()
    logger.info(f"Restoring backup to test database: {backup_path}")

    # Set environment variables for the restore
    os.environ["DB_NAME"] = TEST_DB_NAME

    start_time = time.time()

    # Run the enhanced restore script
    cmd = [
        "python", "enhanced_restore_database.py",
        "--backup-file", str(backup_path),
        "--create-db"
    ]

    process = subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    end_time = time.time()
    duration = end_time - start_time

    logger.info(f"Backup restored in {duration:.2f} seconds")
    logger.debug(process.stdout)

    # Reset environment variables
    os.environ["DB_NAME"] = PROD_DB_NAME

    return True

def verify_database_content():
    """Verify the content of the test database."""
    logger.info("Verifying database content")

    # Set environment variables for psql
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    # Compare record counts between production and test databases
    tables = ["cities", "attractions", "accommodations", "regions"]

    for table in tables:
        # Get production record count
        prod_cmd = [
            "psql",
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-U", DB_USER,
            "-d", PROD_DB_NAME,
            "-t",  # Tuple only output
            "-c", f"SELECT COUNT(*) FROM {table};"
        ]

        prod_process = subprocess.run(
            prod_cmd,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        prod_count = int(prod_process.stdout.strip())

        # Get test record count
        test_cmd = [
            "psql",
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-U", DB_USER,
            "-d", TEST_DB_NAME,
            "-t",  # Tuple only output
            "-c", f"SELECT COUNT(*) FROM {table};"
        ]

        test_process = subprocess.run(
            test_cmd,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        test_count = int(test_process.stdout.strip())

        # Compare counts
        if prod_count == test_count:
            logger.info(f"Table {table}: Record counts match ({prod_count})")
        else:
            logger.error(f"Table {table}: Record counts differ (Prod: {prod_count}, Test: {test_count})")
            return False

    logger.info("Database content verification successful")
    return True

def calculate_compression_ratio(backup_file):
    """Calculate the compression ratio of a backup file."""
    backup_path = Path(backup_file)
    compressed_size = backup_path.stat().st_size

    # Get the uncompressed size by running pg_dump without compression
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    with tempfile.NamedTemporaryFile() as temp_file:
        cmd = [
            "pg_dump",
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-U", DB_USER,
            "-F", "p",  # Plain text format
            "-f", temp_file.name,
            PROD_DB_NAME
        ]

        subprocess.run(
            cmd,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        uncompressed_size = os.path.getsize(temp_file.name)

    compression_ratio = uncompressed_size / compressed_size if compressed_size > 0 else 0

    logger.info(f"Backup file: {backup_file}")
    logger.info(f"Compressed size: {compressed_size / (1024 * 1024):.2f} MB")
    logger.info(f"Uncompressed size: {uncompressed_size / (1024 * 1024):.2f} MB")
    logger.info(f"Compression ratio: {compression_ratio:.2f}x")

    return compression_ratio

def main():
    """Main function to test backup and restore functionality."""
    parser = argparse.ArgumentParser(description="Test database backup and restore functionality")
    parser.add_argument("--skip-cleanup", action="store_true", help="Skip cleanup of test environment")
    parser.add_argument("--force-cleanup", action="store_true", help="Force cleanup even on failure")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info("Starting backup and restore test")

    # Track test environment details for reporting
    test_env = {
        "backup_dir": os.path.abspath(TEST_BACKUP_DIR),
        "test_db": TEST_DB_NAME,
        "backups": []
    }

    try:
        # Set up test environment
        logger.info("Setting up test environment")
        test_backup_path = setup_test_environment()
        logger.info(f"Test backup directory: {test_backup_path}")

        # Create full backup
        logger.info("Creating full backup")
        full_backup = create_full_backup()
        if not full_backup:
            logger.error("Failed to create full backup")
            raise Exception("Full backup creation failed")

        logger.info(f"Full backup created: {full_backup}")
        test_env["backups"].append({"type": "full", "path": full_backup})

        # Calculate compression ratio
        ratio = calculate_compression_ratio(full_backup)
        logger.info(f"Compression ratio: {ratio:.2f}x")

        # Create incremental backup
        logger.info("Creating incremental backup")
        incremental_backup = create_incremental_backup()
        if not incremental_backup:
            logger.warning("Failed to create incremental backup, using full backup for testing")
            incremental_backup = full_backup
        else:
            logger.info(f"Incremental backup created: {incremental_backup}")
            test_env["backups"].append({"type": "incremental", "path": incremental_backup})

        # Restore full backup
        logger.info(f"Restoring full backup to test database: {TEST_DB_NAME}")
        if not restore_backup(full_backup):
            logger.error("Failed to restore full backup")
            raise Exception("Full backup restore failed")

        logger.info("Full backup restored successfully")

        # Verify database content
        logger.info("Verifying database content after full backup restore")
        if not verify_database_content():
            logger.error("Database content verification failed after full backup restore")
            raise Exception("Database verification failed after full backup restore")

        logger.info("Database content verified successfully after full backup restore")

        # Restore incremental backup
        logger.info(f"Restoring incremental backup to test database: {TEST_DB_NAME}")
        if not restore_backup(incremental_backup):
            logger.error("Failed to restore incremental backup")
            raise Exception("Incremental backup restore failed")

        logger.info("Incremental backup restored successfully")

        # Verify database content again
        logger.info("Verifying database content after incremental backup restore")
        if not verify_database_content():
            logger.error("Database content verification failed after incremental restore")
            raise Exception("Database verification failed after incremental backup restore")

        logger.info("Database content verified successfully after incremental backup restore")

        logger.info("Backup and restore test completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Error during backup and restore test: {e}")

        # Print test environment details for debugging
        logger.error("Test environment details:")
        for key, value in test_env.items():
            if key == "backups":
                logger.error(f"  {key}:")
                for backup in value:
                    logger.error(f"    - {backup['type']}: {backup['path']}")
            else:
                logger.error(f"  {key}: {value}")

        logger.error("To debug, examine the test environment and run manual tests")
        logger.error(f"Test backup directory: {test_env['backup_dir']}")
        logger.error(f"Test database: {test_env['test_db']}")

        return 1

    finally:
        # Clean up test environment based on flags
        if args.force_cleanup:
            logger.info("Forcing cleanup of test environment")
            cleanup_test_environment()
        elif args.skip_cleanup:
            logger.info("Skipping cleanup of test environment")
            logger.info(f"Test backup directory: {test_env['backup_dir']}")
            logger.info(f"Test database: {test_env['test_db']}")
        else:
            # Only clean up if test was successful
            if 'e' not in locals():
                logger.info("Cleaning up test environment")
                cleanup_test_environment()
            else:
                logger.info("Test failed, preserving test environment for debugging")
                logger.info(f"Test backup directory: {test_env['backup_dir']}")
                logger.info(f"Test database: {test_env['test_db']}")

if __name__ == "__main__":
    sys.exit(main())
