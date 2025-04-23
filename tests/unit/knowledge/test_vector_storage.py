"""
Unit tests for the vector storage methods in DatabaseManager.
"""
import os
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from src.knowledge.database import DatabaseManager, DatabaseType

# Test constants
TEST_DB_URI = "sqlite:///:memory:"
TEST_EMBEDDING = [0.1, 0.2, 0.3, 0.4, 0.5]
TEST_EMBEDDING_2 = [0.2, 0.3, 0.4, 0.5, 0.6]

class TestVectorStorage:
    """Tests for vector storage methods."""
    
    def setup_method(self):
        """Set up test database manager."""
        self.db_manager = DatabaseManager(database_uri=TEST_DB_URI)
        # Set database type to PostgreSQL for vector tests
        self.db_manager.db_type = DatabaseType.POSTGRES
    
    @patch('src.knowledge.database.DatabaseManager._check_vector_enabled')
    @patch('src.knowledge.database.DatabaseManager._table_exists')
    @patch('src.knowledge.database.DatabaseManager._postgres_column_exists')
    @patch('src.knowledge.database.DatabaseManager.execute_postgres_query')
    def test_add_vector_column(self, mock_execute_query, mock_column_exists, 
                              mock_table_exists, mock_check_vector):
        """Test adding a vector column to a table."""
        # Configure mocks
        mock_check_vector.return_value = True
        mock_table_exists.return_value = True
        
        # Test when column doesn't exist
        mock_column_exists.return_value = False
        
        result = self.db_manager.add_vector_column(
            table="attractions",
            column_name="embedding",
            vector_dimension=768
        )
        
        # Verify result
        assert result is True
        
        # Verify the ALTER TABLE was called
        assert mock_execute_query.call_count == 2
        alter_calls = [call for call in mock_execute_query.call_args_list 
                     if "ALTER TABLE" in call[0][0]]
        assert len(alter_calls) == 1
        assert "ADD COLUMN embedding vector(768)" in alter_calls[0][0][0]
        
        # Verify the CREATE INDEX was called
        index_calls = [call for call in mock_execute_query.call_args_list 
                     if "CREATE INDEX" in call[0][0]]
        assert len(index_calls) == 1
        assert "ON attractions USING ivfflat" in index_calls[0][0][0]
        
        # Test when column already exists
        mock_execute_query.reset_mock()
        mock_column_exists.return_value = True
        
        result = self.db_manager.add_vector_column(
            table="attractions",
            column_name="embedding"
        )
        
        # Verify result
        assert result is True
        
        # Verify no database calls were made
        assert mock_execute_query.call_count == 0
        
        # Test when vector extension not enabled
        mock_check_vector.return_value = False
        
        result = self.db_manager.add_vector_column(
            table="attractions",
            column_name="embedding"
        )
        
        # Verify result
        assert result is False
    
    @patch('src.knowledge.database.DatabaseManager._check_vector_enabled')
    @patch('src.knowledge.database.DatabaseManager.execute_postgres_query')
    def test_store_embedding(self, mock_execute_query, mock_check_vector):
        """Test storing an embedding vector."""
        # Configure mocks
        mock_check_vector.return_value = True
        mock_execute_query.return_value = 1  # 1 row updated
        
        result = self.db_manager.store_embedding(
            table="attractions",
            item_id="test1",
            embedding=TEST_EMBEDDING
        )
        
        # Verify result
        assert result is True
        
        # Verify query was called
        mock_execute_query.assert_called_once()
        query = mock_execute_query.call_args[0][0]
        params = mock_execute_query.call_args[0][1]
        
        # Check query
        assert "UPDATE attractions" in query
        assert "SET embedding = " in query
        assert params == ("test1",)
        
        # Test when no rows are updated
        mock_execute_query.reset_mock()
        mock_execute_query.return_value = 0  # 0 rows updated
        
        result = self.db_manager.store_embedding(
            table="attractions",
            item_id="nonexistent",
            embedding=TEST_EMBEDDING
        )
        
        # Verify result
        assert result is False
        
        # Test when vector extension not enabled
        mock_check_vector.return_value = False
        
        result = self.db_manager.store_embedding(
            table="attractions",
            item_id="test1",
            embedding=TEST_EMBEDDING
        )
        
        # Verify result
        assert result is False
    
    @patch('src.knowledge.database.DatabaseManager._check_vector_enabled')
    @patch('src.knowledge.database.DatabaseManager._get_pg_connection')
    @patch('src.knowledge.database.DatabaseManager._return_pg_connection')
    def test_batch_store_embeddings(self, mock_return_conn, mock_get_conn, mock_check_vector):
        """Test storing multiple embeddings in batch."""
        # Configure mocks
        mock_check_vector.return_value = True
        
        # Create mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        # Configure cursor rowcount for first and third items
        mock_cursor.rowcount = 1
        
        # Test batch storing
        embeddings_data = [
            {"id": "test1", "embedding": TEST_EMBEDDING},
            {"id": "test2", "embedding": TEST_EMBEDDING_2},
            {"id": "test3", "embedding": TEST_EMBEDDING}
        ]
        
        result = self.db_manager.batch_store_embeddings(
            table="attractions",
            embeddings_data=embeddings_data
        )
        
        # Verify result (should be count of successfully stored embeddings)
        assert result == 3
        
        # Verify cursor execute was called for each item
        assert mock_cursor.execute.call_count == 3
        
        # Test with invalid data
        mock_cursor.reset_mock()
        
        invalid_data = [
            {"id": "test1"},  # Missing embedding
            {"embedding": TEST_EMBEDDING}  # Missing id
        ]
        
        result = self.db_manager.batch_store_embeddings(
            table="attractions",
            embeddings_data=invalid_data
        )
        
        # Verify result
        assert result == 0
        assert mock_cursor.execute.call_count == 0
        
        # Test when vector extension not enabled
        mock_check_vector.return_value = False
        
        result = self.db_manager.batch_store_embeddings(
            table="attractions",
            embeddings_data=embeddings_data
        )
        
        # Verify result
        assert result == 0
    
    @patch('src.knowledge.database.DatabaseManager._check_vector_enabled')
    @patch('src.knowledge.database.DatabaseManager.execute_postgres_query')
    def test_get_embedding(self, mock_execute_query, mock_check_vector):
        """Test retrieving an embedding vector."""
        # Configure mocks
        mock_check_vector.return_value = True
        
        # Mock result with embedding vector
        mock_result = {"embedding": TEST_EMBEDDING}
        mock_execute_query.return_value = mock_result
        
        result = self.db_manager.get_embedding(
            table="attractions",
            item_id="test1"
        )
        
        # Verify result
        assert result == TEST_EMBEDDING
        
        # Verify query
        mock_execute_query.assert_called_once()
        query = mock_execute_query.call_args[0][0]
        params = mock_execute_query.call_args[0][1]
        
        assert "SELECT embedding" in query
        assert "FROM attractions" in query
        assert "WHERE id = %s" in query
        assert params == ("test1",)
        
        # Test when no embedding found
        mock_execute_query.reset_mock()
        mock_execute_query.return_value = None
        
        result = self.db_manager.get_embedding(
            table="attractions",
            item_id="nonexistent"
        )
        
        # Verify result
        assert result is None
        
        # Test with non-iterable result
        mock_execute_query.reset_mock()
        mock_execute_query.return_value = {"embedding": 12345}  # Non-iterable value
        
        result = self.db_manager.get_embedding(
            table="attractions",
            item_id="invalid"
        )
        
        # Verify result
        assert result is None
    
    @patch('src.knowledge.database.DatabaseManager._check_vector_enabled')
    @patch('src.knowledge.database.DatabaseManager.execute_postgres_query')
    def test_find_similar(self, mock_execute_query, mock_check_vector):
        """Test finding similar items using vector similarity."""
        # Configure mocks
        mock_check_vector.return_value = True
        
        # Mock results with similarity scores
        mock_results = [
            {
                "id": "test1",
                "name": "Test 1",
                "similarity": 0.95
            },
            {
                "id": "test2",
                "name": "Test 2",
                "similarity": 0.85
            }
        ]
        mock_execute_query.return_value = mock_results
        
        # Test finding similar items
        result = self.db_manager.find_similar(
            table="attractions",
            query_embedding=TEST_EMBEDDING,
            limit=10,
            min_similarity=0.8
        )
        
        # Verify result
        assert len(result) == 2
        assert result[0]["id"] == "test1"
        assert result[1]["id"] == "test2"
        
        # Verify query
        mock_execute_query.assert_called_once()
        query = mock_execute_query.call_args[0][0]
        params = mock_execute_query.call_args[0][1]
        
        assert "SELECT" in query
        assert "FROM attractions" in query
        assert "ORDER BY similarity DESC" in query
        assert "LIMIT %s" in query
        assert params[-1] == 10  # Limit parameter
        
        # Test with additional filters
        mock_execute_query.reset_mock()
        mock_execute_query.return_value = mock_results
        
        result = self.db_manager.find_similar(
            table="attractions",
            query_embedding=TEST_EMBEDDING,
            limit=5,
            additional_filters={"city": "Cairo"}
        )
        
        # Verify result
        assert len(result) == 2
        
        # Verify query with filters
        mock_execute_query.assert_called_once()
        query = mock_execute_query.call_args[0][0]
        params = mock_execute_query.call_args[0][1]
        
        assert "WHERE" in query
        assert "AND city = %s" in query
        assert "Cairo" in params
        assert params[-1] == 5  # Limit parameter
        
        # Test when vector extension not enabled
        mock_check_vector.return_value = False
        
        result = self.db_manager.find_similar(
            table="attractions",
            query_embedding=TEST_EMBEDDING
        )
        
        # Verify empty result
        assert result == []
    
    @patch('src.knowledge.database.DatabaseManager._check_vector_enabled')
    @patch('src.knowledge.database.DatabaseManager.execute_postgres_query')
    def test_hybrid_search(self, mock_execute_query, mock_check_vector):
        """Test hybrid search combining text and vector similarity."""
        # Configure mocks
        mock_check_vector.return_value = True
        
        # Mock results with hybrid scores
        mock_results = [
            {
                "id": "test1",
                "name": "Cairo Tower",
                "hybrid_score": 0.95
            },
            {
                "id": "test2",
                "name": "Cairo Museum",
                "hybrid_score": 0.85
            }
        ]
        mock_execute_query.return_value = mock_results
        
        # Test hybrid search
        result = self.db_manager.hybrid_search(
            table="attractions",
            query_text="Cairo",
            query_embedding=TEST_EMBEDDING,
            text_fields=["name", "description"],
            embedding_weight=0.7,
            text_weight=0.3,
            limit=5
        )
        
        # Verify result
        assert len(result) == 2
        assert result[0]["id"] == "test1"
        assert result[1]["id"] == "test2"
        
        # Verify query
        mock_execute_query.assert_called_once()
        query = mock_execute_query.call_args[0][0]
        params = mock_execute_query.call_args[0][1]
        
        assert "SELECT" in query
        assert "hybrid_score" in query
        assert "name ILIKE %s" in query
        assert "description ILIKE %s" in query
        assert "%Cairo%" in params
        assert params[-1] == 5  # Limit parameter
        
        # Check weights in query
        assert "* 0.7" in query  # embedding_weight
        assert "0.3" in query    # text_weight
        
        # Test with zero weights (should default to equal weights)
        mock_execute_query.reset_mock()
        mock_execute_query.return_value = mock_results
        
        result = self.db_manager.hybrid_search(
            table="attractions",
            query_text="Cairo",
            query_embedding=TEST_EMBEDDING,
            text_fields=["name"],
            embedding_weight=0,
            text_weight=0,
            limit=5
        )
        
        # Verify equal weights were used
        query = mock_execute_query.call_args[0][0]
        assert "* 0.5" in query  # embedding_weight
        assert "0.5" in query    # text_weight
        
        # Test when vector extension not enabled
        mock_check_vector.return_value = False
        
        result = self.db_manager.hybrid_search(
            table="attractions",
            query_text="Cairo",
            query_embedding=TEST_EMBEDDING,
            text_fields=["name"],
            limit=5
        )
        
        # Verify empty result
        assert result == [] 