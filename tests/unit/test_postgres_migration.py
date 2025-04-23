#!/usr/bin/env python3
"""
Unit tests for the PostgreSQL migration script.

These tests verify that the migration script correctly:
1. Maps SQLite types to PostgreSQL types
2. Creates PostgreSQL tables with the correct structure
3. Migrates data from SQLite to PostgreSQL
4. Adds vector columns for embeddings
5. Creates vector indexes for similarity search
6. Adds geospatial columns and indexes
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)

# Import the migration script
from scripts.migrate_to_postgres import (
    get_sqlite_connection,
    get_postgres_connection,
    check_postgres_extensions,
    get_sqlite_tables,
    get_table_columns,
    map_sqlite_to_postgres_type,
    create_postgres_table,
    migrate_table_data,
    add_vector_column,
    create_vector_index,
    add_geospatial_columns,
    REQUIRED_EXTENSIONS
)


class TestPostgresMigration(unittest.TestCase):
    """Test the PostgreSQL migration script."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock database connections
        self.sqlite_conn_patcher = patch('scripts.migrate_to_postgres.sqlite3.connect')
        self.pg_conn_patcher = patch('scripts.migrate_to_postgres.psycopg2.connect')
        
        self.mock_sqlite_connect = self.sqlite_conn_patcher.start()
        self.mock_pg_connect = self.pg_conn_patcher.start()
        
        # Create mock connections and cursors
        self.mock_sqlite_conn = MagicMock()
        self.mock_pg_conn = MagicMock()
        
        self.mock_sqlite_cursor = MagicMock()
        self.mock_pg_cursor = MagicMock()
        
        self.mock_sqlite_conn.cursor.return_value = self.mock_sqlite_cursor
        self.mock_pg_conn.cursor.return_value = self.mock_pg_cursor
        
        self.mock_sqlite_connect.return_value = self.mock_sqlite_conn
        self.mock_pg_connect.return_value = self.mock_pg_conn
        
        # Sample table data
        self.sample_tables = ['attractions', 'cities', 'hotels', 'restaurants']
        self.sample_columns = [
            {'name': 'id', 'type': 'INTEGER'},
            {'name': 'name', 'type': 'TEXT'},
            {'name': 'description', 'type': 'TEXT'},
            {'name': 'latitude', 'type': 'REAL'},
            {'name': 'longitude', 'type': 'REAL'}
        ]
        
        # Sample query results
        self.mock_sqlite_cursor.fetchall.return_value = [
            {'name': 'attractions'}, 
            {'name': 'cities'}, 
            {'name': 'hotels'}, 
            {'name': 'restaurants'}
        ]

    def tearDown(self):
        """Tear down test fixtures."""
        self.sqlite_conn_patcher.stop()
        self.pg_conn_patcher.stop()

    def test_get_sqlite_connection(self):
        """Test that get_sqlite_connection creates a connection."""
        conn = get_sqlite_connection('test.db')
        self.assertEqual(conn, self.mock_sqlite_conn)
        self.mock_sqlite_connect.assert_called_once_with('test.db')

    def test_get_postgres_connection(self):
        """Test that get_postgres_connection creates a connection."""
        conn = get_postgres_connection('postgresql://user:pass@localhost/db')
        self.assertEqual(conn, self.mock_pg_conn)
        self.mock_pg_connect.assert_called_once_with('postgresql://user:pass@localhost/db')

    def test_check_postgres_extensions(self):
        """Test that check_postgres_extensions checks for required extensions."""
        # Mock cursor to return True for all extensions
        self.mock_pg_cursor.fetchone.return_value = [True]
        
        result = check_postgres_extensions(self.mock_pg_conn)
        self.assertTrue(result)
        
        # Verify the cursor called execute for each extension
        self.assertEqual(self.mock_pg_cursor.execute.call_count, len(REQUIRED_EXTENSIONS))

    def test_check_postgres_extensions_missing(self):
        """Test check_postgres_extensions when an extension is missing."""
        # Mock cursor to return False for one extension
        self.mock_pg_cursor.fetchone.side_effect = [[False], [True]]
        
        result = check_postgres_extensions(self.mock_pg_conn)
        self.assertFalse(result)

    def test_get_sqlite_tables(self):
        """Test that get_sqlite_tables returns a list of tables."""
        tables = get_sqlite_tables(self.mock_sqlite_conn)
        self.assertEqual(tables, self.sample_tables)
        
        # Verify the cursor executed the correct query
        self.mock_sqlite_cursor.execute.assert_called_once_with(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )

    def test_get_table_columns(self):
        """Test that get_table_columns returns column information."""
        # Set up mock return value for PRAGMA table_info
        self.mock_sqlite_cursor.fetchall.return_value = [
            {'name': 'id', 'type': 'INTEGER', 'notnull': 1, 'dflt_value': None, 'pk': 1},
            {'name': 'name', 'type': 'TEXT', 'notnull': 1, 'dflt_value': None, 'pk': 0}
        ]
        
        columns = get_table_columns(self.mock_sqlite_conn, 'attractions')
        expected_columns = [
            {'name': 'id', 'type': 'INTEGER'},
            {'name': 'name', 'type': 'TEXT'}
        ]
        
        self.assertEqual(columns, expected_columns)
        
        # Verify the cursor executed the correct query
        self.mock_sqlite_cursor.execute.assert_called_once_with("PRAGMA table_info(attractions)")

    def test_map_sqlite_to_postgres_type(self):
        """Test mapping of SQLite types to PostgreSQL types."""
        test_cases = [
            ('INTEGER', 'INTEGER'),
            ('INT', 'INTEGER'),
            ('REAL', 'REAL'),
            ('TEXT', 'TEXT'),
            ('VARCHAR(255)', 'VARCHAR'),
            ('BOOLEAN', 'BOOLEAN'),
            ('UNKNOWN_TYPE', 'TEXT')  # Default for unknown types
        ]
        
        for sqlite_type, expected_pg_type in test_cases:
            with self.subTest(sqlite_type=sqlite_type):
                pg_type = map_sqlite_to_postgres_type(sqlite_type)
                self.assertEqual(pg_type, expected_pg_type)

    def test_create_postgres_table(self):
        """Test that create_postgres_table creates a table with the correct structure."""
        result = create_postgres_table(self.mock_pg_conn, 'attractions', self.sample_columns)
        self.assertTrue(result)
        
        # Verify the cursor called execute with the correct SQL
        self.mock_pg_cursor.execute.assert_called_once()
        create_call = self.mock_pg_cursor.execute.call_args[0][0]
        
        # Check that the SQL creates a table with the correct columns
        self.assertIn('CREATE TABLE IF NOT EXISTS attractions', create_call)
        for col in self.sample_columns:
            pg_type = map_sqlite_to_postgres_type(col['type'])
            self.assertIn(f"{col['name']} {pg_type}", create_call)
        
        # Verify the transaction was committed
        self.mock_pg_conn.commit.assert_called_once()

    @patch('scripts.migrate_to_postgres.execute_values')
    def test_migrate_table_data(self, mock_execute_values):
        """Test that migrate_table_data migrates data correctly."""
        # Setup mock data
        self.mock_sqlite_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'Pyramids', 'description': 'Ancient pyramids', 'latitude': 29.9792, 'longitude': 31.1342},
            {'id': 2, 'name': 'Sphinx', 'description': 'Ancient sphinx', 'latitude': 29.9753, 'longitude': 31.1376}
        ]
        
        # Call the function
        rows = migrate_table_data(self.mock_sqlite_conn, self.mock_pg_conn, 'attractions', self.sample_columns)
        
        # Verify results
        self.assertEqual(rows, 2)
        
        # Verify execute_values was called correctly
        mock_execute_values.assert_called_once()
        
        # Verify the transaction was committed
        self.mock_pg_conn.commit.assert_called_once()

    def test_add_vector_column(self):
        """Test that add_vector_column adds a vector column to a table."""
        # Mock column doesn't exist
        self.mock_pg_cursor.fetchone.return_value = None
        
        result = add_vector_column(self.mock_pg_conn, 'attractions', 'embedding')
        self.assertTrue(result)
        
        # Verify the cursor executed the correct SQL
        self.mock_pg_cursor.execute.assert_any_call(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'attractions' AND column_name = 'embedding'"
        )
        
        # Verify the transaction was committed
        self.mock_pg_conn.commit.assert_called_once()

    def test_create_vector_index(self):
        """Test that create_vector_index creates a vector index."""
        # Mock index doesn't exist
        self.mock_pg_cursor.fetchone.return_value = None
        
        result = create_vector_index(self.mock_pg_conn, 'attractions', 'embedding')
        self.assertTrue(result)
        
        # Verify the cursor executed the correct SQL
        self.mock_pg_cursor.execute.assert_any_call(
            "SELECT indexname FROM pg_indexes WHERE tablename = 'attractions' AND indexname = 'idx_attractions_embedding'"
        )
        
        # Verify the transaction was committed
        self.mock_pg_conn.commit.assert_called_once()

    def test_add_geospatial_columns(self):
        """Test that add_geospatial_columns adds geospatial columns to tables."""
        # Mock tables exist
        self.mock_pg_cursor.fetchone.side_effect = [
            ['attractions'],  # Table exists
            None,             # Column doesn't exist
            ['cities'],       # Table exists
            None,             # Column doesn't exist
            ['hotels'],       # Table exists
            None,             # Column doesn't exist
            ['restaurants'],  # Table exists
            None              # Column doesn't exist
        ]
        
        result = add_geospatial_columns(self.mock_pg_conn)
        self.assertTrue(result)
        
        # Verify the cursor executed the correct SQL for each table
        self.assertEqual(self.mock_pg_cursor.execute.call_count, 20)  # 8 checks + 12 operations (3 per table)
        
        # Verify the transaction was committed
        self.mock_pg_conn.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main() 