#!/usr/bin/env python3
"""
Run the enhance attractions table migration.

This script:
1. Runs the enhance attractions table migration in parts
2. Verifies the migration was successful
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_postgres_uri():
    """Get PostgreSQL connection URI from environment or use default"""
    return os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")

def connect_to_db():
    """Connect to PostgreSQL database"""
    postgres_uri = get_postgres_uri()
    logger.info(f"Connecting to PostgreSQL database")
    conn = psycopg2.connect(postgres_uri)
    conn.autocommit = False
    return conn

def backup_database():
    """Create a backup of the database before migration"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backups/enhance_attractions_migration_backup_{timestamp}.sql"
        
        # Create backups directory if it doesn't exist
        os.makedirs("backups", exist_ok=True)
        
        # Get database connection parameters from URI
        postgres_uri = get_postgres_uri()
        uri_parts = postgres_uri.replace("postgresql://", "").split("/")
        db_name = uri_parts[1]
        auth_host = uri_parts[0].split("@")
        host = auth_host[1] if len(auth_host) > 1 else auth_host[0]
        auth = auth_host[0].split(":") if len(auth_host) > 1 else ["", ""]
        user = auth[0]
        password = auth[1] if len(auth) > 1 else ""
        
        # Set PGPASSWORD environment variable for pg_dump
        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password
        
        # Run pg_dump
        cmd = [
            "pg_dump",
            "-h", host,
            "-U", user,
            "-d", db_name,
            "-f", backup_file
        ]
        
        logger.info(f"Creating database backup: {backup_file}")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Database backup created successfully: {backup_file}")
            return True
        else:
            logger.error(f"Failed to create database backup: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Error creating database backup: {str(e)}")
        return False

def run_migration(conn):
    """Run the enhance attractions table migration"""
    try:
        migration_files = [
            "migrations/20240628_enhance_attractions_table_part1.sql",
            "migrations/20240628_enhance_attractions_table_part2.sql",
            "migrations/20240628_enhance_attractions_table_part3.sql",
            "migrations/20240628_enhance_attractions_table_part4.sql"
        ]
        
        for migration_file in migration_files:
            logger.info(f"Running migration: {migration_file}")
            
            # Read migration SQL
            with open(migration_file, "r") as f:
                migration_sql = f.read()
            
            # Execute migration
            with conn.cursor() as cursor:
                cursor.execute(migration_sql)
            
            conn.commit()
            logger.info(f"Migration {migration_file} completed successfully")
        
        # Record migration in schema_migrations table
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status, metadata)
                VALUES (%s, %s, NOW(), %s, %s, %s, %s)
            """, (
                "20240628",
                "enhance_attractions_table",
                "migration_checksum",
                0.0,  # Execution time will be updated later
                "success",
                '{"description": "Enhance attractions table with subcategories, visiting info, accessibility info, related attractions, and historical context"}'
            ))
        
        conn.commit()
        logger.info("Migration recorded in schema_migrations table")
        
        return True
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error running migration: {str(e)}")
        return False

def verify_migration(conn):
    """Verify the migration was successful"""
    try:
        # Check if attraction_subcategories table exists
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'attraction_subcategories'
                ) AS attraction_subcategories_exists
            """)
            result = cursor.fetchone()
            
            if not result['attraction_subcategories_exists']:
                logger.error("Migration verification failed: attraction_subcategories table does not exist")
                return False
            
            # Check if subcategories were added
            cursor.execute("SELECT COUNT(*) as count FROM attraction_subcategories")
            result = cursor.fetchone()
            subcategory_count = result['count']
            
            if subcategory_count == 0:
                logger.error("Migration verification failed: no subcategories were added")
                return False
            
            logger.info(f"Found {subcategory_count} attraction subcategories")
            
            # Check if new columns were added to attractions table
            cursor.execute("""
                SELECT 
                    column_name 
                FROM 
                    information_schema.columns 
                WHERE 
                    table_name = 'attractions' 
                    AND column_name IN (
                        'subcategory_id', 
                        'visiting_info', 
                        'accessibility_info',
                        'related_attractions',
                        'historical_context'
                    )
            """)
            columns = cursor.fetchall()
            
            if len(columns) < 5:
                logger.error(f"Migration verification failed: not all columns were added. Found {len(columns)} of 5 expected columns")
                return False
            
            # Check if find_related_attractions function exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_proc
                    WHERE proname = 'find_related_attractions'
                ) AS function_exists
            """)
            result = cursor.fetchone()
            
            if not result['function_exists']:
                logger.error("Migration verification failed: find_related_attractions function does not exist")
                return False
            
            logger.info("Migration verification successful")
            return True
    
    except Exception as e:
        logger.error(f"Error verifying migration: {str(e)}")
        return False

def main():
    """Main function to run the migration"""
    try:
        # Connect to database
        conn = connect_to_db()
        
        # Create a backup
        if not backup_database():
            logger.warning("Failed to create database backup, proceeding with caution")
        
        # Run migration
        if not run_migration(conn):
            logger.error("Migration failed")
            return False
        
        # Verify migration
        if not verify_migration(conn):
            logger.error("Migration verification failed")
            return False
        
        logger.info("Enhance attractions table migration completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error running enhance attractions migration: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = main()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
