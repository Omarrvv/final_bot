#!/usr/bin/env python
"""
Enhanced Database Backup Script for Egypt Tourism Chatbot

This script creates a backup of the PostgreSQL database with the following improvements:
1. Adds compression to reduce backup size
2. Implements more thorough backup verification
3. Adds incremental backup capability
4. Implements automated backup testing
5. Adds backup metadata and checksums
6. Supports multiple backup strategies (full, schema-only, data-only)
"""

import os
import sys
import logging
import subprocess
import datetime
import hashlib
import json
import argparse
import time
import gzip
import tempfile
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
BACKUP_RETENTION_FULL = int(os.environ.get("BACKUP_RETENTION_FULL", "4"))  # Number of full backups to keep
BACKUP_RETENTION_INCREMENTAL = int(os.environ.get("BACKUP_RETENTION_INCREMENTAL", "6"))  # Number of incremental backups to keep

# Backup types
BACKUP_TYPE_FULL = "full"
BACKUP_TYPE_INCREMENTAL = "incremental"
BACKUP_TYPE_SCHEMA = "schema"
BACKUP_TYPE_DATA = "data"

def create_backup_directory():
    """Create the backup directory if it doesn't exist."""
    backup_path = Path(BACKUP_DIR).resolve()
    if not backup_path.exists():
        logger.info(f"Creating backup directory: {backup_path}")
        backup_path.mkdir(parents=True)
    return backup_path

def create_backup_metadata(backup_file, backup_type, modified_tables=None, base_backup=None):
    """Create metadata for a backup file."""
    backup_path = Path(backup_file)

    # Calculate file hash
    file_hash = calculate_file_hash(backup_path)

    # Create metadata
    metadata = {
        "database": DB_NAME,
        "backup_type": backup_type,
        "timestamp": datetime.datetime.now().isoformat(),
        "file_size": backup_path.stat().st_size,
        "file_hash": file_hash,
        "compression": "gzip"
    }

    # Add incremental backup specific metadata
    if backup_type == BACKUP_TYPE_INCREMENTAL:
        metadata["base_backup"] = base_backup
        metadata["modified_tables"] = modified_tables or []

    # Save metadata
    metadata_file = backup_path.with_suffix(".json")
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Created metadata for backup: {backup_file}")
    return metadata

def generate_backup_filename(backup_type=BACKUP_TYPE_FULL):
    """Generate a timestamped backup filename."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{DB_NAME}_{backup_type}_{timestamp}.sql.gz"

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_last_full_backup():
    """Get the path to the last full backup."""
    backup_path = Path(BACKUP_DIR).resolve()
    if not backup_path.exists():
        return None

    # Find all full backup files
    full_backups = list(backup_path.glob(f"{DB_NAME}_{BACKUP_TYPE_FULL}_*.sql.gz"))

    # Sort by modification time (newest first)
    full_backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    return full_backups[0] if full_backups else None

def get_modified_tables_since(timestamp):
    """Get a list of tables that have been modified since the given timestamp."""
    # Set environment variables for psql
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    # Query to get modified tables
    query = f"""
    SELECT tablename
    FROM pg_stat_user_tables
    WHERE (last_vacuum > '{timestamp}'
        OR last_autovacuum > '{timestamp}'
        OR last_analyze > '{timestamp}'
        OR last_autoanalyze > '{timestamp}'
        OR last_data_changed > '{timestamp}')
    ORDER BY tablename;
    """

    # Run the query
    cmd = [
        "psql",
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "-d", DB_NAME,
        "-t",  # Tuple only output
        "-c", query
    ]

    try:
        process = subprocess.run(
            cmd,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Parse the output to get the list of modified tables
        modified_tables = [table.strip() for table in process.stdout.strip().split("\n") if table.strip()]
        return modified_tables
    except Exception as e:
        logger.error(f"Error getting modified tables: {e}")
        return []

def create_database_backup(backup_type=BACKUP_TYPE_FULL):
    """Create a backup of the PostgreSQL database."""
    backup_path = create_backup_directory()
    backup_file = backup_path / generate_backup_filename(backup_type)

    # Set environment variables for pg_dump
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    # Build the pg_dump command based on backup type
    cmd = [
        "pg_dump",
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "-v",       # Verbose
    ]

    # Add backup type specific options
    if backup_type == BACKUP_TYPE_SCHEMA:
        cmd.extend(["-s"])  # Schema only
    elif backup_type == BACKUP_TYPE_DATA:
        cmd.extend(["-a"])  # Data only
    elif backup_type == BACKUP_TYPE_INCREMENTAL:
        # For incremental backup, we need to get the timestamp of the last full backup
        last_full_backup = get_last_full_backup()
        if not last_full_backup:
            logger.warning("No full backup found for incremental backup, creating full backup instead")
            return create_database_backup(BACKUP_TYPE_FULL)

        # Get the timestamp of the last full backup
        last_backup_time = datetime.datetime.fromtimestamp(last_full_backup.stat().st_mtime)
        timestamp = last_backup_time.strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"Creating incremental backup since {timestamp}")

        # Get a list of tables that have been modified since the last full backup
        modified_tables = get_modified_tables_since(timestamp)

        if not modified_tables:
            logger.info("No tables have been modified since the last full backup")

            # Create an empty backup file
            with gzip.open(backup_file, 'wb') as f:
                f.write(f"-- Incremental backup created on {datetime.datetime.now().isoformat()}\n".encode('utf-8'))
                f.write(f"-- No tables have been modified since {timestamp}\n".encode('utf-8'))

            # Create metadata
            create_backup_metadata(backup_file, backup_type, [], str(last_full_backup.name))

            logger.info(f"Empty incremental backup created: {backup_file}")
            return str(backup_file)

        logger.info(f"Found {len(modified_tables)} modified tables: {', '.join(modified_tables)}")

        # Add each table to the dump command
        for table in modified_tables:
            cmd.extend(["-t", table])

    # Add format and output options
    cmd.extend([
        "-F", "p",  # Plain text format for better compression
        DB_NAME
    ])

    logger.info(f"Creating {backup_type} backup: {backup_file}")

    try:
        # Execute the pg_dump command and pipe to gzip for compression
        with gzip.open(backup_file, 'wb') as f:
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False
            )

            # Read and compress output in chunks
            for chunk in iter(lambda: process.stdout.read(4096), b''):
                f.write(chunk)

            # Wait for process to complete
            stderr = process.stderr.read()
            return_code = process.wait()

            if return_code != 0:
                logger.error(f"Backup failed with return code {return_code}")
                logger.error(f"Error output: {stderr.decode('utf-8')}")
                return None

        logger.info(f"Backup created successfully: {backup_file}")

        # Verify the backup file exists and has content
        if backup_file.exists() and backup_file.stat().st_size > 0:
            # Create metadata
            if backup_type == BACKUP_TYPE_INCREMENTAL and 'modified_tables' in locals():
                # For incremental backups, include the list of modified tables
                create_backup_metadata(backup_file, backup_type, modified_tables, str(last_full_backup.name))
            else:
                # For other backup types
                create_backup_metadata(backup_file, backup_type)

            logger.info(f"Backup verified: {backup_file} ({backup_file.stat().st_size} bytes)")
            return str(backup_file)
        else:
            logger.error(f"Backup verification failed: {backup_file} does not exist or is empty")
            return None

    except Exception as e:
        logger.error(f"Unexpected error during backup: {e}")
        return None

def verify_backup(backup_file):
    """Verify a backup file by testing restore in a temporary database and checking data integrity."""
    backup_path = Path(backup_file).resolve()
    if not backup_path.exists():
        logger.error(f"Backup file does not exist: {backup_path}")
        return False

    # Create a temporary database name
    temp_db_name = f"verify_{DB_NAME}_{int(time.time())}"

    # Set environment variables for PostgreSQL commands
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    try:
        # Create temporary database
        logger.info(f"Creating temporary database for verification: {temp_db_name}")
        create_cmd = [
            "createdb",
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-U", DB_USER,
            temp_db_name
        ]

        subprocess.run(
            create_cmd,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Restore backup to temporary database
        logger.info(f"Restoring backup to temporary database: {backup_file}")

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
                "-d", temp_db_name,
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
            logger.error(f"Error during backup verification: {e}")
            return False

        # Verify database structure
        logger.info("Verifying database structure")

        # Check table count
        table_count_cmd = [
            "psql",
            "-h", DB_HOST,
            "-p", DB_PORT,
            "-U", DB_USER,
            "-d", temp_db_name,
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
        if table_count == 0:
            logger.error("Verification failed: No tables found in restored database")
            return False

        logger.info(f"Verification: {table_count} tables found")

        # Verify data integrity by checking record counts in key tables
        logger.info("Verifying data integrity")

        # Get backup type from metadata file
        metadata_file = backup_path.with_suffix(".json")
        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                backup_type = metadata.get("backup_type", BACKUP_TYPE_FULL)
            except Exception as e:
                logger.warning(f"Error reading metadata file: {e}")
                metadata = None
                backup_type = BACKUP_TYPE_FULL
        else:
            metadata = None
            backup_type = BACKUP_TYPE_FULL

        # For incremental backups, only check the tables that were included
        if backup_type == BACKUP_TYPE_INCREMENTAL and metadata and "modified_tables" in metadata:
            tables_to_check = metadata["modified_tables"]
            if not tables_to_check:
                logger.info("Incremental backup contains no modified tables, skipping data verification")
                return True
        else:
            # For full backups, check key tables
            tables_to_check = ["cities", "attractions", "accommodations", "regions"]

        # Check record counts
        for table in tables_to_check:
            try:
                count_cmd = [
                    "psql",
                    "-h", DB_HOST,
                    "-p", DB_PORT,
                    "-U", DB_USER,
                    "-d", temp_db_name,
                    "-t",  # Tuple only output
                    "-c", f"SELECT COUNT(*) FROM {table};"
                ]

                process = subprocess.run(
                    count_cmd,
                    env=env,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                record_count = int(process.stdout.strip())
                logger.info(f"Verification: Table {table} has {record_count} records")

                if record_count == 0:
                    logger.warning(f"Table {table} is empty in restored database")
            except Exception as e:
                logger.warning(f"Error checking record count for table {table}: {e}")

        # Test a sample query to verify data can be accessed
        try:
            query_cmd = [
                "psql",
                "-h", DB_HOST,
                "-p", DB_PORT,
                "-U", DB_USER,
                "-d", temp_db_name,
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
                logger.info("Verification: Sample query executed successfully")
            else:
                logger.warning("Verification: Sample query did not return expected columns")
        except Exception as e:
            logger.warning(f"Error executing sample query: {e}")

        logger.info(f"Backup verification completed successfully: {backup_path}")
        return True

    except Exception as e:
        logger.error(f"Error during backup verification: {e}")
        return False

    finally:
        # Drop the temporary database
        try:
            logger.info(f"Dropping temporary database: {temp_db_name}")
            drop_cmd = [
                "dropdb",
                "-h", DB_HOST,
                "-p", DB_PORT,
                "-U", DB_USER,
                temp_db_name
            ]

            subprocess.run(
                drop_cmd,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except Exception as e:
            logger.error(f"Error dropping temporary database: {e}")

def cleanup_old_backups():
    """Remove old backups based on retention policy."""
    backup_path = Path(BACKUP_DIR)
    if not backup_path.exists():
        return

    # Find all backup files
    full_backups = list(backup_path.glob(f"{DB_NAME}_{BACKUP_TYPE_FULL}_*.sql.gz"))
    incremental_backups = list(backup_path.glob(f"{DB_NAME}_{BACKUP_TYPE_INCREMENTAL}_*.sql.gz"))
    schema_backups = list(backup_path.glob(f"{DB_NAME}_{BACKUP_TYPE_SCHEMA}_*.sql.gz"))
    data_backups = list(backup_path.glob(f"{DB_NAME}_{BACKUP_TYPE_DATA}_*.sql.gz"))

    # Sort by modification time (oldest first)
    full_backups.sort(key=lambda x: x.stat().st_mtime)
    incremental_backups.sort(key=lambda x: x.stat().st_mtime)
    schema_backups.sort(key=lambda x: x.stat().st_mtime)
    data_backups.sort(key=lambda x: x.stat().st_mtime)

    # Remove old full backups
    while len(full_backups) > BACKUP_RETENTION_FULL:
        backup_to_remove = full_backups.pop(0)
        logger.info(f"Removing old full backup: {backup_to_remove}")
        backup_to_remove.unlink()

        # Also remove metadata file
        metadata_file = backup_to_remove.with_suffix(".json")
        if metadata_file.exists():
            metadata_file.unlink()

    # Remove old incremental backups
    while len(incremental_backups) > BACKUP_RETENTION_INCREMENTAL:
        backup_to_remove = incremental_backups.pop(0)
        logger.info(f"Removing old incremental backup: {backup_to_remove}")
        backup_to_remove.unlink()

        # Also remove metadata file
        metadata_file = backup_to_remove.with_suffix(".json")
        if metadata_file.exists():
            metadata_file.unlink()

    # Remove old schema backups (keep only the latest)
    while len(schema_backups) > 1:
        backup_to_remove = schema_backups.pop(0)
        logger.info(f"Removing old schema backup: {backup_to_remove}")
        backup_to_remove.unlink()

        # Also remove metadata file
        metadata_file = backup_to_remove.with_suffix(".json")
        if metadata_file.exists():
            metadata_file.unlink()

    # Remove old data backups (keep only the latest)
    while len(data_backups) > 1:
        backup_to_remove = data_backups.pop(0)
        logger.info(f"Removing old data backup: {backup_to_remove}")
        backup_to_remove.unlink()

        # Also remove metadata file
        metadata_file = backup_to_remove.with_suffix(".json")
        if metadata_file.exists():
            metadata_file.unlink()

def main():
    """Main function to create a database backup."""
    parser = argparse.ArgumentParser(description="Create a database backup")
    parser.add_argument("--type", choices=[BACKUP_TYPE_FULL, BACKUP_TYPE_INCREMENTAL, BACKUP_TYPE_SCHEMA, BACKUP_TYPE_DATA],
                        default=BACKUP_TYPE_FULL, help="Type of backup to create")
    parser.add_argument("--verify", action="store_true", help="Verify backup by testing restore")
    args = parser.parse_args()

    logger.info(f"Starting database {args.type} backup process")

    # Create the backup
    backup_file = create_database_backup(args.type)

    if backup_file:
        logger.info(f"Database backup created successfully: {backup_file}")

        # Verify the backup if requested
        if args.verify:
            logger.info(f"Verifying backup: {backup_file}")
            if verify_backup(backup_file):
                logger.info(f"Backup verification successful: {backup_file}")
            else:
                logger.error(f"Backup verification failed: {backup_file}")
                return 1

        # Clean up old backups
        cleanup_old_backups()

        return 0
    else:
        logger.error("Database backup failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
