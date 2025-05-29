"""
Database initialization module for the Egypt Tourism Chatbot.

This module provides functions for initializing the PostgreSQL database
with the correct schema, including tables, indexes, and foreign keys.
"""

import logging
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import Dict, List, Optional, Tuple, Any

# Configure logging
logger = logging.getLogger(__name__)

# Table definitions with dependencies
TABLE_DEFINITIONS = {
    "users": {
        "sql": """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMPTZ,
                preferences JSONB,
                role TEXT DEFAULT 'user'
            )
        """,
        "dependencies": [],
        "indexes": [
            ("idx_users_username", "username"),
            ("idx_users_email", "email"),
            ("idx_users_role", "role")
        ]
    },
    "regions": {
        "sql": """
            CREATE TABLE IF NOT EXISTS regions (
                id TEXT PRIMARY KEY,
                name JSONB NOT NULL,
                description JSONB,
                country TEXT,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                data JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT
            );

            -- Add foreign key if it doesn't exist
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'regions_user_id_fkey' AND conrelid = 'regions'::regclass
                ) THEN
                    ALTER TABLE regions ADD CONSTRAINT regions_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
                END IF;
            EXCEPTION
                WHEN undefined_table THEN
                    -- Table doesn't exist yet, which is fine
                WHEN undefined_column THEN
                    -- Column doesn't exist yet, which is fine
                WHEN others THEN
                    RAISE;
            END $$;
        """,
        "dependencies": ["users"],
        "indexes": [
            ("idx_regions_name_jsonb", "name", "gin"),
            ("idx_regions_country", "country")
        ]
    },
    "cities": {
        "sql": """
            CREATE TABLE IF NOT EXISTS cities (
                id TEXT PRIMARY KEY,
                name JSONB NOT NULL,
                description JSONB,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                data JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                region_id TEXT
            );

            -- Add foreign keys if they don't exist
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'cities_user_id_fkey' AND conrelid = 'cities'::regclass
                ) THEN
                    ALTER TABLE cities ADD CONSTRAINT cities_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
                END IF;

                -- Add foreign key for region_id if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'cities_region_id_fkey' AND conrelid = 'cities'::regclass
                ) THEN
                    ALTER TABLE cities ADD CONSTRAINT cities_region_id_fkey
                    FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE SET NULL;
                END IF;
            EXCEPTION
                WHEN undefined_table THEN
                    -- Table doesn't exist yet, which is fine
                WHEN undefined_column THEN
                    -- Column doesn't exist yet, which is fine
                WHEN others THEN
                    RAISE;
            END $$;
        """,
        "dependencies": ["users", "regions"],
        "indexes": [
            ("idx_cities_name_jsonb", "name", "gin"),
            ("idx_cities_region_id", "region_id")
        ]
    },
    "attractions": {
        "sql": """
            CREATE TABLE IF NOT EXISTS attractions (
                id TEXT PRIMARY KEY,
                name JSONB NOT NULL,
                description JSONB,
                type_id TEXT,
                city_id TEXT,
                region_id TEXT,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                data JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );

            -- Add user_id column and foreign key if they don't exist
            DO $$
            BEGIN
                -- Add user_id column if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'attractions' AND column_name = 'user_id'
                ) THEN
                    ALTER TABLE attractions ADD COLUMN user_id TEXT;

                    -- Add foreign key for user_id
                    ALTER TABLE attractions ADD CONSTRAINT attractions_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
                END IF;
            EXCEPTION
                WHEN undefined_table THEN
                    -- Table doesn't exist yet, which is fine
                WHEN undefined_column THEN
                    -- Column doesn't exist yet, which is fine
                WHEN others THEN
                    RAISE;
            END $$;
        """,
        "dependencies": ["users"],
        "indexes": [
            ("idx_attractions_name_jsonb", "name", "gin"),
            ("idx_attractions_type_id", "type_id"),
            ("idx_attractions_city_id", "city_id")
        ]
    },
    "restaurants": {
        "sql": """
            CREATE TABLE IF NOT EXISTS restaurants (
                id TEXT PRIMARY KEY,
                name JSONB NOT NULL,
                description JSONB,
                cuisine_id TEXT,
                type_id TEXT,
                city_id TEXT,
                region_id TEXT,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                data JSONB,
                price_range TEXT,
                rating DOUBLE PRECISION,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );

            -- Add user_id column and foreign key if they don't exist
            DO $$
            BEGIN
                -- Add user_id column if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'restaurants' AND column_name = 'user_id'
                ) THEN
                    ALTER TABLE restaurants ADD COLUMN user_id TEXT;

                    -- Add foreign key for user_id
                    ALTER TABLE restaurants ADD CONSTRAINT restaurants_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
                END IF;
            EXCEPTION
                WHEN undefined_table THEN
                    -- Table doesn't exist yet, which is fine
                WHEN undefined_column THEN
                    -- Column doesn't exist yet, which is fine
                WHEN others THEN
                    RAISE;
            END $$;
        """,
        "dependencies": ["users"],
        "indexes": [
            ("idx_restaurants_name_jsonb", "name", "gin"),
            ("idx_restaurants_cuisine_id", "cuisine_id"),
            ("idx_restaurants_city_id", "city_id"),
            ("idx_restaurants_price_range", "price_range")
        ]
    },
    "accommodations": {
        "sql": """
            CREATE TABLE IF NOT EXISTS accommodations (
                id TEXT PRIMARY KEY,
                name JSONB NOT NULL,
                description JSONB,
                type_id TEXT,
                stars INTEGER,
                city_id TEXT,
                region_id TEXT,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                data JSONB,
                price_min NUMERIC,
                price_max NUMERIC,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );

            -- Add user_id column and foreign key if they don't exist
            DO $$
            BEGIN
                -- Add user_id column if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'accommodations' AND column_name = 'user_id'
                ) THEN
                    ALTER TABLE accommodations ADD COLUMN user_id TEXT;

                    -- Add foreign key for user_id
                    ALTER TABLE accommodations ADD CONSTRAINT accommodations_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
                END IF;
            EXCEPTION
                WHEN undefined_table THEN
                    -- Table doesn't exist yet, which is fine
                WHEN undefined_column THEN
                    -- Column doesn't exist yet, which is fine
                WHEN others THEN
                    RAISE;
            END $$;
        """,
        "dependencies": ["users"],
        "indexes": [
            ("idx_accommodations_name_jsonb", "name", "gin"),
            ("idx_accommodations_type_id", "type_id"),
            ("idx_accommodations_city_id", "city_id"),
            ("idx_accommodations_price", "price_min, price_max")
        ]
    },
    "sessions": {
        "sql": """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                data JSONB,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMPTZ
            );

            -- Add user_id column and foreign key if they don't exist
            DO $$
            BEGIN
                -- Add user_id column if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'sessions' AND column_name = 'user_id'
                ) THEN
                    ALTER TABLE sessions ADD COLUMN user_id TEXT;

                    -- Add foreign key for user_id
                    ALTER TABLE sessions ADD CONSTRAINT sessions_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                END IF;
            EXCEPTION
                WHEN undefined_table THEN
                    -- Table doesn't exist yet, which is fine
                WHEN undefined_column THEN
                    -- Column doesn't exist yet, which is fine
                WHEN others THEN
                    RAISE;
            END $$;
        """,
        "dependencies": ["users"],
        "indexes": [
            ("idx_sessions_expires", "expires_at")
        ]
    },
    "analytics": {
        "sql": """
            CREATE TABLE IF NOT EXISTS analytics (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                event_type TEXT NOT NULL,
                event_data JSONB,
                timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );

            -- Add user_id column and foreign key if they don't exist
            DO $$
            BEGIN
                -- Add user_id column if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'analytics' AND column_name = 'user_id'
                ) THEN
                    ALTER TABLE analytics ADD COLUMN user_id TEXT;

                    -- Add foreign key for user_id
                    ALTER TABLE analytics ADD CONSTRAINT analytics_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
                END IF;
            EXCEPTION
                WHEN undefined_table THEN
                    -- Table doesn't exist yet, which is fine
                WHEN undefined_column THEN
                    -- Column doesn't exist yet, which is fine
                WHEN others THEN
                    RAISE;
            END $$;
        """,
        "dependencies": ["users"],
        "indexes": [
            ("idx_analytics_session", "session_id"),
            ("idx_analytics_type", "event_type"),
            ("idx_analytics_time", "timestamp")
        ]
    }
}

def topological_sort(table_definitions: Dict[str, Dict]) -> List[str]:
    """
    Sort tables in topological order based on dependencies.

    Args:
        table_definitions: Dictionary of table definitions with dependencies

    Returns:
        List of table names in dependency order
    """
    # Create a copy of the table definitions to avoid modifying the original
    remaining_tables = {name: table.copy() for name, table in table_definitions.items()}

    # Initialize the result list
    result = []

    # Process tables until all are processed or no progress can be made
    while remaining_tables:
        # Find tables with no unresolved dependencies
        ready_tables = [
            name for name, table in remaining_tables.items()
            if all(dep not in remaining_tables for dep in table["dependencies"])
        ]

        # If no tables are ready, there's a circular dependency
        if not ready_tables:
            raise ValueError("Circular dependency detected in table definitions")

        # Add ready tables to the result and remove them from remaining tables
        for name in ready_tables:
            result.append(name)
            del remaining_tables[name]

    return result

def create_postgres_tables(conn: psycopg2.extensions.connection, vector_dimension: int = 1536) -> None:
    """
    Create required tables in PostgreSQL if they don't exist.

    Args:
        conn: PostgreSQL connection
        vector_dimension: Dimension of vector embeddings
    """
    # Sort tables in topological order
    ordered_tables = topological_sort(TABLE_DEFINITIONS)
    logger.info(f"Creating tables in order: {ordered_tables}")

    # Process each table in a separate transaction
    for table_name in ordered_tables:
        table_def = TABLE_DEFINITIONS[table_name]

        # Create table in its own transaction
        with conn:  # This automatically handles commit/rollback
            with conn.cursor() as cursor:
                # Create table
                try:
                    cursor.execute(table_def["sql"])
                    logger.info(f"Created or verified table: {table_name}")
                except Exception as e:
                    logger.error(f"Error creating table {table_name}: {str(e)}")
                    # Continue with next table instead of failing completely
                    continue

    # Create indexes in a separate pass
    for table_name in ordered_tables:
        table_def = TABLE_DEFINITIONS[table_name]

        # Create indexes in their own transaction
        with conn:  # This automatically handles commit/rollback
            with conn.cursor() as cursor:
                # Create indexes
                for index_def in table_def.get("indexes", []):
                    try:
                        if len(index_def) == 2:
                            # Regular index: (name, columns)
                            index_name, index_columns = index_def
                            cursor.execute(f"""
                                CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({index_columns})
                            """)
                        elif len(index_def) == 3:
                            # Special index with method: (name, columns, method)
                            index_name, index_columns, index_method = index_def
                            cursor.execute(f"""
                                CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} USING {index_method} ({index_columns})
                            """)
                        logger.info(f"Created or verified index: {index_name}")
                    except Exception as e:
                        logger.warning(f"Error creating index {index_def[0]}: {str(e)}")

    # Add geometry columns if PostGIS is available
    with conn:
        with conn.cursor() as cursor:
            try:
                # Check if PostGIS extension exists
                cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'postgis'")
                if cursor.fetchone():
                    # Add geometry columns to appropriate tables
                    tables_with_geo = ["attractions", "restaurants", "accommodations", "cities", "regions"]
                    for table in tables_with_geo:
                        try:
                            cursor.execute(f"""
                                ALTER TABLE {table} ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);
                            """)
                            logger.info(f"Added geometry column to {table}")

                            # Create spatial index in a separate statement
                            try:
                                cursor.execute(f"""
                                    CREATE INDEX IF NOT EXISTS idx_{table}_geom ON {table} USING GIST (geom);
                                """)
                                logger.info(f"Created spatial index for {table}")
                            except Exception as e:
                                logger.warning(f"Error creating spatial index for {table}: {str(e)}")

                        except Exception as e:
                            logger.warning(f"Error adding geometry column to {table}: {str(e)}")
            except Exception as e:
                logger.warning(f"Error checking for PostGIS extension: {str(e)}")

    # Add vector columns if pgvector is available
    with conn:
        with conn.cursor() as cursor:
            try:
                # Check if vector extension exists
                cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                if cursor.fetchone():
                    # Add vector columns to appropriate tables
                    tables_with_vector = ["attractions", "restaurants", "accommodations", "cities"]
                    for table in tables_with_vector:
                        try:
                            cursor.execute(f"""
                                ALTER TABLE {table} ADD COLUMN IF NOT EXISTS embedding vector({vector_dimension});
                            """)
                            logger.info(f"Added vector column to {table}")

                            # Create vector index in a separate statement
                            try:
                                cursor.execute(f"""
                                    CREATE INDEX IF NOT EXISTS idx_{table}_embedding
                                    ON {table} USING ivfflat (embedding vector_cosine_ops);
                                """)
                                logger.info(f"Created vector index for {table}")
                            except Exception as e:
                                logger.warning(f"Error creating vector index for {table}: {str(e)}")

                        except Exception as e:
                            logger.warning(f"Error adding vector column to {table}: {str(e)}")
            except Exception as e:
                logger.warning(f"Error checking for vector extension: {str(e)}")

    logger.info("Database initialization completed successfully")
