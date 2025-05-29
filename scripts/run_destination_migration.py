#!/usr/bin/env python3
"""
Run the destination schema migration and data generation.

This script:
1. Runs the destination schema migration
2. Generates destination data
3. Verifies the migration and data generation
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
        backup_file = f"backups/destination_migration_backup_{timestamp}.sql"
        
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
    """Run the destination schema migration"""
    try:
        migration_file = "migrations/20240622_create_destinations_table.sql"
        
        logger.info(f"Running migration: {migration_file}")
        
        # Read migration SQL
        with open(migration_file, "r") as f:
            migration_sql = f.read()
        
        # Execute migration
        with conn.cursor() as cursor:
            cursor.execute(migration_sql)
        
        conn.commit()
        logger.info("Migration completed successfully")
        
        # Record migration in schema_migrations table
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO schema_migrations (version, name, applied_at, checksum, execution_time, status, metadata)
                VALUES (%s, %s, NOW(), %s, %s, %s, %s)
            """, (
                "20240622",
                "create_destinations_table",
                "migration_checksum",
                0.0,  # Execution time will be updated later
                "success",
                '{"description": "Create destinations table with hierarchical structure for tourism locations"}'
            ))
        
        conn.commit()
        logger.info("Migration recorded in schema_migrations table")
        
        return True
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error running migration: {str(e)}")
        return False

def generate_destination_data():
    """Generate destination data"""
    try:
        logger.info("Generating destination data")
        
        # Run the destination data generation script
        cmd = [sys.executable, "scripts/generate_destination_data.py"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Destination data generation completed successfully")
            logger.info(result.stdout)
            return True
        else:
            logger.error(f"Failed to generate destination data: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Error generating destination data: {str(e)}")
        return False

def verify_migration(conn):
    """Verify the migration was successful"""
    try:
        # Check if destinations table exists
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'destinations'
                ) AS destinations_exists
            """)
            result = cursor.fetchone()
            
            if not result['destinations_exists']:
                logger.error("Migration verification failed: destinations table does not exist")
                return False
            
            # Check if destination_types table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'destination_types'
                ) AS destination_types_exists
            """)
            result = cursor.fetchone()
            
            if not result['destination_types_exists']:
                logger.error("Migration verification failed: destination_types table does not exist")
                return False
            
            # Check if destination_seasons table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'destination_seasons'
                ) AS destination_seasons_exists
            """)
            result = cursor.fetchone()
            
            if not result['destination_seasons_exists']:
                logger.error("Migration verification failed: destination_seasons table does not exist")
                return False
            
            # Check if indexes were created
            cursor.execute("""
                SELECT 
                    indexname 
                FROM 
                    pg_indexes 
                WHERE 
                    tablename = 'destinations' 
                    AND indexname IN (
                        'idx_destinations_type', 
                        'idx_destinations_parent_id', 
                        'idx_destinations_country',
                        'idx_destinations_name_gin',
                        'idx_destinations_description_gin',
                        'idx_destinations_data_gin',
                        'idx_destinations_embedding_hnsw'
                    )
            """)
            indexes = cursor.fetchall()
            
            if len(indexes) < 7:
                logger.error(f"Migration verification failed: not all indexes were created. Found {len(indexes)} of 7 expected indexes")
                return False
            
            logger.info("Migration verification successful")
            return True
    
    except Exception as e:
        logger.error(f"Error verifying migration: {str(e)}")
        return False

def main():
    """Main function to run the migration and data generation"""
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
        
        # Generate destination data
        if not generate_destination_data():
            logger.error("Destination data generation failed")
            return False
        
        logger.info("Destination schema migration and data generation completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error running destination migration: {str(e)}")
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
