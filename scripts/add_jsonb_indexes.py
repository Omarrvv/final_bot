#!/usr/bin/env python
"""
Add JSONB Indexes

This script directly adds recommended JSONB indexes to the database without using the migration system.
It implements the recommendations from the JSONB query optimization analysis.
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
        logging.FileHandler('add_jsonb_indexes.log')
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

def connect_to_database():
    """Connect to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(get_postgres_uri())
        conn.autocommit = False  # We want transactions
        logger.info(f"Connected to database: {DB_NAME}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def add_gin_indexes(conn):
    """Add GIN indexes for JSONB columns"""
    try:
        with conn.cursor() as cursor:
            # Add GIN index to accommodations.data
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'accommodations' AND indexname = 'idx_accommodations_data_gin'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE INDEX idx_accommodations_data_gin ON accommodations USING GIN (data)
                """)
                logger.info("Created GIN index on accommodations.data")
            else:
                logger.info("GIN index on accommodations.data already exists")
            
            # Add GIN index to analytics.event_data
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'analytics' AND indexname = 'idx_analytics_event_data_gin'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE INDEX idx_analytics_event_data_gin ON analytics USING GIN (event_data)
                """)
                logger.info("Created GIN index on analytics.event_data")
            else:
                logger.info("GIN index on analytics.event_data already exists")
            
            # Add GIN index to attractions.data
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'attractions' AND indexname = 'idx_attractions_data_gin'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE INDEX idx_attractions_data_gin ON attractions USING GIN (data)
                """)
                logger.info("Created GIN index on attractions.data")
            else:
                logger.info("GIN index on attractions.data already exists")
            
            # Add GIN index to sessions.data
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'sessions' AND indexname = 'idx_sessions_data_gin'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE INDEX idx_sessions_data_gin ON sessions USING GIN (data)
                """)
                logger.info("Created GIN index on sessions.data")
            else:
                logger.info("GIN index on sessions.data already exists")
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding GIN indexes: {e}")
        return False

def add_expression_indexes(conn):
    """Add expression indexes for specific JSONB fields"""
    try:
        with conn.cursor() as cursor:
            # Add expression index for regions.name->ar
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'regions' AND indexname = 'idx_regions_name_ar'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE INDEX idx_regions_name_ar ON regions ((name->'ar'))
                """)
                logger.info("Created expression index on regions.name->ar")
            else:
                logger.info("Expression index on regions.name->ar already exists")
            
            # Add expression index for regions.name->en
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'regions' AND indexname = 'idx_regions_name_en'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE INDEX idx_regions_name_en ON regions ((name->'en'))
                """)
                logger.info("Created expression index on regions.name->en")
            else:
                logger.info("Expression index on regions.name->en already exists")
            
            # Add expression index for restaurants.data->name
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'restaurants' AND indexname = 'idx_restaurants_data_name'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE INDEX idx_restaurants_data_name ON restaurants ((data->'name'))
                """)
                logger.info("Created expression index on restaurants.data->name")
            else:
                logger.info("Expression index on restaurants.data->name already exists")
            
            # Add expression index for restaurants.data->description
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'restaurants' AND indexname = 'idx_restaurants_data_description'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE INDEX idx_restaurants_data_description ON restaurants ((data->'description'))
                """)
                logger.info("Created expression index on restaurants.data->description")
            else:
                logger.info("Expression index on restaurants.data->description already exists")
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding expression indexes: {e}")
        return False

def add_multilingual_indexes(conn):
    """Add commonly used expression indexes for multilingual fields"""
    try:
        with conn.cursor() as cursor:
            # Add expression indexes for cities.name->en and cities.name->ar
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'cities' AND indexname = 'idx_cities_name_en'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE INDEX idx_cities_name_en ON cities ((name->'en'))
                """)
                logger.info("Created expression index on cities.name->en")
            else:
                logger.info("Expression index on cities.name->en already exists")
            
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'cities' AND indexname = 'idx_cities_name_ar'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE INDEX idx_cities_name_ar ON cities ((name->'ar'))
                """)
                logger.info("Created expression index on cities.name->ar")
            else:
                logger.info("Expression index on cities.name->ar already exists")
            
            # Add expression indexes for attractions.name->en and attractions.name->ar
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'attractions' AND indexname = 'idx_attractions_name_en'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE INDEX idx_attractions_name_en ON attractions ((name->'en'))
                """)
                logger.info("Created expression index on attractions.name->en")
            else:
                logger.info("Expression index on attractions.name->en already exists")
            
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'attractions' AND indexname = 'idx_attractions_name_ar'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE INDEX idx_attractions_name_ar ON attractions ((name->'ar'))
                """)
                logger.info("Created expression index on attractions.name->ar")
            else:
                logger.info("Expression index on attractions.name->ar already exists")
            
            # Add expression indexes for accommodations.name->en and accommodations.name->ar
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'accommodations' AND indexname = 'idx_accommodations_name_en'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE INDEX idx_accommodations_name_en ON accommodations ((name->'en'))
                """)
                logger.info("Created expression index on accommodations.name->en")
            else:
                logger.info("Expression index on accommodations.name->en already exists")
            
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = 'accommodations' AND indexname = 'idx_accommodations_name_ar'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE INDEX idx_accommodations_name_ar ON accommodations ((name->'ar'))
                """)
                logger.info("Created expression index on accommodations.name->ar")
            else:
                logger.info("Expression index on accommodations.name->ar already exists")
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding multilingual indexes: {e}")
        return False

def verify_indexes(conn):
    """Verify that indexes were created"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get all indexes
            cursor.execute("""
                SELECT 
                    tablename, 
                    indexname, 
                    indexdef
                FROM 
                    pg_indexes
                WHERE 
                    schemaname = 'public' AND
                    (indexname LIKE 'idx_%_data_gin' OR
                     indexname LIKE 'idx_%_name_en' OR
                     indexname LIKE 'idx_%_name_ar')
                ORDER BY 
                    tablename, indexname
            """)
            
            indexes = cursor.fetchall()
            
            logger.info(f"Found {len(indexes)} indexes:")
            for index in indexes:
                logger.info(f"  - {index['tablename']}.{index['indexname']}: {index['indexdef']}")
            
            return indexes
    except Exception as e:
        logger.error(f"Error verifying indexes: {e}")
        return []

def main():
    """Main function"""
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return 1
    
    try:
        # Add GIN indexes
        logger.info("Adding GIN indexes...")
        if not add_gin_indexes(conn):
            return 1
        
        # Add expression indexes
        logger.info("Adding expression indexes...")
        if not add_expression_indexes(conn):
            return 1
        
        # Add multilingual indexes
        logger.info("Adding multilingual indexes...")
        if not add_multilingual_indexes(conn):
            return 1
        
        # Verify indexes
        logger.info("Verifying indexes...")
        indexes = verify_indexes(conn)
        
        logger.info("JSONB indexes added successfully")
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    sys.exit(main())
