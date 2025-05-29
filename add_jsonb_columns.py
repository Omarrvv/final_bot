#!/usr/bin/env python
"""
Add JSONB columns and GIN indexes for multilingual fields.
This script adds JSONB columns for name and description fields and creates GIN indexes for them.
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
        logging.FileHandler('logs/jsonb_columns.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_NAME = os.environ.get("DB_NAME", "egypt_chatbot_migration_test")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")

def get_connection():
    """Get a connection to the database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def check_jsonb_columns():
    """Check if JSONB columns exist."""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Check for JSONB columns in attractions table
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'attractions'
                AND column_name IN ('name', 'description');
            """)
            attractions_jsonb = cursor.fetchall()
            
            # Check for JSONB columns in accommodations table
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'accommodations'
                AND column_name IN ('name', 'description');
            """)
            accommodations_jsonb = cursor.fetchall()
            
            # Check for JSONB columns in cities table
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'cities'
                AND column_name IN ('name', 'description');
            """)
            cities_jsonb = cursor.fetchall()
            
            # Check for GIN indexes on JSONB columns
            cursor.execute("""
                SELECT tablename, indexname, indexdef
                FROM pg_indexes
                WHERE indexdef LIKE '%gin%'
                AND tablename IN ('attractions', 'accommodations', 'cities');
            """)
            gin_indexes = cursor.fetchall()
            
            return {
                "attractions_jsonb": attractions_jsonb,
                "accommodations_jsonb": accommodations_jsonb,
                "cities_jsonb": cities_jsonb,
                "gin_indexes": gin_indexes
            }
    except Exception as e:
        logger.error(f"Error checking JSONB columns: {e}")
        return None
    finally:
        conn.close()

def add_jsonb_columns():
    """Add JSONB columns and GIN indexes."""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            # Add JSONB columns to cities table
            cursor.execute("""
                ALTER TABLE cities
                ADD COLUMN IF NOT EXISTS name JSONB,
                ADD COLUMN IF NOT EXISTS description JSONB;
            """)
            
            # Create GIN indexes for JSONB columns in attractions table
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_attractions_name_jsonb
                ON attractions USING gin (name jsonb_path_ops);
                
                CREATE INDEX IF NOT EXISTS idx_attractions_description_jsonb
                ON attractions USING gin (description jsonb_path_ops);
            """)
            
            # Create GIN indexes for JSONB columns in accommodations table
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_accommodations_name_jsonb
                ON accommodations USING gin (name jsonb_path_ops);
                
                CREATE INDEX IF NOT EXISTS idx_accommodations_description_jsonb
                ON accommodations USING gin (description jsonb_path_ops);
            """)
            
            # Create GIN indexes for JSONB columns in cities table
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cities_name_jsonb
                ON cities USING gin (name jsonb_path_ops);
                
                CREATE INDEX IF NOT EXISTS idx_cities_description_jsonb
                ON cities USING gin (description jsonb_path_ops);
            """)
            
            # Commit the changes
            conn.commit()
            
            logger.info("Added JSONB columns and GIN indexes")
            return True
    except Exception as e:
        logger.error(f"Error adding JSONB columns: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def verify_jsonb_columns():
    """Verify that JSONB columns and GIN indexes exist."""
    result = check_jsonb_columns()
    if not result:
        return False
    
    # Check if all tables have JSONB columns
    attractions_jsonb_count = len(result["attractions_jsonb"])
    accommodations_jsonb_count = len(result["accommodations_jsonb"])
    cities_jsonb_count = len(result["cities_jsonb"])
    
    # Check if all tables have GIN indexes
    gin_indexes = result["gin_indexes"]
    attractions_gin_count = sum(1 for idx in gin_indexes if idx["tablename"] == "attractions")
    accommodations_gin_count = sum(1 for idx in gin_indexes if idx["tablename"] == "accommodations")
    cities_gin_count = sum(1 for idx in gin_indexes if idx["tablename"] == "cities")
    
    logger.info(f"JSONB columns: attractions={attractions_jsonb_count}, accommodations={accommodations_jsonb_count}, cities={cities_jsonb_count}")
    logger.info(f"GIN indexes: attractions={attractions_gin_count}, accommodations={accommodations_gin_count}, cities={cities_gin_count}")
    
    # All tables should have 2 JSONB columns (name and description)
    # All tables should have 2 GIN indexes (name and description)
    if (attractions_jsonb_count == 2 and
        accommodations_jsonb_count == 2 and
        cities_jsonb_count == 2 and
        attractions_gin_count == 2 and
        accommodations_gin_count == 2 and
        cities_gin_count == 2):
        logger.info("All JSONB columns and GIN indexes exist")
        return True
    else:
        logger.error("Some JSONB columns or GIN indexes are missing")
        return False

def main():
    """Main function to add JSONB columns and GIN indexes."""
    logger.info("Starting JSONB columns and GIN indexes addition")
    
    # Check for JSONB columns and GIN indexes
    result = check_jsonb_columns()
    if not result:
        logger.error("Failed to check JSONB columns")
        return 1
    
    # Log the current state
    logger.info(f"Found {len(result['attractions_jsonb'])} JSONB columns in attractions table")
    logger.info(f"Found {len(result['accommodations_jsonb'])} JSONB columns in accommodations table")
    logger.info(f"Found {len(result['cities_jsonb'])} JSONB columns in cities table")
    logger.info(f"Found {len(result['gin_indexes'])} GIN indexes")
    
    # Add JSONB columns and GIN indexes
    if add_jsonb_columns():
        logger.info("JSONB columns and GIN indexes added")
    else:
        logger.error("Failed to add JSONB columns and GIN indexes")
        return 1
    
    # Verify the changes
    if verify_jsonb_columns():
        logger.info("JSONB columns and GIN indexes verification passed")
        return 0
    else:
        logger.error("JSONB columns and GIN indexes verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
