#!/usr/bin/env python3
"""
Database Migration Tool

This module provides a unified solution for migrating data between SQLite and PostgreSQL databases.
It handles schema conversion, data migration, and validation with support for:
- JSON/JSONB conversion
- PostGIS spatial data
- pgvector embeddings
- Proper timestamp handling
- Index recreation
"""

import os
import sys
import json
import logging
import sqlite3
import psycopg2
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from psycopg2.extras import Json, DictCursor
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Schema definitions
SCHEMA_DEFINITIONS = {
    "attractions": {
        "id": ("TEXT", "TEXT", "PRIMARY KEY"),
        "name_en": ("TEXT", "TEXT", "NOT NULL"),
        "name_ar": ("TEXT", "TEXT", None),
        "type": ("TEXT", "TEXT", None),
        "city": ("TEXT", "TEXT", None),
        "region": ("TEXT", "TEXT", None),
        "latitude": ("REAL", "DOUBLE PRECISION", None),
        "longitude": ("REAL", "DOUBLE PRECISION", None),
        "description_en": ("TEXT", "TEXT", None),
        "description_ar": ("TEXT", "TEXT", None),
        "data": ("TEXT", "JSONB", None),
        "created_at": ("TEXT", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP"),
        "updated_at": ("TEXT", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP"),
        "user_id": ("TEXT", "TEXT", "REFERENCES users(id) ON DELETE SET NULL"),
        "embedding": (None, "vector(1536)", None),
        "geom": (None, "geometry(Point, 4326)", None)
    },
    "accommodations": {
        "id": ("TEXT", "TEXT", "PRIMARY KEY"),
        "name_en": ("TEXT", "TEXT", "NOT NULL"),
        "name_ar": ("TEXT", "TEXT", None),
        "type": ("TEXT", "TEXT", None),
        "category": ("TEXT", "TEXT", None),
        "city": ("TEXT", "TEXT", None),
        "region": ("TEXT", "TEXT", None),
        "latitude": ("REAL", "DOUBLE PRECISION", None),
        "longitude": ("REAL", "DOUBLE PRECISION", None),
        "description_en": ("TEXT", "TEXT", None),
        "description_ar": ("TEXT", "TEXT", None),
        "price_min": ("REAL", "NUMERIC", None),
        "price_max": ("REAL", "NUMERIC", None),
        "data": ("TEXT", "JSONB", None),
        "created_at": ("TEXT", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP"),
        "updated_at": ("TEXT", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP"),
        "user_id": ("TEXT", "TEXT", "REFERENCES users(id) ON DELETE SET NULL"),
        "embedding": (None, "vector(1536)", None),
        "geom": (None, "geometry(Point, 4326)", None)
    },
    "restaurants": {
        "id": ("TEXT", "TEXT", "PRIMARY KEY"),
        "name_en": ("TEXT", "TEXT", "NOT NULL"),
        "name_ar": ("TEXT", "TEXT", None),
        "cuisine": ("TEXT", "TEXT", None),
        "city": ("TEXT", "TEXT", None),
        "region": ("TEXT", "TEXT", None),
        "latitude": ("REAL", "DOUBLE PRECISION", None),
        "longitude": ("REAL", "DOUBLE PRECISION", None),
        "description_en": ("TEXT", "TEXT", None),
        "description_ar": ("TEXT", "TEXT", None),
        "price_range": ("TEXT", "TEXT", None),
        "data": ("TEXT", "JSONB", None),
        "created_at": ("TEXT", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP"),
        "updated_at": ("TEXT", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP"),
        "user_id": ("TEXT", "TEXT", "REFERENCES users(id) ON DELETE SET NULL"),
        "embedding": (None, "vector(1536)", None),
        "geom": (None, "geometry(Point, 4326)", None)
    },
    "users": {
        "id": ("TEXT", "TEXT", "PRIMARY KEY"),
        "username": ("TEXT", "TEXT", "UNIQUE NOT NULL"),
        "email": ("TEXT", "TEXT", "UNIQUE"),
        "password_hash": ("TEXT", "TEXT", "NOT NULL"),
        "salt": ("TEXT", "TEXT", "NOT NULL"),
        "role": ("TEXT", "TEXT", "DEFAULT 'user'"),
        "data": ("TEXT", "JSONB", None),
        "created_at": ("TEXT", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP"),
        "last_login": ("TEXT", "TIMESTAMPTZ", None)
    },
    "sessions": {
        "id": ("TEXT", "TEXT", "PRIMARY KEY"),
        "user_id": ("TEXT", "TEXT", "REFERENCES users(id) ON DELETE CASCADE"),
        "data": ("TEXT", "JSONB", None),
        "created_at": ("TEXT", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP"),
        "updated_at": ("TEXT", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP"),
        "expires_at": ("TEXT", "TIMESTAMPTZ", None)
    },
    "analytics": {
        "id": ("TEXT", "TEXT", "PRIMARY KEY"),
        "session_id": ("TEXT", "TEXT", None),
        "user_id": ("TEXT", "TEXT", "REFERENCES users(id) ON DELETE SET NULL"),
        "event_type": ("TEXT", "TEXT", "NOT NULL"),
        "event_data": ("TEXT", "JSONB", None),
        "timestamp": ("TEXT", "TIMESTAMPTZ", "DEFAULT CURRENT_TIMESTAMP")
    }
}

# Index definitions
INDEX_DEFINITIONS = {
    "attractions": [
        ("idx_attractions_name", "name_en, name_ar"),
        ("idx_attractions_type", "type"),
        ("idx_attractions_city", "city"),
        ("idx_attractions_user", "user_id"),
        ("idx_attractions_geom", "USING GIST (geom)"),
        ("idx_attractions_embedding", "USING ivfflat (embedding vector_cosine_ops)")
    ],
    "accommodations": [
        ("idx_accommodations_name", "name_en, name_ar"),
        ("idx_accommodations_type", "type"),
        ("idx_accommodations_city", "city"),
        ("idx_accommodations_category", "category"),
        ("idx_accommodations_price", "price_min, price_max"),
        ("idx_accommodations_geom", "USING GIST (geom)"),
        ("idx_accommodations_embedding", "USING ivfflat (embedding vector_cosine_ops)")
    ],
    "restaurants": [
        ("idx_restaurants_name", "name_en, name_ar"),
        ("idx_restaurants_cuisine", "cuisine"),
        ("idx_restaurants_city", "city"),
        ("idx_restaurants_price", "price_range"),
        ("idx_restaurants_geom", "USING GIST (geom)"),
        ("idx_restaurants_embedding", "USING ivfflat (embedding vector_cosine_ops)")
    ],
    "users": [
        ("idx_users_username", "username"),
        ("idx_users_email", "email"),
        ("idx_users_role", "role")
    ],
    "sessions": [
        ("idx_sessions_user", "user_id"),
        ("idx_sessions_expires", "expires_at")
    ],
    "analytics": [
        ("idx_analytics_session", "session_id"),
        ("idx_analytics_user", "user_id"),
        ("idx_analytics_type", "event_type"),
        ("idx_analytics_time", "timestamp")
    ]
}

class DatabaseMigrator:
    """Handles migration between SQLite and PostgreSQL databases."""
    
    def __init__(self, sqlite_path: str, pg_uri: str):
        self.sqlite_path = sqlite_path
        self.pg_uri = pg_uri
        self.batch_size = 1000

    def connect_sqlite(self) -> sqlite3.Connection:
        """Connect to SQLite database"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise

    def connect_postgres(self) -> psycopg2.extensions.connection:
        """Connect to PostgreSQL database"""
        try:
            return psycopg2.connect(self.pg_uri)
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def setup_postgres(self, conn: psycopg2.extensions.connection) -> None:
        """Set up PostgreSQL extensions and schemas"""
        try:
            with conn.cursor() as cur:
                # Enable required extensions
                cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to setup PostgreSQL extensions: {e}")
            conn.rollback()
            raise

    def create_postgres_schema(self, conn: psycopg2.extensions.connection) -> None:
        """Create PostgreSQL schema from definitions"""
        try:
            with conn.cursor() as cur:
                # Create tables in correct order (users first due to foreign keys)
                ordered_tables = ["users", "attractions", "accommodations", 
                                "restaurants", "sessions", "analytics"]
                
                for table in ordered_tables:
                    columns = []
                    for col, (_, pg_type, constraints) in SCHEMA_DEFINITIONS[table].items():
                        if pg_type:  # Skip columns that don't exist in PostgreSQL
                            col_def = f"{col} {pg_type}"
                            if constraints:
                                col_def += f" {constraints}"
                            columns.append(col_def)
                    
                    sql = f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        {', '.join(columns)}
                    )"""
                    cur.execute(sql)
                
                # Create indexes
                for table, indexes in INDEX_DEFINITIONS.items():
                    for idx_name, idx_def in indexes:
                        sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({idx_def})"
                        cur.execute(sql)
                
                conn.commit()
                logger.info("PostgreSQL schema created successfully")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL schema: {e}")
            conn.rollback()
            raise

    def convert_value(self, value: Any, sqlite_type: str, pg_type: str) -> Any:
        """Convert a value from SQLite to PostgreSQL format"""
        if value is None:
            return None
            
        try:
            if pg_type == "JSONB":
                if isinstance(value, str):
                    return Json(json.loads(value))
                return Json(value)
            elif pg_type == "TIMESTAMPTZ":
                if isinstance(value, str):
                    if value == "":
                        return None
                    # Try common date formats
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
                return value
            elif pg_type.startswith("NUMERIC"):
                return float(value) if value else None
            
            return value
        except Exception as e:
            logger.warning(f"Failed to convert value {value} from {sqlite_type} to {pg_type}: {e}")
            return value

    def migrate_table(self, sqlite_conn: sqlite3.Connection, 
                     pg_conn: psycopg2.extensions.connection,
                     table: str) -> Tuple[int, int]:
        """Migrate data from SQLite to PostgreSQL for a single table"""
        inserted = 0
        errors = 0
        
        try:
            # Get columns that exist in both databases
            columns = []
            pg_types = []
            for col, (sqlite_type, pg_type, _) in SCHEMA_DEFINITIONS[table].items():
                if sqlite_type and pg_type:  # Column exists in both databases
                    columns.append(col)
                    pg_types.append(pg_type)

            # Prepare SQL statements
            sqlite_sql = f"SELECT {', '.join(columns)} FROM {table}"
            pg_sql = f"""
                INSERT INTO {table} ({', '.join(columns)}) 
                VALUES ({', '.join(['%s'] * len(columns))})
                ON CONFLICT (id) DO UPDATE SET 
                {', '.join(f"{col} = EXCLUDED.{col}" for col in columns if col != 'id')}
            """

            # Migrate in batches
            with sqlite_conn.cursor() as sqlite_cur, pg_conn.cursor() as pg_cur:
                sqlite_cur.execute(sqlite_sql)
                
                while True:
                    rows = sqlite_cur.fetchmany(self.batch_size)
                    if not rows:
                        break
                        
                    for row in rows:
                        try:
                            # Convert row to dict and handle type conversions
                            values = []
                            row_dict = dict(row)
                            for col, pg_type in zip(columns, pg_types):
                                value = self.convert_value(
                                    row_dict[col],
                                    SCHEMA_DEFINITIONS[table][col][0],
                                    pg_type
                                )
                                values.append(value)
                            
                            pg_cur.execute(pg_sql, values)
                            inserted += 1
                        except Exception as e:
                            logger.error(f"Error migrating row in {table}: {e}")
                            errors += 1
                            continue
                    
                    # Commit each batch
                    pg_conn.commit()
                    
                # Update spatial data if applicable
                if table in ["attractions", "accommodations", "restaurants"]:
                    pg_cur.execute(f"""
                        UPDATE {table} 
                        SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
                        WHERE latitude IS NOT NULL AND longitude IS NOT NULL 
                          AND geom IS NULL
                    """)
                    pg_conn.commit()

            return inserted, errors
            
        except Exception as e:
            logger.error(f"Failed to migrate table {table}: {e}")
            pg_conn.rollback()
            return inserted, errors

    def validate_migration(self, sqlite_conn: sqlite3.Connection,
                         pg_conn: psycopg2.extensions.connection,
                         table: str) -> Dict[str, Any]:
        """Validate migration results for a table"""
        try:
            with sqlite_conn.cursor() as sqlite_cur, pg_conn.cursor() as pg_cur:
                # Get row counts
                sqlite_cur.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_count = sqlite_cur.fetchone()[0]
                
                pg_cur.execute(f"SELECT COUNT(*) FROM {table}")
                pg_count = pg_cur.fetchone()[0]
                
                # Calculate percentage
                percentage = (pg_count / sqlite_count * 100) if sqlite_count > 0 else 100
                is_valid = sqlite_count == pg_count
                
                return {
                    "table": table,
                    "sqlite_count": sqlite_count,
                    "postgres_count": pg_count,
                    "percentage": percentage,
                    "is_valid": is_valid
                }
        except Exception as e:
            logger.error(f"Failed to validate migration for table {table}: {e}")
            return {
                "table": table,
                "error": str(e)
            }

    def run_migration(self) -> Dict[str, Any]:
        """Run the complete migration process"""
        results = {}
        
        try:
            # Connect to both databases
            sqlite_conn = self.connect_sqlite()
            pg_conn = self.connect_postgres()
            
            # Setup PostgreSQL
            self.setup_postgres(pg_conn)
            self.create_postgres_schema(pg_conn)
            
            # Migrate each table
            for table in SCHEMA_DEFINITIONS.keys():
                logger.info(f"Migrating table: {table}")
                inserted, errors = self.migrate_table(sqlite_conn, pg_conn, table)
                validation = self.validate_migration(sqlite_conn, pg_conn, table)
                
                results[table] = {
                    "inserted": inserted,
                    "errors": errors,
                    "validation": validation
                }
                
                logger.info(f"Migration results for {table}: "
                          f"Inserted {inserted}, Errors {errors}, "
                          f"Valid: {validation.get('is_valid', False)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return {"error": str(e)}
        finally:
            try:
                sqlite_conn.close()
                pg_conn.close()
            except:
                pass

def main():
    """Main entry point for the migration script"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Database Migration Tool")
    parser.add_argument("--sqlite-path", default="./data/egypt_chatbot.db",
                      help="Path to SQLite database")
    parser.add_argument("--pg-uri", 
                      default="postgresql://localhost:5432/egypt_chatbot",
                      help="PostgreSQL connection URI")
    parser.add_argument("--batch-size", type=int, default=1000,
                      help="Batch size for processing rows")
    parser.add_argument("--log-file",
                      default=f"migration_{datetime.now():%Y%m%d_%H%M%S}.log",
                      help="Log file path")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(args.log_file)
        ]
    )
    
    # Run migration
    migrator = DatabaseMigrator(args.sqlite_path, args.pg_uri)
    migrator.batch_size = args.batch_size
    results = migrator.run_migration()
    
    # Print summary
    logger.info("\nMigration Summary:")
    for table, result in results.items():
        if "error" in result:
            logger.error(f"{table}: {result['error']}")
        else:
            validation = result["validation"]
            logger.info(f"{table}:")
            logger.info(f"  - Inserted: {result['inserted']}")
            logger.info(f"  - Errors: {result['errors']}")
            logger.info(f"  - Valid: {validation.get('is_valid', False)}")
            logger.info(f"  - Coverage: {validation.get('percentage', 0):.2f}%")

if __name__ == "__main__":
    main()