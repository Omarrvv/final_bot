#!/usr/bin/env python3
"""
Script to install and configure pgvector extension for PostgreSQL.

This script:
1. Checks if the pgvector extension is already installed
2. Installs the pgvector extension if not present
3. Updates existing vector columns to use the pgvector type
4. Creates necessary indexes for vector similarity search

Prerequisites:
- PostgreSQL 11+ with superuser access
- pgvector extension must be available in the PostgreSQL extensions directory
"""

import os
import sys
import logging
import argparse
import psycopg2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import from project
try:
    from src.utils.environment import get_env_var
except ImportError:
    logger.error("Failed to import required modules from project. Make sure the project structure is correct.")
    
    # Fallback implementation
    def get_env_var(name, default=None):
        return os.getenv(name, default)

# Parse arguments
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Install and configure pgvector extension")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print operations without executing them")
    parser.add_argument("--vector-dim", type=int, default=384,
                        help="Dimension of vector embeddings (default: 384)")
    parser.add_argument("--force", action="store_true",
                        help="Force reinstallation even if pgvector is already installed")
    
    return parser.parse_args()

# Load environment
def load_config():
    """Load configuration from .env file."""
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path)
    
    # Get PostgreSQL URI
    postgres_uri = get_env_var("POSTGRES_URI")
    if not postgres_uri:
        logger.error("POSTGRES_URI environment variable not set")
        sys.exit(1)
    
    logger.info(f"Using PostgreSQL URI: {postgres_uri}")
    return postgres_uri

# Connect to PostgreSQL with superuser privileges if possible
def connect_to_postgres(postgres_uri):
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(postgres_uri)
        conn.autocommit = False  # We want to control transactions explicitly
        logger.info("Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        sys.exit(1)

# Check if we have superuser privileges
def check_superuser(conn):
    """Check if the connected user has superuser privileges."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT usesuper FROM pg_user WHERE usename = current_user")
            result = cursor.fetchone()
            
            if result and result[0]:
                logger.info("Connected as superuser")
                return True
            else:
                logger.warning("Not connected as superuser. Some operations may fail.")
                return False
    except Exception as e:
        logger.error(f"Error checking superuser status: {e}")
        return False

# Check if pgvector extension is available
def check_pgvector_availability(conn):
    """Check if pgvector extension is available to be installed."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'vector')")
            result = cursor.fetchone()
            
            if result and result[0]:
                logger.info("pgvector extension is available")
                return True
            else:
                logger.error("pgvector extension is not available. Please install it on your PostgreSQL server.")
                return False
    except Exception as e:
        logger.error(f"Error checking pgvector availability: {e}")
        return False

# Check if pgvector extension is already installed
def check_pgvector_installed(conn):
    """Check if pgvector extension is already installed."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
            result = cursor.fetchone()
            
            if result and result[0]:
                logger.info("pgvector extension is already installed")
                return True
            else:
                logger.info("pgvector extension is not installed")
                return False
    except Exception as e:
        logger.error(f"Error checking pgvector installation: {e}")
        return False

# Install pgvector extension
def install_pgvector(conn, dry_run=False):
    """Install pgvector extension."""
    try:
        with conn.cursor() as cursor:
            if dry_run:
                logger.info("[DRY RUN] Would execute: CREATE EXTENSION vector")
                return True
            
            cursor.execute("CREATE EXTENSION vector")
            conn.commit()
            logger.info("Successfully installed pgvector extension")
            return True
    except Exception as e:
        logger.error(f"Error installing pgvector extension: {e}")
        conn.rollback()
        return False

# Get tables with existing vector columns
def get_tables_with_vector_columns(conn):
    """Get tables that have columns of type vector or that need to be converted to vector."""
    try:
        with conn.cursor() as cursor:
            # Check for tables with 'embedding' columns
            cursor.execute("""
                SELECT DISTINCT table_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND (column_name = 'embedding' OR column_name LIKE 'embedding_%')
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"Found {len(tables)} tables with embedding columns: {', '.join(tables) if tables else 'none'}")
            
            return tables
    except Exception as e:
        logger.error(f"Error getting tables with vector columns: {e}")
        return []

# Check column types and convert to vector if needed
def check_and_convert_columns(conn, tables, vector_dim=384, dry_run=False):
    """Check column types and convert to vector if needed."""
    try:
        columns_converted = 0
        
        with conn.cursor() as cursor:
            for table in tables:
                # Get columns to check
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s 
                    AND (column_name = 'embedding' OR column_name LIKE 'embedding_%%')
                """, (table,))
                
                columns = cursor.fetchall()
                
                for column_name, data_type in columns:
                    # Check if column needs conversion
                    if data_type.lower() != 'vector':
                        # If column is JSONB or text (likely storing vector as JSON)
                        if data_type.lower() in ('jsonb', 'json', 'text'):
                            # Create a temporary column to store vectors
                            temp_column = f"{column_name}_vector"
                            alter_sql = f"ALTER TABLE {table} ADD COLUMN {temp_column} vector({vector_dim})"
                            update_sql = f"""
                            UPDATE {table} 
                            SET {temp_column} = {column_name}::vector({vector_dim})
                            WHERE {column_name} IS NOT NULL
                            """
                            drop_sql = f"ALTER TABLE {table} DROP COLUMN {column_name}"
                            rename_sql = f"ALTER TABLE {table} RENAME COLUMN {temp_column} TO {column_name}"
                            
                            if dry_run:
                                logger.info(f"[DRY RUN] Would convert column {table}.{column_name} from {data_type} to vector({vector_dim})")
                                logger.info(f"[DRY RUN] Would execute: {alter_sql}")
                                logger.info(f"[DRY RUN] Would execute: {update_sql}")
                                logger.info(f"[DRY RUN] Would execute: {drop_sql}")
                                logger.info(f"[DRY RUN] Would execute: {rename_sql}")
                            else:
                                try:
                                    # Execute conversion
                                    cursor.execute(alter_sql)
                                    cursor.execute(update_sql)
                                    cursor.execute(drop_sql)
                                    cursor.execute(rename_sql)
                                    
                                    conn.commit()
                                    logger.info(f"Converted column {table}.{column_name} from {data_type} to vector({vector_dim})")
                                    columns_converted += 1
                                except Exception as e:
                                    logger.error(f"Error converting column {table}.{column_name}: {e}")
                                    conn.rollback()
                        else:
                            # For other types, alter column directly
                            alter_sql = f"ALTER TABLE {table} ALTER COLUMN {column_name} TYPE vector({vector_dim}) USING NULL"
                            
                            if dry_run:
                                logger.info(f"[DRY RUN] Would convert column {table}.{column_name} from {data_type} to vector({vector_dim})")
                                logger.info(f"[DRY RUN] Would execute: {alter_sql}")
                            else:
                                try:
                                    cursor.execute(alter_sql)
                                    conn.commit()
                                    logger.info(f"Converted column {table}.{column_name} from {data_type} to vector({vector_dim})")
                                    columns_converted += 1
                                except Exception as e:
                                    logger.error(f"Error converting column {table}.{column_name}: {e}")
                                    conn.rollback()
                    else:
                        logger.info(f"Column {table}.{column_name} is already of type vector")
        
        logger.info(f"{'Would convert' if dry_run else 'Converted'} {columns_converted} columns to vector type")
        return columns_converted
    except Exception as e:
        logger.error(f"Error checking and converting columns: {e}")
        return 0

# Create or update vector indexes
def create_vector_indexes(conn, tables, dry_run=False):
    """Create vector indexes for similarity search."""
    try:
        indexes_created = 0
        
        with conn.cursor() as cursor:
            for table in tables:
                # Check which embedding columns exist
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s 
                    AND (column_name = 'embedding' OR column_name LIKE 'embedding_%%')
                    AND data_type = 'USER-DEFINED'  -- for vector type
                """, (table,))
                
                columns = [row[0] for row in cursor.fetchall()]
                
                for column in columns:
                    # Check if index exists
                    index_name = f"idx_{table}_{column}"
                    
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM pg_indexes
                            WHERE schemaname = 'public'
                            AND tablename = %s
                            AND indexname = %s
                        )
                    """, (table, index_name))
                    
                    index_exists = cursor.fetchone()[0]
                    
                    if index_exists:
                        logger.info(f"Index {index_name} already exists")
                        continue
                    
                    # Create index using IVFFlat index for better performance
                    sql = f"""
                    CREATE INDEX {index_name} ON {table} 
                    USING ivfflat ({column}) WITH (lists = 100)
                    """
                    
                    if dry_run:
                        logger.info(f"[DRY RUN] Would create index: {sql}")
                    else:
                        try:
                            cursor.execute(sql)
                            conn.commit()
                            logger.info(f"Created index {index_name}")
                            indexes_created += 1
                        except Exception as e:
                            logger.error(f"Error creating index {index_name}: {e}")
                            conn.rollback()
                            continue
        
        logger.info(f"{'Would create' if dry_run else 'Created'} {indexes_created} vector indexes")
        return indexes_created
    except Exception as e:
        logger.error(f"Error creating vector indexes: {e}")
        return 0

# Create test function for pgvector
def create_test_function(conn, dry_run=False):
    """Create a test function to verify pgvector functionality."""
    try:
        with conn.cursor() as cursor:
            # Check if the function already exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_proc
                    WHERE proname = 'test_pgvector'
                )
            """)
            
            function_exists = cursor.fetchone()[0]
            
            if function_exists:
                logger.info("Test function 'test_pgvector' already exists")
                return True
            
            # Create the function
            sql = """
            CREATE OR REPLACE FUNCTION test_pgvector()
            RETURNS TABLE (
                dot_product float8,
                l2_distance float8,
                cosine_distance float8
            )
            AS $$
            DECLARE
                v1 vector(3);
                v2 vector(3);
            BEGIN
                v1 := '[1,2,3]';
                v2 := '[4,5,6]';
                
                RETURN QUERY
                SELECT
                    v1 <#> v2 AS dot_product,
                    v1 <-> v2 AS l2_distance,
                    v1 <=> v2 AS cosine_distance;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            if dry_run:
                logger.info("[DRY RUN] Would create test function: test_pgvector()")
            else:
                cursor.execute(sql)
                conn.commit()
                logger.info("Created test function: test_pgvector()")
            
            return True
    except Exception as e:
        logger.error(f"Error creating test function: {e}")
        conn.rollback()
        return False

# Test pgvector functionality
def test_pgvector(conn):
    """Test pgvector functionality by calling the test function."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM test_pgvector()")
            result = cursor.fetchone()
            
            if result:
                dot_product, l2_distance, cosine_distance = result
                logger.info(f"pgvector test successful!")
                logger.info(f"Dot product: {dot_product}")
                logger.info(f"L2 distance: {l2_distance}")
                logger.info(f"Cosine distance: {cosine_distance}")
                return True
            else:
                logger.error("pgvector test failed: no result returned")
                return False
    except Exception as e:
        logger.error(f"Error testing pgvector: {e}")
        return False

# Main function
def main():
    """Main function to install and configure pgvector."""
    # Parse arguments
    args = parse_args()
    
    # Load configuration
    postgres_uri = load_config()
    
    # Connect to PostgreSQL
    conn = connect_to_postgres(postgres_uri)
    
    try:
        # Check superuser status
        is_superuser = check_superuser(conn)
        
        if not is_superuser:
            logger.warning("Some operations may require superuser privileges")
        
        # Check if pgvector is available
        if not check_pgvector_availability(conn):
            logger.error("pgvector extension is not available. Please install it on your PostgreSQL server.")
            return
        
        # Check if pgvector is already installed
        pgvector_installed = check_pgvector_installed(conn)
        
        # Install pgvector if not installed or if force flag is set
        if not pgvector_installed or args.force:
            if install_pgvector(conn, args.dry_run):
                logger.info("pgvector extension installed successfully")
            else:
                logger.error("Failed to install pgvector extension")
                return
        
        # Get tables with vector columns
        tables = get_tables_with_vector_columns(conn)
        
        if tables:
            # Check and convert columns
            check_and_convert_columns(conn, tables, args.vector_dim, args.dry_run)
            
            # Create vector indexes
            create_vector_indexes(conn, tables, args.dry_run)
        
        # Create test function
        if create_test_function(conn, args.dry_run):
            # Test pgvector functionality
            if not args.dry_run:
                test_pgvector(conn)
        
        logger.info("pgvector setup completed successfully")
        
    except Exception as e:
        logger.error(f"Error setting up pgvector: {e}")
    finally:
        conn.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    main() 