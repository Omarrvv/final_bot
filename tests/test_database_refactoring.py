"""
Test module for database refactoring.

This module contains tests for the refactored database components.
"""
import os
import unittest
from unittest.mock import patch, MagicMock, Mock

from src.knowledge.database_core import DatabaseCore
from src.knowledge.database_factory import DatabaseFactory
from src.knowledge.transaction_manager import TransactionManager
from src.repositories.base_repository import BaseRepository
from src.repositories.attraction_repository import AttractionRepository
from src.knowledge.database_manager_new import DatabaseManager

# Mock modules to avoid import errors
import sys
sys.modules['src.knowledge.vector_tiered_cache'] = MagicMock()
sys.modules['src.utils.query_cache'] = MagicMock()
sys.modules['src.utils.query_monitor'] = MagicMock()
sys.modules['src.utils.query_analyzer'] = MagicMock()
sys.modules['src.utils.query_batch'] = MagicMock()
sys.modules['src.services.service_registry'] = MagicMock()
sys.modules['src.knowledge.database_init'] = MagicMock()

class TestDatabaseCore(unittest.TestCase):
    """Test cases for the DatabaseCore class."""

    @patch('src.knowledge.database_core.psycopg2.connect')
    @patch('src.knowledge.database_core.psycopg2.pool.ThreadedConnectionPool')
    def test_initialization(self, mock_pool, mock_connect):
        """Test initialization of DatabaseCore."""
        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [False]  # Mock superuser check
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock pool
        mock_pool_instance = MagicMock()
        mock_pool_instance._pool = True  # For is_connected check
        mock_pool.return_value = mock_pool_instance

        # Create DatabaseCore instance
        db_core = DatabaseCore("postgresql://user:password@localhost:5432/testdb")

        # Verify connection was attempted
        mock_connect.assert_called_once_with("postgresql://user:password@localhost:5432/testdb")

        # Verify pool was created
        self.assertTrue(mock_pool.called)

        # Verify is_connected returns True
        self.assertTrue(db_core.is_connected())

    def test_execute_query(self):
        """Test execute_query method."""
        # Mock DatabaseCore
        db_core = MagicMock()

        # Mock execute_query
        expected_result = [{"id": 1, "name": "Test"}]
        db_core.execute_query.return_value = expected_result

        # Call execute_query
        result = db_core.execute_query("SELECT * FROM test", ("param",))

        # Verify execute_query was called
        db_core.execute_query.assert_called_once_with("SELECT * FROM test", ("param",))

        # Verify result
        self.assertEqual(result, expected_result)

class TestBaseRepository(unittest.TestCase):
    """Test cases for the BaseRepository class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock DatabaseCore
        self.mock_db_core = MagicMock()

        # Create BaseRepository instance
        self.repo = BaseRepository(self.mock_db_core, "test_table", ["name", "description"])

    def test_get_by_id(self):
        """Test get_by_id method."""
        # Mock execute_query
        expected_result = {"id": "123", "name": '{"en": "Test"}', "description": '{"en": "Test Description"}'}
        self.mock_db_core.execute_query.return_value = expected_result

        # Call get_by_id
        result = self.repo.get_by_id("123")

        # Verify execute_query was called
        self.mock_db_core.execute_query.assert_called_once_with(
            "SELECT * FROM test_table WHERE id = %s",
            ("123",),
            fetchall=False
        )

        # Verify result
        self.assertEqual(result, expected_result)

    def test_find(self):
        """Test find method."""
        # Mock execute_query
        expected_results = [
            {"id": "123", "name": '{"en": "Test"}', "description": '{"en": "Test Description"}'},
            {"id": "456", "name": '{"en": "Test 2"}', "description": '{"en": "Test Description 2"}'}
        ]
        self.mock_db_core.execute_query.return_value = expected_results

        # Call find
        results = self.repo.find({"type": "test"}, limit=10, offset=0)

        # Verify execute_query was called
        self.mock_db_core.execute_query.assert_called_once()

        # Verify results
        self.assertEqual(results, expected_results)

class TestAttractionRepository(unittest.TestCase):
    """Test cases for the AttractionRepository class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock DatabaseCore
        self.mock_db_core = MagicMock()

        # Create AttractionRepository instance
        self.repo = AttractionRepository(self.mock_db_core)

    def test_find_by_type(self):
        """Test find_by_type method."""
        # Mock find
        expected_results = [{"id": "123", "name": "Test", "type_id": "monument"}]
        self.repo.find = MagicMock(return_value=expected_results)

        # Call find_by_type
        results = self.repo.find_by_type("monument")

        # Verify find was called
        self.repo.find.assert_called_once_with(filters={"type_id": "monument"}, limit=10, offset=0)

        # Verify results
        self.assertEqual(results, expected_results)

    def test_search_attractions(self):
        """Test search_attractions method."""
        # Mock execute_query
        expected_results = [{"id": "123", "name": "Test", "type_id": "monument"}]
        self.mock_db_core.execute_query.return_value = expected_results

        # Call search_attractions
        results = self.repo.search_attractions(query="pyramid", type_id="monument")

        # Verify execute_query was called
        self.mock_db_core.execute_query.assert_called_once()

        # Verify results
        self.assertEqual(results, expected_results)

@patch('src.knowledge.database_manager_new.VectorTieredCache')
@patch('src.knowledge.database_manager_new.QueryCache')
@patch('src.knowledge.database_manager_new.DatabaseFactory')
class TestDatabaseManager(unittest.TestCase):
    """Test cases for the DatabaseManager class."""

    def test_initialization(self, mock_factory_class, mock_query_cache_class, mock_vector_cache_class):
        """Test initialization of DatabaseManager."""
        # Mock factory
        mock_factory = MagicMock()
        mock_factory_class.return_value = mock_factory

        # Mock db_core
        mock_db_core = MagicMock()
        mock_factory.get_db_core.return_value = mock_db_core

        # Mock transaction_manager
        mock_transaction_manager = MagicMock()
        mock_factory.get_transaction_manager.return_value = mock_transaction_manager

        # Mock caches
        mock_query_cache = MagicMock()
        mock_query_cache_class.return_value = mock_query_cache
        mock_vector_cache = MagicMock()
        mock_vector_cache_class.return_value = mock_vector_cache

        # Mock _initialize_database
        with patch.object(DatabaseManager, '_initialize_database') as mock_init_db:
            # Create DatabaseManager instance
            db_manager = DatabaseManager("postgresql://user:password@localhost:5432/testdb")

            # Verify factory was created
            mock_factory_class.assert_called_once_with("postgresql://user:password@localhost:5432/testdb")

            # Verify db_core was retrieved
            mock_factory.get_db_core.assert_called_once()

            # Verify transaction_manager was retrieved
            mock_factory.get_transaction_manager.assert_called_once()

            # Verify _initialize_database was called
            mock_init_db.assert_called_once()

    def test_get_attraction(self, mock_factory_class, mock_query_cache_class, mock_vector_cache_class):
        """Test get_attraction method."""
        # Mock factory
        mock_factory = MagicMock()
        mock_factory_class.return_value = mock_factory

        # Mock db_core
        mock_db_core = MagicMock()
        mock_factory.get_db_core.return_value = mock_db_core

        # Mock transaction_manager
        mock_transaction_manager = MagicMock()
        mock_factory.get_transaction_manager.return_value = mock_transaction_manager

        # Mock attraction repository
        mock_repo = MagicMock()
        mock_factory.get_repository.return_value = mock_repo

        # Mock get_by_id
        expected_result = {"id": "123", "name": "Test Pyramid"}
        mock_repo.get_by_id.return_value = expected_result

        # Mock caches
        mock_query_cache = MagicMock()
        mock_query_cache.get_record.return_value = None  # Cache miss
        mock_query_cache_class.return_value = mock_query_cache
        mock_vector_cache = MagicMock()
        mock_vector_cache_class.return_value = mock_vector_cache

        # Mock _initialize_database
        with patch.object(DatabaseManager, '_initialize_database'):
            # Create DatabaseManager instance
            db_manager = DatabaseManager("postgresql://user:password@localhost:5432/testdb")

            # Call get_attraction
            result = db_manager.get_attraction("123")

            # Verify get_repository was called with AttractionRepository
            mock_factory.get_repository.assert_called_once_with(AttractionRepository)

            # Verify get_by_id was called
            mock_repo.get_by_id.assert_called_once_with("123")

            # Verify result
            self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()
