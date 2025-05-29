#!/usr/bin/env python
"""
Run the migration to add JSONB columns to the regions table.

This script:
1. Runs the SQL migration script to add JSONB columns to the regions table
2. Verifies that the columns were added and populated correctly
3. Logs the results
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('regions_jsonb_migration.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_NAME = os.environ.get("DB_NAME", "egypt_chatbot")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")

def get_postgres_uri():
    """Get PostgreSQL connection URI"""
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def run_migration():
    """Run the migration script"""
    postgres_uri = get_postgres_uri()
    
    try:
        # Connect to PostgreSQL
        logger.info(f"Connecting to PostgreSQL database: {DB_NAME}")
        conn = psycopg2.connect(postgres_uri)
        conn.autocommit = True
        
        # Read migration file
        migration_file = "migrations/20250509_add_jsonb_columns_to_regions.sql"
        logger.info(f"Reading migration file: {migration_file}")
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        # Execute migration
        logger.info(f"Executing migration")
        with conn.cursor() as cursor:
            cursor.execute(sql)
        
        logger.info(f"Migration completed successfully")
        
        # Verify migration
        verify_migration(conn)
        
    except Exception as e:
        logger.error(f"Error running migration: {str(e)}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

def verify_migration(conn):
    """Verify that the migration was successful"""
    try:
        logger.info("Verifying migration")
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Check if JSONB columns exist
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'regions' AND column_name IN ('name', 'description')
            """)
            
            columns = cursor.fetchall()
            if len(columns) < 2:
                logger.error(f"❌ JSONB columns not found in regions table")
                return False
            
            for column in columns:
                if column['data_type'] != 'jsonb':
                    logger.error(f"❌ Column {column['column_name']} is not JSONB type (found {column['data_type']})")
                    return False
                
                logger.info(f"✅ Column {column['column_name']} exists with JSONB type")
            
            # Check if GIN indexes exist
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'regions' AND indexname IN ('idx_regions_name_jsonb', 'idx_regions_description_jsonb')
            """)
            
            indexes = cursor.fetchall()
            if len(indexes) < 2:
                logger.error(f"❌ GIN indexes not found for regions table")
                return False
            
            for index in indexes:
                logger.info(f"✅ Index {index['indexname']} exists: {index['indexdef']}")
            
            # Check if data was migrated
            cursor.execute("""
                SELECT COUNT(*) as total_count,
                       COUNT(CASE WHEN name IS NOT NULL AND jsonb_typeof(name) != 'null' THEN 1 END) as name_count,
                       COUNT(CASE WHEN description IS NOT NULL AND jsonb_typeof(description) != 'null' THEN 1 END) as desc_count
                FROM regions
            """)
            
            result = cursor.fetchone()
            total_count = result['total_count']
            name_count = result['name_count']
            desc_count = result['desc_count']
            
            logger.info(f"Total regions: {total_count}")
            logger.info(f"Regions with name JSONB: {name_count} ({name_count/total_count*100 if total_count > 0 else 0:.2f}%)")
            logger.info(f"Regions with description JSONB: {desc_count} ({desc_count/total_count*100 if total_count > 0 else 0:.2f}%)")
            
            if name_count < total_count:
                logger.warning(f"⚠️ Not all regions have name JSONB data")
            else:
                logger.info(f"✅ All regions have name JSONB data")
                
            if desc_count < total_count:
                logger.warning(f"⚠️ Not all regions have description JSONB data")
            else:
                logger.info(f"✅ All regions have description JSONB data")
            
            # Sample the data
            cursor.execute("""
                SELECT id, name, description
                FROM regions
                LIMIT 3
            """)
            
            samples = cursor.fetchall()
            logger.info("Sample data:")
            for sample in samples:
                logger.info(f"  ID: {sample['id']}")
                logger.info(f"  Name: {sample['name']}")
                logger.info(f"  Description: {sample['description']}")
            
            logger.info("Migration verification completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Error verifying migration: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting regions JSONB migration")
    run_migration()
    logger.info("Regions JSONB migration completed")
