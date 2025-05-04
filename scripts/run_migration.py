#!/usr/bin/env python3
"""
Run SQL migration script for Egypt Tourism Chatbot
"""

import os
import sys
import psycopg2
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_postgres_uri():
    """Get PostgreSQL URI from environment or use default"""
    return os.environ.get(
        "POSTGRES_URI", 
        "postgresql://postgres:postgres@localhost:5432/egypt_chatbot"
    )

def run_migration(migration_file):
    """Run a SQL migration file"""
    postgres_uri = get_postgres_uri()
    
    try:
        # Connect to PostgreSQL
        logger.info(f"Connecting to PostgreSQL database")
        conn = psycopg2.connect(postgres_uri)
        conn.autocommit = True
        
        # Read migration file
        logger.info(f"Reading migration file: {migration_file}")
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        # Execute migration
        logger.info(f"Executing migration")
        with conn.cursor() as cursor:
            cursor.execute(sql)
        
        logger.info(f"Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error running migration: {str(e)}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

def verify_migration():
    """Verify that the migration was successful"""
    postgres_uri = get_postgres_uri()
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(postgres_uri)
        
        # Check if JSONB columns exist
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name IN ('attractions', 'restaurants', 'accommodations')
                AND column_name IN ('name', 'description')
                AND data_type = 'jsonb'
            """)
            columns = cursor.fetchall()
            
            if len(columns) == 6:  # 2 columns for each of 3 tables
                logger.info("✅ All JSONB columns were created successfully")
                for table, column, data_type in columns:
                    logger.info(f"  - {table}.{column} ({data_type})")
            else:
                logger.warning(f"⚠️ Only {len(columns)} of 6 expected JSONB columns were found")
                for table, column, data_type in columns:
                    logger.info(f"  - {table}.{column} ({data_type})")
        
        # Check if data was migrated
        tables = ['attractions', 'restaurants', 'accommodations']
        for table in tables:
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table} WHERE name IS NOT NULL
                """)
                count = cursor.fetchone()[0]
                logger.info(f"✅ {table}: {count} rows have data in the name JSONB column")
        
    except Exception as e:
        logger.error(f"Error verifying migration: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Get migration file path
    if len(sys.argv) > 1:
        migration_file = sys.argv[1]
    else:
        # Default to the latest migration
        migration_file = "migrations/20240530_add_jsonb_columns.sql"
    
    # Run migration
    run_migration(migration_file)
    
    # Verify migration
    verify_migration()
