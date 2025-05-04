"""
Tests for database initialization functionality.
"""

import os
import pytest
import psycopg2
import logging
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from src.knowledge.database import DatabaseManager
from src.knowledge.database_init import create_postgres_tables, topological_sort, TABLE_DEFINITIONS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test database URI
TEST_DB_URI = os.environ.get("POSTGRES_URI") or "postgresql://postgres:postgres@localhost:5432/egypt_chatbot_test"

@pytest.fixture(scope="module")
def test_db_connection():
    """Create a test database and return a connection to it."""
    # Extract database name from URI
    db_uri_parts = TEST_DB_URI.split("/")
    db_name = db_uri_parts[-1]
    base_uri = "/".join(db_uri_parts[:-1])

    # Connect to PostgreSQL server (without specifying a database)
    conn = psycopg2.connect(f"{base_uri}/postgres")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        # Create test database if it doesn't exist
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            if not cursor.fetchone():
                cursor.execute(f"CREATE DATABASE {db_name}")
                logger.info(f"Created test database: {db_name}")
            else:
                logger.info(f"Test database {db_name} already exists")

        # Close connection to postgres database
        conn.close()

        # Connect to the test database
        test_conn = psycopg2.connect(TEST_DB_URI)
        test_conn.set_session(autocommit=True)  # Use autocommit mode for setup

        # Enable required extensions
        with test_conn.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Drop all existing tables to start fresh, excluding PostGIS system tables
            cursor.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename NOT IN ('spatial_ref_sys', 'geography_columns', 'geometry_columns')
            """)
            tables = [row[0] for row in cursor.fetchall()]

            # Disable foreign key checks
            cursor.execute("SET session_replication_role = 'replica'")

            # Drop tables
            for table in tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                except Exception as e:
                    logger.warning(f"Could not drop table {table}: {e}")

            # Re-enable foreign key checks
            cursor.execute("SET session_replication_role = 'origin'")

        # Switch back to normal transaction mode for tests
        test_conn.set_session(autocommit=False)

        yield test_conn

        # Clean up: Drop all tables
        test_conn.set_session(autocommit=True)  # Use autocommit mode for cleanup
        with test_conn.cursor() as cursor:
            cursor.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename NOT IN ('spatial_ref_sys', 'geography_columns', 'geometry_columns')
            """)
            tables = [row[0] for row in cursor.fetchall()]

            # Disable foreign key checks
            cursor.execute("SET session_replication_role = 'replica'")

            # Drop tables
            for table in tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                except Exception as e:
                    logger.warning(f"Could not drop table {table}: {e}")

            # Re-enable foreign key checks
            cursor.execute("SET session_replication_role = 'origin'")

        test_conn.close()

    except Exception as e:
        logger.error(f"Error setting up test database: {e}")
        if 'conn' in locals() and conn and not conn.closed:
            conn.close()
        if 'test_conn' in locals() and test_conn and not test_conn.closed:
            test_conn.close()
        raise

def test_topological_sort():
    """Test that tables are sorted correctly based on dependencies."""
    # Create a simple dependency graph
    test_tables = {
        "table1": {"dependencies": []},
        "table2": {"dependencies": ["table1"]},
        "table3": {"dependencies": ["table1", "table2"]},
        "table4": {"dependencies": ["table3"]},
    }

    # Sort tables
    sorted_tables = topological_sort(test_tables)

    # Check that dependencies come before dependents
    assert sorted_tables.index("table1") < sorted_tables.index("table2")
    assert sorted_tables.index("table2") < sorted_tables.index("table3")
    assert sorted_tables.index("table3") < sorted_tables.index("table4")

def test_create_postgres_tables(test_db_connection):
    """Test that tables are created correctly in the database."""
    # Create tables
    create_postgres_tables(test_db_connection)

    # Check that tables exist
    with test_db_connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]

        # Check that all tables were created
        for table_name in TABLE_DEFINITIONS.keys():
            assert table_name in tables, f"Table {table_name} was not created"

        # Check that foreign keys were created correctly
        cursor.execute("""
            SELECT
                tc.table_name, kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM
                information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
            WHERE constraint_type = 'FOREIGN KEY'
        """)

        foreign_keys = cursor.fetchall()

        # Check that user_id foreign keys were created
        user_fks = [fk for fk in foreign_keys if fk[1] == 'user_id' and fk[2] == 'users']
        assert len(user_fks) > 0, "No user_id foreign keys were created"

        # Check that indexes were created
        cursor.execute("""
            SELECT indexname, tablename
            FROM pg_indexes
            WHERE schemaname = 'public'
        """)

        indexes = cursor.fetchall()
        index_count = len(indexes)

        assert index_count > 0, "No indexes were created"
        logger.info(f"Created {index_count} indexes")

def test_database_manager_initialization():
    """Test that DatabaseManager initializes the database correctly."""
    # Set environment variable for test database
    os.environ["POSTGRES_URI"] = TEST_DB_URI

    # Initialize DatabaseManager
    db_manager = DatabaseManager()

    # Check that connection pool is initialized
    assert db_manager.pg_pool is not None

    # Check that tables exist by querying one of them
    result = db_manager.execute_query("SELECT COUNT(*) FROM users")

    # Result should be a list with one dictionary
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 1

    # Clean up
    db_manager.close()

def test_foreign_key_constraints(test_db_connection):
    """Test that foreign key constraints work correctly."""
    # First, create the tables
    create_postgres_tables(test_db_connection)

    # Try to insert a record with a non-existent user_id
    with test_db_connection:  # Use transaction
        with test_db_connection.cursor() as cursor:
            # First, make sure the users table exists and has the expected schema
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'users'
            """)
            columns = cursor.fetchall()
            assert len(columns) > 0, "Users table does not exist or has no columns"

            # Insert a test user
            cursor.execute("""
                INSERT INTO users (id, username, email)
                VALUES ('test_user', 'testuser', 'test@example.com')
                ON CONFLICT (id) DO NOTHING
            """)

    # Verify that the user_id column exists in attractions
    with test_db_connection:
        with test_db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'attractions' AND column_name = 'user_id'
            """)
            user_id_column = cursor.fetchone()
            assert user_id_column is not None, "user_id column does not exist in attractions table"

    # Insert a record with the test user_id
    with test_db_connection:
        with test_db_connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO attractions (id, name_en, user_id)
                VALUES ('test_attraction', 'Test Attraction', 'test_user')
                ON CONFLICT (id) DO NOTHING
            """)

    # Try to insert a record with a non-existent user_id
    try:
        with test_db_connection:
            with test_db_connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO attractions (id, name_en, user_id)
                    VALUES ('test_attraction2', 'Test Attraction 2', 'nonexistent_user')
                """)
        assert False, "Foreign key constraint not enforced"
    except psycopg2.errors.ForeignKeyViolation:
        # This is expected
        pass

    # Clean up
    with test_db_connection:
        with test_db_connection.cursor() as cursor:
            cursor.execute("DELETE FROM attractions WHERE id = 'test_attraction'")
            cursor.execute("DELETE FROM users WHERE id = 'test_user'")

    # Verify that the records were deleted
    with test_db_connection:
        with test_db_connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM attractions WHERE id = 'test_attraction'")
            assert cursor.fetchone()[0] == 0, "Failed to delete test attraction"

            cursor.execute("SELECT COUNT(*) FROM users WHERE id = 'test_user'")
            assert cursor.fetchone()[0] == 0, "Failed to delete test user"
