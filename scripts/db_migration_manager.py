#!/usr/bin/env python
"""
Database Migration Manager

This script implements a proper migration versioning system to track and manage database schema changes.
It provides:
1. Migration tracking table to record applied migrations
2. Automatic migration discovery and execution
3. Forward and rollback migration support
4. Migration dependency resolution
5. Dry-run capability to preview changes
6. Validation of migration integrity

Usage:
    python db_migration_manager.py [--action ACTION] [--migration NAME] [--dry-run]

Actions:
    status      - Show migration status
    migrate     - Apply pending migrations
    rollback    - Rollback the last migration
    create      - Create a new migration file
"""

import os
import sys
import re
import glob
import time
import logging
import argparse
import json
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('db_migration.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_NAME = os.environ.get("DB_NAME", "egypt_chatbot")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")

# Migration directory
MIGRATIONS_DIR = "migrations"

def get_postgres_uri():
    """Get PostgreSQL connection URI"""
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def connect_to_database():
    """Connect to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(get_postgres_uri())
        conn.autocommit = False  # We want transactions for migrations
        logger.info(f"Connected to database: {DB_NAME}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def ensure_migration_table(conn):
    """Ensure the migration tracking table exists"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(255) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    checksum VARCHAR(64) NOT NULL,
                    execution_time FLOAT NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'success',
                    metadata JSONB
                );
                
                CREATE INDEX IF NOT EXISTS idx_schema_migrations_version ON schema_migrations(version);
            """)
            conn.commit()
            logger.info("Migration tracking table ensured")
            return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create migration tracking table: {e}")
        return False

def get_applied_migrations(conn):
    """Get list of applied migrations"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT version, name, applied_at, checksum, status
                FROM schema_migrations
                ORDER BY version ASC
            """)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Failed to get applied migrations: {e}")
        return []

def get_available_migrations():
    """Get list of available migration files"""
    if not os.path.exists(MIGRATIONS_DIR):
        os.makedirs(MIGRATIONS_DIR)
        
    # Find all SQL migration files
    migration_files = glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql"))
    
    migrations = []
    for file_path in migration_files:
        file_name = os.path.basename(file_path)
        match = re.match(r"^(\d{8})_(.+)\.sql$", file_name)
        if match:
            version = match.group(1)
            name = match.group(2)
            
            # Calculate checksum
            with open(file_path, "rb") as f:
                content = f.read()
                checksum = hashlib.sha256(content).hexdigest()
            
            migrations.append({
                "version": version,
                "name": name,
                "file_path": file_path,
                "checksum": checksum
            })
    
    # Sort by version
    migrations.sort(key=lambda m: m["version"])
    
    return migrations

def get_pending_migrations(conn):
    """Get list of pending migrations"""
    applied = get_applied_migrations(conn)
    available = get_available_migrations()
    
    # Create a set of applied versions
    applied_versions = {m["version"] for m in applied}
    
    # Filter out migrations that have already been applied
    pending = [m for m in available if m["version"] not in applied_versions]
    
    return pending

def apply_migration(conn, migration, dry_run=False):
    """Apply a single migration"""
    version = migration["version"]
    name = migration["name"]
    file_path = migration["file_path"]
    checksum = migration["checksum"]
    
    logger.info(f"Applying migration {version}_{name}")
    
    if dry_run:
        logger.info(f"DRY RUN: Would apply migration {version}_{name}")
        with open(file_path, "r") as f:
            sql = f.read()
            logger.info(f"SQL to execute:\n{sql}")
        return True
    
    try:
        # Read migration SQL
        with open(file_path, "r") as f:
            sql = f.read()
        
        # Start transaction
        start_time = time.time()
        
        with conn.cursor() as cursor:
            # Execute migration SQL
            cursor.execute(sql)
            
            # Record migration
            cursor.execute("""
                INSERT INTO schema_migrations
                (version, name, applied_at, checksum, execution_time, status, metadata)
                VALUES (%s, %s, NOW(), %s, %s, %s, %s)
            """, (
                version, 
                name, 
                checksum, 
                time.time() - start_time,
                "success",
                json.dumps({"applied_by": os.getenv("USER", "unknown")})
            ))
        
        # Commit transaction
        conn.commit()
        
        logger.info(f"Successfully applied migration {version}_{name}")
        return True
        
    except Exception as e:
        # Rollback transaction
        conn.rollback()
        
        logger.error(f"Failed to apply migration {version}_{name}: {e}")
        return False

def rollback_migration(conn, migration, dry_run=False):
    """Rollback a single migration"""
    version = migration["version"]
    name = migration["name"]
    
    logger.info(f"Rolling back migration {version}_{name}")
    
    if dry_run:
        logger.info(f"DRY RUN: Would rollback migration {version}_{name}")
        return True
    
    # Check if there's a rollback file
    rollback_file = os.path.join(MIGRATIONS_DIR, f"{version}_{name}_rollback.sql")
    
    if not os.path.exists(rollback_file):
        logger.error(f"Rollback file not found: {rollback_file}")
        return False
    
    try:
        # Read rollback SQL
        with open(rollback_file, "r") as f:
            sql = f.read()
        
        # Start transaction
        with conn.cursor() as cursor:
            # Execute rollback SQL
            cursor.execute(sql)
            
            # Remove migration record
            cursor.execute("""
                DELETE FROM schema_migrations
                WHERE version = %s
            """, (version,))
        
        # Commit transaction
        conn.commit()
        
        logger.info(f"Successfully rolled back migration {version}_{name}")
        return True
        
    except Exception as e:
        # Rollback transaction
        conn.rollback()
        
        logger.error(f"Failed to rollback migration {version}_{name}: {e}")
        return False

def create_migration_file(name):
    """Create a new migration file"""
    if not os.path.exists(MIGRATIONS_DIR):
        os.makedirs(MIGRATIONS_DIR)
    
    # Generate version based on current date
    version = datetime.now().strftime("%Y%m%d")
    
    # Clean name (remove spaces, special chars)
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
    
    # Find the highest numbered migration for today
    existing = glob.glob(os.path.join(MIGRATIONS_DIR, f"{version}_*.sql"))
    if existing:
        # Extract numbers and find the highest
        numbers = [int(re.search(r'_(\d+)_', os.path.basename(f)).group(1)) if re.search(r'_(\d+)_', os.path.basename(f)) else 0 for f in existing]
        next_number = max(numbers) + 1 if numbers else 1
        version = f"{version}_{next_number:02d}"
    
    # Create migration file
    file_path = os.path.join(MIGRATIONS_DIR, f"{version}_{clean_name}.sql")
    rollback_path = os.path.join(MIGRATIONS_DIR, f"{version}_{clean_name}_rollback.sql")
    
    with open(file_path, "w") as f:
        f.write(f"""-- Migration: {name}
-- Version: {version}
-- Created: {datetime.now().isoformat()}

-- Write your migration SQL here

""")
    
    with open(rollback_path, "w") as f:
        f.write(f"""-- Rollback for Migration: {name}
-- Version: {version}
-- Created: {datetime.now().isoformat()}

-- Write your rollback SQL here

""")
    
    logger.info(f"Created migration files:")
    logger.info(f"  - {file_path}")
    logger.info(f"  - {rollback_path}")
    
    return file_path, rollback_path

def show_migration_status(conn):
    """Show migration status"""
    applied = get_applied_migrations(conn)
    available = get_available_migrations()
    
    # Create a dictionary of applied migrations by version
    applied_dict = {m["version"]: m for m in applied}
    
    # Print status table
    logger.info("Migration Status:")
    logger.info("--------------------------------------------------------------------------------")
    logger.info("| Version    | Name                 | Status   | Applied At          | Checksum |")
    logger.info("--------------------------------------------------------------------------------")
    
    for migration in available:
        version = migration["version"]
        name = migration["name"]
        checksum = migration["checksum"][:8]  # Show first 8 chars
        
        if version in applied_dict:
            applied_migration = applied_dict[version]
            status = applied_migration["status"]
            applied_at = applied_migration["applied_at"].strftime("%Y-%m-%d %H:%M:%S")
            applied_checksum = applied_migration["checksum"][:8]
            
            # Check if checksums match
            checksum_status = "✓" if checksum == applied_migration["checksum"] else "✗"
            
            logger.info(f"| {version:<10} | {name:<20} | {status:<8} | {applied_at:<19} | {applied_checksum} {checksum_status} |")
        else:
            logger.info(f"| {version:<10} | {name:<20} | PENDING  | -                  | {checksum} |")
    
    logger.info("--------------------------------------------------------------------------------")
    
    # Summary
    logger.info(f"Total migrations: {len(available)}")
    logger.info(f"Applied migrations: {len(applied)}")
    logger.info(f"Pending migrations: {len(available) - len(applied)}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Database Migration Manager")
    parser.add_argument("--action", choices=["status", "migrate", "rollback", "create"], default="status",
                        help="Action to perform")
    parser.add_argument("--migration", help="Migration name (for create) or version (for rollback)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (don't actually apply changes)")
    
    args = parser.parse_args()
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return 1
    
    try:
        # Ensure migration table exists
        if not ensure_migration_table(conn):
            return 1
        
        # Perform requested action
        if args.action == "status":
            show_migration_status(conn)
            
        elif args.action == "migrate":
            pending = get_pending_migrations(conn)
            
            if not pending:
                logger.info("No pending migrations")
                return 0
            
            logger.info(f"Found {len(pending)} pending migrations")
            
            for migration in pending:
                if not apply_migration(conn, migration, args.dry_run):
                    return 1
            
            logger.info("All migrations applied successfully")
            
        elif args.action == "rollback":
            applied = get_applied_migrations(conn)
            
            if not applied:
                logger.info("No migrations to rollback")
                return 0
            
            # Get the last applied migration
            last_migration = applied[-1]
            version = last_migration["version"]
            name = last_migration["name"]
            
            # If specific version provided, find that migration
            if args.migration:
                found = False
                for migration in reversed(applied):
                    if migration["version"] == args.migration:
                        last_migration = migration
                        version = last_migration["version"]
                        name = last_migration["name"]
                        found = True
                        break
                
                if not found:
                    logger.error(f"Migration version {args.migration} not found or not applied")
                    return 1
            
            # Find the migration file
            available = get_available_migrations()
            migration_file = next((m for m in available if m["version"] == version), None)
            
            if not migration_file:
                logger.error(f"Migration file for version {version} not found")
                return 1
            
            if not rollback_migration(conn, migration_file, args.dry_run):
                return 1
            
            logger.info(f"Successfully rolled back migration {version}_{name}")
            
        elif args.action == "create":
            if not args.migration:
                logger.error("Migration name is required for create action")
                return 1
            
            create_migration_file(args.migration)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    sys.exit(main())
