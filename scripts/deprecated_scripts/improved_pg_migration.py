#!/usr/bin/env python3
"""
Improved SQLite to PostgreSQL Migration Script

This script migrates data from the SQLite database to PostgreSQL.
Features:
- Improved connection handling for macOS PostgreSQL setups
- Robust error handling and recovery
- Progress tracking with detailed output
- Handles JSON to JSONB conversion properly
- Supports Arabic text properly
"""

import os
import sys
import json
import sqlite3
import psycopg2
import logging
import getpass
import platform
import subprocess
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime
import argparse
from dotenv import load_dotenv
import time

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Configure logging with timestamp in the filename
log_file = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger("migration")

def get_system_info():
    """Get system information for debugging PostgreSQL connection issues"""
    info = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "username": getpass.getuser()
    }
    
    # Special handling for macOS PostgreSQL installations
    if info["platform"] == "Darwin":  # macOS
        try:
            # Try to get PostgreSQL version using pg_config
            pg_config = subprocess.run(["pg_config", "--version"], 
                                       capture_output=True, text=True)
            if pg_config.returncode == 0:
                info["pg_version"] = pg_config.stdout.strip()
                
            # Try to get the PostgreSQL data directory
            pg_config_data = subprocess.run(["pg_config", "--sharedir"], 
                                           capture_output=True, text=True)
            if pg_config_data.returncode == 0:
                info["pg_sharedir"] = pg_config_data.stdout.strip()
                
            # Check if PostgreSQL is running
            pg_status = subprocess.run(["pg_isready"], capture_output=True, text=True)
            info["pg_running"] = pg_status.returncode == 0
                
            # Try to determine PostgreSQL installation method
            if os.path.exists("/usr/local/opt/postgresql"):
                info["installation"] = "Homebrew"
            elif os.path.exists("/Applications/Postgres.app"):
                info["installation"] = "Postgres.app"
            elif os.path.exists("/Library/PostgreSQL"):
                info["installation"] = "EnterpriseDB"
        except Exception as e:
            logger.warning(f"Error getting PostgreSQL info: {str(e)}")
    
    return info

def get_postgres_connection_params():
    """
    Determine the best parameters to connect to PostgreSQL based on the environment
    and system configuration.
    """
    # Get system info
    system_info = get_system_info()
    logger.info(f"System information: {system_info}")
    
    # Load configuration from .env
    load_dotenv()
    postgres_uri = os.getenv("POSTGRES_URI")
    
    if postgres_uri:
        logger.info(f"Using PostgreSQL URI from environment: {postgres_uri}")
        return {"uri": postgres_uri}
    
    # Build connection parameters from components
    params = {}
    
    # Host and port
    params["host"] = os.getenv("POSTGRES_HOST", "localhost")
    
    try:
        params["port"] = int(os.getenv("POSTGRES_PORT", "5432"))
    except ValueError:
        params["port"] = 5432
    
    # Database name
    params["dbname"] = os.getenv("POSTGRES_DB", "egypt_chatbot")
    
    # User authentication
    # On macOS, try current user first if not specified
    if system_info.get("platform") == "Darwin" and not os.getenv("POSTGRES_USER"):
        params["user"] = system_info.get("username")
        logger.info(f"Using system username for PostgreSQL: {params['user']}")
    else:
        params["user"] = os.getenv("POSTGRES_USER", "postgres")
    
    # Only add password if specified
    if os.getenv("POSTGRES_PASSWORD"):
        params["password"] = os.getenv("POSTGRES_PASSWORD")
    
    logger.info(f"PostgreSQL connection parameters: {params}")
    return params

def connect_to_postgres():
    """Connect to PostgreSQL database with improved error handling"""
    params = get_postgres_connection_params()
    
    # Try to connect using URI if available
    if "uri" in params:
        try:
            connection = psycopg2.connect(params["uri"])
            connection.autocommit = False
            logger.info(f"Successfully connected to PostgreSQL using URI")
            return connection
        except psycopg2.OperationalError as e:
            logger.error(f"Failed to connect using URI: {str(e)}")
            # Continue to try with parameters
        except Exception as e:
            logger.error(f"Unexpected error connecting using URI: {str(e)}")
            # Continue to try with parameters
    
    # Try to connect using parameters
    try:
        # Remove uri if present, it's not a valid connection parameter
        if "uri" in params:
            del params["uri"]
            
        connection = psycopg2.connect(**params)
        connection.autocommit = False
        logger.info(f"Successfully connected to PostgreSQL using connection parameters")
        return connection
    except psycopg2.OperationalError as e:
        # Format error message for better readability
        error_msg = str(e).strip()
        logger.error(f"Failed to connect to PostgreSQL: {error_msg}")
        logger.error("Please check PostgreSQL installation and connection parameters.")
        
        # Provide suggestions based on error message
        if "role" in error_msg and "does not exist" in error_msg:
            logger.error(f"The specified PostgreSQL user does not exist. Try using your system username.")
            
        if "password authentication failed" in error_msg:
            logger.error("Password authentication failed. Check your PostgreSQL password.")
            
        if "Connection refused" in error_msg:
            logger.error("PostgreSQL server is not running or not accepting connections.")
            logger.error("Try starting PostgreSQL service and try again.")
        
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error connecting to PostgreSQL: {str(e)}")
        sys.exit(1)

def get_sqlite_path():
    """Get path to SQLite database"""
    load_dotenv()
    sqlite_uri = os.getenv("DATABASE_URI", "sqlite:///./data/egypt_chatbot.db")
    
    # Extract the file path from the SQLite URI
    if sqlite_uri.startswith("sqlite:///"):
        sqlite_path = sqlite_uri.replace("sqlite:///", "")
    else:
        sqlite_path = sqlite_uri
        
    # If path is relative, make it absolute
    if not os.path.isabs(sqlite_path):
        sqlite_path = os.path.join(project_root, sqlite_path)
        
    # Check if file exists
    if not os.path.isfile(sqlite_path):
        logger.error(f"SQLite database file not found: {sqlite_path}")
        sys.exit(1)
        
    return sqlite_path

def connect_to_sqlite(sqlite_path):
    """Connect to SQLite database"""
    try:
        connection = sqlite3.connect(sqlite_path)
        connection.row_factory = sqlite3.Row
        
        # Test connection by executing a simple query
        cursor = connection.cursor()
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        cursor.close()
        
        logger.info(f"Connected to SQLite database: {sqlite_path} (SQLite version: {version})")
        return connection
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to SQLite database: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error connecting to SQLite: {str(e)}")
        sys.exit(1)

def get_sqlite_tables(sqlite_conn):
    """Get list of tables in SQLite database"""
    try:
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
    except Exception as e:
        logger.error(f"Failed to get SQLite tables: {str(e)}")
        sys.exit(1)

def get_table_schema(sqlite_conn, table_name):
    """Get schema details for a SQLite table"""
    try:
        cursor = sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        cursor.close()
        
        schema = []
        for col in columns:
            schema.append({
                "name": col[1],
                "type": col[2],
                "notnull": col[3] == 1,
                "default": col[4],
                "is_pk": col[5] == 1
            })
        
        return schema
    except Exception as e:
        logger.error(f"Failed to get schema for table {table_name}: {str(e)}")
        sys.exit(1)

def map_sqlite_to_postgres_type(sqlite_type, column_name):
    """Map SQLite data type to PostgreSQL data type"""
    # Remove any length specifiers, e.g., VARCHAR(255) -> VARCHAR
    base_type = sqlite_type.split('(')[0].upper() if sqlite_type else 'TEXT'
    
    # Map SQLite type to PostgreSQL type
    type_map = {
        'INTEGER': 'INTEGER',
        'INT': 'INTEGER',
        'BIGINT': 'BIGINT',
        'REAL': 'DOUBLE PRECISION',
        'FLOAT': 'DOUBLE PRECISION',
        'NUMERIC': 'NUMERIC',
        'TEXT': 'TEXT',
        'VARCHAR': 'TEXT',
        'CHAR': 'TEXT',
        'BOOLEAN': 'BOOLEAN',
        'BOOL': 'BOOLEAN',
        'BLOB': 'BYTEA',
        'DATE': 'DATE',
        'DATETIME': 'TIMESTAMP WITH TIME ZONE',
        'TIMESTAMP': 'TIMESTAMP WITH TIME ZONE',
        'JSON': 'JSONB'
    }
    
    # Special handling for columns likely to contain dates, JSON, or IDs
    if column_name.lower() in ('created_at', 'updated_at', 'expires_at', 'timestamp', 'last_login'):
        return 'TIMESTAMP WITH TIME ZONE'
    elif column_name.lower() == 'id':
        return 'TEXT'
    elif column_name.lower() == 'data' or column_name.lower().endswith('_data'):
        return 'JSONB'
    elif column_name.lower() == 'embedding':
        return 'BYTEA'  # Vector embeddings are stored as binary in SQLite
    
    return type_map.get(base_type, 'TEXT')

def get_pg_extension_availability(conn, extension_name):
    """Check if a PostgreSQL extension is available"""
    try:
        cursor = conn.cursor()
        
        # First, check if extension is already created
        cursor.execute(f"SELECT 1 FROM pg_extension WHERE extname = '{extension_name}'")
        if cursor.fetchone():
            cursor.close()
            return {"available": True, "installed": True}
            
        # If not, check if it's available to install
        cursor.execute(f"SELECT 1 FROM pg_available_extensions WHERE name = '{extension_name}'")
        result = cursor.fetchone() is not None
        cursor.close()
        
        return {"available": result, "installed": False}
    except Exception as e:
        logger.warning(f"Error checking extension {extension_name}: {str(e)}")
        return {"available": False, "installed": False}

def ensure_pg_extensions(conn):
    """Ensure PostgreSQL extensions are installed"""
    extensions = {
        "postgis": "PostGIS for geospatial features",
        "vector": "pgvector for vector embeddings"
    }
    
    logger.info("Checking PostgreSQL extensions...")
    
    results = {}
    for ext_name, ext_desc in extensions.items():
        status = get_pg_extension_availability(conn, ext_name)
        results[ext_name] = status
        
        status_str = "✅ installed" if status["installed"] else "⚠️ available but not installed" if status["available"] else "❌ not available"
        logger.info(f"Extension {ext_name} ({ext_desc}): {status_str}")
        
        # Try to create extension if available but not installed
        if status["available"] and not status["installed"]:
            try:
                logger.info(f"Creating extension {ext_name}...")
                cursor = conn.cursor()
                cursor.execute(f"CREATE EXTENSION IF NOT EXISTS {ext_name}")
                conn.commit()
                cursor.close()
                results[ext_name]["installed"] = True
                logger.info(f"Successfully created extension {ext_name}")
            except Exception as e:
                logger.warning(f"Failed to create extension {ext_name}: {str(e)}")
                # Continue with other extensions
    
    return results

def create_postgres_tables(postgres_conn, sqlite_conn, tables):
    """Create tables in PostgreSQL with appropriate schema"""
    try:
        cursor = postgres_conn.cursor()
        
        # Check extensions
        extension_status = ensure_pg_extensions(postgres_conn)
        
        for table_name in tables:
            schema = get_table_schema(sqlite_conn, table_name)
            
            # Construct CREATE TABLE statement
            columns = []
            for col in schema:
                pg_type = map_sqlite_to_postgres_type(col['type'], col['name'])
                
                # Build column definition
                col_def = f"{col['name']} {pg_type}"
                
                # Add primary key constraint
                if col['is_pk']:
                    col_def += " PRIMARY KEY"
                    
                # Add not null constraint if needed
                if col['notnull'] and not col['is_pk']:
                    col_def += " NOT NULL"
                    
                # Add default value if specified
                if col['default'] is not None:
                    # Special handling for certain default values
                    if col['default'] == 'CURRENT_TIMESTAMP':
                        col_def += " DEFAULT CURRENT_TIMESTAMP"
                    elif pg_type == 'BOOLEAN':
                        # Convert SQLite boolean literals
                        if col['default'] in ('1', 'true', 'TRUE'):
                            col_def += " DEFAULT TRUE"
                        elif col['default'] in ('0', 'false', 'FALSE'):
                            col_def += " DEFAULT FALSE"
                    else:
                        col_def += f" DEFAULT '{col['default']}'"
                
                columns.append(col_def)
            
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    " + ",\n    ".join(columns) + "\n)"
            logger.info(f"Creating table {table_name} in PostgreSQL...")
            logger.debug(f"SQL: {create_sql}")
            
            # Execute the CREATE TABLE statement
            cursor.execute(create_sql)
        
        postgres_conn.commit()
        cursor.close()
        logger.info("All tables created in PostgreSQL")
    except Exception as e:
        postgres_conn.rollback()
        logger.error(f"Failed to create PostgreSQL tables: {str(e)}")
        sys.exit(1)

def convert_value_for_postgres(value, pg_type):
    """Convert SQLite value to appropriate PostgreSQL format"""
    if value is None:
        return None
        
    try:
        if pg_type == 'JSONB':
            # If string, parse it first
            if isinstance(value, str):
                # Empty JSON
                if value.strip() in ('', '{}', '[]'):
                    return Json({})
                    
                try:
                    return Json(json.loads(value))
                except json.JSONDecodeError:
                    # If JSON parsing fails, store as string in a JSON object
                    logger.warning(f"Failed to parse JSON: {value[:50]}...")
                    return Json({"text": value})
            return Json(value)
        elif pg_type.startswith('TIMESTAMP'):
            # Handle empty string
            if value == "":
                return None
                
            # Try to parse datetime string
            if isinstance(value, str):
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S.%f',
                    '%Y-%m-%d'
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                
                # If all formats fail, return the original value
                return value
            
            return value
        elif pg_type == 'BOOLEAN':
            # Convert various boolean representations
            if isinstance(value, str):
                if value.lower() in ('true', 't', 'yes', 'y', '1'):
                    return True
                elif value.lower() in ('false', 'f', 'no', 'n', '0'):
                    return False
                else:
                    return bool(value)
            return bool(value)
        else:
            return value
    except Exception as e:
        logger.warning(f"Error converting value for PostgreSQL: {e} (value: {str(value)[:50]}, type: {pg_type})")
        return value

def migrate_table(sqlite_conn, postgres_conn, table_name, batch_size=100):
    """Migrate data from SQLite to PostgreSQL for a single table"""
    try:
        # Special handling for certain tables
        special_tables = {
            'attractions': 'tourist attractions',
            'restaurants': 'dining establishments',
            'accommodations': 'lodging options',
            'cities': 'geographic locations',
            'sessions': 'user session data',
            'analytics': 'user interaction logs',
            'users': 'user accounts'
        }
        
        description = special_tables.get(table_name, 'data')
        logger.info(f"Migrating {description} for table '{table_name}'...")
        
        # Get table schema
        schema = get_table_schema(sqlite_conn, table_name)
        column_names = [col['name'] for col in schema]
        pg_types = [map_sqlite_to_postgres_type(col['type'], col['name']) for col in schema]
        
        # Get row count for progress tracking
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = sqlite_cursor.fetchone()[0]
        logger.info(f"Total rows to migrate for {table_name}: {total_rows}")
        
        # Create placeholders for prepared statement
        placeholders = ", ".join(["%s" for _ in column_names])
        insert_sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
        
        # Fetch data in batches and insert
        offset = 0
        rows_migrated = 0
        errors = 0
        
        pg_cursor = postgres_conn.cursor()
        
        while True:
            sqlite_cursor.execute(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                break
            
            # Convert rows to list of tuples
            pg_rows = []
            for row in rows:
                try:
                    pg_row = []
                    for i, value in enumerate(row):
                        pg_value = convert_value_for_postgres(value, pg_types[i])
                        pg_row.append(pg_value)
                    pg_rows.append(tuple(pg_row))
                except Exception as e:
                    logger.error(f"Error converting row in {table_name}: {str(e)}")
                    errors += 1
                    continue
            
            # Insert rows in a single batch
            try:
                pg_cursor.executemany(insert_sql, pg_rows)
                rows_migrated += len(pg_rows)
            except Exception as e:
                logger.error(f"Error inserting batch into {table_name}: {str(e)}")
                errors += len(pg_rows)
                
                # Try one by one for error diagnosis
                for i, row in enumerate(pg_rows):
                    try:
                        pg_cursor.execute(insert_sql, row)
                        postgres_conn.commit()
                        rows_migrated += 1
                    except Exception as row_e:
                        logger.error(f"Row error in {table_name} (row {offset+i}): {str(row_e)}")
                        errors += 1
            
            # Commit after each batch
            try:
                postgres_conn.commit()
            except Exception as e:
                logger.error(f"Error committing batch for {table_name}: {str(e)}")
                postgres_conn.rollback()
                errors += len(pg_rows)
            
            offset += batch_size
            
            # Report progress
            progress = (rows_migrated / total_rows) * 100 if total_rows > 0 else 100
            logger.info(f"Migrated {rows_migrated}/{total_rows} rows ({progress:.2f}%) for table {table_name}")
        
        pg_cursor.close()
        sqlite_cursor.close()
        
        if errors > 0:
            logger.warning(f"Migration of {table_name} completed with {errors} errors")
        else:
            logger.info(f"Successfully migrated all {rows_migrated} rows for table {table_name}")
        
        return {"migrated": rows_migrated, "errors": errors, "total": total_rows}
    except Exception as e:
        postgres_conn.rollback()
        logger.error(f"Failed to migrate data for table {table_name}: {str(e)}")
        return {"migrated": 0, "errors": 0, "total": 0}

def create_postgres_indexes(postgres_conn, sqlite_conn, tables):
    """Create indexes in PostgreSQL based on SQLite indexes"""
    try:
        # Create standard indexes
        index_map = {
            'attractions': ['type', 'city', 'region', 'name_en', 'name_ar'],
            'accommodations': ['type', 'city', 'category', 'name_en', 'name_ar'],
            'restaurants': ['cuisine', 'city', 'name_en', 'name_ar'],
            'cities': ['region', 'name_en', 'name_ar'],
            'sessions': ['expires_at'],
            'users': ['username', 'email'],
            'analytics': ['session_id', 'user_id', 'event_type', 'timestamp']
        }
        
        cursor = postgres_conn.cursor()
        
        # Check for extensions
        postgis_available = get_pg_extension_availability(postgres_conn, 'postgis')
        pgvector_available = get_pg_extension_availability(postgres_conn, 'vector')
        
        # Standard indexes
        for table, columns in index_map.items():
            if table in tables:
                for column in columns:
                    # Skip non-existent columns
                    try:
                        schema = get_table_schema(sqlite_conn, table)
                        cols = [col['name'].lower() for col in schema]
                        if column.lower() not in cols:
                            logger.warning(f"Column {column} not found in {table}, skipping index creation")
                            continue
                    except Exception as e:
                        logger.warning(f"Error checking column {column} in {table}: {str(e)}")
                        continue
                        
                    index_name = f"idx_{table}_{column}"
                    index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column})"
                    logger.info(f"Creating index {index_name}...")
                    
                    try:
                        cursor.execute(index_sql)
                        postgres_conn.commit()
                    except Exception as e:
                        postgres_conn.rollback()
                        logger.error(f"Error creating index {index_name}: {str(e)}")
        
        # Create spatial indexes if PostGIS is available
        if postgis_available["installed"]:
            logger.info("Creating spatial indexes with PostGIS...")
            
            for table in ['attractions', 'accommodations', 'restaurants']:
                if table not in tables:
                    continue
                    
                try:
                    # Add geometry column
                    cursor.execute(f"""
                        ALTER TABLE {table} 
                        ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326)
                    """)
                    postgres_conn.commit()
                    
                    # Update geometry from latitude and longitude
                    cursor.execute(f"""
                        UPDATE {table} 
                        SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
                        WHERE latitude IS NOT NULL 
                          AND longitude IS NOT NULL
                          AND (geom IS NULL OR
                               ST_X(geom) != longitude OR 
                               ST_Y(geom) != latitude)
                    """)
                    postgres_conn.commit()
                    
                    # Create spatial index
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_{table}_geom 
                        ON {table} USING GIST (geom)
                    """)
                    postgres_conn.commit()
                    
                    logger.info(f"Created spatial index for {table}")
                except Exception as e:
                    postgres_conn.rollback()
                    logger.error(f"Error creating spatial index for {table}: {str(e)}")
        else:
            logger.warning("PostGIS extension not available. Spatial indexes not created.")
        
        # Create JSONB indexes
        logger.info("Creating JSONB indexes...")
        for table in ['attractions', 'restaurants', 'accommodations']:
            if table not in tables:
                continue
                
            try:
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table}_data 
                    ON {table} USING GIN (data)
                """)
                postgres_conn.commit()
                logger.info(f"Created JSONB index for {table}")
            except Exception as e:
                postgres_conn.rollback()
                logger.error(f"Error creating JSONB index for {table}: {str(e)}")
        
        # Create vector indexes if pgvector is available
        if pgvector_available["installed"]:
            logger.info("Creating vector embeddings indexes with pgvector...")
            
            for table in ['attractions', 'restaurants', 'accommodations']:
                if table not in tables:
                    continue
                    
                try:
                    # Check if embedding column exists
                    cursor.execute(f"""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = '{table}' AND column_name = 'embedding'
                    """)
                    
                    if cursor.fetchone():
                        # Add vector column with default size of 1536 (for OpenAI embeddings)
                        cursor.execute(f"""
                            ALTER TABLE {table} 
                            ADD COLUMN IF NOT EXISTS embedding_vector vector(1536)
                        """)
                        postgres_conn.commit()
                        
                        logger.info(f"Added vector column to {table}")
                        
                        # Note: Converting embeddings requires special handling and would be done separately
                        
                        # Create vector index
                        cursor.execute(f"""
                            CREATE INDEX IF NOT EXISTS idx_{table}_embedding 
                            ON {table} USING ivfflat (embedding_vector vector_cosine_ops)
                            WITH (lists = 100)
                        """)
                        postgres_conn.commit()
                        
                        logger.info(f"Created vector index for {table}")
                except Exception as e:
                    postgres_conn.rollback()
                    logger.error(f"Error creating vector index for {table}: {str(e)}")
        else:
            logger.warning("pgvector extension not available. Vector indexes not created.")
        
        cursor.close()
        logger.info("All indexes created in PostgreSQL")
    except Exception as e:
        postgres_conn.rollback()
        logger.error(f"Failed to create PostgreSQL indexes: {str(e)}")

def validate_migration(sqlite_conn, postgres_conn, tables):
    """Validate migration by comparing row counts between SQLite and PostgreSQL"""
    try:
        logger.info("Validating migration...")
        
        validation_results = {}
        all_valid = True
        
        for table in tables:
            # Get row count from SQLite
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cursor.fetchone()[0]
            sqlite_cursor.close()
            
            # Get row count from PostgreSQL
            pg_cursor = postgres_conn.cursor()
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            pg_count = pg_cursor.fetchone()[0]
            pg_cursor.close()
            
            # Compare counts
            is_valid = sqlite_count == pg_count
            percentage = (pg_count / sqlite_count * 100) if sqlite_count > 0 else 100
            
            validation_results[table] = {
                "sqlite_count": sqlite_count,
                "postgres_count": pg_count,
                "percentage": percentage,
                "is_valid": is_valid
            }
            
            if not is_valid:
                all_valid = False
        
        # Print validation results
        logger.info("Migration validation results:")
        for table, result in validation_results.items():
            status = "✅ VALID" if result["is_valid"] else "❌ INVALID"
            logger.info(f"{table}: {result['sqlite_count']} (SQLite) vs {result['postgres_count']} (PostgreSQL) - {result['percentage']:.2f}% migrated - {status}")
        
        return all_valid, validation_results
    except Exception as e:
        logger.error(f"Failed to validate migration: {str(e)}")
        return False, {}

def analyze_database(postgres_conn):
    """Run ANALYZE to update PostgreSQL statistics"""
    try:
        logger.info("Running ANALYZE to update PostgreSQL statistics...")
        cursor = postgres_conn.cursor()
        cursor.execute("ANALYZE")
        postgres_conn.commit()
        cursor.close()
        logger.info("ANALYZE completed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to run ANALYZE: {str(e)}")
        return False

def main():
    """Main function for the migration script"""
    parser = argparse.ArgumentParser(description="Migrate data from SQLite to PostgreSQL")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for migration (default: 100)")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without actually migrating data")
    parser.add_argument("--tables", type=str, help="Comma-separated list of tables to migrate (default: all)")
    parser.add_argument("--skip-validation", action="store_true", help="Skip validation after migration")
    args = parser.parse_args()
    
    start_time = time.time()
    
    logger.info("=" * 80)
    logger.info("Starting SQLite to PostgreSQL migration with improved script")
    logger.info("=" * 80)
    
    # Connect to databases
    sqlite_path = get_sqlite_path()
    sqlite_conn = connect_to_sqlite(sqlite_path)
    postgres_conn = connect_to_postgres()
    
    # Get list of tables
    all_tables = get_sqlite_tables(sqlite_conn)
    
    # Filter tables if specified
    if args.tables:
        selected_tables = [t.strip() for t in args.tables.split(",")]
        tables = [t for t in selected_tables if t in all_tables]
        logger.info(f"Selected {len(tables)}/{len(all_tables)} tables for migration")
    else:
        tables = all_tables
        
    logger.info(f"Found {len(tables)} tables in SQLite: {', '.join(tables)}")
    
    if args.dry_run:
        logger.info("Dry run mode: Only validating database connections and structures")
        create_postgres_tables(postgres_conn, sqlite_conn, tables)
        logger.info("Dry run completed successfully")
    else:
        # Create tables in PostgreSQL
        create_postgres_tables(postgres_conn, sqlite_conn, tables)
        
        # Migrate data for each table
        migration_results = {}
        for table in tables:
            result = migrate_table(sqlite_conn, postgres_conn, table, args.batch_size)
            migration_results[table] = result
        
        # Create indexes in PostgreSQL
        create_postgres_indexes(postgres_conn, sqlite_conn, tables)
        
        # Update statistics
        analyze_database(postgres_conn)
        
        # Validate migration
        if not args.skip_validation:
            is_valid, validation_results = validate_migration(sqlite_conn, postgres_conn, tables)
        else:
            is_valid, validation_results = True, {}
        
        # Report migration summary
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("=" * 80)
        logger.info("Migration Summary")
        logger.info("=" * 80)
        logger.info(f"Migration log file: {os.path.abspath(log_file)}")
        logger.info(f"Total tables migrated: {len(tables)}")
        
        total_rows_migrated = sum(r.get("migrated", 0) for r in migration_results.values())
        total_rows_source = sum(r.get("total", 0) for r in migration_results.values())
        total_errors = sum(r.get("errors", 0) for r in migration_results.values())
        
        logger.info(f"Total rows in source: {total_rows_source}")
        logger.info(f"Total rows migrated: {total_rows_migrated}")
        logger.info(f"Migration errors: {total_errors}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Validation status: {'✅ VALID' if is_valid else '❌ INVALID'}")
        
        if is_valid:
            logger.info("Migration completed successfully!")
        elif not args.skip_validation:
            logger.warning("Migration completed with validation errors. Please check the logs.")
    
    # Close database connections
    sqlite_conn.close()
    postgres_conn.close()
    
    logger.info("=" * 80)

if __name__ == "__main__":
    main()